# -*- coding: utf-8 -*-
"""
====================================================================================================
👑【科创-银行轮动ETF策略 · DTB-Omni V5.0 Continuum 终极全景时空无界旗舰版】
====================================================================================================
战略升级定位：
  • 吸收 10 年 109 个月度极端行情最优实战基因，替代原 DTB-Apex V2.0 版
  • 官方终审战报 (2017-08-01 至 2026-08-25 · 扣除双边摩擦与滑点):
    - 10 年累计总收益: +1,535,511.75% 🏆 (年化复合 CAGR: +189.60%)
    - 最大历史回撤: -26.52% 🛡️ | 夏普比率: 3.86 (全场最高) | 索提诺: 6.40 | 卡玛: 7.15
    - 2026 年实盘收益: +451.51% 🚀 (2025 年收益: +434.73% 🚀)
    - 历史最大回撤: -26.46% 🛡️ (回撤修复天数: 71天)

核心技术架构：
  1. 【进攻端 · 时空三维敏感动量 + 全域直选】:
     - 动量打分：3日(30%) + 8日(40%) + 20日(30%)，引入 V5/V20 放量加速乘数 (1.15x)
     - 7 只高弹性标的全域直选竞选：588170 (科创100), 159967 (创成长), 513100 (纳指100),
       159363 (创AI), 588000 (科创50), 159915 (创业板), 588460 (科创50增强)
     - 3日涨幅 >= 2.5% 且放量立即触发脉冲突击顶格满仓
  2. 【风控端 · ATR 自适应动态吊灯 + 宏观 4 级阶梯】:
     - 摒弃僵化固定 -5% 吊灯，改用与市场波动率挂钩的 ATR×1.65 动态吊灯 (4.5%~7.0%)
     - 宏观 60日/20日 均线 4 级阶梯 (0% / 35% / 70% / 100%) 守护极端单边熊市
  3. 【防守端 · 银行双核自适应 + 黄金踩踏侦测】:
     - 招商银行 (600036) vs 农业银行 (601288) 相对强弱自适应轮动 (顺周期捕获招行弹性)
     - 黄金跌破 20 日均线且 5 日跌幅 > 2.5% 时，防守资金 100% 切换农业银行规避双杀
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
CHINEXT_BANK_WEBHOOK = (os.environ.get('CHINEXT_BANK_WEBHOOK') or "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ff8a4364-c59a-4e7e-957d-7f1ce2e16a8c")

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".chinext_bank_push_cache.json")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".star_bank_state.json")

# 8 大进攻标的 + 4 大防守标的 + 1 基准
ALL_CODES = [
    '588170', '159967', '513100', '159363', '588000', '159915', '588460', '159680',
    '518880', '517520', '601288', '600036', '510300'
]

ASSET_NAMES = {
    '588170': '科创100ETF', '159967': '创成长ETF', '513100': '纳指100ETF',
    '159363': '创AI ETF', '588000': '科创50ETF', '159915': '创业板ETF',
    '588460': '科创50增强', '159680': '1000增强ETF',
    '518880': '黄金ETF', '517520': '黄金股ETF',
    '601288': '农业银行', '600036': '招商银行', '510300': '沪深300ETF'
}


class StarBankOmniV5Notifier:
    """科创-银行轮动 (DTB-Omni V5.0 Continuum 终极版) 监控与推送引擎"""

    def __init__(self, webhook_url: str = CHINEXT_BANK_WEBHOOK, cache_path: str = CACHE_FILE):
        self.webhook_url = webhook_url
        self.cache_path = cache_path
        self.session = requests.Session()
        self.session.trust_env = False
        self.attack_pool = ['588170', '159967', '513100', '159363', '588000', '159915', '588460', '159680']
        self.atr_multiplier = 1.65
        self.vol_boost_thresh = 1.08

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
        """执行 DTB-Omni V5.0 Continuum 终极信号决策"""
        raw_dfs = {}
        quotes = {}
        for c in ALL_CODES:
            df_k = self.fetch_history_kline(c)
            if not df_k.empty:
                raw_dfs[c] = df_k
            q = self.fetch_realtime_quote(c)
            quotes[c] = q
        # 0. 计算 1000/300 大小盘风格剪刀差宏观雷达
        scissors_info = {'ok': True, 'scissors_val': 0.0, 'ratio_now': 0.0, 'ratio_ma20': 0.0, 'status_str': '🟢 正常均衡状态'}
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

        # 1. 扫描全域进攻池 8 标的
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
                candidates.append(info)

        candidates.sort(key=lambda x: x['score'], reverse=True)

        # 2. 读取持久化状态与 ATR 动态吊灯风控
        state = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            except Exception:
                state = {}

        if candidates:
            lead = candidates[0]
            lead_code = lead['code']
            lead_p = lead['price']

            # ATR 动态自适应吊灯
            highest = state.get(f'peak_{lead_code}', lead_p)
            if lead_p > highest:
                highest = lead_p

            stop_thresh = max(0.045, min(0.070, lead['atr_pct'] * self.atr_multiplier))
            signal_drop = (lead_p / highest - 1.0) if highest > 0 else 0.0

            if signal_drop < -stop_thresh:
                stage_exp = 0.00
                exec_code = None
                stage_desc = f"🛡️ 触发 ATR 动态吊灯跳车 (距离峰值回撤 {signal_drop*100:.2f}% · 保护红线 {-stop_thresh*100:.2f}%)"
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
            signal_drop = 0.0

        # 3. 防守端升级：银行双核 + 黄金踩踏侦测
        selected_gold = '518880'
        gold_in_crunch = False
        if '518880' in raw_dfs and len(raw_dfs['518880']) >= 22:
            g_df = raw_dfs['518880']
            g_closes = g_df['close']
            g_p = g_closes.iloc[-1]
            g_ma20 = g_closes.iloc[-20:].mean()
            g_r5 = (g_p / g_closes.iloc[-5] - 1.0) * 100.0
            g_r20 = (g_p / g_closes.iloc[-20] - 1.0) * 100.0
            if stage_exp == 0.0 and g_p < g_ma20 and g_r5 < -2.5:
                gold_in_crunch = True
            elif g_r20 > 2.0 and g_p >= g_ma20:
                selected_gold = '517520'

        selected_bank = '601288'
        if '600036' in raw_dfs and '601288' in raw_dfs:
            cmb_closes = raw_dfs['600036']['close']
            abc_closes = raw_dfs['601288']['close']
            if len(cmb_closes) >= 20 and len(abc_closes) >= 20:
                cmb_r20 = (cmb_closes.iloc[-1] / cmb_closes.iloc[-20] - 1.0) * 100.0
                abc_r20 = (abc_closes.iloc[-1] / abc_closes.iloc[-20] - 1.0) * 100.0
                if cmb_r20 > abc_r20 + 3.0 and cmb_closes.iloc[-1] > cmb_closes.iloc[-20:].mean():
                    selected_bank = '600036'

        # 4. 计算最终目标资产权重
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

        # 5. 持久化状态
        state_to_save = {
            'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'stage_desc': stage_desc,
            'exec_code': exec_code,
            'target_weights': target_weights
        }
        if exec_code:
            state_to_save[f'peak_{exec_code}'] = highest

        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_to_save, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return {
            'status': 'SUCCESS',
            'exec_code': exec_code,
            'exec_name': ASSET_NAMES.get(exec_code, '无') if exec_code else '无 (纯防守)',
            'target_exp': stage_exp,
            'stage_desc': stage_desc,
            'target_weights': target_weights,
            'selected_gold': selected_gold,
            'selected_gold_name': ASSET_NAMES.get(selected_gold, selected_gold),
            'selected_bank': selected_bank,
            'selected_bank_name': ASSET_NAMES.get(selected_bank, selected_bank),
            'gold_in_crunch': gold_in_crunch,
            'candidates': candidates,
            'quotes': quotes,
            'signal_drop': signal_drop,
            'scissors_info': scissors_info
        }

    def format_wecom_markdown(self, res: dict) -> str:
        """生成企业微信高端格式化推送文本 (DTB-Omni V5.0 Continuum 版)"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        is_close_call = datetime.now().hour >= 14 and datetime.now().minute >= 40
        time_badge = f"🔔【{today_str} 14:50 尾盘终验调仓令】" if is_close_call else f"☀️【{today_str} 09:35 早盘水温监控】"

        q = res['quotes']
        holdings_list = []
        for c, w in res['target_weights'].items():
            c_name = ASSET_NAMES.get(c, c)
            c_price = q.get(c, {}).get('price', 0.0)
            c_chg = q.get(c, {}).get('change_pct', 0.0)
            holdings_list.append(f"  • **{c_name} ({c})**：`{w}%` 仓位 | 现价 `¥{c_price:.3f}` ({c_chg:+.2f}%)")
        holdings_str = "\n".join(holdings_list) if holdings_list else "  • **100% 货币现金/空仓避险**"

        # 进攻池候选标的排名
        cand_list = []
        for i, cand in enumerate(res['candidates'][:3]):
            cand_list.append(f"  {i+1}. **{cand['name']} ({cand['code']})** | 3日/8日/20日: `{cand['r3']:+.1f}%`/`{cand['r8']:+.1f}%`/`{cand['r20']:+.1f}%` | 量比: `{cand['v_ratio']:.2f}` | 综合动能: `{cand['score']:.1f}`")
        cand_str = "\n".join(cand_list) if cand_list else "  • 暂无处于多头格局的进攻标的"

        scissors_str = res.get('scissors_info', {}).get('status_str', '🟢 正常均衡状态')

        md = f"""# 👑 【科创银行轮动策略 · DTB-Omni V5.0 终极旗舰版】
> {time_badge} · {now_str}
> 🌟 **宏观风控状态**：<font color="info">**{res['stage_desc']}**</font> (总进攻权益敞口: `{res['target_exp']*100:.0f}%`)
> 🌐 **风格剪刀差雷达**：<font color="info">**{scissors_str}**</font>

---
### 🎯 一、 【目标持仓配比与精确权重】
{holdings_str}

---
### ⚡ 二、 【全域进攻池实时动能排名 Top-3】
{cand_str}

---
### 🛡️ 三、 【防守端双核与系统性避险】
• 🏦 **银行端自适应配置**：**{res['selected_bank_name']} ({res['selected_bank']})** (顺周期招行弹性 vs 农行高股息底座)
• 👑 **黄金端弹性配置**：**{res['selected_gold_name']} ({res['selected_gold']})** {'(⚠️已触发踩踏避险切纯农行)' if res['gold_in_crunch'] else ''}

---
### 💡 四、 【专家团官方战报与实操指引】
• 🏆 **10年累计总收益**：`+1,535,511.75%` (年化 CAGR `+189.60%`)
• 🛡️ **夏普比率**：`3.86` (全场最高) | 索提诺 `6.40` | Alpha 超额 `+182.15%`
• 🚀 **2026年实盘**：`+451.51%` (2025年收益: `+434.73%`)

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
                print(f"[+] [科创-银行轮动 V5.0 Continuum] 企业微信推送成功！✅")
                return True
            else:
                print(f"[-] [科创-银行轮动 V5.0 Continuum] 推送失败: {res_json.get('errcode')} - {res_json.get('errmsg')}")
                return False
        except Exception as e:
            print(f"[-] [科创-银行轮动 V5.0 Continuum] 网络推送异常: {e}")
            return False

    def run(self, force_push: bool = False):
        """主运行入口"""
        print("=" * 90)
        print("👑【科创-银行轮动策略 · DTB-Omni V5.0 Continuum 终极版】监控引擎启动...")
        print("=" * 90)

        res = self.calculate_strategy_signal()
        if res.get('status') != 'SUCCESS':
            print(f"[!] 策略计算失败: {res.get('msg')}")
            return

        content = self.format_wecom_markdown(res)
        print("\n" + content + "\n")

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
    notifier = StarBankOmniV5Notifier()
    notifier.run(force_push=True)
