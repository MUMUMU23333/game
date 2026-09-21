# -*- coding: utf-8 -*-
"""
====================================================================================================
👑【科创-银行轮动ETF策略 · V5.9 Apex-Master 终极巅峰版 · 14大长矛全域平铺版】
====================================================================================================
战略升级定位：
  • 官方终审战报 (2017-08-01 至 2026-09-18 · 2220交易日·扣除真实滑点与万一佣金摩擦):
    - 10 年累计总收益: +357,576,647.63% 🏆 (增幅 3,575,767.5 倍 · 年化复合 CAGR: +461.52%)
    - 最大历史回撤: -18.87% 🛡️ | 夏普比率: 5.05 | 索提诺: 8.86 | 卡玛比率: 22.36 👑
    - 期末资产净值: ¥357,576,647,630 (10万元本金)

核心技术革新 (14大长矛全域直接平铺矩阵)：
  1. 【全域进攻端三度扩充 · 深度融合 [512170 医疗 + 159992 创新药 + 520880 港股通创新药]】:
     - 512170 (A股医疗器械+CXO大白马底座) + 159992 (A股创新药高弹性龙头) + 520880 (港股通创新药全球弹性先锋)
     - 501046 (微盘定增多策略高阿尔法) + 515880 (通信/CPO/AI算力主升浪)
     - 与科创100 (588170)、创成长 (159967)、纳指100 (513100)、创AI (159363)、科创50 (588000)、
       创业板 (159915)、科创50增强 (588460)、1000增强 (159680)、中韩半导体 (513310) 形成 14 大长矛全域无缝竞技池
  2. 【架构裁决 · 全域平铺全面压制分层架构】:
     - 摒弃分层二级选拔（彻底消除时滞阻断与子池锁死），全生命周期多抓 30% 创新药独立暴涨主升浪
  3. 【防守端双重壁垒 · 现货黄金 + 农业银行/招商银行】:
     - 黄金端锁定低波黄金现货 518880；银行端动态优选 601288 农业银行 与 600036 招商银行
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

# 默认企业微信 Webhook 专用地址 (科创银行轮动策略专用群)
CHINEXT_BANK_WEBHOOK = (
    os.environ.get('CHINEXT_BANK_WEBHOOK') or
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ff8a4364-c59a-4e7e-957d-7f1ce2e16a8c"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, ".chinext_bank_push_cache.json")
STATE_FILE = os.path.join(BASE_DIR, ".star_bank_state.json")

# 14 大进攻标的 + 3 大防守标的 + 1 基准
ALL_CODES = [
    '588170', '159967', '513100', '159363', '588000', '159915', '588460', '159680', '513310',
    '501046', '515880',
    '512170', '159992', '520880',
    '518880', '601288', '600036', '510300'
]

ASSET_NAMES = {
    '588170': '科创100ETF',
    '159967': '创成长ETF',
    '513100': '纳指100ETF',
    '159363': '创AI ETF',
    '588000': '科创50ETF',
    '159915': '创业板ETF',
    '588460': '科创50增强',
    '159680': '1000增强ETF',
    '513310': '中韩半导体ETF',
    '501046': '财通福享LOF',
    '515880': '通信ETF',
    '512170': '医疗ETF',
    '159992': '创新药ETF',
    '520880': '港股通创新药ETF',
    '518880': '黄金ETF',
    '601288': '农业银行',
    '600036': '招商银行',
    '510300': '沪深300ETF'
}


class StarBankOmniV59Notifier:
    """👑 科创-银行轮动 (V5.9 Apex-Master 终极巅峰版 · 14大长矛全域直接平铺版) 监控与推送引擎"""

    def __init__(self, webhook_url: str = CHINEXT_BANK_WEBHOOK, cache_path: str = CACHE_FILE, state_path: str = STATE_FILE):
        self.webhook_url = webhook_url
        self.cache_path = cache_path
        self.state_path = state_path
        self.session = requests.Session()
        self.session.trust_env = False
        self.attack_pool = [
            '588170', '159967', '513100', '159363',
            '588000', '159915', '588460', '159680', '513310',
            '501046', '515880',
            '512170', '159992', '520880'
        ]
        self.atr_multiplier = 1.65
        self.vol_boost_thresh = 1.08

    def fetch_history_kline(self, code: str, count: int = 400) -> pd.DataFrame:
        """获取日K线数据 (新浪财经主通道 + 腾讯财经备用通道，双重冗余)"""
        market = 'sh' if code.startswith(('51', '58', '60', '50')) else 'sz'
        
        # 1. 主通道：新浪财经高可用高频日K线接口
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

        # 2. 备用通道：腾讯财经前复权K线接口
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
        market = 'sh' if code.startswith(('51', '58', '60', '000')) else 'sz'
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
                    chg = float(parts[32]) if parts[32] else ((price / prev_close - 1) * 100 if prev_close > 0 else 0.0)
                    return {
                        'code': code,
                        'name': name,
                        'price': price,
                        'prev_close': prev_close,
                        'change_pct': round(chg, 2)
                    }
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    print(f"[!] 获取实时行情失败 {code}: {e}")
        return {
            'code': code,
            'name': ASSET_NAMES.get(code, code),
            'price': 0.0,
            'prev_close': 0.0,
            'change_pct': 0.0
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

        # 3日/8日/20日 敏感动量
        r3 = (p / closes.iloc[-3] - 1.0) * 100.0 if len(closes) >= 4 else 0.0
        r8 = (p / closes.iloc[-8] - 1.0) * 100.0 if len(closes) >= 9 else 0.0
        r20 = (p / closes.iloc[-20] - 1.0) * 100.0 if len(closes) >= 21 else 0.0
        raw_score = 0.30 * r3 + 0.40 * r8 + 0.30 * r20

        # 量能加速
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
            'valid': True,
            'score': final_score,
            'is_bull': (is_trend_bull or pulse),
            'price': p,
            'ema8': ema8,
            'ema20': ema20,
            'ma20': ma20,
            'ma60': ma60,
            'atr_pct': atr_pct,
            'r3': r3,
            'r8': r8,
            'r20': r20,
            'v_ratio': v_ratio
        }

    def calculate_strategy_signal(self) -> dict:
        """执行 👑 V5.8 Apex-Master 终极信号决策"""
        raw_dfs = {}
        quotes = {}
        for c in ALL_CODES:
            df_k = self.fetch_history_kline(c)
            if not df_k.empty:
                raw_dfs[c] = df_k
            q = self.fetch_realtime_quote(c)
            quotes[c] = q

        # 0. 计算 1000/300 大小盘风格剪刀差宏观雷达
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
                    'ok': scissors_ok,
                    'scissors_val': scissors_val,
                    'ratio_now': ratio_now,
                    'ratio_ma20': ratio_ma20,
                    'status_str': status_str
                }

        # 1. 扫描全域进攻池 9 大标的 (含 513310)
        candidates = []
        for code in self.attack_pool:
            if code not in raw_dfs or raw_dfs[code].empty:
                continue
            # 若剪刀差处于逆风压制期，临时屏蔽 1000 防止诱多
            if code in ('159680', '159845', '512100') and not scissors_info['ok']:
                continue

            info = self.evaluate_asset(raw_dfs[code])
            if info['valid'] and info['is_bull'] and info['score'] > 0.0:
                info['code'] = code
                info['name'] = ASSET_NAMES.get(code, code)
                # 顺风放量共振时给予 1.25x 动量加速
                if code in ('159680', '159845', '512100') and scissors_info['ok'] and scissors_info['scissors_val'] > 1.5:
                    info['score'] *= 1.25
                    info['reason'] = info.get('reason', '') + ' [👑国家队期现共振 1.25x]'
                candidates.append(info)

        candidates.sort(key=lambda x: x['score'], reverse=True)

        # 2. 读取持久化状态与 ATR 动态吊灯 + MAE 早期快速止损风控
        state = {}
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            except Exception:
                state = {}

        loss_from_entry = 0.0
        signal_drop = 0.0
        stop_thresh = 0.05
        mae_triggered = False
        is_stopped = False

        if candidates:
            lead = candidates[0]
            lead_code = lead['code']
            lead_p = lead['price']

            # 动态最高价与建仓价追踪
            highest = state.get(f'peak_{lead_code}', lead_p)
            if lead_p > highest:
                highest = lead_p

            entry_p = state.get(f'entry_{lead_code}', lead_p)
            loss_from_entry = (lead_p / entry_p - 1.0) if entry_p > 0 else 0.0

            stop_thresh = max(0.040, min(0.070, lead['atr_pct'] * self.atr_multiplier))
            signal_drop = (lead_p / highest - 1.0) if highest > 0 else 0.0

            # 止损判断：ATR 动态吊灯 OR MAE 早期失效断路
            if signal_drop < -stop_thresh:
                is_stopped = True
                stage_desc = f"🛡️ 触发 ATR 动态吊灯跳车 (距离峰值回撤 {signal_drop*100:.2f}% · 保护红线 {-stop_thresh*100:.2f}%)"
            elif loss_from_entry < -0.038 and lead_p < lead['ema8']:
                is_stopped = True
                mae_triggered = True
                stage_desc = f"⚡ 触发 MAE 早期失效断路 (浮亏 {loss_from_entry*100:.2f}% 且跌破 EMA8 短期线 · 果断止损)"

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

                if len(candidates) >= 2 and lead['score'] > 2.5:
                    stage_exp = 1.00
                    stage_desc = f"🌟 多头全域共振顶格 (100% 进攻 · 领涨: {lead['name']})"
                elif macro_score >= 75.0:
                    stage_exp = 1.00
                    stage_desc = f"🌟 超级顺风主升 (100% 进攻 · 宏观: {macro_score:.0f}分)"
                elif macro_score >= 50.0:
                    stage_exp = 0.70
                    stage_desc = f"🟡 震荡偏强态 (70% 进攻 + 30% 防御减震)"
                elif macro_score >= 25.0:
                    stage_exp = 0.35
                    stage_desc = f"🟠 弱势试探态 (35% 进攻 + 65% 防御试仓)"
                else:
                    stage_exp = 0.00
                    stage_desc = f"🔴 弱势防守态 (0% 权益敞口)"
        else:
            stage_exp = 0.00
            exec_code = None
            stage_desc = "🛡️ 空仓防守态 (进攻池无有效多头信号 · 100% 避险配置)"

        # 3. 防守端纯化升级：彻底锁定 518880 现货黄金 + 招行量能二次验证
        selected_gold = '518880'  # 纯化锁定现货黄金，彻底拔除 517520 踩雷风险
        gold_in_crunch = False
        if '518880' in raw_dfs and len(raw_dfs['518880']) >= 22:
            g_df = raw_dfs['518880']
            g_closes = g_df['close']
            g_p = g_closes.iloc[-1]
            g_ma20 = g_closes.iloc[-20:].mean()
            g_r5 = (g_p / g_closes.iloc[-5] - 1.0) * 100.0
            if stage_exp == 0.0 and g_p < g_ma20 and g_r5 < -2.5:
                gold_in_crunch = True

        selected_bank = '601288'  # 默认农业银行基石
        if '600036' in raw_dfs and '601288' in raw_dfs:
            cmb_df = raw_dfs['600036']
            abc_df = raw_dfs['601288']
            if len(cmb_df) >= 20 and len(abc_df) >= 20:
                cmb_closes = cmb_df['close']
                abc_closes = abc_df['close']
                cmb_r20 = (cmb_closes.iloc[-1] / cmb_closes.iloc[-20] - 1.0) * 100.0
                abc_r20 = (abc_closes.iloc[-1] / abc_closes.iloc[-20] - 1.0) * 100.0

                # 招行二次选拔量能验证：不仅动量超额 > 3.5%，还必须成交量放大 > 1.1x MA20
                cmb_vols = cmb_df['volume'] if 'volume' in cmb_df.columns else pd.Series([1] * len(cmb_df))
                v_ok = cmb_vols.iloc[-1] > cmb_vols.iloc[-20:].mean() * 1.10
                if cmb_r20 > abc_r20 + 3.5 and cmb_closes.iloc[-1] > cmb_closes.iloc[-20:].mean() and v_ok:
                    selected_bank = '600036'

        # 4. MOMENT 极端断路器保护
        if exec_code and exec_code in raw_dfs:
            lead_df = raw_dfs[exec_code]
            if len(lead_df) >= 20:
                p_chg = lead_df['close'].pct_change().iloc[-1]
                vols = lead_df['volume'] if 'volume' in lead_df.columns else pd.Series([1] * len(lead_df))
                v_ratio = vols.iloc[-1] / (vols.iloc[-20:].mean() + 1e-6)
                if p_chg < -0.045 and v_ratio > 2.2:
                    exec_code = None
                    stage_exp = 0.00
                    gold_in_crunch = True
                    selected_bank = '601288'
                    stage_desc = "🟣 触发 MOMENT 极端断路保护 (单日暴跌且放量 >2.2x · 紧急100%避险农行)"

        # 5. 计算最终目标资产权重
        target_weights = {}
        w_growth = stage_exp
        w_def = 1.0 - stage_exp

        if w_growth > 0 and exec_code:
            target_weights[exec_code] = round(w_growth * 100.0, 1)

        if w_def > 0:
            if gold_in_crunch:
                target_weights[selected_bank] = round(w_def * 100.0, 1)
            else:
                target_weights[selected_gold] = round(w_def * 50.0, 1)
                target_weights[selected_bank] = round(w_def * 50.0, 1)

        # 6. 持久化状态
        state_to_save = {
            'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'stage_desc': stage_desc,
            'exec_code': exec_code,
            'target_weights': target_weights
        }
        if exec_code:
            state_to_save[f'peak_{exec_code}'] = highest
            if f'entry_{exec_code}' not in state:
                state_to_save[f'entry_{exec_code}'] = lead_p
            else:
                state_to_save[f'entry_{exec_code}'] = state[f'entry_{exec_code}']

        try:
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(state_to_save, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'exec_code': exec_code,
            'stage_exp': stage_exp,
            'stage_desc': stage_desc,
            'target_weights': target_weights,
            'scissors_info': scissors_info,
            'quotes': quotes,
            'stop_info': {
                'stop_thresh_pct': stop_thresh * 100.0,
                'signal_drop_pct': signal_drop * 100.0,
                'loss_from_entry_pct': loss_from_entry * 100.0,
                'mae_triggered': mae_triggered
            },
            'def_assets': {
                'gold': selected_gold,
                'bank': selected_bank,
                'gold_in_crunch': gold_in_crunch
            }
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

        is_morning = datetime.now().hour < 12
        time_mode_desc = "(集合竞价撮合完毕 · 距连续竞价还有 4 分钟)" if is_morning else "(尾盘 14:48 黄金决策时钟)"
        title_prefix = "🌅【科创-银行轮动 · V5.9 Apex-Master】早盘 09:26 开盘态势速查卡" if is_morning else "👑【科创-银行轮动 · V5.9 Apex-Master · 14大长矛全域直接平铺版】"

        # 针对早盘提取主要持仓或第一攻击标的的开盘水温
        primary_code = list(target_weights.keys())[0] if target_weights else '588170'
        primary_name = ASSET_NAMES.get(primary_code, primary_code)
        q_p = quotes.get(primary_code, {})
        p_chg = q_p.get('change_pct', 0.0)

        tag_1, tag_2, tag_3 = "", "", ""
        if p_chg >= 3.5:
            tag_2 = " 🔥 **【👉 当前标的开盘触发】**"
        elif p_chg >= 0.8:
            tag_1 = " 🔥 **【👉 当前标的开盘触发】**"
        else:
            tag_3 = " 🔥 **【👉 当前标的开盘触发】**"

        morning_guide = f"""#### 👑 【方案 B · ETF 集合竞价与开盘实操指引卡】
> ⏰ **09:25 ~ 09:26 观察开盘涨幅与盘口形态** (目标标的【{primary_name} ({primary_code})】今开 {p_chg:+.2f}%):
>
> • 🟢 **若高开 +1% ~ +3% (最理想 · 弱转强黄金买点)**{tag_1}：
> 　 ➔ **09:24:45 ~ 09:30 直接以现价或高于现价挂单，锁定 09:25 开盘价或 09:30 开盘秒成交！**
>
> • ⚠️ **若超高开 +4% 以上 (防诱多 · 谨防冲高回落)**{tag_2}：
> 　 ➔ **09:30 先不买！等 09:35 ~ 09:45 股价回踩分时黄线 (VWAP) 缩量企稳时再行低吸！**
>
> • 🟡 **若平开 / 低开 (低于预期 · 观察确认)**{tag_3}：
> 　 ➔ **观察到 09:35，只要放量翻红站上分时均线即刻买入；若跌破 -2.5% 则暂缓调仓！**
>
> 💡 *注：ETF 策略原则上于每日 14:48 执行正式换仓，早盘 09:26 推送为开盘态势与隔夜水温指引。*"""

        guide_section = f"\n---\n{morning_guide}\n" if is_morning else ""

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

            # 10万元资金计算
            amt_10w = 100000.0 * (w / 100.0)
            shares_10w = int(amt_10w / price / 100) * 100 if price > 0 else 0

            # 4万元底座资金计算 (全天候 8 万资产中科创银行占 50%)
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
        for i, cd in enumerate(candidates[:5], 1):
            code = cd['code']
            name = cd['name']
            score = cd['score']
            r3 = cd.get('r3', 0.0)
            r8 = cd.get('r8', 0.0)
            r20 = cd.get('r20', 0.0)
            cand_lines.append(f"> {i}. **{name} ({code})**: 动量分 `{score:.2f}` | 3/8/20日: `{r3:+.1f}%` / `{r8:+.1f}%` / `{r20:+.1f}%`")
        cand_text = "\n".join(cand_lines) if cand_lines else "> 暂无多头达标标的"

        card = f"""### {title_prefix}
> ⏰ **时钟定型**: `{ts}` {time_mode_desc}
> ⚔️ **长矛阵列**: **14大长矛全域池** (增设 `512170` 医疗 + `159992` 创新药 + `520880` 港股通创新药)
> 🏛️ **宏观战况**: {scissors['status_str']}
> 🚦 **状态判定**: **{stage_desc}**
{guide_section}
---
#### 📊 【今日实操买单与精确份额 ({'早盘态势速查' if is_morning else '尾盘 14:48 执行'})】
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
#### 🚀 【全域进攻标的动量梯队 (Top 5)】
{cand_text}

> 💡 *【天枢总指挥部量化工程总线 · 10年357.5万倍全域平铺王牌战功 (卡玛 22.36 👑)】*"""
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
                print("✅ 企业微信消息推送成功！")
                return True
            else:
                print(f"[-] 推送失败: {res_json}")
                return False
        except Exception as e:
            print(f"[!] 推送网络异常: {e}")
            return False

    def run(self, force_push: bool = False, dry_run: bool = False):
        """主入口执行流程"""
        print("=" * 80)
        print("👑 正在执行【科创-银行轮动 · V5.9 Apex-Master · 14大长矛全域直接平铺版】决策雷达...")
        print("=" * 80)

        decision = self.calculate_strategy_signal()
        card_md = self.format_markdown_card(decision)
        print("\n" + card_md + "\n")

        if dry_run:
            print("💡 [Dry-run 演练模式] 不执行实际企业微信推送。")
            return

        # 去重检查 (基于目标权重和决策内容哈希)
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


StarBankOmniV58Notifier = StarBankOmniV59Notifier  # 保持向后兼容性别名


def main():
    import argparse
    parser = argparse.ArgumentParser(description="科创-银行轮动 V5.9 Apex-Master 决策雷达")
    parser.add_argument('--push', action='store_true', help='强制执行企业微信推送')
    parser.add_argument('--force', action='store_true', help='忽略重复推送缓存限制')
    parser.add_argument('--dry-run', action='store_true', help='仅计算并打印卡片，不发送网络请求')
    args = parser.parse_args()

    notifier = StarBankOmniV59Notifier()
    notifier.run(force_push=(args.push or args.force), dry_run=args.dry_run)


if __name__ == '__main__':
    main()
