# -*- coding: utf-8 -*-
import urllib.request, json, ssl, time, concurrent.futures, sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 扩展全市场各行业核心股票池（覆盖金融、消费、科技、新能源、周期、医药、制造等）
stock_pool = [
    # 白酒/食品/消费
    'sh600519', 'sz000858', 'sz000568', 'sh600809', 'sz002304', 'sh603288', 'sz000895', 'sh600887',
    'sh600779', 'sz000799', 'sh603369', 'sh600600', 'sh600132', 'sz002568', 'sz000596', 'sh600702',
    # 医药生物/医疗/CXO/中药
    'sh600276', 'sz300760', 'sz300122', 'sh603259', 'sz000963', 'sz000661', 'sh600436', 'sz300347',
    'sz002252', 'sz300015', 'sh600196', 'sh600763', 'sz000538', 'sh600079', 'sz300595', 'sh600998',
    'sh600521', 'sz002821', 'sz300142', 'sh603392',
    # 新能源/光伏/锂电/储能
    'sz300750', 'sz002594', 'sh601012', 'sz002460', 'sz002466', 'sz300274', 'sh601877', 'sz002812',
    'sh600438', 'sz002074', 'sz300014', 'sh688599', 'sz300763', 'sh603806', 'sh600875', 'sz002129',
    'sz002202', 'sh601615', 'sh688223', 'sz300316',
    # 半导体/芯片/硬科技
    'sh688981', 'sh688012', 'sz002371', 'sh603501', 'sh603986', 'sz002049', 'sh600584', 'sz300661',
    'sh688041', 'sh600703', 'sz002156', 'sz300308', 'sz300502', 'sh688036', 'sh688008', 'sh603893',
    'sz002185', 'sh600460', 'sh688126', 'sz002409',
    # AI人工智能/算力/数字经济/互联网
    'sz300418', 'sz002230', 'sh601360', 'sz002236', 'sh600570', 'sz300059', 'sh600588', 'sz300033',
    'sh600050', 'sh601728', 'sh600941', 'sz000977', 'sh603019', 'sz002415', 'sz300002', 'sz002065',
    'sh603444', 'sz300339', 'sh688111', 'sz002123',
    # 周期/大宗/资源/化工/有色
    'sh601857', 'sh600028', 'sh601088', 'sh601899', 'sh600547', 'sh600111', 'sh600309', 'sh600019',
    'sh601225', 'sh601898', 'sz000878', 'sz000426', 'sh600362', 'sh603993', 'sh600497', 'sh601600',
    'sz000630', 'sh600516', 'sh600219', 'sz000792',
    # 金融/券商/银行/保险
    'sh600030', 'sh601318', 'sh601166', 'sh600036', 'sh601398', 'sh601288', 'sh601939', 'sh601988',
    'sh601688', 'sz000776', 'sh600999', 'sz000166', 'sh600958', 'sh601788', 'sh601211', 'sz002736',
    'sh601601', 'sh601336', 'sz000001', 'sh601818', 'sh601998',
    # 军工装备/高端制造/低空经济
    'sh600893', 'sh600760', 'sz000768', 'sz002179', 'sh600316', 'sh600150', 'sh601989', 'sh600879',
    'sh600862', 'sz002013', 'sz000738', 'sh600372', 'sz000099', 'sz002389',
    # 汽车产业链/家电/高端制造
    'sh601238', 'sh601633', 'sz000625', 'sh600104', 'sz002050', 'sh600699', 'sz002920', 'sz300680',
    'sz000333', 'sz000651', 'sh600690', 'sz002241', 'sh601799', 'sz002475'
]

# 批量获取中文名称
name_map = {}
for i in range(0, len(stock_pool), 40):
    batch = stock_pool[i:i+40]
    quote_url = 'http://qt.gtimg.cn/q=' + ','.join(batch)
    try:
        req = urllib.request.Request(quote_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            for line in resp.read().decode('gbk').split(';'):
                if '~' in line:
                    p = line.split('~')
                    if len(p) > 2:
                        name_map[p[2]] = p[1]
    except Exception as e:
        pass

def process_stock(sym):
    code_pure = sym[2:]
    name = name_map.get(code_pure, code_pure)
    url = f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,2024-06-01,2024-08-20,100,qfq'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            stock_data = data.get('data', {}).get(sym, {})
            klines = stock_data.get('qfqday', stock_data.get('day', []))
            if not klines:
                return None
            
            df = pd.DataFrame(klines, columns=['date', 'open', 'close', 'high', 'low', 'volume'][:len(klines[0])])
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            
            df_jun = df[df['date'].str.startswith('2024-06')]
            df_jul = df[df['date'].str.startswith('2024-07')]
            # 8月18日对应交易日（2024年8月18日为周日，对应周五8月16日或周一8月19日）
            df_aug18 = df[(df['date'] >= '2024-08-15') & (df['date'] <= '2024-08-19')]
            
            if df_jun.empty or df_jul.empty or df_aug18.empty:
                return None
                
            h_jun = df_jun.iloc[-1]['high']
            l_jul = df_jul.iloc[-1]['low']
            h_aug18 = df_aug18['high'].max()  # 取8月18日前后最高价
            
            mid_line = (h_jun + l_jul) / 2.0
            # 突破幅度 (8月18日最高价 - 中轴半分位)
            break_diff = h_aug18 - mid_line
            break_pct = (break_diff / mid_line) * 100.0
            
            return {
                'code': code_pure,
                'name': name,
                'h_jun': h_jun,
                'l_jul': l_jul,
                'mid_line': mid_line,
                'h_aug18': h_aug18,
                'break_diff': break_diff,
                'break_pct': break_pct,
                'is_break_above': break_diff > 0
            }
    except Exception as e:
        return None

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    futures = {executor.submit(process_stock, s): s for s in stock_pool}
    for future in concurrent.futures.as_completed(futures):
        res = future.result()
        if res:
            results.append(res)

df_all = pd.DataFrame(results)
# 筛选 8月18日最高价 > 中轴线 (突破强势股)
df_strong = df_all[df_all['is_break_above'] == True].sort_values(by='break_pct', ascending=False).reset_index(drop=True)

print(f"★ 扫描完成！共分析 {len(df_all)} 只核心标的。")
print(f"★ 其中【8月18日最高价 > (6月高+7月低)/2 中轴半分位】的强势突破股票共有: {len(df_strong)} 只 (占比 {len(df_strong)/len(df_all)*100:.1f}%)。\n")

print("=" * 95)
print(f"{'序号':<4} {'代码':<8} {'股票名称':<10} {'6月底高点':<10} {'7月底低点':<10} {'中轴半分位':<10} {'8/18最高价':<10} {'突破超额(元)':<12} {'突破幅度%':<10}")
print("=" * 95)

for idx, r in df_strong.iterrows():
    print(f"{idx+1:<4} {r['code']:<8} {r['name']:<10} {r['h_jun']:<10.2f} {r['l_jul']:<10.2f} {r['mid_line']:<10.2f} {r['h_aug18']:<10.2f} {r['break_diff']:<+12.2f} {r['break_pct']:<+10.2f}%")

print("=" * 95)
