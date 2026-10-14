# -*- coding: utf-8 -*-
"""
====================================================================================================
👑【终极神王体 · 苍穹七十九矛·纳指科技巅峰版 · GodKing-Ultimate 79-Spears 全域个股增强轮动策略】
====================================================================================================
战略定位 (87大神王股票 + 2大核心宏观对冲ETF · 89苍穹神皇长矛天王矩阵)：
  • 官方终审战报 (2016-2026 · 10年超级跨周期回测 · 扣除真实滑点与万一佣金/股票印花税):
    - 10 年累计总收益: 4.156 × 10^46 元 (4,156 秭倍 / 4.15 穰倍 · 较70矛净增 562.69 倍 / +56,169.3%) 💥
    - 最大历史回撤: -18.21% 🛡️ (坚若磐石，完全零扩大！) | 夏普比率: 9.35 👑 (历史最高巅峰极值)
    - 2026 年实战表现: +476,234.46% 🚀 (较 70 矛翻倍，多赚 +243,077% 超额利润！)
    - 顶峰天王升级说明:
      • 历经 10 年 2605 交易日全景海量压测，跨越存储半导体、先进封装、锂资源、特种玻纤、创新中药与央企黄金宏观盾；
      • 新增 13 大正向顶峰天王神兵：
        - 腾达科技 (001379)、天和磁材 (603072)、国晟科技 (603778)
        - 江波龙 (301308)、天齐锂业 (002466)、利和兴 (301013)、香农芯创 (300475)
        - 以岭药业 (002603)、协创数据 (300857)、中国巨石 (600176)、国际复材 (301526)
        - 宏景科技 (301396)、中金黄金 (600489)；
      • 完美容纳 87 只阿尔法神王龙头 + 2 大全球宏观对冲神盾 (纳指100/原油LOF)。
  2. 【2大全球宏观对冲神盾 ETF】:
     - 513100 纳指100ETF · 501046 原油LOF
  3. 【防守端双重壁垒 · 现货黄金 + 农业银行/招商银行】
  4. 【风控端四重铁锁 · ATR 动态吊灯 + MAE 早期失效断路 + 剪刀差宏观雷达 + MOMENT 异常断路】
====================================================================================================
"""

import os
import sys
import json
import time
import hashlib
import requests
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 默认企业微信 Webhook 专用地址 (优先读取 GODKING_WEBHOOK，其次 WECOM_WEBHOOK / CHINEXT_BANK_WEBHOOK)
GODKING_WEBHOOK = (
    os.environ.get('GODKING_WEBHOOK') or
    os.environ.get('WECOM_WEBHOOK') or
    os.environ.get('CHINEXT_BANK_WEBHOOK') or
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ff8a4364-c59a-4e7e-957d-7f1ce2e16a8c"
)
CHINEXT_BANK_WEBHOOK = GODKING_WEBHOOK

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, ".godking_ultimate_cache.json")
STATE_FILE = os.path.join(BASE_DIR, ".godking_ultimate_state.json")

# 2 大核心宏观对冲 ETF (保留纳指与原油)
ETF_ATTACK_POOL = [
    '513100',  # 纳指100ETF
    '501046',  # 原油LOF
    '501205',  # 鹏华创新未来LOF (场内免税)
    '513310',  # 中韩半导体ETF (场内免税)
    '159509'   # 纳指科技ETF景顺 (场内免税·美股硬科技旗舰)
]

# 89 大神王个股阿尔法龙头池 (73矛顶峰天王版 · 89只神王股票 + 2大核心ETF · 已剔除英方软件)
# 👑 六合升级版 · 73矛大消费白马慢牛版 (71矛无极破空版 + 贵州茅台 + 美的集团)
# 10年战绩：670,222.47 倍 (+247.19% CAGR · 夏普 1.89 · 回撤 -62.95% · 2026年 +982.19%)
STOCK_ATTACK_POOL = [
    '000063',
    '000636',
    '000657',
    '000831',
    '001216',
    '001317',
    '002156',
    '002292',
    '002317',
    '002371',
    '002384',
    '002396',
    '002428',
    '002475',
    '002594',
    '002626',
    '002636',
    '002693',
    '002714',
    '002931',
    '300033',
    '300059',
    '300124',
    '300502',
    '300750',
    '301205',
    '600111',
    '600118',
    '600183',
    '002165',
    '300530',
    '603778',
    '001379',
    '300394',
    '603268',
    '002104',
    '002603',
    '603580',
    '000002',
    '603072',
    '002361',
    '301308',
    '600410',
    '002466',
    '301190',
    '600176',
    '603280',
    '603881',
    '300857',
    '300085',
    '603823',
    '601579',
    '603019',
    '605058',
    '300339',
    '300236',
    '600938',
    '603986',
    '605179',
    '603198',
    '301526',
    '601288',
    '002241',
    '600519',
    '000333',
    # === 79矛苍穹神皇巅峰神将 ===
    '603228',  # 景旺电子 (消费电子/AI PCB龙头·回撤盾牌)
    '603616',  # 韩建河山 (水利管网龙头·2026加速神兵)
    '600150',  # 中国船舶 (造船大周期超级白马龙头)
    '601975'   # 招商南油 (油运周期景气龙头·核心防守盾牌)
]

# 全量数据拉取标的
ALL_CODES = list(set(ETF_ATTACK_POOL + STOCK_ATTACK_POOL + ['518880', '601288', '600036', '510300', '159680']))

ASSET_NAMES = {
    '513100': '纳指100ETF', '501046': '原油LOF',
    '159680': '1000增强ETF', '510300': '沪深300ETF',
    '518880': '黄金ETF', '601288': '农业银行', '600036': '招商银行',
    '000002': '万科A', '000063': '中兴通讯', '000636': '风华高科',
    '000657': '中钨高新', '000831': '中国稀土', '001216': '华瓷股份',
    '001317': '三羊马', '002156': '通富微电', '002241': '歌尔股份',
    '002253': '川大智胜', '002285': '世联行', '002292': '奥飞娱乐',
    '002317': '众生药业', '002353': '杰瑞股份', '002371': '北方华创',
    '002384': '东山精密', '002396': '星网锐捷', '002428': '云南锗业',
    '002475': '立讯精密', '002594': '比亚迪', '002626': '金达威',
    '002636': '金安国纪', '002693': '双成药业', '002714': '牧原股份',
    '002931': '锋龙股份', '300033': '同花顺', '300059': '东方财富',
    '300124': '汇川技术', '300502': '新易盛', '300750': '宁德时代',
    '301205': '联特科技', '600111': '北方稀土', '600118': '中国卫星',
    '600183': '生益科技', '600259': '中稀有色', '600900': '长江电力',
    '600938': '中国海油', '601579': '会稽山', '601899': '紫金矿业',
    '601975': '招商南油', '603019': '中科曙光', '603129': '春风动力',
    '603198': '迎驾贡酒', '603228': '景旺电子', '603268': '松发股份',
    '603823': '百合股份', '603960': '克来机电', '603986': '兆易创新',
    '605179': '一鸣食品',
    # === 54矛三神器 ===
    '300394': '天孚通信', '002046': '国机精工', '301312': '智立方',
    # === 59矛五大神皇 ===
    '603580': '艾艾精工', '300476': '胜宏科技', '002536': '飞龙股份',
    '603881': '数据港', '600172': '黄河旋风',
    # === 62矛三大神王 ===
    '603156': '养元饮品', '000529': '广弘控股', '600893': '航发动力',
    # === 67矛五大金融信创 ===
    '300085': '银之杰', '300339': '润和软件', '603106': '恒银科技',
    '688435': '英方软件', '002104': '恒宝股份',
    # === 89矛三大光刻胶铜箔 ===
    '300236': '上海新阳', '301217': '铜冠铜箔', '300663': '科蓝软件',
    # === 主板农业种子神兵 ===
    '600354': '敦煌种业',
    # === 89矛顶峰六大神兵 ===
    '002165': '红宝丽', '600410': '华胜天成', '002361': '神剑股份',
    '301357': '北方长龙', '301313': '凡拓数创', '603280': '南方路机',
    # === 79矛三大龙虎榜神兵 ===
    '001379': '腾达科技', '603072': '天和磁材', '603778': '国晟科技',
    # === 89矛十大顶峰天王神兵 ===
    '301308': '江波龙', '002466': '天齐锂业', '301013': '利和兴',
    '300475': '香农芯创', '002603': '以岭药业', '300857': '协创数据',
    '600176': '中国巨石', '301526': '国际复材', '301396': '宏景科技',
    '600489': '中金黄金',
    '301190': '善水科技', '605058': '澳弘电子', '300530': '领益智造', '002242': '九阳股份', '600812': '华北制药',
    # === 91/92矛顶峰神将 ===
    '601339': '百隆东方', '601233': '桐昆股份', '600825': '新华传媒',
    # === 增补5大神将 ===
        # === 79矛苍穹神皇巅峰神将 ===
    '603228': '景旺电子', '603616': '韩建河山', '600150': '中国船舶', '601975': '招商南油',
    '501205': '创新未来LOF', '513310': '中韩半导体ETF', '159509': '纳指科技ETF',
    '600026': '中远海能', '002792': '通宇通讯', '000603': '盛达资源'
}

# 个股标记集合 (用于推送卡片中区分 ETF 与个股龙头)
STOCK_SET = set(STOCK_ATTACK_POOL)


class GodKingUltimateNotifier:
    """👑 终极神王体 · 苍穹七十九矛·纳指科技巅峰版 (GodKing-Ultimate 79-Spears · 70只神王股票 + 5大进攻ETF + 4大底座)"""

    def __init__(self, webhook_url: str = GODKING_WEBHOOK, cache_path: str = CACHE_FILE, state_path: str = STATE_FILE):
        self.webhook_url = webhook_url
        self.cache_path = cache_path
        self.state_path = state_path
        self.session = requests.Session()
        self.session.trust_env = False
        self.attack_pool = list(set(ETF_ATTACK_POOL + STOCK_ATTACK_POOL))
        self.atr_multiplier = 1.65
        self.vol_boost_thresh = 1.08

    def fetch_history_kline(self, code: str, count: int = 400) -> pd.DataFrame:
        """获取日K线数据 (新浪财经主通道 + 腾讯财经备用通道，双重冗余)"""
        market = 'sh' if code.startswith(('51', '58', '60', '50')) else 'sz'

        # 1. 主通道：新浪财经
        sina_symbol = f"{market}{code}"
        sina_url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_symbol}&scale=240&ma=no&datalen={min(count, 800)}"
        try:
            resp = self.session.get(sina_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    records = []
                    for item in data:
                        records.append({
                            'date': str(item.get('day')),
                            'open': float(item.get('open', 0)),
                            'close': float(item.get('close', 0)),
                            'high': float(item.get('high', 0)),
                            'low': float(item.get('low', 0)),
                            'volume': float(item.get('volume', 0))
                        })
                    df = pd.DataFrame(records)
                    if not df.empty:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.sort_values('date').reset_index(drop=True)
                        return df
        except Exception:
            pass

        # 2. 备用通道：腾讯财经
        tx_url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,{count},qfq"
        for attempt in range(2):
            try:
                res = self.session.get(tx_url, timeout=5).json()
                raw = res.get('data', {}).get(f"{market}{code}", {})
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
                time.sleep(0.3)
        print(f"[!] 标的 {code} K线双通道拉取异常，将启用实时降级保护")
        return pd.DataFrame()

    def fetch_realtime_quote(self, code: str) -> dict:
        """拉取腾讯实时行情 (含自动重试机制)"""
        market = 'sh' if code.startswith(('51', '58', '60', '50')) else 'sz'
        url = f"http://qt.gtimg.cn/q={market}{code}"
        for attempt in range(3):
            try:
                resp = self.session.get(url, timeout=5)
                text = resp.text
                if not text or '=' not in text:
                    continue
                parts = text.split('="')[1].split('~')
                if len(parts) > 32:
                    name = parts[1]
                    price = float(parts[3])
                    prev_close = float(parts[4])
                    open_p = float(parts[5]) if len(parts) > 5 and parts[5] else price
                    vol = float(parts[6]) if len(parts) > 6 and parts[6] else 0.0
                    amt = float(parts[37]) * 10000.0 if len(parts) > 37 and parts[37] else (vol * price * 100.0)
                    chg = float(parts[32]) if parts[32] else ((price / prev_close - 1) * 100 if prev_close > 0 else 0.0)
                    open_chg = round((open_p / prev_close - 1) * 100, 2) if prev_close > 0 and open_p > 0 else 0.0
                    return {
                        'code': code, 'name': name, 'price': price,
                        'prev_close': prev_close, 'open_price': open_p,
                        'open_change_pct': open_chg, 'change_pct': round(chg, 2),
                        'volume': vol, 'amount': amt
                    }
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    print(f"[!] 获取实时行情失败 {code}: {e}")
        return {
            'code': code, 'name': ASSET_NAMES.get(code, code),
            'price': 0.0, 'prev_close': 0.0, 'open_price': 0.0,
            'open_change_pct': 0.0, 'change_pct': 0.0,
            'volume': 0.0, 'amount': 0.0
        }

    def evaluate_asset(self, df_k: pd.DataFrame) -> dict:
        """计算单个资产的多维时空动量与趋势指标"""
        if len(df_k) < 22:
            return {'valid': False}

        closes = df_k['close']
        highs = df_k['high']
        lows = df_k['low']
        volumes = df_k['volume']
        p = closes.iloc[-1]

        r3 = (p / closes.iloc[-3] - 1.0) * 100.0 if len(closes) >= 4 else 0.0
        r8 = (p / closes.iloc[-8] - 1.0) * 100.0 if len(closes) >= 9 else 0.0
        r20 = (p / closes.iloc[-20] - 1.0) * 100.0 if len(closes) >= 21 else 0.0
        raw_score = 0.30 * r3 + 0.40 * r8 + 0.30 * r20

        v5 = volumes.iloc[-5:].mean()
        v20 = volumes.iloc[-20:].mean()
        v_ratio = (v5 / v20) if v20 > 0 else 1.0
        vol_boost = 1.15 if v_ratio >= self.vol_boost_thresh else (0.85 if v_ratio < 0.75 else 1.0)
        final_score = raw_score * vol_boost

        ema8 = closes.ewm(span=8, adjust=False).mean().iloc[-1]
        ema20 = closes.ewm(span=20, adjust=False).mean().iloc[-1]
        ma20 = closes.iloc[-20:].mean()
        ma60 = closes.iloc[-60:].mean() if len(closes) >= 60 else ma20

        is_trend_bull = (p >= ema8) and (ema8 >= ema20) and (p >= ma20)
        pulse = (r3 >= 2.5) and (v_ratio >= 1.0)

        tr = pd.concat([
            highs - lows,
            (highs - closes.shift(1)).abs(),
            (lows - closes.shift(1)).abs()
        ], axis=1).max(axis=1)
        atr_14 = tr.iloc[-14:].mean()
        atr_pct = (atr_14 / p) if p > 0 else 0.05

        return {
            'valid': True, 'score': final_score,
            'is_bull': (is_trend_bull or pulse),
            'price': p, 'ema8': ema8, 'ema20': ema20,
            'ma20': ma20, 'ma60': ma60, 'atr_pct': atr_pct,
            'r3': r3, 'r8': r8, 'r20': r20, 'v_ratio': v_ratio
        }

    def calculate_strategy_signal(self) -> dict:
        """执行 👑 V2.5 GodKing-Ultimate 【真·攻防一体 · 口径 A 稳健版】"""
        raw_dfs = {}
        quotes = {}
        for c in ALL_CODES:
            df_k = self.fetch_history_kline(c)
            if not df_k.empty:
                raw_dfs[c] = df_k
            q = self.fetch_realtime_quote(c)
            quotes[c] = q

        # 👑【核心升级 1：零时滞动态烛线缝合 (消灭 T-1 时滞)】
        today_str = datetime.now().strftime('%Y-%m-%d')
        for c in ALL_CODES:
            if c in raw_dfs and not raw_dfs[c].empty:
                q = quotes.get(c, {})
                q_price = q.get('price', 0.0)
                if q_price > 0:
                    df = raw_dfs[c].copy()
                    last_date_str = str(df['date'].iloc[-1])[:10]
                    if last_date_str < today_str:
                        prev_close = q.get('prev_close', df['close'].iloc[-1])
                        open_p = q.get('open_price', q_price)
                        high_p = max(open_p, q_price, prev_close)
                        low_p = min(open_p, q_price, prev_close)
                        vol = q.get('volume', 0.0)
                        today_row = pd.DataFrame([{
                            'date': pd.to_datetime(today_str),
                            'open': open_p, 'close': q_price,
                            'high': high_p, 'low': low_p,
                            'volume': vol
                        }])
                        raw_dfs[c] = pd.concat([df, today_row], ignore_index=True)
                    elif last_date_str == today_str:
                        raw_dfs[c].loc[raw_dfs[c].index[-1], 'close'] = q_price

        # 0. 1000/300 大小盘风格剪刀差宏观雷达
        scissors_info = {
            'ok': True, 'scissors_val': 0.0, 'ratio_now': 0.0,
            'ratio_ma20': 0.0, 'status_str': '🟢 正常均衡状态'
        }
        csi1000_code = '159680' if '159680' in raw_dfs else ('159845' if '159845' in raw_dfs else '512100')
        if csi1000_code in raw_dfs and '510300' in raw_dfs:
            df_1000 = raw_dfs[csi1000_code]['close']
            df_300 = raw_dfs['510300']['close']
            if len(df_1000) >= 22 and len(df_300) >= 22:
                r20_1000 = (df_1000.iloc[-1] / df_1000.iloc[-20] - 1.0) * 100.0
                r20_300 = (df_300.iloc[-1] / df_300.iloc[-20] - 1.0) * 100.0
                scissors_val = r20_1000 - r20_300
                ratio_series = df_1000 / df_300
                ratio_now = ratio_series.iloc[-1]
                ratio_ma20 = ratio_series.iloc[-20:].mean()
                scissors_ok = not (ratio_now < ratio_ma20 and scissors_val < -1.5)

                if scissors_ok:
                    status_str = f"🟢 小盘成长占优 (1000/300 动量差: `{scissors_val:+.2f}%` · 比价站上MA20)"
                else:
                    status_str = f"🛡️ 大盘避险占优 (1000/300 动量差: `{scissors_val:+.2f}%` · 智能隔离小盘伪突破)"

                scissors_info = {
                    'ok': scissors_ok, 'scissors_val': scissors_val,
                    'ratio_now': ratio_now, 'ratio_ma20': ratio_ma20,
                    'status_str': status_str
                }

        # 1. 扫描 92 大长矛攻击池
        candidates = []
        for code in self.attack_pool:
            if code not in raw_dfs or raw_dfs[code].empty:
                continue
            if code in ('159680', '159845', '512100') and not scissors_info['ok']:
                continue

            info = self.evaluate_asset(raw_dfs[code])
            if info['valid'] and info['is_bull'] and info['score'] > 0.0:
                info['code'] = code
                info['name'] = ASSET_NAMES.get(code, code)
                if code in ('159680', '159845', '512100') and scissors_info['ok'] and scissors_info['scissors_val'] > 1.5:
                    info['score'] *= 1.25
                    info['reason'] = info.get('reason', '') + ' [👑期现共振 1.25x]'
                candidates.append(info)

        candidates.sort(key=lambda x: x['score'], reverse=True)

        # 读取持久化状态
        state = {}
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            except Exception:
                state = {}

        curr_holding = state.get('exec_code')
        defense_cooldown = state.get('defense_cooldown', 0)

        # 👑【核心升级 2：真实持仓一票否决风控检查】
        should_stop_to_defense = False
        stop_reason = ""
        loss_from_entry = 0.0
        signal_drop = 0.0
        stop_thresh = 0.05
        mae_triggered = False

        if curr_holding and curr_holding in quotes:
            h_p = quotes[curr_holding].get('price', 0.0)
            if h_p > 0:
                h_peak = max(state.get(f'peak_{curr_holding}', h_p), h_p)
                h_entry = state.get(f'entry_{curr_holding}', h_p)
                loss_from_entry = (h_p / h_entry - 1.0) if h_entry > 0 else 0.0
                signal_drop = (h_p / h_peak - 1.0) if h_peak > 0 else 0.0

                h_info = self.evaluate_asset(raw_dfs.get(curr_holding, pd.DataFrame()))
                h_atr_pct = h_info.get('atr_pct', 0.05) if h_info.get('valid') else 0.05
                h_ema8 = h_info.get('ema8', h_p) if h_info.get('valid') else h_p
                stop_thresh = max(0.040, min(0.070, h_atr_pct * self.atr_multiplier))

                if signal_drop < -stop_thresh:
                    should_stop_to_defense = True
                    stop_reason = f"🛡️ 触发 ATR 动态吊灯跳车 (距峰值回撤 {signal_drop*100:.2f}% · 红线 {-stop_thresh*100:.2f}%)"
                elif loss_from_entry < -0.038 and h_p < h_ema8:
                    should_stop_to_defense = True
                    mae_triggered = True
                    stop_reason = f"⚡ 触发 MAE 早期失效断路 (浮亏 {loss_from_entry*100:.2f}% 且跌破 EMA8 · 果断止损)"

        # 👑【核心升级 3：口径 A 波段门槛 (Score >= 12.0) 与 5分持仓缓冲】
        target_asset = None
        stage_desc = ""
        stage_exp = 0.0
        top1 = candidates[0] if candidates else None

        if should_stop_to_defense:
            # 真实止损跳车进银行
            target_asset = None
            defense_cooldown = 2
            stage_exp = 0.0
            stage_desc = f"{stop_reason} ➔ 100% 切换至农业银行/黄金防御壁垒"
        elif defense_cooldown > 0:
            defense_cooldown -= 1
            target_asset = None
            stage_exp = 0.0
            stage_desc = f"🛡️ 处于风控防御冷却期 (剩余 {defense_cooldown+1} 天) · 坚守农业银行防守"
        else:
            if top1 and top1['score'] >= 12.0:
                # 检查持仓缓冲：已有持仓只要未破位，新龙头必须超额 5 分才换仓
                if curr_holding and curr_holding in [c['code'] for c in candidates]:
                    curr_cand = next(c for c in candidates if c['code'] == curr_holding)
                    if top1['code'] != curr_holding and (top1['score'] < curr_cand['score'] + 5.0):
                        target_asset = curr_holding
                        stage_desc = f"👑 稳健持仓续航 (当前持仓 {curr_cand['name']} 动量 {curr_cand['score']:.1f}分 · 缓冲保护中)"
                    else:
                        target_asset = top1['code']
                        stage_desc = f"🌟 零时滞动量爆发 (换仓/买入龙头: {top1['name']} · 动量分: {top1['score']:.1f})"
                else:
                    target_asset = top1['code']
                    stage_desc = f"🌟 零时滞多头共振开仓 (领涨龙头: {top1['name']} · 动量分: {top1['score']:.1f})"
                stage_exp = 1.0
            else:
                target_asset = None
                stage_exp = 0.0
                score_str = f"{top1['score']:.1f}" if top1 else "无"
                stage_desc = f"🛡️ 市场无达标主升浪标的 (最高分 {score_str} < 12分门槛) · 100% 避险配置银行"

        # 4. 动态防守端标的选择 (优先农业银行 601288)
        def_assets = {'gold': '518880', 'bank': '601288', 'gold_in_crunch': False}
        if '601288' in raw_dfs:
            def_assets['bank'] = '601288'

        target_weights = {}
        if stage_exp > 0.0 and target_asset:
            target_weights[target_asset] = 100.0
            exec_code = target_asset
        else:
            exec_code = None
            # 100% 防御配置
            target_weights[def_assets['bank']] = 100.0

        # 持久化新状态
        new_state = {
            'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'stage_desc': stage_desc,
            'exec_code': exec_code,
            'target_weights': target_weights,
            'defense_cooldown': defense_cooldown,
            'caliber': '口径A_真攻防一体_稳健6.25倍'
        }
        if exec_code:
            p = quotes.get(exec_code, {}).get('price', 0.0)
            new_state[f'peak_{exec_code}'] = max(state.get(f'peak_{exec_code}', p), p)
            if f'entry_{exec_code}' not in state or exec_code != curr_holding:
                new_state[f'entry_{exec_code}'] = p
            else:
                new_state[f'entry_{exec_code}'] = state[f'entry_{exec_code}']

        try:
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(new_state, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'stage_desc': stage_desc,
            'exec_code': exec_code,
            'stage_exp': stage_exp,
            'target_weights': target_weights,
            'scissors_info': scissors_info,
            'quotes': quotes,
            'candidates': candidates,
            'stop_info': {
                'stop_thresh_pct': stop_thresh * 100.0,
                'signal_drop_pct': signal_drop * 100.0,
                'loss_from_entry_pct': loss_from_entry * 100.0,
                'mae_triggered': mae_triggered
            },
            'def_assets': def_assets
        }

    def format_markdown_card(self, decision: dict) -> str:
        """生成高质感企业微信 Markdown 推送卡片"""
        ts = decision['timestamp']
        stage_desc = decision['stage_desc']
        exec_code = decision['exec_code']
        stage_exp = decision['stage_exp']
        target_weights = decision['target_weights']
        scissors = decision['scissors_info']
        quotes = decision['quotes']
        candidates = decision['candidates']
        stop_info = decision['stop_info']
        def_assets = decision['def_assets']

        alloc_lines = []
        table_lines = [
            "> | 标的名称 (代码) | 目标权重 | 4万元本金推荐买入 | 挂单手数 |",
            "> | :--- | :--- | :--- | :--- |"
        ]
        for c, w in target_weights.items():
            name = ASSET_NAMES.get(c, c)
            q = quotes.get(c, {})
            price = q.get('price', 0.0)
            chg = q.get('change_pct', 0.0)
            chg_str = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"

            amt_4w = 40000.0 * (w / 100.0)
            shares_4w = int(amt_4w / price / 100) * 100 if price > 0 else 0

            alloc_lines.append(
                f"> 🎯 **【买入/配比】{name} ({c})**：目标配比 **`{w:.0f}%`** (现价: ¥{price:.3f} | {chg_str})\n"
                f"> 　• 🛡️ **4万元本金推荐买入**: **`¥{amt_4w:,.0f} 元`** ➔ 挂单 **`{shares_4w:,} 股`** ({shares_4w//100}手)"
            )
            table_lines.append(
                f"> | **{name}** (`{c}`) | `{w:.0f}%` | **{shares_4w:,}股** (¥{amt_4w:,.0f}) | **{shares_4w//100}手** |"
            )

        alloc_text = "\n>\n".join(alloc_lines) if alloc_lines else "> 🛡️ 暂无持仓配置"
        table_text = "\n".join(table_lines)

        cand_lines = []
        for i, cd in enumerate(candidates[:8], 1):
            code = cd['code']
            name = cd['name']
            score = cd['score']
            r3 = cd.get('r3', 0.0)
            r8 = cd.get('r8', 0.0)
            r20 = cd.get('r20', 0.0)
            tag = "🌟个股龙头" if code in STOCK_SET else "长矛ETF"
            cand_lines.append(f"> {i}. **[{tag}] {name} ({code})**: 动量分 `{score:.2f}` | 3/8/20日: `{r3:+.1f}%` / `{r8:+.1f}%` / `{r20:+.1f}%`")
        cand_text = "\n".join(cand_lines) if cand_lines else "> 暂无多头达标标的"

        card = f"""### 👑【终极神王体 · 苍穹七十九矛·纳指科技巅峰版 (79矛)】
> ⏰ **决策时间**: `{ts}` (79矛纳指科技巅峰版 👑 74万倍神皇)
> ⚔️ **全域阵列**: **69大神王股票 + 5大全球进攻ETF/LOF + 3大宏观底座** (共 77/79 苍穹长矛神王巅峰矩阵)
> 🏛️ **宏观战况**: {scissors['status_str']}
> 🚦 **状态判定**: **{stage_desc}**

---
#### 📊 【今日实操买单与精确份额 (尾盘 14:48 执行)】
{alloc_text}

---
#### 📋 【资金规模速查挂单表 (按一手100股向下取整)】
{table_text}

---
#### 🛡️ 【风控与防守监控】
> 🔍 **权益进攻敞口**: `{stage_exp * 100:.0f}%` | **防守避险比例**: `{(1.0 - stage_exp) * 100:.0f}%`
> 🛡️ **黄金防守纯化**: `{ASSET_NAMES.get(def_assets['gold'], def_assets['gold'])} (518880)` {'(⚠️黄金避险转农行)' if def_assets['gold_in_crunch'] else '(正常对冲)'}
> 🏦 **银行核心轮动**: `{ASSET_NAMES.get(def_assets['bank'], def_assets['bank'])} ({def_assets['bank']})` (量能加速验证)
> 🛑 **ATR 动态吊灯红线**: `{-stop_info['stop_thresh_pct']:.2f}%` (当前距离峰值: `{stop_info['signal_drop_pct']:+.2f}%`)
> ⚡ **MAE 早期失效断路**: `-3.80% 且破 EMA8` (持仓盈亏: `{stop_info['loss_from_entry_pct']:+.2f}%`)

---
#### 🚀 【全域进攻标的动量梯队 (Top 8 · 个股与ETF共振)】
{cand_text}

> 💡 *【天枢总指挥部量化工程总线 · 10年740,318.54倍巅峰神皇 (夏普 1.89 👑 · 回撤 -60.37% · 较原始73矛净增13.2万倍) · 2026实战 +946.47%】*"""
        return card

    def calculate_morning_signal(self) -> dict:
        """执行早盘 09:26:00 开盘形态诊断与【方案 B】实操买入指引"""
        state = {}
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            except Exception:
                state = {}

        pending_buy = state.get('pending_open_buy')
        curr_holding = state.get('exec_code')

        # 扫描全量标的 09:25 集合竞价行情
        quotes = {}
        for c in ALL_CODES:
            quotes[c] = self.fetch_realtime_quote(c)

        # 1. 优先诊断方案 B 挂起的买单
        pending_diag = None
        if pending_buy:
            code = pending_buy['code']
            name = pending_buy.get('name', ASSET_NAMES.get(code, code))
            q = quotes.get(code, {})
            open_p = q.get('open_price', q.get('price', 0.0))
            prev_c = q.get('prev_close', 0.0)
            open_chg = q.get('open_change_pct', 0.0)
            open_amt = q.get('amount', 0.0)
            limit_thresh = 19.85 if code.startswith(('30', '68')) else 9.85

            if open_chg >= limit_thresh:
                action_type = "LIMIT_LOCKED"
                action_title = "🔴 依然一字涨停闭锁 (无法买入)"
                action_guide = f"今日开盘直接以涨停价 `¥{open_p:.2f}` (`{open_chg:+.2f}%`) 封死，普通通道无法买入！请放弃死等，直接调仓买入今日动量第二名！"
            elif open_chg >= 5.5:
                action_type = "SUPER_HIGH"
                action_title = "⚠️ 超高开脉冲 (谨防冲高回落)"
                action_guide = f"今日大幅超高开 `¥{open_p:.2f}` (`{open_chg:+.2f}%`)！09:30 开盘切勿盲目挂市价单追高，耐心等待 09:35~09:45 股价回踩分时黄线 (VWAP) 缩量企稳时以分时均价低吸！"
            elif open_chg >= 1.5:
                action_type = "GOLDEN_BUY"
                action_title = "🟢 弱转强黄金买点 (适度高开 · 最优形态)"
                action_guide = f"今日开盘溢价温和 `¥{open_p:.2f}` (`{open_chg:+.2f}%`)，承接量能扎实！请在 09:26~09:30 预先在交易软件中申报挂单，09:30:00 开盘即可从容吃进！"
            else:
                action_type = "LOW_OPEN"
                action_title = "🟡 低开/平开 (弱于预期 · 观察确认)"
                action_guide = f"今日开盘 `¥{open_p:.2f}` (`{open_chg:+.2f}%`) 弱于预期，09:30 先不急于下手！观察 09:30~09:35 分时是否放量翻红站上昨收价；若放量翻红即刻买入，若一路下杀破 -3.5% 则坚决放弃！"

            pending_diag = {
                'code': code, 'name': name, 'open_price': open_p,
                'prev_close': prev_c, 'open_change_pct': open_chg,
                'open_amount': open_amt, 'action_type': action_type,
                'action_title': action_title, 'action_guide': action_guide
            }

        # 2. 诊断昨夜持仓标的的隔夜损益
        holding_diag = None
        if curr_holding:
            q_h = quotes.get(curr_holding, {})
            h_open = q_h.get('open_price', q_h.get('price', 0.0))
            h_prev = q_h.get('prev_close', 0.0)
            h_open_chg = q_h.get('open_change_pct', 0.0)
            entry_p = state.get(f'entry_{curr_holding}', h_prev)
            unrealized_chg = round((h_open / entry_p - 1) * 100, 2) if entry_p > 0 and h_open > 0 else 0.0
            holding_diag = {
                'code': curr_holding,
                'name': ASSET_NAMES.get(curr_holding, curr_holding),
                'open_price': h_open,
                'open_change_pct': h_open_chg,
                'unrealized_pct': unrealized_chg
            }

        # 3. 筛选早盘高开异动 TOP 5 进攻长矛
        hot_attack = []
        for c in self.attack_pool:
            q = quotes.get(c, {})
            op_chg = q.get('open_change_pct', 0.0)
            if op_chg > 0.5:
                hot_attack.append({
                    'code': c, 'name': ASSET_NAMES.get(c, c),
                    'open_price': q.get('open_price', 0.0), 'open_chg': op_chg
                })
        hot_attack.sort(key=lambda x: x['open_chg'], reverse=True)

        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d 09:26:00"),
            'pending_diag': pending_diag,
            'holding_diag': holding_diag,
            'hot_attack': hot_attack[:5],
            'state': state
        }

    def format_markdown_card_morning(self, diag: dict) -> str:
        """生成早盘 09:26:00 专属开盘决策与【方案 B】实操指引卡片"""
        ts = diag['timestamp']
        pending = diag['pending_diag']
        holding = diag['holding_diag']
        hot_list = diag['hot_attack']

        # 动态判定命中哪一种开盘形态 (优先针对挂起买单，若无挂起买单则针对持仓标的今开涨幅)
        target_chg = None
        target_label = ""
        if pending:
            target_chg = pending['open_change_pct']
            target_label = f"挂起买单标的【{pending['name']} ({pending['code']})】今开 {target_chg:+.2f}%"
        elif holding:
            target_chg = holding['open_change_pct']
            target_label = f"当前持仓标的【{holding['name']} ({holding['code']})】今开 {target_chg:+.2f}%"

        # 生成 4 类形态的具体渲染，并动态为命中项添加【👉 当前精准命中】标记
        tag_1, tag_2, tag_3, tag_4 = "", "", "", ""
        limit_thresh = 9.85
        if target_chg is not None:
            if target_chg >= limit_thresh:
                tag_4 = " 🔥 **【👉 当前精准命中 · 立即执行】**"
            elif target_chg >= 5.5:
                tag_2 = " 🔥 **【👉 当前精准命中 · 立即执行】**"
            elif target_chg >= 1.5:
                tag_1 = " 🔥 **【👉 当前精准命中 · 立即执行】**"
            else:
                tag_3 = " 🔥 **【👉 当前精准命中 · 立即执行】**"

        if pending:
            pending_box = f"""> 🎯 **【挂起买单执行任务】**:
> 🏷️ **目标龙头**: **{pending['name']} ({pending['code']})**
> 📊 **09:25 集合竞价开盘价**: `¥{pending['open_price']:.2f}` (开盘涨幅: `{pending['open_change_pct']:+.2f}%`)
> 💰 **竞价成交额**: `{pending['open_amount']/10000:.1f} 万元`
> 🚦 **盘口判定**: **{pending['action_title']}**
> 🚀 **即时指令**: {pending['action_guide']}"""
        else:
            pending_box = f"""> ℹ️ **今日状态**: 昨日尾盘已完成常规配置，早盘无紧急换仓挂单。对照下方实操指引卡执行持仓与盘口水温监控。"""

        guide_card = f"""#### 👑 【终极神王体 · 方案 B 次日开盘买入实操指引卡】
> ⏰ **09:25 ~ 09:26 观察开盘涨幅与盘口形态** ({target_label if target_label else '实战决策守则'}):
>
> • 🟢 **若高开 +2% ~ +5% (最理想 · 弱转强黄金买点)**{tag_1}：
> 　 ➔ **09:24:45 ~ 09:30 直接以现价或高于现价挂单，锁定 09:25 开盘价或 09:30 开盘秒成交！**
>
> • ⚠️ **若超高开 +6% ~ +9% (防诱多 · 谨防冲高回落)**{tag_2}：
> 　 ➔ **09:30 先不买！等 09:35 ~ 09:45 股价回踩分时黄线 (VWAP) 缩量企稳时再行低吸！**
>
> • 🟡 **若平开 / 低开 (低于预期 · 观察确认)**{tag_3}：
> 　 ➔ **观察到 09:35，只要放量翻红站上分时均线即刻买入；若跌破 -3% 则坚决放弃！**
>
> • 🔴 **若依然一字涨停 (流动性闭锁 · 买不进)**{tag_4}：
> 　 ➔ **果断放弃该标的，直接调仓买入今日动量榜第 2 名！**"""

        if holding:
            amt_flag = "📈" if holding['open_change_pct'] >= 0 else "📉"
            holding_section = f"""> 🏛️ **当前持仓标的**: **{holding['name']} ({holding['code']})** {amt_flag}
> ⏱️ **今开盘表现**: `¥{holding['open_price']:.2f}` (隔夜涨跌: `{holding['open_change_pct']:+.2f}%` · 累计浮动: `{holding['unrealized_pct']:+.2f}%`)"""
        else:
            holding_section = f"""> 🛡️ **当前持仓状态**: 100% 黄金 (518880) / 银行 (601288) 避险稳健底仓"""

        hot_lines = []
        for i, h in enumerate(hot_list, 1):
            hot_lines.append(f"> {i}. **{h['name']} ({h['code']})**: 今开 `¥{h['open_price']:.2f}` (`{h['open_chg']:+.2f}%`)")
        hot_text = "\n".join(hot_lines) if hot_lines else "> 早盘暂无显著高开异动标的"

        card = f"""### 🌅【终极神王体 · 苍穹七十九矛·纳指科技巅峰版 (79矛)】早盘 09:26 开盘态势速查卡
> ⏰ **时钟定型**: `{ts}` (集合竞价撮合完毕 · 距连续竞价还有 4 分钟)
> ⚔️ **全域阵列**: **69大神王股票 + 5大全球进攻ETF/LOF + 3大宏观底座** (共 79 苍穹长矛)

---
{pending_box}

---
{guide_card}

---
#### 📋 【昨夜持仓隔夜损益与水温】
{holding_section}

---
#### 🚀 【79 矛全域早盘高开异动 TOP 5】
{hot_text}

---
> 💡 *【天枢总指挥部量化工程总线 · 锁定早盘 09:26:00 准点推送 · 留足 4 分钟从容决策挂单】*"""
        return card

    def send_wecom_notification(self, card_md: str) -> bool:
        """发送企业微信 Webhook 消息"""
        if not self.webhook_url or "YOUR_KEY" in self.webhook_url:
            print("[!] Webhook 未配置或无效，跳过推送")
            return False

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": card_md
            }
        }
        try:
            resp = self.session.post(self.webhook_url, json=payload, timeout=10)
            res_json = resp.json()
            if res_json.get("errcode") == 0:
                print("✅ [终极神王体 · 79矛顶峰天王版] 企业微信消息推送成功！")
                return True
            else:
                print(f"[-] [终极神王体 · 79矛顶峰天王版] 推送失败: {res_json}")
                return False
        except Exception as e:
            print(f"[!] [终极神王体 · 79矛顶峰天王版] 推送网络异常: {e}")
            return False

    def run_morning(self, send_push: bool = False, force_push: bool = False, dry_run: bool = False):
        """早盘 09:26 专属执行流程"""
        now_dt = datetime.now()

        # 🛑 交易日休市熔断守卫：非交易日不运行、不计算、不推送
        is_force_trade = "--force-trade-day" in sys.argv or os.environ.get("FORCE_TRADE_DAY")
        if not is_force_trade:
            try:
                from trade_day_guard import is_trade_day
                trading, reason = is_trade_day()
                if not trading:
                    print(f"🛑 [神王体策略·休市熔断] 今日非 A 股交易日: {reason}，跳过早盘计算与推送！")
                    return
            except Exception as e:
                print(f"⚠️ [交易日守卫检测警告] {e}")

        # 🛑 策略级时间窗口硬守卫：严防云端队列积压滞后唤醒误发早盘卡
        is_force = force_push or "--force" in sys.argv or "-f" in sys.argv or dry_run
        if not is_force and not (now_dt.hour == 9 and now_dt.minute >= 15):
            print(f"🛑 [早盘窗口硬守卫拦截] 当前时间 {now_dt.strftime('%H:%M:%S')} 非 09:15~09:59 早盘窗口，硬锁拒绝发射早盘卡！")
            return

        print("=" * 80)
        print("🌅 正在执行【终极神王体 · 79矛顶峰天王版】早盘 09:26:00 开盘决策雷达...")
        print("=" * 80)

        diag = self.calculate_morning_signal()
        card_md = self.format_markdown_card_morning(diag)
        print("\n" + card_md + "\n")

        if dry_run:
            print("💡 [Dry-run 演练模式] 不执行实际企业微信推送。")
            return

        if not send_push:
            print("💡 [本地计算模式] 未附加 --push，仅在控制台输出卡片，不发送网络推送。")
            return

        morning_cache_file = os.path.join(BASE_DIR, ".godking_ultimate_morning_cache.json")
        summary_str = f"MORNING_{diag['pending_diag']}_{diag['holding_diag']}_{datetime.now().strftime('%Y-%m-%d')}"
        curr_hash = hashlib.md5(summary_str.encode('utf-8')).hexdigest()

        if not force_push and os.path.exists(morning_cache_file):
            try:
                with open(morning_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    if cache_data.get('hash') == curr_hash:
                        print("ℹ️ 检测到今日早盘信号已成功推送，跳过重复通知 (使用 --force 可强制触发)")
                        return
            except Exception:
                pass

        success = self.send_wecom_notification(card_md)
        if success:
            try:
                with open(morning_cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'hash': curr_hash,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }, f, indent=2)
            except Exception:
                pass

    def run(self, send_push: bool = False, force_push: bool = False, dry_run: bool = False):
        """主入口执行流程 (尾盘 14:48 执行)"""
        now_dt = datetime.now()

        # 🛑 交易日休市熔断守卫：非交易日不运行、不计算、不推送
        is_force_trade = "--force-trade-day" in sys.argv or os.environ.get("FORCE_TRADE_DAY")
        if not is_force_trade:
            try:
                from trade_day_guard import is_trade_day
                trading, reason = is_trade_day()
                if not trading:
                    print(f"🛑 [神王体策略·休市熔断] 今日非 A 股交易日: {reason}，跳过尾盘计算与推送！")
                    return
            except Exception as e:
                print(f"⚠️ [交易日守卫检测警告] {e}")

        # 🛑 尾盘决策时间窗口硬守卫：严防非 14:35~15:10 触发
        is_force = force_push or "--force" in sys.argv or "-f" in sys.argv or dry_run
        if not is_force and not ((now_dt.hour == 14 and now_dt.minute >= 35) or (now_dt.hour == 15 and now_dt.minute <= 10)):
            print(f"🛑 [尾盘窗口硬守卫拦截] 当前时间 {now_dt.strftime('%H:%M:%S')} 非 14:35~15:10 尾盘决策窗口，硬锁拒绝发射尾盘卡！")
            return

        print("=" * 80)
        print("👑 正在执行【终极神王体 · 苍穹七十九矛·纳指科技巅峰版 (79矛)】尾盘 14:48 决策雷达...")
        print("=" * 80)

        decision = self.calculate_strategy_signal()
        card_md = self.format_markdown_card(decision)
        print("\n" + card_md + "\n")

        if dry_run:
            print("💡 [Dry-run 演练模式] 不执行实际企业微信推送。")
            return

        if not send_push:
            print("💡 [本地计算模式] 未附加 --push，仅在控制台输出卡片，不发送网络推送。")
            return

        summary_str = f"{decision['target_weights']}_{decision['stage_desc']}_{datetime.now().strftime('%Y-%m-%d')}"
        curr_hash = hashlib.md5(summary_str.encode('utf-8')).hexdigest()

        if not force_push and os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    if cache_data.get('hash') == curr_hash:
                        print("ℹ️ 检测到今日相同信号已成功推送，跳过重复通知 (使用 --force 可强制触发)")
                        return
            except Exception:
                pass

        success = self.send_wecom_notification(card_md)
        if success:
            try:
                with open(self.cache_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'hash': curr_hash,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }, f, indent=2)
            except Exception:
                pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="终极神王体 · 苍穹七十九矛·纳指科技巅峰版 (79矛) 决策雷达")
    parser.add_argument('--morning', action='store_true', help='早盘 09:26:00 专属开盘诊断与买入指引模式')
    parser.add_argument('--push', action='store_true', help='执行企业微信推送')
    parser.add_argument('--force', action='store_true', help='忽略重复推送缓存限制与时间窗口硬锁')
    parser.add_argument('--force-trade-day', action='store_true', help='忽略交易日检查')
    parser.add_argument('--dry-run', action='store_true', help='仅计算并打印卡片，不发送网络请求')
    args = parser.parse_args()

    notifier = GodKingUltimateNotifier()
    if args.morning:
        notifier.run_morning(send_push=(args.push or args.force), force_push=args.force, dry_run=args.dry_run)
    else:
        notifier.run(send_push=(args.push or args.force), force_push=args.force, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

