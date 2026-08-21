# -*- coding: utf-8 -*-
"""
================================================================================
⭐ 七星高照 ETF 动量轮动策略 - 企业微信推送引擎 (精准日期与时序节点版)
================================================================================
核心规范：
  1. 交易时间节点全带日期：(YYYY-MM-DD HH:MM 尾盘确认)
  2. 持仓天数与盈亏透视：明确标注【已持仓 X 个交易日】与【盈利/亏损 XX 元 (+XX.XX%)】
  3. 极简专业卡片：突出 🔴卖出/🟢买入/🛡️续持 与 盈亏安全垫
  4. 动量榜 Top3：仅保留前 3 名核心有效梯队，折叠无效与深跌标的
  5. 防重复推送拦截（Idempotent Lock）：按 [交易日_阶段] 去重，严防重复打扰
  6. 统一真实状态源：杜绝收盘后推送冲突数据
================================================================================
"""

import os
import sys
import json
import time
import hashlib
import requests
from datetime import datetime

# 七星策略企业微信 Webhook 专用地址
DEFAULT_QIXING_WEBHOOK = os.environ.get(
    'QIXING_WECOM_WEBHOOK',
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=46012c55-7fd0-4060-baa8-fc110bb3ca5d"
)

QIXING_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".qixing_push_cache.json")


class QiXingWeComNotifier:
    """七星 ETF 动量轮动策略企业微信通知器"""

    def __init__(self, webhook_url: str = DEFAULT_QIXING_WEBHOOK, cache_path: str = QIXING_CACHE_FILE):
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
            print(f"[!] 七星缓存写入异常: {e}")

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
        stage: str,               # 如 "14:48 尾盘确认"
        action_type: str,         # "HOLD" (继续持有最强龙头) 或 "TRANSFER" (触发调仓换标)
        total_asset: float,       # 账户总资产 (如 82617.28)
        position_pct: float,      # 仓位百分比 (如 99.1)
        current_pos: dict,        # 持仓字典
        target_buy: dict = None,  # 买入字典 (TRANSFER时提供)
        top_candidates: list = None, # 动量打分前3名
        timeline: list = None,    # 当日时序全景
        special_reason: str = None # 特殊情况说明
    ) -> str:
        """渲染带精准日期、专业清爽的七星策略 Markdown 格式"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # 确保 stage 带有完整日期
        if not stage.startswith("20"):
            full_stage = f"{today_str} {stage}"
        else:
            full_stage = stage

        pnl_val = current_pos.get('pnl_amount', 0.0)
        pnl_pct = current_pos.get('pnl_pct', 0.0)
        hold_days = current_pos.get('holding_days', current_pos.get('days', 1))
        buy_date_str = f" (建仓日: {current_pos['buy_date']})" if 'buy_date' in current_pos else ""
        
        if pnl_val >= 0:
            pnl_tag = f"🔴 **盈利 +¥{pnl_val:,.2f} 元 (+{pnl_pct:.2f}%)**"
            pnl_color_txt = f"<font color=\"warning\">**盈利 +¥{pnl_val:,.2f} 元 (+{pnl_pct:.2f}%)**</font>"
        else:
            pnl_tag = f"🟢 **亏损 -¥{abs(pnl_val):,.2f} 元 ({pnl_pct:.2f}%)**"
            pnl_color_txt = f"<font color=\"info\">**亏损 -¥{abs(pnl_val):,.2f} 元 ({pnl_pct:.2f}%)**</font>"

        # 动量榜 Top3 精简与过滤标记
        medals = ["🥇", "🥈", "🥉"]
        rank_lines = []
        for i, c in enumerate((top_candidates or [])[:3]):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            trend_tag = "📈 上行趋势" if c.get('score', 0) > 0 else "📉 回调筑底"
            status = c.get('status', ('✅ 领跑' if i == 0 else '备选'))
            rank_lines.append(f"{i+1}. {medal} **{c['name']} ({c['code']})**: 得分 `{c['score']:.3f}` ({trend_tag} | {status})")
        top_block = "\n".join(rank_lines) if rank_lines else "• 动量天梯榜数据更新中..."

        # 特殊情况与决策归因模块
        special_block = ""
        if special_reason:
            special_block = f"""---
### ⚠️ 【特殊情况与决策归因】
> {special_reason}
"""

        # 当日时序节点 (全部带有完整日期)
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
                {"time": f"{today_str} 09:30", "desc": "开盘监控 (跨板块7大主题ETF动量扫描)"},
                {"time": f"{today_str} 14:40", "desc": "尾盘动量终测 (原版公式斜率与波动率平价测算)"},
                {"time": f"{today_str} 14:47", "desc": "卖出执行 (清退动量衰减标的)" if action_type == 'TRANSFER' else "动量校验 (龙头优势稳固，无需卖出)"},
                {"time": f"{today_str} 14:48", "desc": f"买入建仓 ({target_buy['name']})" if action_type == 'TRANSFER' and target_buy else "续持确认 (持仓标的吃满波段)"},
                {"time": f"{today_str} 15:02", "desc": "收盘归档与账户资产净值结算"}
            ]
            for t in default_timeline:
                timeline_lines.append(f"• `⏰ {t['time']}` {t['desc']}")
        timeline_block = "\n".join(timeline_lines)

        if action_type == "TRANSFER" and target_buy:
            markdown = f"""# 🔔 七星量化 调仓换标报告 ({full_stage})
> 💰 **账户总资产**：¥{total_asset:,.2f} 元 (仓位: {position_pct:.1f}%) | 策略：⭐ **七星跨板块轮动**

### 🎯 【今日执行指令】(按时间节点)
🔴 **卖出** [{today_str} 14:47]：`{current_pos['code']}` {current_pos['name']} · **{current_pos.get('amount', 0):,}股** (清仓)
   └ 结算：已持仓 {hold_days} 日 | 成本 ¥{current_pos['cost']:.3f} ➔ 现价 ¥{current_pos['price']:.3f} | {pnl_color_txt}

🟢 **买入** [{today_str} 14:48]：`{target_buy['code']}` {target_buy['name']} · **约 {target_buy.get('amount', 0):,}股**
   └ 挂单：参考价 **¥{target_buy['price']:.3f}** (动量得分 `{target_buy.get('score', 0):.3f}`)

---
### 📈 【今日动量天梯榜 Top3】
{top_block}
{special_block}
---
### ⏱️ 【当日时序节点全景】
{timeline_block}

> 💡 *风控防线：止损线 ¥{current_pos.get('stop_price', 0):.3f} (距 5% 硬止损尚有 {current_pos.get('cushion_pct', 0):+.2f}% 安全垫)*
"""
        else:
            leader_score = current_pos.get('score', 0.050)
            markdown = f"""# 🛡️ 七星量化 持仓与动量报告 ({full_stage})
> 💰 **账户总资产**：¥{total_asset:,.2f} 元 (仓位: {position_pct:.1f}%) | 状态：<font color="info">**【继续持有最强龙头】**</font>

### 📦 【当前持仓与实时盈亏】
• **当前标的**：`{current_pos['code']}` **{current_pos['name']}**
• **持仓规模**：{current_pos.get('amount', 0):,} 股 (市值 ¥{current_pos.get('market_val', 0):,.2f} 元)
• **持仓历时**：已持仓 **{hold_days}** 个交易日{buy_date_str}
• **成本/现价**：¥{current_pos['cost']:.3f} ➔ ¥{current_pos['price']:.3f}
• **盈亏状态**：{pnl_tag}
• **龙头优势**：动量分 `{leader_score:.3f}` (有效动量领跑，继续持有吃满主升浪)

---
### 📈 【今日动量天梯榜 Top3】
{top_block}
{special_block}
---
### ⏱️ 【当日时序节点全景】
{timeline_block}

> 💡 *风控提示：建议在每个交易日 {today_str} 14:47 卖出、{today_str} 14:48 买入执行 (止损线 ¥{current_pos.get('stop_price', 0):.3f} · 安全垫 {current_pos.get('cushion_pct', 0):+.2f}%)*
"""
        return markdown.strip()

    def send_notification(
        self,
        stage: str,
        action_type: str,
        total_asset: float,
        position_pct: float,
        current_pos: dict,
        target_buy: dict = None,
        top_candidates: list = None,
        timeline: list = None,
        special_reason: str = None,
        force: bool = False
    ) -> bool:
        push_key = f"QIXING_{stage.split()[-2] if len(stage.split())>=2 else stage}_{action_type}"

        if not force and self._is_duplicate(push_key):
            print(f"[i] [七星量化] 今日阶段 [{stage}] 已经推送过，防重复机制已拦截。")
            return True

        markdown_body = self.format_report(
            stage=stage,
            action_type=action_type,
            total_asset=total_asset,
            position_pct=position_pct,
            current_pos=current_pos,
            target_buy=target_buy,
            top_candidates=top_candidates,
            timeline=timeline,
            special_reason=special_reason
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
                print(f"[+] [七星量化·企业微信] 推送成功 ({stage})！")
                self._record_push(push_key, content_hash)
                return True
            else:
                print(f"[-] [七星量化·企业微信] 推送失败: {res_json.get('errcode')} - {res_json.get('errmsg')}")
                return False
        except Exception as e:
            print(f"[-] [七星量化·企业微信] 网络异常: {e}")
            return False


if __name__ == '__main__':
    notifier = QiXingWeComNotifier()
    today_str = datetime.now().strftime("%Y-%m-%d")

    sample_current_pos = {
        'code': '518880',
        'name': '华安黄金ETF',
        'amount': 9124,
        'market_val': 81842.28,
        'cost': 8.950,
        'price': 8.970,
        'pnl_amount': 182.48,
        'pnl_pct': 0.22,
        'holding_days': 5,
        'buy_date': '2026-08-14',
        'stop_price': 8.502,
        'cushion_pct': 5.21
    }

    sample_top = [
        {'name': '南方原油LOF', 'code': '501018', 'score': 0.080, 'status': '❌ 溢价熔断(溢价率>20%)'},
        {'name': '华安黄金ETF', 'code': '518880', 'score': 0.050, 'status': '✅ 顺延领跑(现持仓)'},
        {'name': '华夏豆粕ETF', 'code': '159985', 'score': 0.026, 'status': '备选'},
    ]

    sample_special_reason = """• **为什么未买入榜首【南方原油LOF (501018)】？**
  - **触发风控**：501018 触发了 QDII/LOF **高溢价率熔断机制** (二级市场溢价率已超风控阈值 20%)，策略主动规避高位接盘杀溢价的踩踏风险；
  - **执行决策**：根据策略风控规则，自动顺延由有效标的第 1 名 **华安黄金ETF (518880)** 接管，继续持有吃满主升浪！"""

    print(">>> 正在向企业微信发送【七星量化·带精准日期】实测报告...")
    notifier.send_notification(
        stage=f"{today_str} 14:48 尾盘确认",
        action_type="HOLD",
        total_asset=82617.28,
        position_pct=99.1,
        current_pos=sample_current_pos,
        top_candidates=sample_top,
        special_reason=sample_special_reason,
        force=True
    )
