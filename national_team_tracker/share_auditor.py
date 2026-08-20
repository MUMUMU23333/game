"""
T+1 交易所官方份额审计模块 (Official Share Auditor)
基于交易所公布的每日基金总份额变动 (Share Delta)，精确核算国家队真金白银净买入/净卖出金额。
"""

import os
import json
import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

from .config import ETF_UNIVERSE, SHARE_AUDIT_CONFIG
from .data_fetcher import DataFetcher


class ShareAuditor:
    """国家队份额与资金审计引擎"""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "data_cache")
        os.makedirs(self.data_dir, exist_ok=True)
        self.history_file = os.path.join(self.data_dir, "shares_history.json")
        self.fetcher = DataFetcher()

    def load_shares_history(self) -> Dict[str, Dict[str, float]]:
        """
        读取本地缓存的历史每日份额记录
        格式: { "YYYY-MM-DD": { "510300": 238.58, "510050": 69.40, ... } }
        """
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_shares_snapshot(self, date_str: str, shares_dict: Dict[str, float]):
        """保存当日份额快照"""
        history = self.load_shares_history()
        history[date_str] = shares_dict
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def audit_today_inflow(self) -> Dict[str, Any]:
        """
        审计今日/最新公布的官方份额变动与净流入资金
        """
        quotes = self.fetcher.get_realtime_quotes()
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 获取当前总份额 (单位：亿份) 与 现价
        current_shares: Dict[str, float] = {}
        for code, q in quotes.items():
            current_shares[code] = q.get("total_shares_yi", 0.0)

        # 保存今日份额快照
        self.save_shares_snapshot(today_str, current_shares)

        # 加载历史记录对比昨日份额
        history = self.load_shares_history()
        sorted_dates = sorted(list(history.keys()))
        
        prev_shares: Dict[str, float] = {}
        if len(sorted_dates) >= 2:
            prev_date = sorted_dates[-2]
            prev_shares = history.get(prev_date, {})
        else:
            prev_shares = current_shares.copy()

        audit_rows = []
        total_inflow_yi = 0.0
        category_summary = {"沪深300": 0.0, "上证50": 0.0, "中证500/1000": 0.0, "中证A500": 0.0, "双创板": 0.0}

        for code, quote in quotes.items():
            info = ETF_UNIVERSE.get(code, {})
            name = info.get("name", code)
            cat = info.get("category", "其他")
            price = quote["price"]
            curr_s = quote.get("total_shares_yi", 0.0)
            prev_s = prev_shares.get(code, curr_s)

            # 份额变动 (亿份)
            delta_shares = round(curr_s - prev_s, 4)
            # 净申购资金 = 份额变动 * 现价 (亿元)
            inflow_money = round(delta_shares * price, 2)
            total_inflow_yi += inflow_money

            # 统计各分类资金流
            if "300" in cat:
                category_summary["沪深300"] += inflow_money
            elif "50" in cat and "500" not in cat:
                category_summary["上证50"] += inflow_money
            elif "500" in cat or "1000" in cat:
                category_summary["中证500/1000"] += inflow_money
            elif "A500" in cat:
                category_summary["中证A500"] += inflow_money
            elif "科创" in cat or "创业" in cat:
                category_summary["双创板"] += inflow_money

            # 定性动作
            if inflow_money >= SHARE_AUDIT_CONFIG["HEAVY_INFLOW_THRESHOLD_YI"]:
                action = "🟢 巨额净申购 (重度增持)"
            elif inflow_money >= SHARE_AUDIT_CONFIG["MEDIUM_INFLOW_THRESHOLD_YI"]:
                action = "🟢 明显净申购 (温和增持)"
            elif inflow_money <= -SHARE_AUDIT_CONFIG["MEDIUM_INFLOW_THRESHOLD_YI"]:
                action = "🔴 明显净赎回 (主力减仓)"
            else:
                action = "⚪ 份额平稳"

            audit_rows.append({
                "code": code,
                "name": name,
                "category": cat,
                "price": price,
                "current_shares_yi": curr_s,
                "delta_shares_yi": delta_shares,
                "inflow_money_yi": inflow_money,
                "action": action,
                "amount_yi": quote.get("amount_yi", 0.0)
            })

        # 按净流入金额从大到小排序
        audit_rows.sort(key=lambda x: x["inflow_money_yi"], reverse=True)

        # 判定总体宏观态势
        if total_inflow_yi >= SHARE_AUDIT_CONFIG["TOTAL_INFLOW_ALERT_YI"]:
            macro_verdict = f"🚀 国家队大规模真金白银注入 (全市场宽基净流入 +{total_inflow_yi:.1f} 亿元)"
        elif total_inflow_yi >= 10.0:
            macro_verdict = f"🛡️ 国家队温和托底护盘 (净流入 +{total_inflow_yi:.1f} 亿元)"
        elif total_inflow_yi <= -10.0:
            macro_verdict = f"⚠️ 机构阶段性资金流出 (净流出 {total_inflow_yi:.1f} 亿元)"
        else:
            macro_verdict = "⚪ 市场资金处于常态平衡期"

        return {
            "date": today_str,
            "total_inflow_yi": round(total_inflow_yi, 2),
            "macro_verdict": macro_verdict,
            "category_summary": {k: round(v, 2) for k, v in category_summary.items()},
            "details": audit_rows
        }
