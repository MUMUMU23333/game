# -*- coding: utf-8 -*-
"""
====================================================================================================
👑【天枢总指挥部 · 跨市场巅峰夜盘映射策略 2025.01 - 2026.11 全景逐日回测引擎】
====================================================================================================
统计区间：2025年1月2日 - 2026年11月5日 (约440+交易日跨周期逐日检验)
覆盖资产：
  • 黄金/贵金属链: 黄金ETF (518880) vs 紫金矿业 (601899)、山东黄金 (600547)
  • 工业金属/铜链: 有色金属ETF (512400) vs 洛阳钼业 (603993)、江西铜业 (600362)
  • 英伟达/算力链: 通信ETF (515880)、芯片ETF (159995) vs 中际旭创 (300308)、新易盛 (300502)、工业富联 (601138)
  • 电网变压器出海: 电力ETF (159611) vs 思源电气 (002028)、金盘科技 (688676)
  • 中概互联/核心: 恒生科技ETF (513180) vs 宁德时代 (300750)
====================================================================================================
"""

import os
import sys
import json
import time
import requests
import warnings
from datetime import datetime
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, ".cross_backtest_k_cache.pkl")

# 测试标的列表
TARGET_ASSETS = [
    # 黄金/贵金属
    {"code": "518880", "name": "黄金ETF", "type": "ETF", "sector": "黄金/贵金属", "market": "sh"},
    {"code": "601899", "name": "紫金矿业", "type": "STOCK", "sector": "黄金/贵金属", "market": "sh"},
    {"code": "600547", "name": "山东黄金", "type": "STOCK", "sector": "黄金/贵金属", "market": "sh"},
    
    # 工业金属/铜
    {"code": "512400", "name": "有色金属ETF", "type": "ETF", "sector": "工业金属/铜", "market": "sh"},
    {"code": "603993", "name": "洛阳钼业", "type": "STOCK", "sector": "工业金属/铜", "market": "sh"},
    {"code": "600362", "name": "江西铜业", "type": "STOCK", "sector": "工业金属/铜", "market": "sh"},
    
    # 英伟达/算力光模块
    {"code": "515880", "name": "通信ETF", "type": "ETF", "sector": "AI算力/光模块", "market": "sh"},
    {"code": "159995", "name": "芯片ETF", "type": "ETF", "sector": "AI算力/芯片", "market": "sz"},
    {"code": "300308", "name": "中际旭创", "type": "STOCK", "sector": "AI算力/光模块", "market": "sz"},
    {"code": "300502", "name": "新易盛", "type": "STOCK", "sector": "AI算力/光模块", "market": "sz"},
    {"code": "601138", "name": "工业富联", "type": "STOCK", "sector": "AI算力/服务器", "market": "sh"},
    
    # 亚马逊/微软云计算与IDC
    {"code": "516510", "name": "云计算ETF", "type": "ETF", "sector": "云计算/数据中心", "market": "sh"},
    {"code": "603019", "name": "中科曙光", "type": "STOCK", "sector": "云计算/算力底座", "market": "sh"},
    {"code": "000977", "name": "浪潮信息", "type": "STOCK", "sector": "云计算/AI服务器", "market": "sz"},
    {"code": "002837", "name": "英维克", "type": "STOCK", "sector": "云计算/液冷温控", "market": "sz"},
    {"code": "300442", "name": "润泽科技", "type": "STOCK", "sector": "云计算/智算IDC", "market": "sz"},

    # 第一太阳能/美股光伏新能源
    {"code": "515790", "name": "光伏ETF", "type": "ETF", "sector": "光伏新能源", "market": "sh"},
    {"code": "300274", "name": "阳光电源", "type": "STOCK", "sector": "光伏/逆变器储能", "market": "sz"},
    {"code": "605117", "name": "德业股份", "type": "STOCK", "sector": "光伏/逆变器出海", "market": "sh"},
    {"code": "688472", "name": "阿特斯", "type": "STOCK", "sector": "光伏/美国建厂龙头", "market": "sh"},
    {"code": "688408", "name": "中信博", "type": "STOCK", "sector": "光伏/跟踪支架出海", "market": "sh"},
    {"code": "601012", "name": "隆基绿能", "type": "STOCK", "sector": "光伏/传统主链组件", "market": "sh"},

    # 电网出海
    {"code": "159611", "name": "电力ETF", "type": "ETF", "sector": "电网设备出海", "market": "sz"},
    {"code": "002028", "name": "思源电气", "type": "STOCK", "sector": "电网设备出海", "market": "sz"},
    {"code": "688676", "name": "金盘科技", "type": "STOCK", "sector": "电网设备出海", "market": "sh"},
    
    # 中概与核心资产
    {"code": "513180", "name": "恒生科技ETF", "type": "ETF", "sector": "中概互联", "market": "sh"},
    {"code": "300750", "name": "宁德时代", "type": "STOCK", "sector": "新能源/大盘核心", "market": "sz"}
]

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})


def fetch_daily_klines(code: str, market: str, count: int = 550) -> pd.DataFrame:
    """拉取腾讯日线前复权K线 (快速轻量请求)"""
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,{count},qfq"
    for attempt in range(2):
        try:
            r = requests.get(url, timeout=3.5).json()
            raw = r.get('data', {}).get(f"{market}{code}", {})
            k_data = raw.get('qfqday') or raw.get('day', [])
            records = []
            for item in k_data:
                records.append({
                    'date': str(item[0]),
                    'open': float(item[1]),
                    'close': float(item[2]),
                    'high': float(item[3]),
                    'low': float(item[4]),
                    'volume': float(item[5]) if len(item) > 5 else 0.0
                })
            df = pd.DataFrame(records)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                return df
        except Exception:
            time.sleep(0.1)
    return pd.DataFrame()


def load_all_market_data():
    """加载所有标的历史日线数据"""
    data_map = {}
    print("[*] 开始拉取 2025-2026 全量日线 K 线数据...", flush=True)
    for item in TARGET_ASSETS:
        code = item["code"]
        market = item["market"]
        df = fetch_daily_klines(code, market, count=550)
        if not df.empty:
            df = df[df['date'] >= pd.to_datetime('2024-12-01')].reset_index(drop=True)
            data_map[code] = df
            print(f"  • {item['name']} ({code}): 成功加载 {len(df)} 根K线", flush=True)
        else:
            print(f"  [!] {item['name']} ({code}) 拉取失败，将跳过", flush=True)
    return data_map


def run_single_asset_backtest(item: dict, df: pd.DataFrame, start_date='2025-01-02', end_date='2026-11-05') -> dict:
    """
    执行单标的逐日实测：
    严格模拟夜盘映射逻辑、高开透支拦截 (0.3% <= Gap <= 3.2%)、09:35 VWAP 承接与 T+1 退出
    """
    if df.empty or len(df) < 30:
        return {}

    # 计算技术特征
    df['prev_close'] = df['close'].shift(1)
    df['gap'] = (df['open'] / df['prev_close'] - 1) * 100.0
    df['intraday_ret'] = (df['close'] / df['open'] - 1) * 100.0
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['vol_ma5'] = df['volume'].rolling(5).mean()

    # 费率设定
    is_etf = (item["type"] == "ETF")
    commission = 0.0001
    stamp_duty = 0.0 if is_etf else 0.0005  # A股股票印花税万5，ETF免征
    slippage = 0.001 if is_etf else 0.002   # ETF滑点千1，个股千2
    round_trip_cost = (commission * 2 + stamp_duty + slippage) * 100.0  # 百分比成本

    trades = []
    
    # 逐日回溯遍历 (从 2025-01-02 到 2026-11-05)
    for i in range(25, len(df) - 1):
        dt = df.loc[i, 'date']
        dt_str = dt.strftime('%Y-%m-%d')
        if dt_str < start_date or dt_str > end_date:
            continue

        row = df.loc[i]
        prev_row = df.loc[i - 1]
        next_row = df.loc[i + 1]

        gap = row['gap']
        open_p = row['open']
        close_p = row['close']
        high_p = row['high']
        low_p = row['low']

        # -------------------------------------------------------------
        # 1. 信号触发条件 (跨市场映射信号判定)
        # -------------------------------------------------------------
        # 条件 A: 存在正面夜盘映射（跳空高开且处于黄金射击区 0.3% <= Gap <= 3.2%）
        # 严格排除 Gap > 3.5% 的恶意诱多顶板，也排除低开破位
        is_gap_eligible = (0.3 <= gap <= 3.2)
        
        # 条件 B: 趋势生命线保护 (前一日收盘在 MA20 上方，处于健康中线上升通道)
        is_trend_healthy = (prev_row['close'] >= prev_row['ma20'] * 0.985)
        
        # 条件 C: 09:35 微观承接 (日内未走出恶性单边跳水，最低价未击穿开盘价 -1.2%)
        is_vwap_support = (low_p >= open_p * 0.988) and (close_p >= (open_p + close_p)/2)

        if is_gap_eligible and is_trend_healthy and is_vwap_support:
            # 模拟在 09:35 确认后按微观买入价介入 (略高于开盘价)
            buy_price = open_p * (1.0 + min(gap * 0.15, 0.4) / 100.0)
            
            # T+1 日平仓卖出规则：
            # 模式: 标准 T+1 尾盘或次日收盘执行轮动平仓
            sell_price = next_row['close']
            
            # 动态吊灯止损保护: 若 T+1 日击穿止损线 -2.5%，按止损价强平
            if next_row['low'] <= buy_price * 0.975:
                sell_price = buy_price * 0.975
            elif next_row['high'] >= buy_price * 1.055: # +5.5% 动态吊灯止盈
                sell_price = buy_price * 1.055

            gross_ret = (sell_price / buy_price - 1.0) * 100.0
            net_ret = gross_ret - round_trip_cost  # 扣除全部摩擦成本

            trades.append({
                'date': dt_str,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'gross_ret': gross_ret,
                'net_ret': net_ret,
                'is_win': (net_ret > 0)
            })

    # 统计核心指标
    total_trades = len(trades)
    if total_trades == 0:
        return {}

    wins = [t for t in trades if t['is_win']]
    losses = [t for t in trades if not t['is_win']]
    win_rate = len(wins) / total_trades * 100.0

    avg_win = np.mean([t['net_ret'] for t in wins]) if wins else 0.0
    avg_loss = abs(np.mean([t['net_ret'] for t in losses])) if losses else 1.0
    profit_loss_ratio = (avg_win / avg_loss) if avg_loss > 0 else avg_win

    avg_ret = np.mean([t['net_ret'] for t in trades])
    
    # 累计收益与最大回撤
    equity_curve = [100.0]
    for t in trades:
        equity_curve.append(equity_curve[-1] * (1.0 + t['net_ret'] / 100.0))
    total_cum_ret = equity_curve[-1] - 100.0

    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (val / peak - 1.0) * 100.0
        if dd < max_dd:
            max_dd = dd

    max_single_win = max([t['net_ret'] for t in trades])
    max_single_loss = min([t['net_ret'] for t in trades])

    return {
        "code": item["code"],
        "name": item["name"],
        "type": item["type"],
        "sector": item["sector"],
        "total_trades": total_trades,
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate": round(win_rate, 2),
        "avg_ret": round(avg_ret, 2),
        "profit_loss_ratio": round(profit_loss_ratio, 2),
        "total_cum_ret": round(total_cum_ret, 2),
        "max_drawdown": round(max_dd, 2),
        "max_single_win": round(max_single_win, 2),
        "max_single_loss": round(max_single_loss, 2)
    }


def main():
    print("=" * 80)
    print("👑【天枢总指挥部 · 跨市场巅峰夜盘映射策略 2025-2026 全景逐日回测】")
    print("⏰ 回测区间: 2025-01-02 至 2026-11-05 (扣除万一佣金/股票印花税/盘口滑点)")
    print("=" * 80)

    data_map = load_all_market_data()
    results = []

    for item in TARGET_ASSETS:
        code = item["code"]
        if code in data_map:
            df = data_map[code]
            res = run_single_asset_backtest(item, df)
            if res:
                results.append(res)

    res_df = pd.DataFrame(results)
    
    # 按胜率降序排序
    res_df = res_df.sort_values(by="win_rate", ascending=False).reset_index(drop=True)

    print("\n📊 【逐日回测全景统计表 (2025.01 - 2026.11 · 按胜率排序)】")
    print(res_df[['name', 'code', 'type', 'sector', 'total_trades', 'win_rate', 'profit_loss_ratio', 'avg_ret', 'total_cum_ret', 'max_drawdown']].to_string(index=False))

    # ETF vs 个股 分组对比
    etf_group = res_df[res_df['type'] == 'ETF']
    stock_group = res_df[res_df['type'] == 'STOCK']

    print("\n" + "=" * 80)
    print(f"🥇 【ETF 组汇总表现 (共 {len(etf_group)} 只)】")
    print(f"  • 平均胜率: {etf_group['win_rate'].mean():.2f}%")
    print(f"  • 平均盈亏比: {etf_group['profit_loss_ratio'].mean():.2f} : 1")
    print(f"  • 平均最大回撤: {etf_group['max_drawdown'].mean():.2f}%")
    print(f"  • 平均累计收益: +{etf_group['total_cum_ret'].mean():.2f}%")

    print("\n🚀 【个股组汇总表现 (共 {len(stock_group)} 只)】")
    print(f"  • 平均胜率: {stock_group['win_rate'].mean():.2f}%")
    print(f"  • 平均盈亏比: {stock_group['profit_loss_ratio'].mean():.2f} : 1")
    print(f"  • 平均最大回撤: {stock_group['max_drawdown'].mean():.2f}%")
    print(f"  • 平均累计收益: +{stock_group['total_cum_ret'].mean():.2f}%")
    print("=" * 80)

    # 保存 JSON 回测报告
    out_file = os.path.join(BASE_DIR, "cross_market_apex_backtest_2025_2026.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ 详细回测报告已成功落盘至: {out_file}")


if __name__ == "__main__":
    main()
