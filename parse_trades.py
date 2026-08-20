# -*- coding: utf-8 -*-
import os, sys, re
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

log_path = r'c:\Users\Administrator\Desktop\量化策略源代码\五福5.2日内趋势-Clone.txt'

# We can parse all trades: Buy and Sell
trades = []
# Also let's find all dates in the log
daily_positions = {}

with open(log_path, 'r', encoding='gbk', errors='ignore') as f:
    for line in f:
        # Match Buy: 买入 512770.XSHG 战略新兴 数量22900 价格2.179
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
            
        # Match Sell: 卖出 159967.XSHE 创业板成长ETF华夏 数量44000 或 已卖出: 512770.XSHG 或 止损卖出
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
print(f"Total parsed trade executions: {len(df_trades)}")
if not df_trades.empty:
    print(df_trades.head(10))
    print(df_trades.tail(10))
