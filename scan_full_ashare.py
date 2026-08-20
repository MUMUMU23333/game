# -*- coding: utf-8 -*-
import urllib.request, json, ssl, time, concurrent.futures, sys, os
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("================================================================================")
print("★ 启动 A 股全市场（5,000+ 只股票）量化扫描引擎...")
print("★ 筛选条件: 8月18日最高价 > (6月底高点 + 7月底低点) 的中轴半分位")
print("================================================================================")

# 1. 抓取全市场 5500+ A 股列表
def get_page(p):
    url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={p}&num=100&sort=symbol&asc=1&node=hs_a&symbol=&_s_r_a=init'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            return json.loads(resp.read().decode('gbk', errors='ignore'))
    except Exception:
        return []

all_stocks_raw = []
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(get_page, p) for p in range(1, 60)]
    for f in concurrent.futures.as_completed(futures):
        res = f.result()
        if res:
            all_stocks_raw.extend(res)

print(f"★ 成功获取全市场标的: {len(all_stocks_raw)} 只")

# 剔除 ST、*ST、退市股
valid_stocks = []
for item in all_stocks_raw:
    sym = item.get('symbol', '')
    name = item.get('name', '')
    if 'ST' in name or '*ST' in name or '退' in name:
        continue
    if sym.startswith(('sh60', 'sh68', 'sz00', 'sz30', 'bj8', 'bj9', 'bj4')):
        valid_stocks.append({'symbol': sym, 'code': item.get('code', sym[2:]), 'name': name})

print(f"★ 剔除 ST/退市后，待扫描有效标的: {len(valid_stocks)} 只")

# 2. 多线程高并发调取 K 线并计算公式
def check_stock_kline(item):
    sym = item['symbol']
    name = item['name']
    code = item['code']
    
    url = f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,2024-06-01,2024-08-20,100,qfq'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            stock_data = data.get('data', {}).get(sym, {})
            klines = stock_data.get('qfqday', stock_data.get('day', []))
            if not klines or len(klines) < 15:
                return None
            
            df = pd.DataFrame(klines)
            # 格式: [date, open, close, high, low, volume]
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume'][:len(df.columns)]
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            
            df_jun = df[df['date'].str.startswith('2024-06')]
            df_jul = df[df['date'].str.startswith('2024-07')]
            df_aug18 = df[(df['date'] >= '2024-08-15') & (df['date'] <= '2024-08-19')]
            
            if df_jun.empty or df_jul.empty or df_aug18.empty:
                return None
                
            h_jun = df_jun.iloc[-1]['high']
            l_jul = df_jul.iloc[-1]['low']
            h_aug18 = df_aug18['high'].max()
            
            if h_jun <= 0 or l_jul <= 0 or h_aug18 <= 0:
                return None
                
            mid_line = (h_jun + l_jul) / 2.0
            break_diff = h_aug18 - mid_line
            break_pct = (break_diff / mid_line) * 100.0
            
            if break_diff > 0:  # 筛选 8/18最高 > 中轴线
                return {
                    'code': code,
                    'symbol': sym,
                    'name': name,
                    'h_jun': round(h_jun, 3),
                    'l_jul': round(l_jul, 3),
                    'mid_line': round(mid_line, 3),
                    'h_aug18': round(h_aug18, 3),
                    'break_diff': round(break_diff, 3),
                    'break_pct': round(break_pct, 2)
                }
    except Exception:
        return None

results = []
count = 0
start_t = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
    futures = [executor.submit(check_stock_kline, item) for item in valid_stocks]
    for f in concurrent.futures.as_completed(futures):
        res = f.result()
        if res:
            results.append(res)
        count += 1
        if count % 1000 == 0:
            print(f"  - 进度: 已扫描 {count}/{len(valid_stocks)} 只股票，已命中 {len(results)} 只...")

df_results = pd.DataFrame(results).sort_values(by='break_pct', ascending=False).reset_index(drop=True)
elapsed = time.time() - start_t

print(f"\n================================================================================")
print(f"★ 全市场扫描完毕！耗时: {elapsed:.1f} 秒")
print(f"★ 全市场符合【8月18日最高价 > (6月底高点+7月底低点)/2】的股票共计: {len(df_results)} 只！")
print(f"================================================================================")

# 保存完整结果至 CSV
csv_path = r'c:\Users\Administrator\Desktop\量化策略源代码\A股全市场_8月18日突破中轴半分位选股清单.csv'
df_results.to_csv(csv_path, index=False, encoding='utf_8_sig')
print(f"★ 完整清单已成功导出至: {csv_path}\n")

# 打印 TOP 35 领涨突破先锋
print("=== TOP 35 全市场最强突破龙头股票 ===")
print(f"{'排名':<4} {'代码':<8} {'名称':<10} {'6月底高':<9} {'7月底低':<9} {'中轴半分位':<11} {'8/18最高':<9} {'突破超额':<10} {'突破幅度%':<10}")
print("-" * 88)
for i in range(min(35, len(df_results))):
    r = df_results.iloc[i]
    print(f"{i+1:<4} {r['code']:<8} {r['name']:<10} {r['h_jun']:<9.2f} {r['l_jul']:<9.2f} {r['mid_line']:<11.2f} {r['h_aug18']:<9.2f} {r['break_diff']:<+10.2f} {r['break_pct']:<+10.2f}%")
