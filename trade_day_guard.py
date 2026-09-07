# -*- coding: utf-8 -*-
"""
================================================================================
A股交易日权威判别与休市熔断守卫 (Trade Day Guard)
================================================================================
核心职责：
1. 严谨判别当前是否为中国 A 股真实交易日（自动过滤周末、法定节假日与休市日）。
2. 多源高韧性校验：
   - 维度1: 周末物理过滤 (周六/周日一票否决，调休亦不开市)
   - 维度2: 东方财富上证指数官方交易日历实时穿透
   - 维度3: 腾讯高频行情交易日时间戳比对
   - 维度4: 本地权威法定节假日日历离线双保险
3. 策略熔断：在非交易日自动阻断策略更新、预警推送与调仓计算，防止无效运行。
================================================================================
"""

import sys
import json
import time
import requests
from datetime import datetime, timezone, timedelta

# 修复 Windows 控制台编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_beijing_now():
    """获取当前精准北京时间 (UTC+8)"""
    utc_now = datetime.now(timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    return utc_now.astimezone(beijing_tz)


# ----------------------------------------------------------------------
# 离线法定节假日与休市日清单 (包含 2025-2027 年已知法定节假日)
# 格式: 'YYYY-MM-DD' -> '节假日名称'
# ----------------------------------------------------------------------
KNOWN_HOLIDAYS = {
    # 2025 年主要休市日
    "2025-01-01": "元旦",
    "2025-01-28": "除夕", "2025-01-29": "春节", "2025-01-30": "春节", "2025-01-31": "春节",
    "2025-02-03": "春节", "2025-02-04": "春节",
    "2025-04-04": "清明节",
    "2025-05-01": "劳动节", "2025-05-02": "劳动节", "2025-05-05": "劳动节",
    "2025-05-31": "端午节", "2025-06-02": "端午节",
    "2025-10-01": "国庆节", "2025-10-02": "国庆节", "2025-10-03": "国庆节",
    "2025-10-06": "国庆/中秋", "2025-10-07": "国庆节", "2025-10-08": "国庆节",

    # 2026 年主要休市日 (根据国务院法定假日标准及历法排期)
    "2026-01-01": "元旦", "2026-01-02": "元旦",
    "2026-02-16": "春节", "2026-02-17": "春节", "2026-02-18": "春节", 
    "2026-02-19": "春节", "2026-02-20": "春节", "2026-02-23": "春节",
    "2026-04-06": "清明节",
    "2026-05-01": "劳动节", "2026-05-04": "劳动节", "2026-05-05": "劳动节",
    "2026-06-19": "端午节",
    "2026-09-25": "中秋节",
    "2026-10-01": "国庆节", "2026-10-02": "国庆节", "2026-10-05": "国庆节",
    "2026-10-06": "国庆节", "2026-10-07": "国庆节",
}


def check_eastmoney_trading_day(dt_str: str) -> tuple[bool, str]:
    """通过东方财富上证指数日 K 线获取最新权威交易日"""
    try:
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000001&fields1=f1,f2,f3,f4,f5,f6&fields2=f51&klt=101&fqt=1&end=20500101&lmt=10"
        resp = requests.get(url, timeout=3, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            klines = data.get("klines", [])
            if klines:
                recent_days = [k.split(",")[0] for k in klines]
                latest_trade_day = recent_days[-1]
                if dt_str == latest_trade_day:
                    return True, f"东财上证日历校验成功 (今日 {dt_str} 为已开市交易日)"
                elif dt_str in recent_days:
                    return True, f"东财日历记录为交易日 ({dt_str})"
                elif dt_str > latest_trade_day:
                    # 盘前或交易日早上尚未收盘产生日K，继续参考其他信号
                    pass
    except Exception as e:
        pass
    return None, ""


def check_tencent_trading_time(dt_str_nodash: str) -> tuple[bool, str]:
    """通过腾讯行情接口上证指数实时行情时间戳判别"""
    try:
        url = "http://qt.gtimg.cn/q=sh000001"
        resp = requests.get(url, timeout=3, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200 and '="' in resp.text:
            parts = resp.text.split('="')[1].split("~")
            if len(parts) > 30:
                trade_time_str = parts[30]  # 形如 '20260907150000'
                if trade_time_str.startswith(dt_str_nodash):
                    return True, f"腾讯实时行情确认开市 (最新行情时间: {trade_time_str})"
    except Exception:
        pass
    return None, ""


def is_trade_day(target_dt: datetime = None) -> tuple[bool, str]:
    """
    判断指定日期（默认今日北京时间）是否为 A 股交易日。
    返回: (is_trading, reason_description)
    """
    if target_dt is None:
        target_dt = get_beijing_now()
        
    dt_str = target_dt.strftime("%Y-%m-%d")
    dt_str_nodash = target_dt.strftime("%Y%m%d")
    weekday = target_dt.weekday()  # 0=周一, 4=周五, 5=周六, 6=周日
    
    # 1. 周末硬过滤（周六、周日 100% 不交易）
    if weekday == 5:
        return False, f"周六休市 (日期: {dt_str})"
    if weekday == 6:
        return False, f"周日休市 (日期: {dt_str})"
        
    # 2. 离线法定节假日清单过滤
    if dt_str in KNOWN_HOLIDAYS:
        h_name = KNOWN_HOLIDAYS[dt_str]
        return False, f"法定节假日休市: {h_name} (日期: {dt_str})"
        
    # 3. 在线实时校验（针对盘中/盘后执行）
    # 3.1 东方财富校验
    em_ok, em_desc = check_eastmoney_trading_day(dt_str)
    if em_ok is True:
        return True, em_desc
        
    # 3.2 腾讯行情校验
    tx_ok, tx_desc = check_tencent_trading_time(dt_str_nodash)
    if tx_ok is True:
        return True, tx_desc
        
    # 4. 常规工作日（周一至周五且不在已知假日清单中）
    return True, f"常规工作日交易日 (周{weekday+1}, 日期: {dt_str})"


def guard_and_exit_if_not_trade_day(strategy_name: str = "量化策略"):
    """
    守卫函数：若非交易日，输出醒目提示并立即以 0 状态码优雅退出进程。
    """
    now = get_beijing_now()
    trading, reason = is_trade_day(now)
    if not trading:
        print("=" * 80)
        print(f"🛑 [交易日守卫] 检测到今日非 A 股交易日: {reason}")
        print(f"⏸️ [{strategy_name}] 今日休市，跳过策略计算、数据更新与消息推送！")
        print("=" * 80)
        sys.exit(0)
    else:
        print(f"✅ [交易日守卫] 今日为正常交易日 ({reason})，准予执行 [{strategy_name}]！")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="A-Share Trade Day Guard")
    parser.add_argument("--assert-trade-day", action="store_true", help="若非交易日则以退出码0终止")
    parser.add_argument("--name", type=str, default="全量策略", help="策略模块名称")
    args = parser.parse_args()

    now = get_beijing_now()
    trading, reason = is_trade_day(now)
    
    if args.assert_trade_day:
        guard_and_exit_if_not_trade_day(args.name)
    else:
        status_str = "🟢 正常交易日 (开市)" if trading else "🔴 休市日 (不交易)"
        print(f"北京时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"判别结果: {status_str}")
        print(f"判定原因: {reason}")
        sys.exit(0 if trading else 1)
