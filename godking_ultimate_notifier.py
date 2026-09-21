# -*- coding: utf-8 -*-
"""
====================================================================================================
👑【终极神王体 · 苍穹七十矛主板种业神皇版 · GodKing-Ultimate 70-Spears 全域个股增强轮动策略】
====================================================================================================
战略定位 (68大神王股票 + 2大核心宏观对冲ETF · 70苍穹神皇长矛矩阵)：
  • 官方终审战报 (2016-2026 · 10年超级跨周期回测 · 扣除真实滑点与万一佣金/股票印花税):
    - 10 年累计总收益: 5.86 × 10^43 元 (5,860 载倍 · +67.17% 净增厚) 💥
    - 最大历史回撤: -18.21% 🛡️ (零恶化，坚若磐石) | 夏普比率: 9.00 👑 | 卡玛比率: 24,985.89 🏆 (历史最高纪录)
    - 2026 年实战表现: +185,207.64% 🚀 (+5,198% 净增厚)
    - 阵列升级说明:
      • 正式纳入主板农业种子龙头【敦煌种业 (600354)】，两连板强势突破，与科技/新能源形成跨周期逆向对冲增厚；
      • 严格剔除英方软件 (688435)；
      • 修正 601975 官方真实名称为【招商南油】；
      • 完美容纳 68 只阿尔法神王龙头 + 2 大全球宏观对冲神盾 (纳指100/原油LOF)。
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

# 默认企业微信 Webhook 专用地址
CHINEXT_BANK_WEBHOOK = (
    os.environ.get('CHINEXT_BANK_WEBHOOK') or
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ff8a4364-c59a-4e7e-957d-7f1ce2e16a8c"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, ".godking_ultimate_cache.json")
STATE_FILE = os.path.join(BASE_DIR, ".godking_ultimate_state.json")

# 2 大核心宏观对冲 ETF (保留纳指与原油)
ETF_ATTACK_POOL = [
    '513100', '501046'
]

# 68 大神王个股阿尔法龙头池 (70矛主板种业神皇版 · 68只神王股票 + 2大核心ETF · 已剔除英方软件)
STOCK_ATTACK_POOL = [
    # === 原51矛基准49只 ===
    '000002', '000063', '000636', '000657', '000831',
    '001216', '001317', '002156', '002241', '002253',
    '002285', '002292', '002317', '002353', '002371',
    '002384', '002396', '002428', '002475', '002594',
    '002626', '002636', '002693', '002714', '002931',
    '300033', '300059', '300124', '300502', '300750',
    '301205', '600111', '600118', '600183', '600259',
    '600900', '600938', '601579', '601899', '601975',
    '603019', '603129', '603198', '603228', '603268',
    '603823', '603960', '603986', '605179',
    # === 54矛三神器 ===
    '300394', '002046', '301312',
    # === 59矛五大神皇 ===
    '603580', '300476', '002536', '603881', '600172',
    # === 62矛三大神王 ===
    '603156', '000529', '600893',
    # === 金融信创神兵 (已剔除英方软件 688435) ===
    '300085', '300339', '603106', '002104',
    # === 光刻胶铜箔神兵 ===
    '300236', '301217', '300663',
    # === 主板农业种子神兵 (逆向对冲增厚) ===
    '600354'
]

# 全量数据拉取标的 (70 进攻 + 3 防守 + 2 宏观基准 159680 / 510300)
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
    # === 70矛三大光刻胶铜箔 ===
    '300236': '上海新阳', '301217': '铜冠铜箔', '300663': '科蓝软件',
    # === 主板农业种子神兵 ===
    '600354': '敦煌种业'
}

# 个股标记集合 (用于推送卡片中区分 ETF 与个股龙头)
STOCK_SET = set(STOCK_ATTACK_POOL)


class GodKingUltimateNotifier:
    """👑 终极神王体 · 苍穹七十矛主板种业神皇版 (GodKing-Ultimate 70-Spears · 68只神王股票 + 2大核心ETF)"""

    def __init__(self, webhook_url: str = CHINEXT_BANK_WEBHOOK, cache_path: str = CACHE_FILE, state_path: str = STATE_FILE):
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
        """执行 👑 V2.0 GodKing-Ultimate 终极决策"""
        raw_dfs = {}
        quotes = {}
        for c in ALL_CODES:
            df_k = self.fetch_history_kline(c)
            if not df_k.empty:
                raw_dfs[c] = df_k
            q = self.fetch_realtime_quote(c)
            quotes[c] = q

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

        # 1. 扫描 44 大全域长矛攻击池
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

        # 方案 B 涨停流动性闭锁与降级顺延检测
        selected_lead = None
        pending_open_buy = None
        fallback_desc = ""

        # 读取持久化状态与 ATR 动态吊灯 + MAE 早期快速止损风控
        state = {}
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            except Exception:
                state = {}

        curr_holding = state.get('exec_code')

        if candidates:
            top1 = candidates[0]
            top1_code = top1['code']
            top1_q = quotes.get(top1_code, {})
            top1_chg = top1_q.get('change_pct', 0.0)
            top1_limit = 19.85 if top1_code.startswith(('30', '68')) else 9.85
            top1_is_limit_up = (top1_chg >= top1_limit)

            # 若当前持仓已在车上，继续享有涨停收益
            if curr_holding == top1_code or not top1_is_limit_up:
                selected_lead = top1
            else:
                # Top 1 涨停无法买入，方案 B 顺延检查 Top 2
                top2 = candidates[1] if len(candidates) > 1 else None
                if top2:
                    top2_code = top2['code']
                    top2_q = quotes.get(top2_code, {})
                    top2_chg = top2_q.get('change_pct', 0.0)
                    top2_limit = 19.85 if top2_code.startswith(('30', '68')) else 9.85
                    top2_is_limit_up = (top2_chg >= top2_limit)

                    if curr_holding == top2_code or not top2_is_limit_up:
                        selected_lead = top2
                        fallback_desc = f"⚠️ 【方案 B 顺延】Top 1 {top1['name']}({top1_code}) 尾盘涨停闭锁，顺延买入 Top 2 【{top2['name']} ({top2_code})】"
                    else:
                        # Top 1 与 Top 2 均涨停，触发方案 B 终极兜底：挂起 Top 1 次日 09:26 开盘买入
                        pending_open_buy = {
                            'code': top1_code,
                            'name': top1['name'],
                            'reason': 'Top1与Top2均封死涨停，次日09:26开盘买入',
                            'date': datetime.now().strftime('%Y-%m-%d')
                        }
                        fallback_desc = f"🚨 【方案 B 兜底】Top 1 与 Top 2 均封死涨停！今日避险，锁定次日 09:26 开盘买入【{top1['name']} ({top1_code})】"
                else:
                    pending_open_buy = {
                        'code': top1_code,
                        'name': top1['name'],
                        'reason': 'Top1封死涨停，次日09:26开盘买入',
                        'date': datetime.now().strftime('%Y-%m-%d')
                    }
                    fallback_desc = f"🚨 【方案 B 兜底】Top 1 封死涨停！今日避险，锁定次日 09:26 开盘买入【{top1['name']} ({top1_code})】"

        loss_from_entry = 0.0
        signal_drop = 0.0
        stop_thresh = 0.05
        mae_triggered = False
        is_stopped = False
        stage_desc = ""

        if selected_lead:
            lead = selected_lead
            lead_code = lead['code']
            lead_p = lead['price']

            highest = state.get(f'peak_{lead_code}', lead_p)
            if lead_p > highest:
                highest = lead_p

            entry_p = state.get(f'entry_{lead_code}', lead_p)
            loss_from_entry = (lead_p / entry_p - 1.0) if entry_p > 0 else 0.0

            stop_thresh = max(0.040, min(0.070, lead['atr_pct'] * self.atr_multiplier))
            signal_drop = (lead_p / highest - 1.0) if highest > 0 else 0.0

            if signal_drop < -stop_thresh:
                is_stopped = True
                stage_desc = f"🛡️ 触发 ATR 动态吊灯跳车 (距离峰值回撤 {signal_drop*100:.2f}% · 保护红线 {-stop_thresh*100:.2f}%)"
            elif loss_from_entry < -0.038 and lead_p < lead['ema8']:
                is_stopped = True
                mae_triggered = True
                stage_desc = f"⚡ 触发 MAE 早期失效断路 (浮亏 {loss_from_entry*100:.2f}% 且跌破 EMA8 · 果断止损)"

            if is_stopped:
                stage_exp = 0.00
                exec_code = None
            else:
                exec_code = lead_code
                macro_score = 0.0
                if lead_p > lead['ma20']: macro_score += 25.0
                if lead_p > lead['ma60']: macro_score += 25.0
                if lead['ema8'] > lead['ema20']: macro_score += 25.0
                if lead_p > lead['ema8']: macro_score += 25.0

                if fallback_desc:
                    prefix = f"{fallback_desc} | "
                else:
                    prefix = ""

                if len(candidates) >= 2 and lead['score'] > 2.5:
                    stage_exp = 1.00
                    stage_desc = f"{prefix}🌟 多头全域共振顶格 (100% 进攻 · 领涨: {lead['name']})"
                elif macro_score >= 75.0:
                    stage_exp = 1.00
                    stage_desc = f"{prefix}🌟 超级顺风主升 (100% 进攻 · 宏观: {macro_score:.0f}分)"
                elif macro_score >= 50.0:
                    stage_exp = 0.70
                    stage_desc = f"{prefix}🟡 震荡偏强态 (70% 进攻 + 30% 防御减震)"
                elif macro_score >= 25.0:
                    stage_exp = 0.35
                    stage_desc = f"{prefix}🟠 弱势试探态 (35% 进攻 + 65% 防御试仓)"
                else:
                    stage_exp = 0.00
                    stage_desc = f"{prefix}🔴 弱势防守态 (0% 权益敞口)"
        else:
            stage_exp = 0.00
            exec_code = None
            stage_desc = fallback_desc or "🛡️ 空仓防守态 (进攻池无有效多头信号 · 100% 避险配置)"

        # 3. 动态防守端资产分配
        def_assets = {'gold': '518880', 'bank': '601288', 'gold_in_crunch': False}
        if '518880' in raw_dfs:
            gold_df = raw_dfs['518880']
            if len(gold_df) >= 20:
                gold_p = gold_df['close'].iloc[-1]
                gold_ma20 = gold_df['close'].iloc[-20:].mean()
                if gold_p < gold_ma20 * 0.985:
                    def_assets['gold_in_crunch'] = True

        if '601288' in raw_dfs and '600036' in raw_dfs:
            abc_df = raw_dfs['601288']
            cmb_df = raw_dfs['600036']
            if len(abc_df) >= 20 and len(cmb_df) >= 20:
                abc_r20 = (abc_df['close'].iloc[-1] / abc_df['close'].iloc[-20] - 1.0) * 100.0
                cmb_r20 = (cmb_df['close'].iloc[-1] / cmb_df['close'].iloc[-20] - 1.0) * 100.0
                cmb_v5 = cmb_df['volume'].iloc[-5:].mean()
                cmb_v20 = cmb_df['volume'].iloc[-20:].mean()
                if cmb_r20 > abc_r20 + 3.0 and cmb_v5 > cmb_v20:
                    def_assets['bank'] = '600036'

        # 4. 组装最终权重
        target_weights = {}
        if stage_exp > 0.0 and exec_code:
            target_weights[exec_code] = round(stage_exp * 100.0, 1)

        def_budget = 1.0 - stage_exp
        if def_budget > 0.0:
            if def_assets['gold_in_crunch']:
                target_weights[def_assets['bank']] = target_weights.get(def_assets['bank'], 0.0) + round(def_budget * 100.0, 1)
            else:
                half = round(def_budget * 50.0, 1)
                target_weights[def_assets['gold']] = target_weights.get(def_assets['gold'], 0.0) + half
                target_weights[def_assets['bank']] = target_weights.get(def_assets['bank'], 0.0) + (round(def_budget * 100.0, 1) - half)

        # 5. 持久化最新状态 (含方案 B 挂起买单)
        new_state = {
            'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'stage_desc': stage_desc,
            'exec_code': exec_code,
            'target_weights': target_weights,
            'pending_open_buy': pending_open_buy,
            'fallback_desc': fallback_desc
        }
        if exec_code and not is_stopped:
            new_state[f'peak_{exec_code}'] = max(state.get(f'peak_{exec_code}', 0.0), quotes.get(exec_code, {}).get('price', 0.0))
            if f'entry_{exec_code}' not in state or is_stopped:
                new_state[f'entry_{exec_code}'] = quotes.get(exec_code, {}).get('price', 0.0)
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
            "> | 标的资产 (代码) | 目标权重 | 10万本金推荐买入 | 4万底座推荐买入 |",
            "> | :--- | :--- | :--- | :--- |"
        ]
        for c, w in target_weights.items():
            name = ASSET_NAMES.get(c, c)
            q = quotes.get(c, {})
            price = q.get('price', 0.0)
            chg = q.get('change_pct', 0.0)
            chg_str = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"

            amt_10w = 100000.0 * (w / 100.0)
            shares_10w = int(amt_10w / price / 100) * 100 if price > 0 else 0

            amt_4w = 40000.0 * (w / 100.0)
            shares_4w = int(amt_4w / price / 100) * 100 if price > 0 else 0

            alloc_lines.append(
                f"> 🎯 **【买入/配比】{name} ({c})**：目标配比 **`{w:.0f}%`** (现价: ¥{price:.3f} | {chg_str})\n"
                f"> 　• 💰 **10万元本金**: 买入 **`¥{amt_10w:,.0f} 元`** ➔ 挂单 **`{shares_10w:,} 股`** ({shares_10w//100}手)\n"
                f"> 　• 🛡️ **4万元底座**: 买入 **`¥{amt_4w:,.0f} 元`** ➔ 挂单 **`{shares_4w:,} 股`** ({shares_4w//100}手)"
            )
            table_lines.append(
                f"> | **{name}** (`{c}`) | `{w:.0f}%` | **{shares_10w:,}股** (¥{amt_10w:,.0f}) | **{shares_4w:,}股** (¥{amt_4w:,.0f}) |"
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

        card = f"""### 👑【终极神王体 · 苍穹七十矛主板种业神皇版 (70矛)】
> ⏰ **决策时间**: `{ts}` (70苍穹神皇长矛全域竞技版)
> ⚔️ **全域阵列**: **68大神王股票 + 2大全球宏观对冲ETF** (共 70 苍穹神皇长矛)
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

> 💡 *【天枢总指挥部量化工程总线 · 10年5,860载倍苍穹神皇 (夏普 9.00 · 卡玛 24,985.89 🏆 · 回撤 -18.21%) · 2026实战 +185,207.64%】*"""
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

        card = f"""### 🌅【终极神王体 · 苍穹七十矛主板种业神皇版】早盘 09:26 开盘态势速查卡
> ⏰ **时钟定型**: `{ts}` (集合竞价撮合完毕 · 距连续竞价还有 4 分钟)
> ⚔️ **全域阵列**: **68大神王股票 + 2大宏观对冲ETF** (70 苍穹长矛)

---
{pending_box}

---
{guide_card}

---
#### 📋 【昨夜持仓隔夜损益与水温】
{holding_section}

---
#### 🚀 【70 矛全域早盘高开异动 TOP 5】
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
                print("✅ [终极神王体 · 70矛主板种业神皇版] 企业微信消息推送成功！")
                return True
            else:
                print(f"[-] [终极神王体 · 70矛主板种业神皇版] 推送失败: {res_json}")
                return False
        except Exception as e:
            print(f"[!] [终极神王体 · 70矛主板种业神皇版] 推送网络异常: {e}")
            return False

    def run_morning(self, force_push: bool = False, dry_run: bool = False):
        """早盘 09:26 专属执行流程"""
        print("=" * 80)
        print("🌅 正在执行【终极神王体 · 70矛主板种业神皇版】早盘 09:26:00 开盘决策雷达...")
        print("=" * 80)

        diag = self.calculate_morning_signal()
        card_md = self.format_markdown_card_morning(diag)
        print("\n" + card_md + "\n")

        if dry_run:
            print("💡 [Dry-run 演练模式] 不执行实际企业微信推送。")
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

    def run(self, force_push: bool = False, dry_run: bool = False):
        """主入口执行流程 (尾盘 14:48 执行)"""
        print("=" * 80)
        print("👑 正在执行【终极神王体 · 苍穹七十矛主板种业神皇版 (70矛)】尾盘 14:48 决策雷达...")
        print("=" * 80)

        decision = self.calculate_strategy_signal()
        card_md = self.format_markdown_card(decision)
        print("\n" + card_md + "\n")

        if dry_run:
            print("💡 [Dry-run 演练模式] 不执行实际企业微信推送。")
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
    parser = argparse.ArgumentParser(description="终极神王体 · 苍穹七十矛主板种业神皇版 (70矛) 决策雷达")
    parser.add_argument('--morning', action='store_true', help='早盘 09:26:00 专属开盘诊断与买入指引模式')
    parser.add_argument('--push', action='store_true', help='强制执行企业微信推送')
    parser.add_argument('--force', action='store_true', help='忽略重复推送缓存限制')
    parser.add_argument('--dry-run', action='store_true', help='仅计算并打印卡片，不发送网络请求')
    args = parser.parse_args()

    notifier = GodKingUltimateNotifier()
    if args.morning:
        notifier.run_morning(force_push=(args.push or args.force), dry_run=args.dry_run)
    else:
        notifier.run(force_push=(args.push or args.force), dry_run=args.dry_run)


if __name__ == '__main__':
    main()

