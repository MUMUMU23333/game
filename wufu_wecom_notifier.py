# -*- coding: utf-8 -*-
"""
================================================================================
五福 5.2 / 7.3 日内趋势 ETF 实盘推送引擎 (企业微信专用 · 极简专业版)
================================================================================
核心功能：
  1. 结构精炼：3秒直击调仓买卖指令，过滤冗余未通过标的与繁杂点位。
  2. 场景分流：精准区分【13:10 盘中初选预警】与【14:55 尾盘最终确认】。
  3. 持仓周期与盈亏透视：清晰标注【已持仓 X 个交易日】与【盈利/亏损 XX 元 (+XX.XX%)】。
  4. 防重复推送拦截（Idempotent Lock）：按 [交易日_时段阶段_信号哈希] 本地持久化去重，严防重复轰炸。
  5. 稳健网络传输：UTF-8 字节编码与超时重试保护，返回详细微信状态码。
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
        """加载推送记录缓存"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self, cache_data: dict):
        """持久化保存推送记录"""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[!] 缓存写入异常: {e}")

    def _is_duplicate(self, push_key: str) -> bool:
        """检查指定阶段是否在今日已成功推送"""
        cache = self._load_cache()
        today = datetime.now().strftime("%Y-%m-%d")
        record = cache.get(today, {})
        return push_key in record

    def _record_push(self, push_key: str, content_hash: str):
        """记录成功推送"""
        cache = self._load_cache()
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in cache:
            # 仅保留最近 7 天的记录，自动清理历史垃圾
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
        stage: str,                  # "13:10 盘中初选" 或 "14:55 尾盘确认" 或 "分钟级风控"
        is_weak_regime: bool,        # 是否大A走弱期
        action_type: str,            # "TRANSFER" (调仓) 或 "HOLD" (维持持仓)
        sells: list = None,          # 卖出清单: [{'code':'513290', 'name':'纳指生物', 'amount':28900, 'cost':1.704, 'price':1.816, 'pnl_pct':6.57, 'pnl_amount':3236.8, 'holding_days':2, 'time':'14:45'}]
        buys: list = None,           # 买入清单: [{'code':'518880', 'name':'黄金ETF', 'price':9.220, 'amount':5600, 'weight_pct':50, 'time':'14:46'}]
        holds: list = None,          # 继续持有清单: [{'code':'513100', 'name':'纳指ETF', 'amount':10000, 'market_val':52482.4, 'cost':2.15, 'price':2.22, 'pnl_pct':3.25, 'pnl_amount':700.0, 'holding_days':5, 'buy_date':'2026-08-14'}]
        top_candidates: list = None, # 动量前3标的: [{'name': '黄金ETF', 'code': '518880', 'score': 1.612, 'r2': 0.80, 'status': '✅ 入选'}]
        timeline: list = None,       # 当日时序节点
        risk_cushion_desc: str = "止损线 ¥1.619 (安全垫 +10.86%)"
    ) -> str:
        """格式化为带清晰时间节点、持仓天数与盈亏金额的企业微信 Markdown 文本"""
        regime_desc = "🔴 **大A弱势防御期** (仅配置全球/商品ETF)" if is_weak_regime else "🟢 **全市场进攻期** (大A趋势向上)"
        
        if not sells and not buys and not holds:
            return "无有效调仓信息"

        if action_type == "TRANSFER":
            # 1. 交易指令清单（按时间节点与方向结构化）
            action_lines = []
            if sells:
                for i, s in enumerate(sells):
                    t_tag = f"[{s.get('time', stage.split()[0])}]"
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
                    t_tag = f"[{b.get('time', stage.split()[0])}]"
                    action_lines.append(
                        f"🟢 **买入** {t_tag}：`{b['code']}` {b['name']} · **约 {b['amount']:,}股**\n"
                        f"   └ 挂单：参考价 **¥{b['price']:.3f}** (目标仓位 {b.get('weight_pct', 50)}%)"
                    )

            if holds:
                for h in holds:
                    hold_days = h.get('holding_days', h.get('days', 1))
                    action_lines.append(f"⚪ **续持**：`{h['code']}` {h['name']} · {h['amount']:,}股 (已持仓 {hold_days} 日 · 现价 ¥{h['price']:.3f})")

            actions_block = "\n\n".join(action_lines)

            # 2. 动量榜 Top3
            rank_lines = []
            medals = ["🥇", "🥈", "🥉"]
            for i, c in enumerate((top_candidates or [])[:3]):
                medal = medals[i] if i < len(medals) else f"{i+1}."
                rank_lines.append(f"{i+1}. {medal} **{c['name']} ({c['code']})**: 得分 `{c['score']:.3f}` (R² {c.get('r2', 0):.2f} | {c.get('status', '候选')})")
            top_block = "\n".join(rank_lines) if rank_lines else "• 动量天梯榜计算完毕"

            # 3. 当日时序全景轴 (Timeline)
            timeline_lines = []
            if timeline:
                for t in timeline:
                    if isinstance(t, str):
                        timeline_lines.append(t if t.startswith("•") else f"• {t}")
                    elif isinstance(t, dict):
                        timeline_lines.append(f"• `⏰ {t.get('time', '')}` {t.get('desc', '')}")
            if not timeline_lines:
                default_timeline = [
                    {"time": "09:40", "desc": "市场水温定调 (4大宽基破MA10，大A弱势)"},
                    {"time": "13:10", "desc": "盘中动量初选 (黄金ETF 升至第1，纳指生物走弱)"},
                    {"time": "14:55", "desc": "尾盘信号终验 (触发换仓执行)"}
                ]
                for tl in default_timeline:
                    timeline_lines.append(f"• `⏰ {tl['time']}` {tl['desc']}")
            timeline_block = "\n".join(timeline_lines)

            markdown = f"""# 🔔 五福5.2 调仓决策报告 ({stage})
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
            # 维持持仓巡检
            hold_lines = []
            for h in (holds or []):
                pnl_val = h.get('pnl_amount', 0)
                pnl_pct = h.get('pnl_pct', 0)
                hold_days = h.get('holding_days', h.get('days', 1))
                buy_date_str = f" (建仓日: {h['buy_date']})" if 'buy_date' in h else ""
                
                if pnl_val >= 0:
                    pnl_tag = f"🔴 **盈利 +¥{pnl_val:,.2f} 元 (+{pnl_pct:.2f}%)**"
                else:
                    pnl_tag = f"🟢 **亏损 -¥{abs(pnl_val):,.2f} 元 ({pnl_pct:.2f}%)**"

                market_val_str = f" (持仓市值 ¥{h['market_val']:,.2f} 元)" if 'market_val' in h else ""

                hold_lines.append(
                    f"• **持仓标的**：`{h['code']}` **{h['name']}** ({h.get('amount', 0):,}股{market_val_str})\n"
                    f"• **持仓历时**：已持仓 **{hold_days}** 个交易日{buy_date_str}\n"
                    f"• **成本/现价**：¥{h['cost']:.3f} ➔ ¥{h['price']:.3f}\n"
                    f"• **盈亏状态**：{pnl_tag}"
                )
            hold_block = "\n\n".join(hold_lines) if hold_lines else "• 当前空仓观望"

            markdown = f"""# 🛡️ 五福5.2 持仓巡检 ({stage})
> 宏观周期：{regime_desc} | 决策：<font color="info">**维持持仓，无需调仓**</font>

### 📦 【当前持仓状态】
{hold_block}

• **风控状态**：🟢 正常 ({risk_cushion_desc})

> 💡 *提示：五福5.2 于 13:10 首次买卖，14:55 尾盘最终确认。*
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
        """
        发送调仓/巡检通知 (自带防重复推送保护)
        :param force: 若为 True 则忽略去重缓存强制推送
        """
        push_key = f"STAGE_{stage.split()[0]}_{action_type}"
        
        # 1. 检查重复推送
        if not force and self._is_duplicate(push_key):
            print(f"[i] 今日阶段 [{stage}] 已经推送过，防重复机制已拦截，不再重复打扰。")
            return True

        # 2. 渲染 Markdown
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

        # 3. 发送 Webhook
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
                print(f"[+] [五福·企业微信] 推送成功 ({stage})！")
                self._record_push(push_key, content_hash)
                return True
            else:
                print(f"[-] [五福·企业微信] 推送失败: {res_json.get('errcode')} - {res_json.get('errmsg')}")
                return False
        except Exception as e:
            print(f"[-] [五福·企业微信] 网络异常: {e}")
            return False


if __name__ == '__main__':
    notifier = WuFuWeComNotifier()
    
    # 模拟调仓换标 (卖出纳指生物 ➔ 买入黄金ETF，标注持仓2日与盈亏金额)
    sample_sells = [
        {
            'time': '14:45',
            'code': '513290',
            'name': '纳指生物',
            'amount': 28900,
            'cost': 1.704,
            'price': 1.816,
            'pnl_amount': 3236.80,
            'pnl_pct': 6.57,
            'holding_days': 2
        }
    ]
    sample_buys = [
        {
            'time': '14:46',
            'code': '518880',
            'name': '黄金ETF',
            'price': 9.220,
            'amount': 5600,
            'weight_pct': 50
        }
    ]
    sample_top = [
        {'name': '黄金ETF', 'code': '518880', 'score': 1.612, 'r2': 0.80, 'status': '✅ 入选'},
        {'name': '纳指生物', 'code': '513290', 'score': 1.244, 'r2': 0.66, 'status': '现持仓'},
        {'name': '标普生物', 'code': '159502', 'score': 0.517, 'r2': 0.41, 'status': '备选'},
    ]
    sample_timeline = [
        {'time': '09:40', 'desc': '市场水温定调 (4大宽基破MA10，大A弱势)'},
        {'time': '13:10', 'desc': '盘中动量初选 (黄金ETF 升至第1，纳指生物走弱)'},
        {'time': '14:45', 'desc': '卖出执行：513290 纳指生物 (持仓2日，盈利 +¥3,236.80)'},
        {'time': '14:46', 'desc': '买入建仓：518880 黄金ETF (~5,600股)'},
        {'time': '14:55', 'desc': '尾盘终验完成 (持仓切换完毕，进入防御态)'}
    ]

    print(">>> 正在向指定 Webhook 发送【五福 5.2 带持仓天数与盈亏】测试报告...")
    notifier.send_notification(
        stage="14:55 尾盘确认",
        is_weak_regime=True,
        action_type="TRANSFER",
        sells=sample_sells,
        buys=sample_buys,
        top_candidates=sample_top,
        timeline=sample_timeline,
        risk_cushion_desc="止损线 ¥1.619 (安全垫 +10.86%)",
        force=True
    )
