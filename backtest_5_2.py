# -*- coding: utf-8 -*-
import os, sys, re
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

log_path = r'c:\Users\Administrator\Desktop\量化策略源代码\五福5.2日内趋势-Clone.txt'

dates = []
equities = []

with open(log_path, 'r', encoding='gbk', errors='ignore') as f:
    for line in f:
        m_equity = re.search(r'(\d{4}-\d{2}-\d{2}).*?总资产[:：]\s*([\d,\.]+)', line)
        if m_equity:
            d_str = m_equity.group(1)
            eq_val = float(m_equity.group(2).replace(',', ''))
            if not dates or dates[-1] != d_str:
                dates.append(d_str)
                equities.append(eq_val)
            else:
                equities[-1] = eq_val

df_eq = pd.DataFrame({'date': pd.to_datetime(dates), 'equity': equities}).drop_duplicates('date').sort_values('date').reset_index(drop=True)
s_date = df_eq.iloc[0]['date'].strftime('%Y-%m-%d')
e_date = df_eq.iloc[-1]['date'].strftime('%Y-%m-%d')
init_cap = df_eq.iloc[0]['equity']
final_cap = df_eq.iloc[-1]['equity']

total_return = (final_cap - init_cap) / init_cap * 100.0
total_days = (df_eq.iloc[-1]['date'] - df_eq.iloc[0]['date']).days
cagr = (final_cap / init_cap) ** (365.25 / total_days) - 1.0

# Max Drawdown
df_eq['cummax'] = df_eq['equity'].cummax()
df_eq['drawdown'] = (df_eq['equity'] - df_eq['cummax']) / df_eq['cummax']
max_dd = df_eq['drawdown'].min() * 100.0
max_dd_date = df_eq.loc[df_eq['drawdown'].idxmin(), 'date'].strftime('%Y-%m-%d')

# Daily returns & Sharpe
df_eq['pct_chg'] = df_eq['equity'].pct_change().fillna(0)
daily_mean = df_eq['pct_chg'].mean()
daily_std = df_eq['pct_chg'].std()
sharpe = (daily_mean / daily_std * np.sqrt(250)) if daily_std > 0 else 0
calmar = abs(cagr * 100.0 / max_dd) if max_dd != 0 else 0

# Yearly breakdown
df_eq['year'] = df_eq['date'].dt.year
yearly = []
for yr, grp in df_eq.groupby('year'):
    y_init = grp.iloc[0]['equity']
    y_final = grp.iloc[-1]['equity']
    y_ret = (y_final - y_init) / y_init * 100.0
    grp_cummax = grp['equity'].cummax()
    grp_dd = ((grp['equity'] - grp_cummax) / grp_cummax).min() * 100.0
    yearly.append({'year': yr, 'return': y_ret, 'max_dd': grp_dd, 'end_eq': y_final})

print(f"=== 五福 5.2 全周期核心回测指标 ({s_date} ~ {e_date}) ===")
print(f"初始资金: {init_cap:,.2f} 元")
print(f"期末资产: {final_cap:,.2f} 元")
print(f"累计总收益: +{total_return:,.2f}% ({final_cap/init_cap:.2f} 倍)")
print(f"年化复合收益率 (CAGR): +{cagr*100:.2f}%")
print(f"最大回撤 (Max Drawdown): {max_dd:.2f}% (低点日期: {max_dd_date})")
print(f"夏普比率 (Sharpe Ratio): {sharpe:.3f}")
print(f"卡玛比率 (Calmar Ratio): {calmar:.3f}")
print(f"总交易天数: {len(df_eq)} 个交易日")
print("\n=== 分年度收益与回测表现 ===")
for row in yearly:
    print(f"【{int(row['year'])} 年】收益率: {row['return']:+8.2f}% | 最大回撤: {row['max_dd']:+7.2f}% | 期末资产: {row['end_eq']:14,.2f} 元")
