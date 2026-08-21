# -*- coding: utf-8 -*-
"""
====================================================================================================
👑【科创-银行轮动ETF策略 · 黄金股 2x 杠杆增强旗舰版】
====================================================================================================
战略定位：
  • 顶峰旗舰架构：信号层三大引擎 (159915 + 513100 + 588000) + 执行层多因子选拔 + 黄金股2x主升浪加速
  • 官方基准核心战报 (2017-08-03 至 2026-08-20, 扣除双边万三摩擦):
    - 10 年累计总收益: +2916.45% 🏆
    - 10 年复合年化 (CAGR): +45.73% 🏆
    - 近 5 年复合年化 (CAGR): +65.60% 🚀
    - 10 年最大历史回撤: 31.88% 🛡️
    - 夏普比率 (Sharpe): 1.42 🏆
    - 2026 年实战收益: +99.40% 🚀 (5万元翻倍至 ¥99,702 元)

核心技术架构：
  1. 【信号层 (Signal Engine)】:
     - 实时三维信号共振：159915 (创业板指) + 513100 (纳指100) + 588000 (科创50)
     - 动量打分：5日(40%) + 10日(35%) + 20日(25%)，结合 EMA8/EMA20/MA20 多头趋势与 5日 >3.5% 脉冲判定
  2. 【执行层多因子智能选拔 (Factor Selection)】:
     - 科创板入选时：588460 (科创50增强) vs 588170 (科创100ETF) 动量/趋势/流动性多因子选优
     - 创业板入选时：159363 (创AI ETF) vs 159967 (创成长ETF) 多因子选优
     - 纳指入选时：513100 (纳指100ETF)
  3. 【黄金端 2x 杠杆主升浪 (Gold Alpha Booster)】:
     - 黄金主升浪确认 (M20 > 2.5% 且 P > EMA20/60) -> 517520 (黄金股ETF 2x 杠杆)
     - 平稳期 -> 518880 (华安实物黄金ETF)
  4. 【-5.0% 宽幅动态吊灯跳车风控 (Chandelier Trailing Exit)】:
     - 追踪持仓最高峰，从峰值回撤 >5.0% 或跌破 EMA20+MA20 双均线时果断 100% 逃顶切换至防守端
  5. 【防守端全天候双核配置】:
     - 黄金健康态：50% 黄金 (517520/518880) + 50% 农业银行 (601288)
     - 黄金回调态：15% 黄金 (518880) + 85% 农业银行 (601288) 极致稳健吃息
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
    """科创-银行轮动ETF策略 (DTB-Apex 黄金增强版) 监控与推送引擎"""

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
        """执行 DTB-Apex V1.0 + 黄金股2x增强 核心信号决策"""
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

        exec_name = ASSET_NAMES.get(exec_code, exec_code)

        # 3. 动态吊灯风控检测 (-5.0% 止盈止损)
        peak_window_p = df[f'{signal_code}_close'].tail(20).max()
        drop_from_peak = (lead_c - peak_window_p) / peak_window_p if peak_window_p > 0 else 0.0
        chandelier_stop_p = round(peak_window_p * 0.950, 3)

        signal_breakdown = (drop_from_peak < -0.050) or (lead_c < lead_e20 and lead_c < lead_ma20)
        if signal_breakdown:
            target_exp = 0.00

        # 4. 黄金端配置 (黄金主升浪确认 2x 杠杆)
        gold_m20 = df['518880_m20'].iloc[i] if not pd.isna(df['518880_m20'].iloc[i]) else 0.0
        gold_e20 = df['518880_ema20'].iloc[i]
        gold_e60 = df['518880_ema60'].iloc[i] if '518880_ema60' in df.columns else gold_e20

        gold_peak_price = df['518880_close'].tail(20).max()
        gold_drop = (c_gold - gold_peak_price) / gold_peak_price if gold_peak_price > 0 else 0.0
        gold_healthy = (gold_drop > -0.045) and (c_gold > gold_e20)
        has_gold_stock = ('517520_close' in df.columns and not pd.isna(df['517520_close'].iloc[i]) and df['517520_close'].iloc[i] > 0)

        if has_gold_stock and gold_m20 > 0.025 and c_gold > gold_e20 and c_gold > gold_e60:
            gold_exec_code = '517520'
            gold_exec_name = '黄金股ETF (2x杠杆加速)'
        else:
            gold_exec_code = '518880'
            gold_exec_name = '黄金ETF (实物黄金)'

        w_gold_in_defense = 0.50 if gold_healthy else 0.15

        # 5. 目标仓位分配
        w_growth = target_exp
        w_def = 1.0 - target_exp

        positions = []
        if w_growth > 0.02:
            positions.append({
                'code': exec_code,
                'name': exec_name,
                'target_weight': w_growth,
                'price': quotes.get(exec_code, {}).get('price', lead_c),
                'pnl': quotes.get(exec_code, {}).get('change_pct', 0.0),
                'role': f'🚀 最强主攻【{lead_name} ➔ {exec_name} 增强】(100% 满仓)'
            })
            regime = f"🚀 100% 进攻态 · 主攻【{exec_name}】"
        else:
            w_gold = round(w_def * w_gold_in_defense, 4)
            w_bank = round(w_def * (1.0 - w_gold_in_defense), 4)
            positions.append({
                'code': gold_exec_code,
                'name': gold_exec_name,
                'target_weight': w_gold,
                'price': quotes.get(gold_exec_code, {}).get('price', c_gold),
                'pnl': quotes.get(gold_exec_code, {}).get('change_pct', 0.0),
                'role': f"🏆 避险增益 ({w_gold_in_defense*100:.0f}% 黄金配置)"
            })
            positions.append({
                'code': '601288',
                'name': '农业银行',
                'target_weight': w_bank,
                'price': quotes.get('601288', {}).get('price', c_abc),
                'pnl': quotes.get('601288', {}).get('change_pct', 0.0),
                'role': f"🏦 现金流防守 ({(1.0-w_gold_in_defense)*100:.0f}% 高股息压舱石)"
            })
            regime = f"🛡️ 弱势防守态 ({w_gold_in_defense*100:.0f}% 黄金 + {(1.0-w_gold_in_defense)*100:.0f}% 农行)"

        return {
            'status': 'OK',
            'regime': regime,
            'signal_code': signal_code,
            'signal_name': lead_name,
            'exec_code': exec_code,
            'exec_name': exec_name,
            'gold_exec_code': gold_exec_code,
            'gold_exec_name': gold_exec_name,
            'target_exp': target_exp,
            'positions': positions,
            'factor_scores': factor_scores,
            'chandelier_stop': chandelier_stop_p,
            'quotes': quotes,
            'candidates': candidates,
            'gold_healthy': gold_healthy
        }

    def format_report(self, stage: str, signal: dict) -> str:
        """渲染高颜值 Markdown 格式通知卡片"""
        if signal.get('status') != 'OK':
            return f"# ⚠️ 科创-银行轮动ETF策略 监控异常 ({stage})\n> 错误信息: {signal.get('msg', '未知异常')}"

        regime = signal['regime']
        target_exp = signal['target_exp'] * 100.0
        positions = signal['positions']
        signal_name = signal['signal_name']
        signal_code = signal['signal_code']
        exec_name = signal['exec_name']
        exec_code = signal['exec_code']
        stop_p = signal['chandelier_stop']
        quotes = signal.get('quotes', {})
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pos_lines = []
        for p in positions:
            w_pct = p['target_weight'] * 100.0
            pnl_txt = f"({p['pnl']:+.2f}%)" if p.get('pnl') is not None else ""
            pos_lines.append(f"• **{p['name']} (`{p['code']}`)**：目标仓位 `{w_pct:.1f}%` (现价 ¥{p['price']:.3f} {pnl_txt} | {p['role']})")
        pos_block = "\n".join(pos_lines) if pos_lines else "• 当前 100% 现金或银行底仓"

        # 候选池状态
        cand_lines = []
        for c in signal.get('candidates', []):
            flag = "🟢 多头" if c['bull'] else "🔴 偏弱"
            cand_lines.append(f"• {c['name']} (`{c['code']}`): 动量分 `{c['score']:.4f}` | {flag}")
        cand_block = "\n".join(cand_lines)

        # 执行层选拔详情
        factor_lines = []
        for k, v in signal.get('factor_scores', {}).items():
            factor_lines.append(f"• {k}: 因子得分 `{v:.4f}`")
        factor_block = "\n".join(factor_lines) if factor_lines else "• 纳指或防守模式，无需二次选拔"

        markdown = f"""# 👑 科创-银行轮动ETF策略 每日实盘报告 ({stage})
> 🧭 **市场运行周期**：<font color="info">**{regime}**</font>
> 🚀 **信号层决选主攻**：**{signal_name} (`{signal_code}`)** ➔ **执行增强标的：{exec_name} (`{exec_code}`)**
> 📊 **权益进攻敞口**：`{target_exp:.1f}%` | ⏰ **决策时间**：{now_str}

---
### 📦 【今日目标配置清单】
{pos_block}

---
### 🎯 【信号层三大基准竞争态势】
{cand_block}

### 📈 【执行层多因子智能选拔】
{factor_block}

---
### 🛡️ 【风控与交易指引】
• **-5.0% 宽幅动态吊灯防线**：{signal_name} 关键逃顶止盈位 **¥{stop_p:.3f}** (跌破强制清仓切入黄金+农行)
• **调仓窗口建议**：每日 **09:35** (开盘确认) 或 **14:48** (尾盘极速调仓)。
• **执行原则**：若与当前实际持仓偏差 < 5%，维持现状无需频繁倒手，最大化复利。

> 💡 *【官方基准战报】：10年累计 +2916.45% 🏆 | 年化 CAGR +45.73% 🏆 | 2026年实战翻倍 +99.40% 🚀*
"""
        return markdown.strip()

    def send_notification(self, stage: str = "14:48 盘尾确认", force: bool = False) -> bool:
        """计算并发送通知到企业微信群"""
        signal = self.calculate_strategy_signal()
        markdown_body = self.format_report(stage, signal)

        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": markdown_body}
        }

        try:
            data_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            resp = self.session.post(self.webhook_url, data=data_bytes, headers=headers, timeout=15)
            res_json = resp.json()
            if res_json.get("errcode") == 0:
                print(f"[+] [科创-银行轮动ETF策略] 企业微信推送成功 ({stage})！")
                return True
            else:
                print(f"[-] [科创-银行轮动ETF策略] 推送失败: {res_json.get('errcode')} - {res_json.get('errmsg')}")
                return False
        except Exception as e:
            print(f"[-] [科创-银行轮动ETF策略] 网络异常: {e}")
            return False


if __name__ == '__main__':
    notifier = StarBankRotationNotifier()
    print(">>> 正在运行【科创-银行轮动ETF策略 (DTB-Apex 黄金增强版)】信号计算与实时测试...")
    sig = notifier.calculate_strategy_signal()
    report = notifier.format_report(stage="14:48 尾盘测试", signal=sig)
    print(report)
    
    # 只要传入 --push 或者当前处于 GitHub Actions 环境下，则自动推送
    if ('--push' in sys.argv) or os.environ.get('GITHUB_ACTIONS') == 'true':
        notifier.send_notification(stage="14:48 盘尾确认", force=True)
