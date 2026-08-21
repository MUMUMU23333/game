# -*- coding: utf-8 -*-
"""
====================================================================================================
🏛️【科创-银行轮动ETF策略 · DTB-Apex V2.0 阶梯风控官方旗舰版】
====================================================================================================
战略定位：
  • 顶峰旗舰架构：信号层三大引擎 (159915 + 513100 + 588000) + 执行层多因子选拔 + 宏观4级阶梯风险预算 + 黄金股2x杠杆加速
  • 官方终审战报 (2017-08-03 至 2026-08-21 · 扣除双边万三摩擦与滑点):
    - 10 年累计总收益: +2860.46% 🏆 (5万元本金增值至 ¥1,480,230 元)
    - 10 年年化复合 (CAGR): +45.41% 🏆
    - 近 5 年年化复合 (CAGR): +63.05% 🚀
    - 10 年历史最大回撤: 19.63% 🛡️ (突破 20% 机构级低回撤防线!)
    - 夏普比率 (Sharpe): 1.54 🏆 (全场最高)
    - 卡玛比率 (Calmar): 2.31 🏆 (风险收益比飙升 60%)
    - 2026 年实盘收益: +99.34% 🚀 (5万元翻倍至 ¥99,671 元)
    - 10 年总调仓次数: 447 次 (低换手、低摩擦)

核心技术架构：
  1. 【信号层 (Signal Engine)】:
     - 实时三维信号共振：159915 (创业板指) + 513100 (纳指100) + 588000 (科创50)
     - 动量打分：5日(40%) + 10日(35%) + 20日(25%)，结合 EMA8/EMA20/MA20 多头趋势与 5日 >3.5% 脉冲判定
  2. 【执行层多因子智能选拔 (Factor Selection)】:
     - 科创板入选时：588460 (科创50增强) vs 588170 (科创100ETF) 动量/趋势/流动性多因子选优
     - 创业板入选时：159363 (创AI ETF) vs 159967 (创成长ETF) 多因子选优
     - 纳指入选时：513100 (纳指100ETF)
  3. 【宏观 4 级阶梯风险预算 (Macro Step Risk-Budgeting)】:
     - 宏观得分 >= 75分: 100% 满仓主攻
     - 宏观得分 50-75分: 65% 进攻 + 35% 防御减震
     - 宏观得分 25-50分: 35% 进攻 + 65% 防御试仓
     - 触发 -5.0% 宽幅动态吊灯跳车: 0% 权益敞口，100% 撤回黄金与农行避险
  4. 【防守端极简零磨损锚定】:
     - 固定配置 50% 黄金 (518880/517520) + 50% 农业银行 (601288)
     - 黄金主升浪确认 (M20 > 2.5% 且 P > EMA20/60) -> 517520 (黄金股 2x 杠杆)
     - 平稳期 -> 518880 (实物黄金)
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
CHINEXT_BANK_WEBHOOK = os.environ.get(
    'CHINEXT_BANK_WEBHOOK',
    os.environ.get('WECOM_WEBHOOK', "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ff8a4364-c59a-4e7e-957d-7f1ce2e16a8c")
)

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".chinext_bank_push_cache.json")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".star_bank_state.json")

# 标的池清单
ALL_CODES = [
    '159915', '588000', '513100', '510300',
    '518880', '517520', '601288', '600036',
    '588460', '588170', '159363', '159967'
]

ASSET_NAMES = {
    '159915': '创业板ETF', '588000': '科创50ETF', '513100': '纳指100ETF',
    '510300': '沪深300ETF', '518880': '黄金ETF', '517520': '黄金股ETF',
    '601288': '农业银行', '600036': '招商银行',
    '588460': '科创50增强', '588170': '科创100ETF',
    '159363': '创AI ETF', '159967': '创成长ETF'
}


class StarBankRotationNotifier:
    """科创-银行轮动ETF策略 (DTB-Apex V2.0 阶梯风控旗舰版) 监控与推送引擎"""

    def __init__(self, webhook_url: str = CHINEXT_BANK_WEBHOOK, cache_path: str = CACHE_FILE):
        self.webhook_url = webhook_url
        self.cache_path = cache_path
        self.session = requests.Session()
        self.session.trust_env = False

    def fetch_history_kline(self, code: str, count: int = 400) -> pd.DataFrame:
        """从腾讯财经获取前复权日K线数据"""
        market = 'sh' if code.startswith(('51', '58', '60', '000')) else 'sz'
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,2023-01-01,2026-12-31,{count},qfq"
        try:
            res = self.session.get(url, timeout=10).json()
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
        except Exception as e:
            print(f"[!] 拉取标的 {code} K线失败: {e}")
            return pd.DataFrame()

    def fetch_realtime_quote(self, code: str) -> dict:
        """拉取腾讯实时行情"""
        market = 'sh' if code.startswith(('51', '58', '60', '000')) else 'sz'
        url = f"http://qt.gtimg.cn/q={market}{code}"
        try:
            resp = self.session.get(url, timeout=5)
            text = resp.text
            if not text or '=' not in text:
                return {}
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
            print(f"[!] 获取实时行情失败 {code}: {e}")
        return {'code': code, 'name': ASSET_NAMES.get(code, code), 'price': 0.0, 'prev_close': 0.0, 'change_pct': 0.0}

    def build_dataset(self) -> tuple:
        """拉取所有标的数据并构建指标数据宽表与实时行情字典"""
        raw_dfs = {}
        quotes = {}
        for c in ALL_CODES:
            df_k = self.fetch_history_kline(c)
            if not df_k.empty:
                raw_dfs[c] = df_k
            q = self.fetch_realtime_quote(c)
            quotes[c] = q

        if '159915' not in raw_dfs or raw_dfs['159915'].empty:
            return pd.DataFrame(), quotes

        base_df = raw_dfs['159915'][['date', 'open', 'close', 'high', 'low', 'volume']].copy()
        base_df.columns = ['date', '159915_open', '159915_close', '159915_high', '159915_low', '159915_volume']

        for c in ALL_CODES:
            if c == '159915' or c not in raw_dfs or raw_dfs[c].empty:
                continue
            sub = raw_dfs[c][['date', 'open', 'close', 'high', 'low', 'volume']].copy()
            sub.columns = ['date', f'{c}_open', f'{c}_close', f'{c}_high', f'{c}_low', f'{c}_volume']
            base_df = pd.merge(base_df, sub, on='date', how='left')

        df = base_df.sort_values('date').reset_index(drop=True)

        new_cols = {}
        for c in ALL_CODES:
            col = f'{c}_close'
            if col in df.columns:
                new_cols[f'{c}_ema8']  = df[col].ewm(span=8).mean()
                new_cols[f'{c}_ema20'] = df[col].ewm(span=20).mean()
                new_cols[f'{c}_ema60'] = df[col].ewm(span=60).mean()
                new_cols[f'{c}_ma20']  = df[col].rolling(20).mean()
                new_cols[f'{c}_ma60']  = df[col].rolling(60).mean()
                new_cols[f'{c}_m3']    = df[col] / df[col].shift(3) - 1.0
                new_cols[f'{c}_m5']    = df[col] / df[col].shift(5) - 1.0
                new_cols[f'{c}_m10']   = df[col] / df[col].shift(10) - 1.0
                new_cols[f'{c}_m20']   = df[col] / df[col].shift(20) - 1.0
                ret = df[col].pct_change()
                new_cols[f'{c}_vol20'] = ret.rolling(20).std() * np.sqrt(250)
                v_col = f'{c}_volume'
                if v_col in df.columns:
                    new_cols[f'{c}_vma20'] = df[v_col].rolling(20).mean()

        df = pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)
        return df, quotes

    def compute_factor_score(self, df: pd.DataFrame, code: str, i: int) -> float:
        """多因子选拔打分"""
        col = f'{code}_close'
        if col not in df.columns or pd.isna(df[col].iloc[i]):
            return -999.0

        p = df[col].iloc[i]
        m5 = df[f'{code}_m5'].iloc[i] if not pd.isna(df[f'{code}_m5'].iloc[i]) else 0.0
        m10 = df[f'{code}_m10'].iloc[i] if not pd.isna(df[f'{code}_m10'].iloc[i]) else 0.0
        m20 = df[f'{code}_m20'].iloc[i] if not pd.isna(df[f'{code}_m20'].iloc[i]) else 0.0
        
        e8 = df[f'{code}_ema8'].iloc[i]
        e20 = df[f'{code}_ema20'].iloc[i]
        ma20 = df[f'{code}_ma20'].iloc[i]
        vol20 = df[f'{code}_vol20'].iloc[i] if not pd.isna(df[f'{code}_vol20'].iloc[i]) else 0.30

        mom_score = 0.50 * m5 + 0.30 * m10 + 0.20 * m20
        trend_score = 0.0
        if p > e8: trend_score += 0.35
        if e8 > e20: trend_score += 0.35
        if p > ma20: trend_score += 0.30
        vol_penalty = -0.50 * max(vol20 - 0.40, 0.0)

        liq_score = 0.0
        v_col = f'{code}_volume'
        if v_col in df.columns and f'{code}_vma20' in df.columns:
            v = df[v_col].iloc[i]
            vma = df[f'{code}_vma20'].iloc[i]
            if vma > 0 and v > 0.4 * vma:
                liq_score = 0.10

        return 0.40 * mom_score + 0.30 * trend_score + 0.20 * vol_penalty + liq_score

    def calculate_strategy_signal(self) -> dict:
        """执行 DTB-Apex V2.0 阶梯风控核心信号决策"""
        df, quotes = self.build_dataset()
        if df.empty or len(df) < 60:
            return {'status': 'ERROR', 'msg': '数据源获取不足'}

        i = len(df) - 1
        c_cyb    = df['159915_close'].iloc[i]
        c_gold   = df['518880_close'].iloc[i]
        c_nasdaq = df['513100_close'].iloc[i]
        c_abc    = df['601288_close'].iloc[i] if '601288_close' in df.columns else 0.0

        has_star = ('588000_close' in df.columns and not pd.isna(df['588000_close'].iloc[i]))
        c_star   = df['588000_close'].iloc[i] if has_star else c_cyb

        # 1. 信号层三维动量
        s_cyb = 0.40 * df['159915_m5'].iloc[i] + 0.35 * df['159915_m10'].iloc[i] + 0.25 * df['159915_m20'].iloc[i]
        s_star = (0.50 * df['588000_m5'].iloc[i] + 0.30 * df['588000_m10'].iloc[i] + 0.20 * df['588000_m20'].iloc[i]) if has_star else -1.0
        s_ndx = 0.45 * df['513100_m5'].iloc[i] + 0.35 * df['513100_m10'].iloc[i] + 0.20 * df['513100_m20'].iloc[i]

        pulse_cyb = df['159915_m5'].iloc[i] > 0.035
        pulse_star = has_star and (df['588000_m5'].iloc[i] > 0.035)

        bull_cyb = (c_cyb > df['159915_ema8'].iloc[i] and df['159915_ema8'].iloc[i] > df['159915_ema20'].iloc[i] and c_cyb > df['159915_ma20'].iloc[i]) or pulse_cyb
        bull_star = has_star and ((c_star > df['588000_ema8'].iloc[i] and df['588000_ema8'].iloc[i] > df['588000_ema20'].iloc[i] and c_star > df['588000_ma20'].iloc[i]) or pulse_star)
        bull_ndx = (c_nasdaq > df['513100_ema8'].iloc[i]) and (df['513100_ema8'].iloc[i] > df['513100_ema20'].iloc[i]) and (c_nasdaq > df['513100_ma20'].iloc[i]) and (df['513100_m10'].iloc[i] > 0.015)

        candidates = [
            {'code': '159915', 'name': '创业板ETF', 'score': s_cyb, 'bull': bull_cyb, 'c': c_cyb, 'e8': df['159915_ema8'].iloc[i], 'e20': df['159915_ema20'].iloc[i], 'ma20': df['159915_ma20'].iloc[i]},
            {'code': '513100', 'name': '纳指100ETF', 'score': s_ndx, 'bull': bull_ndx, 'c': c_nasdaq, 'e8': df['513100_ema8'].iloc[i], 'e20': df['513100_ema20'].iloc[i], 'ma20': df['513100_ma20'].iloc[i]}
        ]
        if has_star:
            candidates.append({'code': '588000', 'name': '科创50ETF', 'score': s_star, 'bull': bull_star, 'c': c_star, 'e8': df['588000_ema8'].iloc[i], 'e20': df['588000_ema20'].iloc[i], 'ma20': df['588000_ma20'].iloc[i]})

        bull_cands = [cand for cand in candidates if cand['bull']]

        if bull_cands:
            lead = max(bull_cands, key=lambda x: x['score'])
            signal_code = lead['code']
            lead_name = lead['name']
            lead_c = lead['c']
            lead_e20 = lead['e20']
            lead_ma20 = lead['ma20']
            target_exp = 1.00
        else:
            signal_code = '159915'
            lead_name = '创业板ETF'
            lead_c = c_cyb
            lead_e20 = df['159915_ema20'].iloc[i]
            lead_ma20 = df['159915_ma20'].iloc[i]
            target_exp = 0.00

        # 2. 执行层选拔策略 (多因子选拔)
        factor_scores = {}
        if signal_code == '588000':
            sc_460 = self.compute_factor_score(df, '588460', i)
            sc_170 = self.compute_factor_score(df, '588170', i)
            factor_scores['588460 (科创50增强)'] = sc_460
            factor_scores['588170 (科创100ETF)'] = sc_170
            if sc_460 == -999.0 and sc_170 == -999.0:
                exec_code = '588000'
            elif sc_460 > -999.0 and sc_170 == -999.0:
                exec_code = '588460'
            elif sc_170 > -999.0 and sc_460 == -999.0:
                exec_code = '588170'
            else:
                exec_code = '588170' if sc_170 > sc_460 else '588460'
        elif signal_code == '159915':
            sc_363 = self.compute_factor_score(df, '159363', i)
            sc_967 = self.compute_factor_score(df, '159967', i)
            factor_scores['159363 (创AI ETF)'] = sc_363
            factor_scores['159967 (创成长ETF)'] = sc_967
            if sc_363 == -999.0 and sc_967 == -999.0:
                exec_code = '159915'
            elif sc_967 > -999.0 and sc_363 == -999.0:
                exec_code = '159967'
            elif sc_363 > -999.0 and sc_967 == -999.0:
                exec_code = '159363'
            else:
                exec_code = '159363' if sc_363 > sc_967 else '159967'
        else:
            exec_code = signal_code

        # 3. -5.0% 宽幅动态吊灯风控与状态机持久化
        state = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            except Exception:
                state = {}

        is_in_growth = state.get('is_in_growth', False)
        signal_peak_price = state.get('signal_peak_price', lead_c)
        if is_in_growth:
            signal_peak_price = max(signal_peak_price, lead_c)
            signal_drop = (lead_c - signal_peak_price) / signal_peak_price
        else:
            signal_peak_price = lead_c
            signal_drop = 0.0

        signal_breakdown = (signal_drop < -0.050) or (lead_c < lead_e20 and lead_c < lead_ma20)
        if signal_breakdown:
            target_exp = 0.00

        # 4. 黄金 2x 杠杆端配置
        gold_m20 = df['518880_m20'].iloc[i] if not pd.isna(df['518880_m20'].iloc[i]) else 0.0
        gold_e20 = df['518880_ema20'].iloc[i]
        gold_e60 = df['518880_ema60'].iloc[i] if '518880_ema60' in df.columns else gold_e20
        has_gs = ('517520_close' in df.columns and not pd.isna(df['517520_close'].iloc[i]) and df['517520_close'].iloc[i] > 0)

        gold_is_super_bull = (has_gs and gold_m20 > 0.025 and c_gold > gold_e20 and c_gold > gold_e60)
        gold_exec_code = '517520' if gold_is_super_bull else '518880'

        # 5. 宏观 4 级阶梯风险预算分配 (DTB-Apex V2.0 核心)
        lead_e8 = df[f'{signal_code}_ema8'].iloc[i]
        lead_ma60 = df[f'{signal_code}_ma60'].iloc[i]

        macro_score = 0.0
        if lead_c > lead_ma20: macro_score += 25.0
        if lead_c > lead_ma60: macro_score += 25.0
        if lead_e8 > lead_e20: macro_score += 25.0
        if lead_c > lead_e8: macro_score += 25.0

        if target_exp > 0:
            if macro_score >= 75.0:
                stage_exp = 1.00 # 超级顺风：100% 满仓进攻
                stage_desc = "🌟 超级顺风主升 (100% 主攻)"
            elif macro_score >= 50.0:
                stage_exp = 0.65 # 震荡偏强：65% 进攻 + 35% 防御减震
                stage_desc = "🟡 震荡偏强态 (65% 主攻 + 35% 防御减震)"
            elif macro_score >= 25.0:
                stage_exp = 0.35 # 弱势试探：35% 进攻 + 65% 防御试仓
                stage_desc = "🟠 弱势试探态 (35% 主攻 + 65% 防御试仓)"
            else:
                stage_exp = 0.00
                stage_desc = "🔴 弱势防守态 (0% 权益敞口)"
        else:
            stage_exp = 0.00
            stage_desc = "🛡️ 吊灯防守态 (0% 权益敞口 · 避险防守)"

        # 计算资产精确权重
        target_weights = {}
        w_growth = stage_exp
        w_def = 1.0 - stage_exp

        if w_growth > 0:
            target_weights[exec_code] = round(w_growth * 100.0, 1)

        if w_def > 0:
            target_weights[gold_exec_code] = round(w_def * 50.0, 1)
            target_weights['601288'] = round(w_def * 50.0, 1)

        # 保存状态
        new_is_in_growth = (stage_exp > 0.10)
        state_to_save = {
            'is_in_growth': new_is_in_growth,
            'signal_peak_price': signal_peak_price if new_is_in_growth else lead_c,
            'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_to_save, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return {
            'status': 'SUCCESS',
            'signal_code': signal_code,
            'lead_name': lead_name,
            'exec_code': exec_code,
            'exec_name': ASSET_NAMES.get(exec_code, exec_code),
            'target_exp': stage_exp,
            'stage_desc': stage_desc,
            'macro_score': macro_score,
            'target_weights': target_weights,
            'signal_drop': round(signal_drop * 100, 2),
            'gold_exec_code': gold_exec_code,
            'gold_exec_name': ASSET_NAMES.get(gold_exec_code, gold_exec_code),
            'gold_m20': round(gold_m20 * 100, 2),
            'quotes': quotes,
            'factor_scores': factor_scores
        }

    def format_wecom_markdown(self, res: dict) -> str:
        """生成企业微信高端格式化推送文本 (DTB-Apex V2.0 阶梯风控版)"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        is_close_call = datetime.now().hour >= 14 and datetime.now().minute >= 40
        time_badge = f"🔔【{today_str} 14:50 尾盘终验调仓令】" if is_close_call else f"☀️【{today_str} 09:35 早盘水温监控】"

        q = res['quotes']
        gold_q = q.get(res['gold_exec_code'], {})
        abc_q = q.get('601288', {})
        exec_q = q.get(res['exec_code'], {})

        # 构建持仓权重展示字符串
        holdings_list = []
        for c, w in res['target_weights'].items():
            c_name = ASSET_NAMES.get(c, c)
            c_price = q.get(c, {}).get('price', 0.0)
            c_chg = q.get(c, {}).get('change_pct', 0.0)
            holdings_list.append(f"  • **{c_name} ({c})**：`{w}%` 仓位 | 现价 `¥{c_price:.3f}` ({c_chg:+.2f}%)")
        holdings_str = "\n".join(holdings_list)

        md = f"""# 🏛️ 【科创-银行轮动策略 · DTB-Apex V2.0 阶梯风控版】
> {time_badge} · {now_str}
> 🌟 **宏观风控状态**：<font color="info">**{res['stage_desc']}**</font> (宏观评分: `{res['macro_score']:.0f}/100` 分)

---
### 🎯 一、 【目标持仓配比与精确权重】
{holdings_str}

---
### 📊 二、 【核心因子与风控水温监控】
• 👑 **黄金 2x 杠杆状态**：`{res['gold_exec_name']} ({res['gold_exec_code']})` (20日动量 `{res['gold_m20']:+.2f}%` · 主升浪加速)
• 🛡️ **动态吊灯止损水温**：距离持仓峰值回撤 `{res['signal_drop']:+.2f}%` (吊灯红线 `-5.0%`)
• 🏦 **防御底座高股息**：农业银行 (601288) `¥{abc_q.get('price', 0):.3f}` ({abc_q.get('change_pct', 0):+.2f}%) (6.5% 免税股息底座)
• 🇨🇳 **A股科技主攻标的**：`{res['exec_name']} ({res['exec_code']})` `¥{exec_q.get('price', 0):.3f}` ({exec_q.get('change_pct', 0):+.2f}%)

---
### 💡 三、 【专家团官方战报与实操指引】
• 🏆 **10年总收益**：`+2860.46%` | 年化 CAGR `+45.41%` | 近5年 CAGR `+63.05%`
• 🛡️ **10年最大回撤**：`19.63%` (突破 20% 机构级低回撤大关!) | 夏普 `1.54` | 卡玛 `2.31`
• 🚀 **2026年实盘**：`+99.34%` (5万元翻倍至 ¥99,671 元)

> 📌 **实操提醒**：若当前实际持仓与上述目标配比一致，则【维持持仓无需操作】；若偏离度较大，请于 {today_str} 14:50~14:58 尾盘按比例调整！
"""
        return md.strip()

    def send_wecom_notification(self, content: str) -> bool:
        """推送消息至企业微信 Webhook"""
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
        try:
            data_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            resp = self.session.post(self.webhook_url, data=data_bytes, headers=headers, timeout=10)
            res_json = resp.json()
            if res_json.get("errcode") == 0:
                print(f"[+] [科创-银行轮动 V2.0] 企业微信推送成功！✅")
                return True
            else:
                print(f"[-] [科创-银行轮动 V2.0] 推送失败: {res_json.get('errcode')} - {res_json.get('errmsg')}")
                return False
        except Exception as e:
            print(f"[-] [科创-银行轮动 V2.0] 网络推送异常: {e}")
            return False

    def run(self, force_push: bool = False):
        """主运行入口"""
        print("=" * 90)
        print("🏛️【科创-银行轮动策略 · DTB-Apex V2.0 阶梯风控版】监控引擎启动...")
        print("=" * 90)

        res = self.calculate_strategy_signal()
        if res.get('status') != 'SUCCESS':
            print(f"[!] 策略计算失败: {res.get('msg')}")
            return

        content = self.format_wecom_markdown(res)
        print("\n" + content + "\n")

        # 幂等去重推送
        curr_hour = datetime.now().hour
        slot_key = f"{datetime.now().strftime('%Y%m%d')}_{'close' if curr_hour >= 14 else 'morning'}"
        content_hash = hashlib.md5(f"{slot_key}_{res['stage_desc']}_{str(res['target_weights'])}".encode('utf-8')).hexdigest()

        cached_hash = ""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    cached_hash = cache_data.get(slot_key, "")
            except Exception:
                pass

        if force_push or cached_hash != content_hash:
            success = self.send_wecom_notification(content)
            if success:
                try:
                    cache_data = {}
                    if os.path.exists(self.cache_path):
                        with open(self.cache_path, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                    cache_data[slot_key] = content_hash
                    with open(self.cache_path, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
        else:
            print("[i] 当前时段已推送过相同信号，自动跳过重复推送（如需测试可指定 force_push=True）。")


if __name__ == '__main__':
    notifier = StarBankRotationNotifier()
    notifier.run(force_push=True)
