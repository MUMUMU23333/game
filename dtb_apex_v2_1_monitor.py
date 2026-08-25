# -*- coding: utf-8 -*-
"""
====================================================================================================
🏛️【DTB-Apex V2.1 · 尾盘 10 分钟极速调仓 · 实盘监控与企业微信推送引擎】
====================================================================================================
模式二：Close-of-Day 尾盘极速调仓 (高胜率 · 当日收盘模式)

运行时间：每交易日 14:50 (北京时间) — 收盘前 10 分钟黄金决策窗口
核心逻辑：
  1. 拉取所有标的实时行情 + 80 日历史 K 线
  2. 运行 V2.1 信号决策引擎 (软风险预算 + 多因子选拔 + 防御篮子 + 现金选择权)
  3. 对比昨日持仓状态 (.dtb_apex_state.json 持久化)
  4. 渲染企业微信 Markdown 推送卡片
  5. 防重复推送 + UTF-8 编码保护

架构来源：DTB-Apex V2.1 Adaptive Institutional Edition
  - 信号层：159915 创业板指 + 513100 纳指100 + 588000 科创50
  - 风控层：-5% 动态吊灯跳车 + Soft Risk Budget [0.60 ~ 1.00]
  - 执行层：多因子选拔 (科创 588460/588170, 创业板 159363/159967)
  - 黄金端：主升浪确认 → 517520 (黄金股 2x), 平稳期 → 518880 (实物黄金)
  - 防御层：银行双雄择优 (601288 农行 vs 600036 招行) + 黄金动态配比
====================================================================================================
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import requests
from datetime import datetime

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# =====================================================================
# 配置常量
# =====================================================================
DEFAULT_WECOM_WEBHOOK = os.environ.get(
    'WECOM_WEBHOOK',
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b74cac3-9fc2-497c-a287-b591246e3393"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, ".dtb_apex_state.json")
PUSH_CACHE_FILE = os.path.join(SCRIPT_DIR, ".dtb_apex_push_cache.json")

# 全量资产池
ALL_CODES = [
    '159915', '588000', '513100', '510300',
    '518880', '517520', '601288', '600036',
    '588460', '588170', '159363', '159967'
]

# 差异化交易摩擦 (双边)
FRICTION_RATES = {
    '159915': 0.0005, '588000': 0.0005, '513100': 0.0004,
    '588460': 0.0005, '588170': 0.0005, '159363': 0.0005, '159967': 0.0005,
    '518880': 0.0003, '517520': 0.0004,
    '601288': 0.0002, '600036': 0.0002, '510300': 0.0003
}

# 信号层标的 (用于判断牛熊信号)
SIGNAL_CODES = ['159915', '588000', '513100']

# 成长型资产 (用于判断是否需要清空成长仓位)
GROWTH_ASSETS = ['159915', '513100', '588000', '588460', '588170', '159363', '159967']

# 资产中文名映射
ASSET_NAMES = {
    '159915': '创业板ETF', '588000': '科创50ETF', '513100': '纳指100ETF',
    '510300': '沪深300ETF', '518880': '黄金ETF', '517520': '黄金股ETF',
    '601288': '农业银行', '600036': '招商银行',
    '588460': '科创50增强', '588170': '科创100ETF',
    '159363': '创AI ETF', '159967': '创成长ETF'
}

session = requests.Session()
session.trust_env = False


# =====================================================================
# 数据层：历史 K 线 + 实时行情
# =====================================================================
def fetch_history_kline(code: str, days: int = 500) -> pd.DataFrame:
    """拉取历史前复权日 K 线 (腾讯财经接口)"""
    market = 'sh' if code.startswith(('51', '58', '60', '000')) else 'sz'
    today_str = datetime.now().strftime('%Y-%m-%d')
    chunks = [
        ('2014-01-01', '2016-12-31'),
        ('2017-01-01', '2019-12-31'),
        ('2020-01-01', '2022-12-31'),
        ('2023-01-01', today_str)
    ]
    records = []
    seen = set()
    for s_date, e_date in chunks:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,{s_date},{e_date},800,qfq"
        try:
            res = session.get(url, timeout=15).json()
            raw = res.get('data', {}).get(f"{market}{code}", {})
            k = raw.get('qfqday') or raw.get('day', [])
            for item in k:
                d = str(item[0])
                if d not in seen:
                    seen.add(d)
                    records.append({
                        'date': d,
                        'open': float(item[1]),
                        'close': float(item[2]),
                        'high': float(item[3]),
                        'low': float(item[4]),
                        'volume': float(item[5]) if len(item) > 5 else 0.0
                    })
        except Exception as e:
            print(f"[!] 拉取 {code} K线异常: {e}")
    df = pd.DataFrame(records)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
    return df


def fetch_realtime_quote(code: str) -> dict:
    """拉取腾讯实时行情"""
    market = 'sh' if code.startswith(('51', '58', '60', '000')) else 'sz'
    url = f"http://qt.gtimg.cn/q={market}{code}"
    try:
        resp = session.get(url, timeout=5)
        text = resp.text
        if not text or '=' not in text:
            return {}
        parts = text.split('="')[1].split('~')
        if len(parts) > 30:
            return {
                'code': code,
                'name': parts[1],
                'price': float(parts[3]),
                'prev_close': float(parts[4]),
                'change_pct': float(parts[32]) if parts[32] else 0.0
            }
    except Exception as e:
        print(f"[!] 获取实时行情失败 {code}: {e}")
    return {'code': code, 'name': ASSET_NAMES.get(code, code), 'price': 0.0, 'prev_close': 0.0, 'change_pct': 0.0}


# =====================================================================
# 技术指标预计算引擎
# =====================================================================
def build_indicator_dataframe() -> pd.DataFrame:
    """构建包含所有资产 OHLCV 和技术指标的宽表"""
    print(">>> [1/4] 正在拉取所有标的历史 K 线数据...")
    raw_dfs = {}
    for c in ALL_CODES:
        raw_dfs[c] = fetch_history_kline(c)
        row_count = len(raw_dfs[c]) if not raw_dfs[c].empty else 0
        print(f"    ✓ {ASSET_NAMES.get(c, c)} ({c}): {row_count} 条日线")

    # 以创业板 ETF 为主轴构建宽表
    base_df = raw_dfs['159915'][['date', 'open', 'close', 'high', 'low', 'volume']].copy()
    base_df.columns = ['date', '159915_open', '159915_close', '159915_high', '159915_low', '159915_volume']

    for c in ALL_CODES:
        if c == '159915':
            continue
        if raw_dfs[c].empty:
            continue
        sub = raw_dfs[c][['date', 'open', 'close', 'high', 'low', 'volume']].copy()
        sub.columns = ['date', f'{c}_open', f'{c}_close', f'{c}_high', f'{c}_low', f'{c}_volume']
        base_df = pd.merge(base_df, sub, on='date', how='left')

    df = base_df.sort_values('date').reset_index(drop=True)

    # 计算技术指标
    print(">>> [2/4] 正在计算全量技术指标...")
    for c in ALL_CODES:
        col = f'{c}_close'
        if col not in df.columns:
            continue
        df[f'{c}_ema8']   = df[col].ewm(span=8).mean()
        df[f'{c}_ema20']  = df[col].ewm(span=20).mean()
        df[f'{c}_ema60']  = df[col].ewm(span=60).mean()
        df[f'{c}_ma20']   = df[col].rolling(20).mean()
        df[f'{c}_ma60']   = df[col].rolling(60).mean()
        df[f'{c}_ma120']  = df[col].rolling(120).mean()
        df[f'{c}_m3']     = df[col] / df[col].shift(3) - 1.0
        df[f'{c}_m5']     = df[col] / df[col].shift(5) - 1.0
        df[f'{c}_m10']    = df[col] / df[col].shift(10) - 1.0
        df[f'{c}_m20']    = df[col] / df[col].shift(20) - 1.0
        ret = df[col].pct_change()
        df[f'{c}_vol20']  = ret.rolling(20).std() * np.sqrt(250)
        v_col = f'{c}_volume'
        if v_col in df.columns:
            df[f'{c}_vma20'] = df[v_col].rolling(20).mean()

    # 黄金相对强弱
    if '517520_close' in df.columns and '518880_close' in df.columns:
        df['gold_rs'] = df['517520_close'] / df['518880_close']
        df['gold_rs_ma20'] = df['gold_rs'].rolling(20).mean()

    return df


# =====================================================================
# V2.1 信号决策引擎
# =====================================================================
def compute_factor_score(df: pd.DataFrame, code: str, i: int) -> float:
    """多因子选拔得分 (Momentum 40% + Trend 30% + RiskAdj 30%)"""
    col = f'{code}_close'
    if col not in df.columns or pd.isna(df[col].iloc[i]):
        return -999.0

    p = df[col].iloc[i]
    m5  = df[f'{code}_m5'].iloc[i]  if not pd.isna(df[f'{code}_m5'].iloc[i])  else 0.0
    m10 = df[f'{code}_m10'].iloc[i] if not pd.isna(df[f'{code}_m10'].iloc[i]) else 0.0
    m20 = df[f'{code}_m20'].iloc[i] if not pd.isna(df[f'{code}_m20'].iloc[i]) else 0.0

    e8  = df[f'{code}_ema8'].iloc[i]
    e20 = df[f'{code}_ema20'].iloc[i]
    ma20 = df[f'{code}_ma20'].iloc[i]
    vol20 = df[f'{code}_vol20'].iloc[i] if not pd.isna(df[f'{code}_vol20'].iloc[i]) else 0.30

    mom_score = 0.50 * m5 + 0.30 * m10 + 0.20 * m20

    trend_score = 0.0
    if p > e8:   trend_score += 0.40
    if e8 > e20: trend_score += 0.35
    if p > ma20: trend_score += 0.25

    sharpe_proxy = (m20 / (vol20 + 1e-4)) * np.sqrt(250 / 20)
    risk_adj = np.tanh(sharpe_proxy * 0.5)

    return 0.40 * mom_score + 0.30 * trend_score + 0.30 * risk_adj


def calculate_soft_risk_budget(df: pd.DataFrame, i: int) -> float:
    """
    软风险预算系数 [0.60, 1.00]:
    沪深300趋势(30%) + 纳指趋势(30%) + 波动率(20%) + 黄金强度(20%)
    """
    risk_score = 0.0

    # 1. 沪深300趋势 (30%)
    c_300 = df['510300_close'].iloc[i] if '510300_close' in df.columns and not pd.isna(df['510300_close'].iloc[i]) else 0
    e20_300 = df['510300_ema20'].iloc[i] if '510300_ema20' in df.columns and not pd.isna(df['510300_ema20'].iloc[i]) else c_300
    m20_300 = df['510300_m20'].iloc[i] if '510300_m20' in df.columns and not pd.isna(df['510300_m20'].iloc[i]) else 0
    if c_300 > e20_300:
        risk_score += 0.18
    if m20_300 > 0:
        risk_score += 0.12

    # 2. 纳指100趋势 (30%)
    c_ndx = df['513100_close'].iloc[i]
    e20_ndx = df['513100_ema20'].iloc[i]
    m20_ndx = df['513100_m20'].iloc[i] if not pd.isna(df['513100_m20'].iloc[i]) else 0
    if c_ndx > e20_ndx:
        risk_score += 0.18
    if m20_ndx > 0:
        risk_score += 0.12

    # 3. 波动率健康度 (20%)
    vol_cyb = df['159915_vol20'].iloc[i] if not pd.isna(df['159915_vol20'].iloc[i]) else 0.30
    if vol_cyb < 0.35:
        risk_score += 0.20
    elif vol_cyb < 0.45:
        risk_score += 0.10

    # 4. 黄金对冲强弱 (20%)
    c_gold = df['518880_close'].iloc[i]
    e20_gold = df['518880_ema20'].iloc[i]
    if c_gold > e20_gold:
        risk_score += 0.20

    return 0.60 + 0.40 * risk_score


def run_signal_engine(df: pd.DataFrame) -> dict:
    """
    运行 V2.1 信号决策引擎 (使用最新一行数据)

    返回:
      signal_code: 信号层选中的基准标的
      exec_code: 执行层实际交易标的
      target_weights: 目标权重字典
      soft_budget: 软风险预算倍率
      gold_exec_code: 黄金端执行标的
      bank_exec_code: 银行端执行标的
      factor_scores: 各标的因子得分
      is_growth: 是否处于成长进攻态
      diagnostics: 诊断信息
    """
    i = len(df) - 1  # 最新一行 (当日数据)
    dates = df['date']
    dt = dates.iloc[i]

    # ---------------------------------------------------------------
    # 信号层：三大基准指数评分
    # ---------------------------------------------------------------
    c_cyb    = df['159915_close'].iloc[i]
    c_nasdaq = df['513100_close'].iloc[i]
    has_star = '588000_close' in df.columns and not pd.isna(df['588000_close'].iloc[i])
    c_star   = df['588000_close'].iloc[i] if has_star else c_cyb

    s_cyb  = 0.40 * df['159915_m5'].iloc[i] + 0.35 * df['159915_m10'].iloc[i] + 0.25 * df['159915_m20'].iloc[i]
    s_star = (0.50 * df['588000_m5'].iloc[i] + 0.30 * df['588000_m10'].iloc[i] + 0.20 * df['588000_m20'].iloc[i]) if has_star else -1.0
    s_ndx  = 0.45 * df['513100_m5'].iloc[i] + 0.35 * df['513100_m10'].iloc[i] + 0.20 * df['513100_m20'].iloc[i]

    # 脉冲检测
    pulse_cyb  = df['159915_m5'].iloc[i] > 0.035
    pulse_star = has_star and (df['588000_m5'].iloc[i] > 0.035)

    # 牛熊判断
    bull_cyb = (c_cyb > df['159915_ema8'].iloc[i] and
                df['159915_ema8'].iloc[i] > df['159915_ema20'].iloc[i] and
                c_cyb > df['159915_ma20'].iloc[i]) or pulse_cyb

    bull_star = has_star and (
        (c_star > df['588000_ema8'].iloc[i] and
         df['588000_ema8'].iloc[i] > df['588000_ema20'].iloc[i] and
         c_star > df['588000_ma20'].iloc[i]) or pulse_star
    )

    bull_ndx = (c_nasdaq > df['513100_ema8'].iloc[i] and
                df['513100_ema8'].iloc[i] > df['513100_ema20'].iloc[i] and
                c_nasdaq > df['513100_ma20'].iloc[i] and
                df['513100_m10'].iloc[i] > 0.015)

    candidates = [
        {'code': '159915', 'score': s_cyb, 'bull': bull_cyb},
        {'code': '513100', 'score': s_ndx, 'bull': bull_ndx}
    ]
    if has_star:
        candidates.append({'code': '588000', 'score': s_star, 'bull': bull_star})

    bull_cands = [c for c in candidates if c['bull']]

    if bull_cands:
        lead = max(bull_cands, key=lambda x: x['score'])
        signal_code = lead['code']
        soft_budget = calculate_soft_risk_budget(df, i)
        target_exp = soft_budget
    else:
        signal_code = '159915'
        target_exp = 0.00
        soft_budget = 0.00

    # ---------------------------------------------------------------
    # 执行层：多因子选拔 + 现金选择权
    # ---------------------------------------------------------------
    factor_scores = {}
    exec_code = signal_code

    if signal_code == '588000':
        sc_460 = compute_factor_score(df, '588460', i)
        sc_170 = compute_factor_score(df, '588170', i)
        factor_scores['588460'] = sc_460
        factor_scores['588170'] = sc_170
        if sc_460 == -999.0 and sc_170 == -999.0:
            exec_code = '588000'
        elif sc_460 > -999.0 and sc_170 == -999.0:
            exec_code = '588460'
        elif sc_170 > -999.0 and sc_460 == -999.0:
            exec_code = '588170'
        else:
            best_sc = max(sc_460, sc_170)
            if best_sc < -0.05:
                exec_code = 'CASH'
            else:
                exec_code = '588170' if sc_170 > sc_460 else '588460'

    elif signal_code == '159915':
        sc_363 = compute_factor_score(df, '159363', i)
        sc_967 = compute_factor_score(df, '159967', i)
        factor_scores['159363'] = sc_363
        factor_scores['159967'] = sc_967
        if sc_363 == -999.0 and sc_967 == -999.0:
            exec_code = '159915'
        elif sc_967 > -999.0 and sc_363 == -999.0:
            exec_code = '159967'
        elif sc_363 > -999.0 and sc_967 == -999.0:
            exec_code = '159363'
        else:
            best_sc = max(sc_363, sc_967)
            if best_sc < -0.05:
                exec_code = 'CASH'
            else:
                exec_code = '159363' if sc_363 > sc_967 else '159967'

    elif signal_code == '513100':
        factor_scores['513100'] = compute_factor_score(df, '513100', i)

    # ---------------------------------------------------------------
    # 动态吊灯风控 (使用历史数据)
    # ---------------------------------------------------------------
    # 检查近期 5 日是否触发 -5% 吊灯跳车
    lead_col = f'{signal_code}_close'
    if lead_col in df.columns and i >= 5:
        recent_peak = df[lead_col].iloc[max(0, i-20):i+1].max()
        current = df[lead_col].iloc[i]
        drop_from_peak = (current - recent_peak) / recent_peak if recent_peak > 0 else 0

        lead_e20 = df[f'{signal_code}_ema20'].iloc[i]
        lead_ma20 = df[f'{signal_code}_ma20'].iloc[i]
        signal_breakdown = (drop_from_peak < -0.050) or (current < lead_e20 and current < lead_ma20)

        if signal_breakdown and target_exp > 0:
            target_exp = 0.00

    is_growth = (target_exp > 0.10 and exec_code != 'CASH')

    # ---------------------------------------------------------------
    # 防御全息动态篮子
    # ---------------------------------------------------------------
    c_gold = df['518880_close'].iloc[i]
    gold_m20 = df['518880_m20'].iloc[i] if not pd.isna(df['518880_m20'].iloc[i]) else 0
    gold_e20 = df['518880_ema20'].iloc[i]
    gold_e60 = df['518880_ema60'].iloc[i] if '518880_ema60' in df.columns else gold_e20

    gold_healthy = c_gold > gold_e20

    # 黄金股相对强弱
    rs_ok = True
    if 'gold_rs' in df.columns and 'gold_rs_ma20' in df.columns:
        curr_rs = df['gold_rs'].iloc[i]
        ma_rs = df['gold_rs_ma20'].iloc[i]
        if not pd.isna(curr_rs) and not pd.isna(ma_rs):
            rs_ok = (curr_rs >= ma_rs * 0.99)

    has_gold_stock = '517520_close' in df.columns and not pd.isna(df['517520_close'].iloc[i]) and df['517520_close'].iloc[i] > 0
    if has_gold_stock and gold_m20 > 0.025 and c_gold > gold_e20 and c_gold > gold_e60 and rs_ok:
        gold_exec_code = '517520'
    else:
        gold_exec_code = '518880'

    # 银行双雄择优
    if '600036_close' in df.columns and not pd.isna(df['600036_close'].iloc[i]):
        sc_abc = compute_factor_score(df, '601288', i)
        sc_cmb = compute_factor_score(df, '600036', i)
        bank_exec_code = '600036' if sc_cmb > sc_abc else '601288'
        factor_scores['601288'] = sc_abc
        factor_scores['600036'] = sc_cmb
    else:
        bank_exec_code = '601288'

    w_gold_in_defense = 0.50 if gold_healthy else 0.15

    # ---------------------------------------------------------------
    # 目标权重计算
    # ---------------------------------------------------------------
    target_weights = {c: 0.0 for c in ALL_CODES}
    w_growth = target_exp if exec_code != 'CASH' else 0.0
    w_def = 1.0 - w_growth

    if exec_code in target_weights and exec_code != 'CASH':
        target_weights[exec_code] = w_growth

    if w_def > 0:
        w_bank = 1.0 - w_gold_in_defense
        target_weights[gold_exec_code] += w_def * w_gold_in_defense
        target_weights[bank_exec_code] += w_def * w_bank

    # 诊断信息
    diagnostics = {
        'date': str(dt.date()) if hasattr(dt, 'date') else str(dt),
        'signal_scores': {
            '159915': round(float(s_cyb), 4),
            '513100': round(float(s_ndx), 4),
            '588000': round(float(s_star), 4) if has_star else None
        },
        'bull_flags': {
            '159915': bool(bull_cyb),
            '513100': bool(bull_ndx),
            '588000': bool(bull_star) if has_star else False
        },
        'soft_budget': round(float(soft_budget), 4),
        'target_exposure': round(float(target_exp), 4),
        'gold_healthy': bool(gold_healthy),
        'gold_rs_ok': bool(rs_ok),
        'w_gold_in_defense': round(float(w_gold_in_defense), 4)
    }

    return {
        'signal_code': signal_code,
        'exec_code': exec_code,
        'target_weights': {k: round(v, 4) for k, v in target_weights.items()},
        'soft_budget': round(float(soft_budget), 4),
        'gold_exec_code': gold_exec_code,
        'bank_exec_code': bank_exec_code,
        'factor_scores': {k: round(float(v), 4) for k, v in factor_scores.items()},
        'is_growth': is_growth,
        'diagnostics': diagnostics
    }


# =====================================================================
# 持仓状态管理
# =====================================================================
def load_state() -> dict:
    """加载上次持仓状态"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'holding_code': None, 'holding_name': None, 'entry_date': None, 'entry_price': 0.0, 'holding_days': 0}


def save_state(state: dict):
    """持久化持仓状态"""
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] 持仓状态写入失败: {e}")


# =====================================================================
# 防重复推送
# =====================================================================
def is_duplicate_push(push_key: str) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(PUSH_CACHE_FILE):
        try:
            with open(PUSH_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            return push_key in cache.get(today, {})
        except Exception:
            pass
    return False


def record_push(push_key: str):
    today = datetime.now().strftime("%Y-%m-%d")
    cache = {}
    if os.path.exists(PUSH_CACHE_FILE):
        try:
            with open(PUSH_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception:
            pass
    if today not in cache:
        # 清理 7 天前的记录
        old_keys = [k for k in cache if k < today]
        for k in old_keys[:-7] if len(old_keys) > 7 else []:
            del cache[k]
        cache[today] = {}
    cache[today][push_key] = datetime.now().strftime("%H:%M:%S")
    try:
        with open(PUSH_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# =====================================================================
# 企业微信 Markdown 推送渲染
# =====================================================================
def render_wecom_markdown(signal_result: dict, quotes: dict, prev_state: dict) -> str:
    """渲染企业微信 Markdown 推送卡片"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diag = signal_result['diagnostics']

    exec_code = signal_result['exec_code']
    exec_name = ASSET_NAMES.get(exec_code, exec_code)
    signal_code = signal_result['signal_code']
    signal_name = ASSET_NAMES.get(signal_code, signal_code)
    gold_exec = signal_result['gold_exec_code']
    gold_name = ASSET_NAMES.get(gold_exec, gold_exec)
    bank_exec = signal_result['bank_exec_code']
    bank_name = ASSET_NAMES.get(bank_exec, bank_exec)
    soft_budget = signal_result['soft_budget']
    is_growth = signal_result['is_growth']
    target_weights = signal_result['target_weights']

    # 判断调仓类型
    prev_holding = prev_state.get('holding_code')
    if is_growth:
        current_main = exec_code
    else:
        current_main = 'DEFENSE'  # 防御态

    is_switch = (prev_holding != current_main) and prev_holding is not None

    # 状态徽章
    if is_growth:
        if exec_code == 'CASH':
            badge = "💰 【现金选择权 · 拒绝强行买入】"
        else:
            badge = "🚀 【成长进攻态】"
    else:
        badge = "🛡️ 【防御避险态】"

    # 行情速览
    quote_lines = []
    for c in ['159915', '588000', '513100', '518880', '517520', '601288', '600036']:
        q = quotes.get(c, {})
        if q and q.get('price', 0) > 0:
            name = ASSET_NAMES.get(c, c)
            chg = q.get('change_pct', 0)
            color = "warning" if chg > 0 else ("info" if chg < 0 else "comment")
            quote_lines.append(f"• {name} ({c}): <font color=\"{color}\">{q['price']:.3f} 元 ({chg:+.2f}%)</font>")

    quote_block = "\n".join(quote_lines) if quote_lines else "• 行情数据加载中..."

    # 调仓指令
    if is_switch:
        prev_name = ASSET_NAMES.get(prev_holding, prev_holding) if prev_holding else "空仓"
        hold_days = prev_state.get('holding_days', 0)
        action_block = f"""**⚡ 【调仓指令】**
🔴 **卖出** `{prev_holding}` {prev_name} (持仓 {hold_days} 日)
🟢 **买入** `{exec_code if is_growth else f'{gold_exec}+{bank_exec}'}` {exec_name if is_growth else f'{gold_name}+{bank_name}'}"""
    else:
        if is_growth and exec_code != 'CASH':
            action_block = f"**⚪ 【续持】** `{exec_code}` {exec_name} (持仓 {prev_state.get('holding_days', 0)+1} 日)"
        else:
            action_block = f"**⚪ 【续持防御】** {gold_name} ({gold_exec}) + {bank_name} ({bank_exec})"

    # 权重配置
    weight_lines = []
    for c, w in sorted(target_weights.items(), key=lambda x: -x[1]):
        if w > 0.001:
            name = ASSET_NAMES.get(c, c)
            weight_lines.append(f"• {name} ({c}): **{w*100:.1f}%**")
    weight_block = "\n".join(weight_lines) if weight_lines else "• 全仓现金"

    # 因子得分
    factor_lines = []
    for c, sc in sorted(signal_result['factor_scores'].items(), key=lambda x: -x[1]):
        name = ASSET_NAMES.get(c, c)
        marker = "✅ 入选" if c == exec_code else "候选"
        factor_lines.append(f"• {name} ({c}): `{sc:.4f}` ({marker})")
    factor_block = "\n".join(factor_lines) if factor_lines else "• 无因子数据"

    # 信号层牛熊
    bull_flags = diag['bull_flags']
    bull_lines = []
    for c, flag in bull_flags.items():
        name = ASSET_NAMES.get(c, c)
        icon = "🟢" if flag else "🔴"
        s = diag['signal_scores'].get(c, 0)
        s_str = f"{s:.4f}" if s is not None else "N/A"
        bull_lines.append(f"• {icon} {name} ({c}): 信号分 `{s_str}` ({'趋势做多' if flag else '趋势偏弱'})")
    bull_block = "\n".join(bull_lines)

    markdown = f"""### 🏛️ DTB-Apex V2.1 · 尾盘 10 分钟极速调仓信号

> ⏰ **决策时间**：{now_str} (北京时间)
> 🎯 **执行模式**：模式二 · 尾盘 14:50~15:00 当日收盘调仓

**📊 实时行情速览**:
{quote_block}

---
{action_block}

---
**📐 目标权重配置**:
{weight_block}

---
**🎯 信号层三大基准牛熊判断**:
{bull_block}

**📈 执行层多因子选拔**:
{factor_block}

---
**⚙️ V2.1 机构级量化雷达**:
• **软风险预算倍率**: `{soft_budget:.2f}` ({'进攻' if soft_budget > 0.80 else '谨慎' if soft_budget > 0.60 else '防御'})
• **成长目标敞口**: `{diag['target_exposure']*100:.1f}%`
• **黄金健康度**: {'🟢 健康' if diag['gold_healthy'] else '🟡 回调'} | 黄金股相对强弱: {'🟢 OK' if diag['gold_rs_ok'] else '🔴 偏弱'}
• **防御端黄金占比**: `{diag['w_gold_in_defense']*100:.0f}%`
• **当前状态**: {badge}

> 💡 *DTB-Apex V2.1 Adaptive Institutional · 软风险预算 + 防御资产全息动态篮子 + 现金选择权*"""

    return markdown.strip()


# =====================================================================
# 主函数：监控入口
# =====================================================================
def run_monitor(webhook_url: str = DEFAULT_WECOM_WEBHOOK, dry_run: bool = False, force: bool = False):
    """
    运行实盘监控引擎

    Args:
        webhook_url: 企业微信 Webhook 地址
        dry_run: 若 True 则仅打印不推送
        force: 若 True 则忽略防重复推送
    """
    print("=" * 100)
    print("🏛️ DTB-Apex V2.1 · 尾盘 10 分钟极速调仓 · 实盘监控引擎启动")
    print("=" * 100)

    # 1. 构建指标宽表
    df = build_indicator_dataframe()
    if df.empty or len(df) < 100:
        print("[!] 数据不足，无法运行信号引擎")
        return

    # 2. 拉取实时行情
    print(">>> [3/4] 正在拉取实时行情...")
    quotes = {}
    for c in ALL_CODES:
        q = fetch_realtime_quote(c)
        if q and q.get('price', 0) > 0:
            quotes[c] = q
            print(f"    ✓ {ASSET_NAMES.get(c, c)} ({c}): {q['price']:.3f} 元 ({q.get('change_pct', 0):+.2f}%)")

    # 3. 运行信号引擎
    print(">>> [4/4] 正在运行 V2.1 信号决策引擎...")
    signal_result = run_signal_engine(df)

    print(f"\n    🎯 信号层选中: {signal_result['signal_code']} ({ASSET_NAMES.get(signal_result['signal_code'], '')})")
    print(f"    ⚡ 执行层标的: {signal_result['exec_code']} ({ASSET_NAMES.get(signal_result['exec_code'], '')})")
    print(f"    🛡️ 黄金端执行: {signal_result['gold_exec_code']} ({ASSET_NAMES.get(signal_result['gold_exec_code'], '')})")
    print(f"    🏦 银行端执行: {signal_result['bank_exec_code']} ({ASSET_NAMES.get(signal_result['bank_exec_code'], '')})")
    print(f"    📐 软风险预算: {signal_result['soft_budget']:.2f}")
    print(f"    📊 成长进攻态: {'是' if signal_result['is_growth'] else '否'}")

    # 4. 加载上次状态
    prev_state = load_state()

    # 5. 渲染 Markdown
    markdown_body = render_wecom_markdown(signal_result, quotes, prev_state)
    print(f"\n{'='*80}")
    print(markdown_body)
    print(f"{'='*80}")

    # 6. 更新持仓状态
    if signal_result['is_growth'] and signal_result['exec_code'] != 'CASH':
        new_main = signal_result['exec_code']
    else:
        new_main = 'DEFENSE'

    if prev_state.get('holding_code') == new_main:
        new_state = {
            'holding_code': new_main,
            'holding_name': ASSET_NAMES.get(new_main, new_main),
            'entry_date': prev_state.get('entry_date', datetime.now().strftime('%Y-%m-%d')),
            'entry_price': prev_state.get('entry_price', 0.0),
            'holding_days': prev_state.get('holding_days', 0) + 1,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'signal_result': signal_result
        }
    else:
        q = quotes.get(new_main if new_main != 'DEFENSE' else signal_result['gold_exec_code'], {})
        new_state = {
            'holding_code': new_main,
            'holding_name': ASSET_NAMES.get(new_main, new_main),
            'entry_date': datetime.now().strftime('%Y-%m-%d'),
            'entry_price': q.get('price', 0.0),
            'holding_days': 1,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'signal_result': signal_result
        }
    save_state(new_state)
    print(f"\n[+] 持仓状态已更新: {new_state['holding_code']} ({new_state['holding_name']})")

    # 7. 推送企业微信
    if dry_run:
        print("\n[i] DRY RUN 模式 — 跳过企业微信推送")
        return

    push_key = f"DTB_V2.1_{datetime.now().strftime('%H')}"
    if not force and is_duplicate_push(push_key):
        print(f"\n[i] 今日 {push_key} 已推送，防重复机制拦截")
        return

    if not webhook_url:
        print("\n[!] 未配置 WECOM_WEBHOOK，跳过推送")
        return

    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {"msgtype": "markdown", "markdown": {"content": markdown_body}}

    try:
        data_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        resp = session.post(webhook_url, data=data_bytes, headers=headers, timeout=15)
        res_json = resp.json()

        if res_json.get("errcode") == 0:
            print(f"\n[+] [企业微信] 推送成功！✅")
            record_push(push_key)
        else:
            print(f"\n[-] [企业微信] 推送失败: {res_json.get('errcode')} - {res_json.get('errmsg')}")
    except Exception as e:
        print(f"\n[-] [企业微信] 网络异常: {e}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='DTB-Apex V2.1 尾盘极速调仓监控引擎')
    parser.add_argument('--dry-run', action='store_true', help='仅打印信号不推送')
    parser.add_argument('--force', action='store_true', help='忽略防重复推送')
    parser.add_argument('--webhook', default=DEFAULT_WECOM_WEBHOOK, help='企业微信 Webhook URL')
    args = parser.parse_args()

    run_monitor(webhook_url=args.webhook, dry_run=args.dry_run, force=args.force)
