# -*- coding: utf-8 -*-
import os, sys, re
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

log_path = r'c:\Users\Administrator\Desktop\量化策略源代码\五福5.2日内趋势-Clone.txt'

# 1. Parse all trades
trades = []
with open(log_path, 'r', encoding='gbk', errors='ignore') as f:
    for line in f:
        # Match Buy
        m_buy = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?买入\s+([0-9]{6}\.[A-Z]{4})\s+.*?数量(\d+)\s+价格([\d\.]+)', line)
        if m_buy:
            dt_str, code, shares, price = m_buy.groups()
            trades.append({
                'datetime': dt_str,
                'date': dt_str[:10],
                'type': 'BUY',
                'code': code,
                'shares': int(shares),
                'price': float(price),
                'amount': int(shares) * float(price)
            })
            continue
            
        # Match Sell
        m_sell = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?(卖出|已卖出|止损).*?([0-9]{6}\.[A-Z]{4})\s+.*?数量(\d+)\s+价格([\d\.]+)', line)
        if m_sell:
            dt_str, action, code, shares, price = m_sell.groups()
            trades.append({
                'datetime': dt_str,
                'date': dt_str[:10],
                'type': 'SELL',
                'code': code,
                'shares': int(shares),
                'price': float(price),
                'amount': int(shares) * float(price)
            })

df_trades = pd.DataFrame(trades)

# 2. Reconstruct round-trip closed trades
closed_trades = []
current_holding = None

for idx, row in df_trades.iterrows():
    if row['type'] == 'BUY':
        current_holding = row
    elif row['type'] == 'SELL' and current_holding is not None:
        buy_row = current_holding
        buy_amt = buy_row['amount']
        sell_amt = row['amount']
        # Apply commission万1 (0.0001) per side
        pnl = sell_amt * (1 - 0.0001) - buy_amt * (1 + 0.0001)
        pnl_pct = (row['price'] - buy_row['price']) / buy_row['price']
        hold_days = (pd.to_datetime(row['date']) - pd.to_datetime(buy_row['date'])).days
        closed_trades.append({
            'code': row['code'],
            'buy_dt': buy_row['datetime'],
            'sell_dt': row['datetime'],
            'buy_price': buy_row['price'],
            'sell_price': row['price'],
            'shares': row['shares'],
            'buy_amt': buy_amt,
            'sell_amt': sell_amt,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'hold_days': hold_days,
            'year': int(row['date'][:4])
        })
        current_holding = None

df_closed = pd.DataFrame(closed_trades)

# 3. Reconstruct daily equity curve from closed trades
initial_cash = 50000.0
cash = initial_cash
equity_history = [{'date': '2021-01-04', 'equity': initial_cash}]

for idx, row in df_closed.iterrows():
    cash += row['pnl']
    equity_history.append({'date': row['sell_dt'][:10], 'equity': cash})

df_eq = pd.DataFrame(equity_history).drop_duplicates('date', keep='last').sort_values('date').reset_index(drop=True)
df_eq['date'] = pd.to_datetime(df_eq['date'])
df_eq['cummax'] = df_eq['equity'].cummax()
df_eq['drawdown'] = (df_eq['equity'] - df_eq['cummax']) / df_eq['cummax']

# Calculate Metrics
total_trades = len(df_closed)
win_trades = df_closed[df_closed['pnl'] > 0]
loss_trades = df_closed[df_closed['pnl'] <= 0]
win_rate = len(win_trades) / total_trades * 100.0

avg_win = win_trades['pnl_pct'].mean() * 100.0
avg_loss = abs(loss_trades['pnl_pct'].mean()) * 100.0
profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

total_win_amt = win_trades['pnl'].sum()
total_loss_amt = abs(loss_trades['pnl'].sum())
profit_factor = total_win_amt / total_loss_amt if total_loss_amt > 0 else 0

final_equity = cash
total_return = (final_equity - initial_cash) / initial_cash * 100.0
total_days = (df_eq.iloc[-1]['date'] - df_eq.iloc[0]['date']).days
cagr = ((final_equity / initial_cash) ** (365.25 / total_days) - 1.0) * 100.0
max_dd = df_eq['drawdown'].min() * 100.0
max_dd_date = df_eq.loc[df_eq['drawdown'].idxmin(), 'date'].strftime('%Y-%m-%d')

# Daily returns for Sharpe
df_eq['pct_chg'] = df_eq['equity'].pct_change().fillna(0)
sharpe = (df_eq['pct_chg'].mean() / df_eq['pct_chg'].std() * np.sqrt(250)) if df_eq['pct_chg'].std() > 0 else 0
calmar = abs(cagr / max_dd) if max_dd != 0 else 0

print("=" * 70)
print("【五福 5.2 原版】全周期逐笔回测分析报告 (2021-01-04 ~ 2026-08-11)")
print("=" * 70)
print(f"★ 初始本金: {initial_cash:,.2f} 元")
print(f"★ 期末资产: {final_equity:,.2f} 元")
print(f"★ 累计总收益: +{total_return:,.2f}% ({final_equity/initial_cash:.2f} 倍)")
print(f"★ 年化复合收益率 (CAGR): +{cagr:.2f}%")
print(f"★ 最大历史回撤 (MaxDD): {max_dd:.2f}% (低点日期: {max_dd_date})")
print(f"★ 夏普比率 (Sharpe): {sharpe:.3f}")
print(f"★ 卡玛比率 (Calmar): {calmar:.3f}")
print(f"★ 总交易笔数: {total_trades} 笔 (盈利: {len(win_trades)} 笔, 亏损: {len(loss_trades)} 笔)")
print(f"★ 交易胜率 (Win Rate): {win_rate:.2f}%")
print(f"★ 单笔盈亏比 (P/L Ratio): {profit_loss_ratio:.2f} (平均盈利: +{avg_win:.2f}%, 平均亏损: -{avg_loss:.2f}%)")
print(f"★ 获利因子 (Profit Factor): {profit_factor:.2f}")
print(f"★ 平均持仓周期: {df_closed['hold_days'].mean():.1f} 天")
print("=" * 70)

print("\n=== 分年度详细战绩统计 ===")
yearly_stats = []
for yr, grp in df_closed.groupby('year'):
    yr_wins = grp[grp['pnl'] > 0]
    yr_losses = grp[grp['pnl'] <= 0]
    yr_win_rate = len(yr_wins) / len(grp) * 100.0
    yr_pnl = grp['pnl'].sum()
    yearly_stats.append({
        'year': yr,
        'trades': len(grp),
        'win_rate': yr_win_rate,
        'pnl': yr_pnl,
        'avg_win_pct': yr_wins['pnl_pct'].mean() * 100 if len(yr_wins) > 0 else 0,
        'avg_loss_pct': yr_losses['pnl_pct'].mean() * 100 if len(yr_losses) > 0 else 0
    })

for s in yearly_stats:
    print(f"【{s['year']}年】交易: {s['trades']:3d} 笔 | 胜率: {s['win_rate']:5.1f}% | 净盈利: +{s['pnl']:12,.2f} 元 | 均盈: +{s['avg_win_pct']:4.1f}% | 均亏: {s['avg_loss_pct']:4.1f}%")

print("\n=== TOP 5 单笔超级暴利交易 ===")
top5_wins = df_closed.sort_values(by='pnl_pct', ascending=False).head(5)
for _, r in top5_wins.iterrows():
    print(f"  - [{r['code']}] {r['buy_dt'][:10]} 买入({r['buy_price']:.3f}) ➔ {r['sell_dt'][:10]} 卖出({r['sell_price']:.3f}) | 收益: +{r['pnl_pct']*100:.2f}% | 盈利: +{r['pnl']:,.2f}元 (持有 {r['hold_days']} 天)")

print("\n=== TOP 5 单笔最大止损控制交易 ===")
top5_losses = df_closed.sort_values(by='pnl_pct', ascending=True).head(5)
for _, r in top5_losses.iterrows():
    print(f"  - [{r['code']}] {r['buy_dt'][:10]} 买入({r['buy_price']:.3f}) ➔ {r['sell_dt'][:10]} 止损({r['sell_price']:.3f}) | 亏损: {r['pnl_pct']*100:.2f}% | 止损: {r['pnl']:,.2f}元 (持有 {r['hold_days']} 天)")
