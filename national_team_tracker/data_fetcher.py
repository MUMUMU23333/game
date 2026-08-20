"""
数据获取模块 (Data Fetcher)
支持 T+0 毫秒级多源行情批量获取、分时/日K线历史获取与交易所官方份额数据拉取。
"""

import os
import time
import datetime
from typing import Dict, List, Optional, Any
import requests
import pandas as pd

from .config import ETF_UNIVERSE


def sanitize_network_environment():
    """清理 Windows 下无效或未开启的代理环境变量，确保网络直连通畅"""
    proxy_keys = [
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        "http_proxy", "https_proxy", "all_proxy"
    ]
    for k in proxy_keys:
        os.environ.pop(k, None)
    os.environ["NO_PROXY"] = "*"


# 模块加载时自动清理网络环境
sanitize_network_environment()


class DataFetcher:
    """多源高可靠量化数据拉取引擎"""

    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def get_realtime_quotes(self, codes: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        批量拉取实时高频行情 (使用腾讯高并发行情接口，耗时 < 100ms)
        返回包含：现价、昨收、开盘、最高、最低、成交量(手)、成交额(万元)、总份额(份)、估值净值、折溢价率等
        """
        if codes is None:
            codes = list(ETF_UNIVERSE.keys())

        # 构造腾讯行情代码前缀 (sh / sz)
        query_list = []
        for code in codes:
            info = ETF_UNIVERSE.get(code, {})
            market = info.get("market", "SH").lower()
            query_list.append(f"{market}{code}")

        url = f"http://qt.gtimg.cn/q={','.join(query_list)}"
        result = {}

        try:
            resp = self.session.get(url, timeout=3)
            raw_text = resp.content.decode("gbk", errors="ignore")
            lines = raw_text.strip().split(";")

            for line in lines:
                if not line.strip() or "~" not in line:
                    continue
                parts = line.split("~")
                if len(parts) < 80:
                    continue

                code = parts[2]
                name = ETF_UNIVERSE.get(code, {}).get("name", parts[1])

                try:
                    price = float(parts[3])
                    pre_close = float(parts[4])
                    open_p = float(parts[5])
                    volume_lots = float(parts[6])       # 成交量 (手)
                    high = float(parts[33])
                    low = float(parts[34])
                    amount_wan = float(parts[37])       # 成交额 (万元)
                    turnover_rate = float(parts[38])    # 换手率 (%)
                    market_cap_yi = float(parts[44])    # 总市值 (亿元)
                    
                    # 总份额 (部分接口在 72 字段，单位：份)
                    total_shares = float(parts[72]) if parts[72] and parts[72].isdigit() else 0.0
                    
                    # 折溢价率与 IOPV 估值
                    iopv = float(parts[81]) if len(parts) > 81 and parts[81] else price
                    discount_rate = float(parts[80]) if len(parts) > 80 and parts[80] else 0.0

                    # 涨跌幅 (%) 与涨跌额
                    chg_pct = float(parts[32])
                    chg_val = float(parts[31])

                    # 5档买卖盘大单统计
                    bid_vol_total = sum([float(parts[i]) for i in [10, 12, 14, 16, 18] if i < len(parts) and parts[i].isdigit()])
                    ask_vol_total = sum([float(parts[i]) for i in [20, 22, 24, 26, 28] if i < len(parts) and parts[i].isdigit()])

                    result[code] = {
                        "code": code,
                        "name": name,
                        "price": price,
                        "pre_close": pre_close,
                        "open": open_p,
                        "high": high,
                        "low": low,
                        "volume_lots": volume_lots,
                        "volume_shares": volume_lots * 100,
                        "amount_wan": amount_wan,
                        "amount_yi": round(amount_wan / 10000.0, 4),
                        "chg_pct": chg_pct,
                        "chg_val": chg_val,
                        "turnover_rate": turnover_rate,
                        "market_cap_yi": market_cap_yi,
                        "total_shares": total_shares,
                        "total_shares_yi": round(total_shares / 1e8, 4) if total_shares > 0 else round(market_cap_yi / max(price, 0.01), 4),
                        "iopv": iopv,
                        "discount_rate": discount_rate,
                        "bid_vol_5": bid_vol_total,
                        "ask_vol_5": ask_vol_total,
                        "timestamp": parts[30] if len(parts) > 30 else datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    }
                except Exception as ex:
                    continue

        except Exception as e:
            print(f"[DataFetcher] 获取实时行情异常: {e}")

        return result

    def get_etf_daily_history(self, code: str, lookback: int = 30) -> pd.DataFrame:
        """
        拉取单只 ETF 近期日线历史数据（用于计算量能基准与均线）
        """
        market = ETF_UNIVERSE.get(code, {}).get("market", "SH").lower()
        secid = f"1.{code}" if market == "sh" else f"0.{code}"
        
        # 尝试通过新浪/腾讯日K线接口获取
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,{lookback},qfq"
        try:
            resp = self.session.get(url, timeout=4)
            data = resp.json()
            raw_node = data.get("data", {}).get(f"{market}{code}", {})
            k_data = raw_node.get("qfqday") or raw_node.get("day", [])
            
            records = []
            for item in k_data:
                # 格式: [日期, 开盘, 收盘, 最高, 最低, 成交量(手)]
                records.append({
                    "date": str(item[0]),
                    "open": float(item[1]),
                    "close": float(item[2]),
                    "high": float(item[3]),
                    "low": float(item[4]),
                    "volume": float(item[5]),
                    "amount_wan": float(item[2]) * float(item[5]) * 100 / 10000.0
                })
            df = pd.DataFrame(records)
            return df
        except Exception as e:
            return pd.DataFrame()

    def get_official_etf_shares_history(self, code: str) -> pd.DataFrame:
        """
        拉取官方 ETF 份额历史数据 (通过 AKShare 或东财基金规模变动接口)
        """
        try:
            import akshare as ak
            # 优先调用 akshare
            df = ak.fund_etf_scale_sse() if code.startswith("51") or code.startswith("56") or code.startswith("58") else ak.fund_scale_daily_szse()
            return df
        except Exception:
            return pd.DataFrame()
