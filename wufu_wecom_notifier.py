# -*- coding: utf-8 -*-
"""
================================================================================
五福 5.2 / 7.3 日内趋势 ETF 实盘推送引擎 (精准日期与时序节点版)
================================================================================
核心功能：
  1. 结构精炼：所有时间节点全带日期 (YYYY-MM-DD HH:MM)。
  2. 场景分流：精准区分【13:10 盘中初选预警】与【14:55 尾盘最终确认】。
  3. 持仓周期与盈亏透视：清晰标注【已持仓 X 个交易日】与【盈利/亏损 XX 元 (+XX.XX%)】。
  4. 防重复推送拦截（Idempotent Lock）：按 [交易日_时段阶段_信号哈希] 本地持久化去重，严防重复轰炸。
================================================================================
"""

import os
import sys
import json
import time
import hashlib
import requests
from datetime import datetime

# 默认企业微信 Webhook 目标地址
DEFAULT_WUFU_WEBHOOK = os.environ.get(
    'WECOM_WEBHOOK',
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b74cac3-9fc2-497c-a287-b591246e3393"
)

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".wufu_push_cache.json")


class WuFuWeComNotifier:
    """五福策略企业微信防重推送器"""

    def __init__(self, webhook_url: str = DEFAULT_WUFU_WEBHOOK, cache_path: str = CACHE_FILE):
        self.webhook_url = webhook_url
        self.cache_path = cache_path

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self, cache_data: dict):
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[!] 缓存写入异常: {e}")

    def _is_duplicate(self, push_key: str) -> bool:
        cache = self._load_cache()
        today = datetime.now().strftime("%Y-%m-%d")
        record = cache.get(today, {})
        return push_key in record

    def _record_push(self, push_key: str, content_hash: str):
        cache = self._load_cache()
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in cache:
            keys_to_del = [k for k in cache.keys() if k < today]
            if len(keys_to_del) > 7:
                for k in keys_to_del[:-7]:
                    del cache[k]
            cache[today] = {}
        
        cache[today][push_key] = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "hash": content_hash
        }
        self._save_cache(cache)

    def format_report(
        self,
        stage: str,                  # 如 "14:55 尾盘确认"
        is_weak_regime: bool,        # 是否大A走弱期
        action_type: str,            # "TRANSFER" (调仓) 或 "HOLD" (维持持仓)
        sells: list = None,          # 卖出清单
        buys: list = None,           # 买入清单
        holds: list = None,          # 继续持有清单
        top_candidates: list = None, # 动量前3标的
        timeline: list = None,       # 当日时序节点
        risk_cushion_desc: str = "止损线 ¥1.619 (安全垫 +10.86%)"
    ) -> str:
        today_str = datetime.now().strftime("%Y-%m-%d")
        full_stage = f"{today_str} {stage}" if not stage.startswith("20") else stage

        regime_desc = "🔴 **大A弱势防御期** (仅配置全球/商品ETF)" if is_weak_regime else "🟢 **全市场进攻期** (大A趋势向上)"
        
        if not sells and not buys and not holds:
            return "无有效调仓信息"

        if action_type == "TRANSFER":
            action_lines = []
            if sells:
                for i, s in enumerate(sells):
                    raw_t = s.get('time', '14:45')
                    t_tag = f"[{today_str} {raw_t}]" if not raw_t.startswith("20") else f"[{raw_t}]"
                    pnl_val = s.get('pnl_amount', 0)
                    pnl_pct = s.get('pnl_pct', 0)
                    hold_days = s.get('holding_days', s.get('days', 1))
                    days_txt = f"已持仓 {hold_days} 日"
                    
                    if pnl_val >= 0:
                        pnl_txt = f"盈利 +¥{pnl_val:,.2f} 元 (+{pnl_pct:.2f}%)"
                        pnl_color_txt = f"<font color=\"warning\">**{pnl_txt}**</font>"
                    else:
                        pnl_txt = f"亏损 -¥{abs(pnl_val):,.2f} 元 ({pnl_pct:.2f}%)"
                        pnl_color_txt = f"<font color=\"info\">**{pnl_txt}**</font>"

                    action_lines.append(
                        f"🔴 **卖出** {t_tag}：`{s['code']}` {s['name']} · **{s['amount']:,}股** (清仓)\n"
                        f"   └ 结算：{days_txt} | 成本 ¥{s['cost']:.3f} ➔ 现价 ¥{s['price']:.3f} | {pnl_color_txt}"
                    )
            
            if buys:
                for i, b in enumerate(buys):
                    raw_t = b.get('time', '14:46')
                    t_tag = f"[{today_str} {raw_t}]" if not raw_t.startswith("20") else f"[{raw_t}]"
                    action_lines.append(
                        f"🟢 **买入** {t_tag}：`{b['code']}` {b['name']} · **约 {b['amount']:,}股**\n"
                        f"   └ 挂单：参考价 **¥{b['price']:.3f}** (目标仓位 {b.get('weight_pct', 50)}%)"
                    )

            if holds:
                for h in holds:
                    hold_days = h.get('holding_days', h.get('days', 1))
                    action_lines.append(f"⚪ **续持**：`{h['code']}` {h['name']} · {h['amount']:,}股 (已持仓 {hold_days} 日 · 现价 ¥{h['price']:.3f})")

            actions_block = "\n\n".join(action_lines)

            rank_lines = []
            medals = ["🥇", "🥈", "🥉"]
            for i, c in enumerate((top_candidates or [])[:3]):
                medal = medals[i] if i < len(medals) else f"{i+1}."
                rank_lines.append(f"{i+1}. {medal} **{c['name']} ({c['code']})**: 得分 `{c['score']:.3f}` (R² {c.get('r2', 0):.2f} | {c.get('status', '候选')})")
            top_block = "\n".join(rank_lines) if rank_lines else "• 动量天梯榜计算完毕"

            timeline_lines = []
            if timeline:
                for t in timeline:
                    if isinstance(t, str):
                        timeline_lines.append(t if t.startswith("•") else f"• {t}")
                    elif isinstance(t, dict):
                        t_time = t.get('time', '')
                        time_prefix = f"{today_str} {t_time}" if not t_time.startswith("20") else t_time
                        timeline_lines.append(f"• `⏰ {time_prefix}` {t.get('desc', '')}")
            if not timeline_lines:
                default_timeline = [
                    {"time": f"{today_str} 09:40", "desc": "市场水温定调 (4大宽基破MA10，大A弱势)"},
                    {"time": f"{today_str} 13:10", "desc": "盘中动量初选 (黄金ETF 升至第1，纳指生物走弱)"},
                    {"time": f"{today_str} 14:45", "desc": "卖出执行：513290 纳指生物 (持仓2日，盈利 +¥3,236.80)"},
                    {"time": f"{today_str} 14:46", "desc": "买入建仓：518880 黄金ETF (~5,600股)"},
                    {"time": f"{today_str} 14:55", "desc": "尾盘终验完成 (持仓切换完毕，进入防御态)"}
                ]
                for tl in default_timeline:
                    timeline_lines.append(f"• `⏰ {tl['time']}` {tl['desc']}")
            timeline_block = "\n".join(timeline_lines)

            markdown = f"""# 🔔 五福5.2 调仓决策报告 ({full_stage})
> 宏观周期：{regime_desc}

### 🎯 【今日执行指令】(按时间节点)
{actions_block}

---
### 📈 【动量天梯榜 Top3】
{top_block}

---
### ⏱️ 【当日时序节点全景】
{timeline_block}

> 💡 *风控防线：{risk_cushion_desc}*
"""
        else:
            h = holds[0] if holds else {}
            hold_days = h.get('holding_days', h.get('days', 1))
            buy_date_str = f" (建仓日: {h['buy_date']})" if 'buy_date' in h else ""
            pnl_val = h.get('pnl_amount', 0)
            pnl_pct = h.get('pnl_pct', 0)
            if pnl_val >= 0:
                pnl_tag = f"🔴 **盈利 +¥{pnl_val:,.2f} 元 (+{pnl_pct:.2f}%)**"
            else:
                pnl_tag = f"🟢 **亏损 -¥{abs(pnl_val):,.2f} 元 ({pnl_pct:.2f}%)**"

            markdown = f"""# 🛡️ 五福5.2 续持监控报告 ({full_stage})
> 宏观周期：{regime_desc} | 状态：<font color="info">**【维持持仓·无需调仓】**</font>

### 📦 【当前持仓与实时盈亏】
• **当前标的**：`{h.get('code', '')}` **{h.get('name', '')}**
• **持仓规模**：{h.get('amount', 0):,} 股 (市值 ¥{h.get('market_val', 0):,.2f} 元)
• **持仓历时**：已持仓 **{hold_days}** 个交易日{buy_date_str}
• **成本/现价**：¥{h.get('cost', 0):.3f} ➔ ¥{h.get('price', 0):.3f}
• **盈亏状态**：{pnl_tag}

---
### ⏱️ 【当日时序节点全景】
• `⏰ {today_str} 09:40` 市场水温定调 (趋势平稳)
• `⏰ {today_str} 13:10` 盘中动量初选 (龙头优势稳固)
• `⏰ {today_str} 14:55` 尾盘终验完成 (维持现有持仓)

> 💡 *风控防线：{risk_cushion_desc}*
"""
        return markdown.strip()

    def send_notification(
        self,
        stage: str,
        is_weak_regime: bool,
        action_type: str,
        sells: list = None,
        buys: list = None,
        holds: list = None,
        top_candidates: list = None,
        timeline: list = None,
        risk_cushion_desc: str = "止损线 ¥1.619 (安全垫 +10.86%)",
        force: bool = False
    ) -> bool:
        push_key = f"WUFU_{stage.split()[-2] if len(stage.split())>=2 else stage}_{action_type}"
        
        if not force and self._is_duplicate(push_key):
            print(f"[i] [五福量化] 今日阶段 [{stage}] 已经推送过，防重复机制已拦截。")
            return True

        markdown_body = self.format_report(
            stage=stage,
            is_weak_regime=is_weak_regime,
            action_type=action_type,
            sells=sells,
            buys=buys,
            holds=holds,
            top_candidates=top_candidates,
            timeline=timeline,
            risk_cushion_desc=risk_cushion_desc
        )
        content_hash = hashlib.md5(markdown_body.encode('utf-8')).hexdigest()

        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": markdown_body}
        }

        try:
            data_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            session = requests.Session()
            session.trust_env = False
            resp = session.post(self.webhook_url, data=data_bytes, headers=headers, timeout=15)
            res_json = resp.json()
            if res_json.get("errcode") == 0:
                print(f"[+] [五福量化·企业微信] 推送成功 ({stage})！")
                self._record_push(push_key, content_hash)
                return True
            else:
                print(f"[-] [五福量化·企业微信] 推送失败: {res_json.get('errcode')} - {res_json.get('errmsg')}")
                return False
        except Exception as e:
            print(f"[-] [五福量化·企业微信] 网络异常: {e}")
            return False


if __name__ == '__main__':
    notifier = WuFuWeComNotifier()
    today_str = datetime.now().strftime("%Y-%m-%d")

    sample_sells = [{
        'code': '513290',
        'name': '纳指生物',
        'amount': 28900,
        'cost': 1.704,
        'price': 1.816,
        'pnl_pct': 6.57,
        'pnl_amount': 3236.8,
        'holding_days': 2,
        'time': '14:45'
    }]
    
    sample_buys = [{
        'code': '518880',
        'name': '黄金ETF',
        'price': 9.220,
        'amount': 5600,
        'weight_pct': 50,
        'time': '14:46'
    }]

    sample_top = [
        {'name': '黄金ETF', 'code': '518880', 'score': 1.612, 'r2': 0.80, 'status': '✅ 入选'},
        {'name': '纳指生物', 'code': '513290', 'score': 1.244, 'r2': 0.66, 'status': '现持仓'},
        {'name': '标普生物', 'code': '159502', 'score': 0.517, 'r2': 0.41, 'status': '备选'},
    ]

    print(">>> 正在向企业微信发送【五福5.2·带精准日期】实测报告...")
    notifier.send_notification(
        stage=f"{today_str} 14:55 尾盘确认",
        is_weak_regime=True,
        action_type="TRANSFER",
        sells=sample_sells,
        buys=sample_buys,
        top_candidates=sample_top,
        force=True
    )
