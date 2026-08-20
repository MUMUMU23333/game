"""
T+0 盘中异动雷达 (Intraday Anomaly Scanner)
实时监测宽基 ETF 爆量脉冲、分时急拉托底、尾盘突击与买卖盘失衡等异常信号。
"""

import time
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .config import ETF_UNIVERSE, INTRADAY_CONFIG
from .data_fetcher import DataFetcher


@dataclass
class IntradayAlert:
    """盘中异动警报数据结构"""
    timestamp: str
    code: str
    name: str
    category: str
    price: float
    chg_pct: float
    score: float           # 综合异动评分 (0 - 100)
    level: str            # 严重等级: CRITICAL(红色紧急), WARNING(黄色预警), INFO(提示)
    reasons: List[str]    # 异动触发原因列表
    amount_yi: float      # 当日累计成交额 (亿元)
    volume_ratio: float   # 相对放量倍数


class IntradayScanner:
    """盘中异动监测引擎"""

    def __init__(self, fetcher: Optional[DataFetcher] = None):
        self.fetcher = fetcher or DataFetcher()
        # 缓存过去的历史快照，用于计算分时动量与放量速度
        self.snapshots_history: List[Dict[str, Any]] = []
        self.max_history_len = 30  # 保留最近 30 次轮询快照

    def scan_once(self) -> Dict[str, Any]:
        """
        执行单次市场异动全盘扫描，返回扫描结果与警报列表
        """
        quotes = self.fetcher.get_realtime_quotes()
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_hm = datetime.datetime.now().strftime("%H:%M")

        alerts: List[IntradayAlert] = []
        metrics_list = []

        # 记录快照
        self.snapshots_history.append(quotes)
        if len(self.snapshots_history) > self.max_history_len:
            self.snapshots_history.pop(0)

        # 判断是否处于尾盘防守关键期 (14:00 - 15:00)
        is_tail_hour = current_hm >= INTRADAY_CONFIG["TAIL_HOUR_START"]

        for code, quote in quotes.items():
            info = ETF_UNIVERSE.get(code, {})
            name = info.get("name", quote.get("name", code))
            category = info.get("category", "宽基")
            price = quote["price"]
            chg_pct = quote["chg_pct"]
            amount_yi = quote["amount_yi"]
            bid5 = quote["bid_vol_5"]
            ask5 = quote["ask_vol_5"]

            reasons = []
            score = 0.0

            # ----------------------------------------------------
            # 因子 1: 绝对与相对成交额量能评估 (最高 40 分)
            # ----------------------------------------------------
            # 核心主力 510300/510050 成交额超过一定级别加分
            if amount_yi >= 50.0:
                score += 35
                reasons.append(f"🔥 成交额突破天量 ({amount_yi:.1f}亿)")
            elif amount_yi >= 20.0:
                score += 25
                reasons.append(f"⚡ 成交额显著放大 ({amount_yi:.1f}亿)")
            elif amount_yi >= 8.0:
                score += 15

            # 计算短期放量斜率 (若有历史快照)
            volume_ratio = 1.0
            if len(self.snapshots_history) >= 3:
                prev_quote = self.snapshots_history[0].get(code)
                if prev_quote and prev_quote.get("amount_wan", 0) > 0:
                    delta_amount = quote["amount_wan"] - prev_quote["amount_wan"]
                    if delta_amount > 15000:  # 短时间流入超 1.5 亿
                        score += 15
                        reasons.append(f"🚀 短周期急速爆量 (+{delta_amount/10000:.2f}亿)")

            # ----------------------------------------------------
            # 因子 2: 盘口拉升与动量特征 (最高 30 分)
            # ----------------------------------------------------
            if chg_pct >= 1.5:
                score += 25
                reasons.append(f"📈 宽基指数强势上攻 (+{chg_pct:.2f}%)")
            elif chg_pct >= 0.6:
                score += 15
                reasons.append(f"📈 宽基温和反弹 (+{chg_pct:.2f}%)")
            elif chg_pct <= -1.5 and amount_yi > 15.0:
                score += 20
                reasons.append(f"🛡️ 水下巨量托底防守 (跌幅{chg_pct:.2f}%但放巨量)")

            # ----------------------------------------------------
            # 因子 3: 尾盘突击加权 (最高 20 分)
            # ----------------------------------------------------
            if is_tail_hour:
                score += 10
                if amount_yi >= 10.0:
                    score += 10
                    reasons.append("⏰ 14:00后关键防守时段放量护盘")

            # ----------------------------------------------------
            # 因子 4: 买卖盘深度失衡 (最高 10 分 - 托单/吃单特征)
            # ----------------------------------------------------
            if ask5 > 0 and (bid5 / max(ask5, 1.0)) >= 2.5:
                score += 10
                reasons.append(f"🧱 买盘深度显著占优 (买5/卖5={bid5/max(ask5, 1.0):.1f}x)")

            # 归一化评分 (0 - 100)
            final_score = min(round(score, 1), 100.0)

            # 确定预警等级
            if final_score >= INTRADAY_CONFIG["ALERT_SCORE_THRESHOLD"]:
                level = "CRITICAL"
            elif final_score >= 45:
                level = "WARNING"
            else:
                level = "INFO"

            metric_item = {
                "code": code,
                "name": name,
                "category": category,
                "price": price,
                "chg_pct": chg_pct,
                "amount_yi": amount_yi,
                "score": final_score,
                "level": level,
                "reasons": reasons,
                "total_shares_yi": quote.get("total_shares_yi", 0.0),
                "discount_rate": quote.get("discount_rate", 0.0)
            }
            metrics_list.append(metric_item)

            if final_score >= 45 and len(reasons) > 0:
                alerts.append(IntradayAlert(
                    timestamp=current_time_str,
                    code=code,
                    name=name,
                    category=category,
                    price=price,
                    chg_pct=chg_pct,
                    score=final_score,
                    level=level,
                    reasons=reasons,
                    amount_yi=amount_yi,
                    volume_ratio=volume_ratio
                ))

        # 按异动评分从高到低排序
        metrics_list.sort(key=lambda x: x["score"], reverse=True)
        alerts.sort(key=lambda x: x.score, reverse=True)

        return {
            "timestamp": current_time_str,
            "is_tail_hour": is_tail_hour,
            "metrics": metrics_list,
            "alerts": alerts,
            "total_etfs": len(quotes),
            "critical_count": len([a for a in alerts if a.level == "CRITICAL"]),
            "warning_count": len([a for a in alerts if a.level == "WARNING"])
        }
