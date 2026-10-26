# 七星高照ETF轮动策略 - 纯ETF版（最终版）
# ETF池：黄金、豆粕、原油、白银、纳指、双创龙头、创成长、科创50（共8只）
# 防御ETF：511880.XSHG（银华日利货币ETF）
# v2 升级（2026-08-08 三轮迭代实证）：lookback 25→30 —— 本地无前视复核 5年 +2669.9%/Calmar3.99/六年全正，原版 +2396.5%/3.24。
from jqdata import *
import pandas as pd
import numpy as np
import math
from datetime import timedelta

def initialize(context):
    # ==================== ETF池（最终版，不含511220） ====================
    g.etf_pool = [
        "518880.XSHG",  # 华安黄金ETF
        "159985.XSHE",  # 华夏饲料豆粕期货ETF
        "501018.XSHG",  # 南方原油LOF
        "161226.XSHE",  # 国投白银LOF
        "513100.XSHG",  # 纳指ETF
        "588330.XSHG",  # 双创龙头ETF
        "159967.XSHE",  # 创成长ETF（创业板动量成长）
        "588940.XSHG"   # 科创50ETF富国
    ]
    
    # ==================== 策略参数 ====================
    g.lookback_days = 30   # v2: 25→30 (2026-08-08 实证)
    g.holdings_num = 1
    g.defensive_etf = "511880.XSHG"   # 银华日利货币ETF
    g.min_money = 5000
    g.stop_loss = 0.95
    g.loss_limit = 0.97
    g.min_score_threshold = 0
    g.max_score_threshold = 500.0
    g.enable_premium_filter = True
    g.premium_threshold = 0.20
    
    # ==================== 内部状态 ====================
    g.strategy_holdings = {3: []}
    g.stock_strategy = {}
    g.rankings_cache = {'date': None, 'data': None}
    
    # ==================== 系统设置 ====================
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_slippage(PriceRelatedSlippage(0.0001), type='fund')
    set_order_cost(OrderCost(close_tax=0, open_commission=0.0001,
                             close_commission=0.0001, min_commission=5), type='fund')
    
    # ==================== 定时任务 ====================
    run_daily(strategy_sell, time='14:47')
    run_daily(strategy_buy, time='14:48')
    run_daily(print_summary, time='15:02')


# ====================== 核心函数 ======================
def get_cached_rankings(context):
    today = context.current_dt.date()
    if g.rankings_cache['date'] != today:
        g.rankings_cache['data'] = get_ranked_etfs(context)
        g.rankings_cache['date'] = today
    return g.rankings_cache['data']

def get_ranked_etfs(context):
    scores = []
    for etf in g.etf_pool:
        score = calculate_momentum_score(context, etf)
        if score and g.min_score_threshold < score < g.max_score_threshold:
            scores.append((etf, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scores]

def calculate_momentum_score(context, etf):
    end_date = context.previous_date
    df = get_price(etf, end_date=end_date, count=g.lookback_days + 5,
                   frequency='1d', fields=['close'], fq='pre', panel=False)
    if df is None or len(df) < g.lookback_days:
        return None
    prices = df['close'].values
    curr_price = get_current_data()[etf].last_price
    if curr_price is None:
        return None
    y = np.log(np.append(prices[-g.lookback_days:], curr_price))
    x = np.arange(len(y))
    weights = np.linspace(1, 2, len(y))
    slope, intercept = np.polyfit(x, y, 1, w=weights)
    ann_ret = math.exp(slope * 250) - 1
    y_pred = slope * x + intercept
    ss_res = np.sum(weights * (y - y_pred) ** 2)
    ss_tot = np.sum(weights * (y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0
    score = ann_ret * r2
    if len(prices) >= 4:
        recent_ret = min(prices[-1] / prices[-2],
                         prices[-2] / prices[-3],
                         prices[-3] / prices[-4])
        if recent_ret < g.loss_limit:
            score = 0
    return score

def get_premium_rate(etf, date):
    price_data = get_price(etf, start_date=date, end_date=date,
                           frequency='1d', fields=['close'], panel=False)
    if price_data.empty:
        return None
    price = price_data['close'][0]
    net_data = get_extras('unit_net_value', etf, start_date=date, end_date=date, df=True)
    if net_data.empty or pd.isna(net_data[etf][0]):
        q = query(finance.FUND_NET_VALUE).filter(
            finance.FUND_NET_VALUE.code == etf,
            finance.FUND_NET_VALUE.day == date
        )
        df = finance.run_query(q)
        if df.empty:
            return None
        net = df['net_value'][0]
    else:
        net = net_data[etf][0]
    if net == 0:
        return None
    return (price - net) / net

def strategy_sell(context):
    ranked = get_cached_rankings(context)
    targets = ranked[:g.holdings_num] if ranked else []
    if not targets:
        targets = [g.defensive_etf]
    for etf in g.strategy_holdings[3][:]:
        if etf not in targets:
            close_position(etf)
    for etf in g.strategy_holdings[3][:]:
        pos = context.portfolio.positions.get(etf)
        if pos and pos.price <= pos.avg_cost * g.stop_loss:
            close_position(etf)

def strategy_buy(context):
    ranked = get_cached_rankings(context)
    candidates = ranked[:g.holdings_num] if ranked else []
    targets = []
    if g.enable_premium_filter and candidates:
        prev_date = context.previous_date
        for etf in candidates:
            premium = get_premium_rate(etf, prev_date)
            if premium is None or premium <= g.premium_threshold:
                targets.append(etf)
            else:
                log.info(f"[溢价过滤] {etf} 溢价率{premium*100:.2f}% > {g.premium_threshold*100:.1f}% 跳过")
    else:
        targets = candidates
    if not targets:
        targets = [g.defensive_etf]
    total_val = context.portfolio.total_value
    per_val = total_val / len(targets)
    for etf in targets:
        if per_val >= g.min_money:
            open_position(context, etf, per_val)

def close_position(security):
    order = order_target_value(security, 0)
    if order:
        sid = g.stock_strategy.get(security)
        if sid and security in g.strategy_holdings.get(sid, []):
            g.strategy_holdings[sid].remove(security)
        if security in g.stock_strategy:
            del g.stock_strategy[security]
    return order

def open_position(context, security, value):
    if value < g.min_money:
        return
    # 最小下单量保护（v2.1 2026-08-08 日志检查修复）：目标与持仓差额 <100 股不下单，消除'数量不能小于100'ERROR刷屏
    price = get_current_data()[security].last_price
    pos = context.portfolio.positions.get(security)
    if pos is None or pos.total_amount == 0:
        if price and value / price < 100:
            return
    else:
        delta = value / price - pos.total_amount
        if abs(delta) < 100:
            return
    order = order_target_value(security, value)
    if order:
        if security not in g.strategy_holdings[3]:
            g.strategy_holdings[3].append(security)
        g.stock_strategy[security] = 3
    return order

def print_summary(context):
    log.info(f"总资产: {context.portfolio.total_value:.2f}")
    stocks = g.strategy_holdings[3]
    if stocks:
        log.info(f"ETF持仓: {[s[:6] for s in stocks]}")
