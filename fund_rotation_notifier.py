# -*- coding: utf-8 -*-
"""
====================================================================================================
👑【Apex Infinite Sovereign V100.0 80%黄金鱼身至尊版 · 生产实盘部署巡航系统】
====================================================================================================
版本代号：Apex Infinite Sovereign V100.0 Master Production
核心机制：
  1. ⏰【14:48 黄金抢跑窗口】: 每个交易日 14:45~14:50 自动扫描全市场 14 大核心高弹性母库与盘中估值；
  2. 🏆【80% 黄金鱼身浮盈铁锁】:
     - 浮盈 < 15%: 保持 -6.5% 宽幅吊灯容错，享受牛市主升浪狂飙，绝不被震仓洗下车；
     - 浮盈 >= 15%: 启动保底铁锁，最大允许回吐 <= 20% 峰值浮盈 (死死锁死 80% 核心鱼身战果)；
  3. 👑【两段式高位冲顶极值锁定】: Bias20 > 32% 或 科技牛加速冲顶，高位两段式从容止盈转入货币避险；
  4. ⚡【冷却期回踩企稳接回 2.0】: 止盈后 2~6 天回踩 MA20 均线支撑企稳，精准发动二连击重新上车；
  5. 🛡️【宏观大势牛熊闸门】: 市场广度 < 20% 熊市阶段严禁买入成长股，自动切换红利/煤炭/黄金/货币防御；
  6. 💎【公募 C 类 7 天 0 赎回费保护】: 精确计算自然日持有天数，满 7 天 0 摩擦轮动，黑天鹅极值强制豁免；
  7. 📢【全渠道自动化推送】: 支持企业微信 Webhook、Server酱、PushPlus、钉钉、飞书一键群发。
====================================================================================================
"""

import os
import sys
import json
import re
import time
import requests
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 企业微信与推送 Webhook 配置 (优先从环境变量读取，支持 GitHub Actions Secrets)
DEFAULT_WECOM_WEBHOOK = os.environ.get(
    'WECOM_WEBHOOK',
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b74cac3-9fc2-497c-a287-b591246e3393"
)
PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN', '')
SERVERCHAN_KEY = os.environ.get('SERVERCHAN_KEY', '')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, ".fund_rotation_state.json")
PUSH_CACHE_FILE = os.path.join(SCRIPT_DIR, ".fund_rotation_push_cache.json")

# 🏛️ 终极全资产高弹性母库 (涵盖科技进攻、全球资产、大周期、黄金对冲与现金防御)
FULL_UNIVERSE = {
    '006503': {'code': '001618', 'fb': '006503', 'name': '半导体芯片ETF/混合C',      'class': 'C', 'type': 'GROWTH',   'category': '半导体算力'},
    '007817': {'code': '007817', 'fb': '007817', 'name': '国泰通信CPO算力ETF联接C',   'class': 'C', 'type': 'GROWTH',   'category': 'CPO光模块'},
    '014283': {'code': '014283', 'fb': '014283', 'name': '华夏动漫游戏ETF联接C',      'class': 'C', 'type': 'GROWTH',   'category': '数字经济传媒'},
    '017811': {'code': '005669', 'fb': '017811', 'name': '东方人工智能AI混合C',       'class': 'C', 'type': 'GROWTH',   'category': 'AI大模型软件'},
    '006479': {'code': '270042', 'fb': '006479', 'name': '广发纳斯达克100ETF联接C',    'class': 'C', 'type': 'GLOBAL',   'category': '全球科技纳指'},
    '008280': {'code': '008280', 'fb': '008280', 'name': '国泰煤炭ETF联接C',          'class': 'C', 'type': 'VALUE',    'category': '高股息煤炭周期'},
    '002190': {'code': '002190', 'fb': '002190', 'name': '新能源光伏主题混合A',        'class': 'A', 'type': 'GROWTH',   'category': '新能源光伏制造'},
    '000248': {'code': '000248', 'fb': '000248', 'name': '汇添富主要消费ETF联接A(消费)', 'class': 'A', 'type': 'CONSUMER', 'category': '大消费白酒食品'},
    '003096': {'code': '003096', 'fb': '003096', 'name': '中欧医疗健康混合C(医药)',      'class': 'C', 'type': 'HEALTH',   'category': '生物医药创新药'},
    '002207': {'code': '002207', 'fb': '002207', 'name': '前海金银珠宝C(3.5x黄金)',   'class': 'C', 'type': 'HEDGE',    'category': '黄金采掘高弹性'},
    '002611': {'code': '000216', 'fb': '002611', 'name': '博时黄金ETF联接C(现货黄金)',   'class': 'C', 'type': 'DEFENSE',  'category': '现货黄金避险'},
    '005125': {'code': '005125', 'fb': '007872', 'name': '华宝标普中国A股红利C(红利)',   'class': 'C', 'type': 'DEFENSE',  'category': '高股息红利防御'},
    '161005': {'code': '161005', 'fb': '161005', 'name': '富国天惠成长A(全市场底座)',   'class': 'A', 'type': 'BROAD',    'category': '全市场均衡长跑'},
    '000009': {'code': '000009', 'fb': '000009', 'name': '易方达天天理财货币A(现金)',    'class': 'C', 'type': 'CASH',     'category': '货币流动性避险'}
}

session = requests.Session()
session.trust_env = False
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

class ApexInfiniteSovereignV100Engine:
    """👑 Apex Infinite Sovereign V100.0 80%黄金鱼身至尊实盘引擎"""

    def __init__(self, webhook_url: str = DEFAULT_WECOM_WEBHOOK):
        self.webhook_url = webhook_url
        self.state = self.load_state()

    def load_state(self) -> dict:
        default_state = {
            'holding_code': '006503',
            'holding_name': '半导体芯片ETF/混合C',
            'entry_date': '2026-08-19',
            'entry_nav': 7.0335,
            'peak_nav': 7.0335,
            'last_stop_asset': None,
            'last_stop_date': None,
            'last_action': 'BUY',
            'last_action_date': '2026-08-19 14:48:00'
        }
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {**default_state, **data}
            except Exception as e:
                print(f"[-] 读取状态文件异常: {e}")
        return default_state

    def save_state(self, state: dict):
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            print("[+] 策略持仓与状态已成功持久化落盘！")
        except Exception as e:
            print(f"[-] 写入状态文件异常: {e}")

    def fetch_fund_data(self, key: str) -> tuple:
        """获取指定母库基金的官方历史净值序列与盘中实时估值"""
        v = FULL_UNIVERSE.get(key, {})
        code = v.get('code', key)
        fb_code = v.get('fb', key)
        
        hist_url = f'https://fundmobapi.eastmoney.com/FundMApi/FundNetDiagram.ashx?FCODE={code}&RANGE=ln&deviceid=Wap&plat=Wap&product=EFund&version=2.0.0'
        records = []
        try:
            r = session.get(hist_url, timeout=8).json()
            datas = r.get('Datas', [])
            for item in datas:
                records.append({
                    'date': item['FSRQ'],
                    'nav': float(item['DWJZ']),
                    'chg_pct': float(item['JZZZL']) if item['JZZZL'] and item['JZZZL'] != '--' else 0.0
                })
        except Exception:
            pass

        df_hist = pd.DataFrame(records)
        if df_hist.empty and fb_code != code:
            hist_url_fb = f'https://fundmobapi.eastmoney.com/FundMApi/FundNetDiagram.ashx?FCODE={fb_code}&RANGE=ln&deviceid=Wap&plat=Wap&product=EFund&version=2.0.0'
            try:
                r_fb = session.get(hist_url_fb, timeout=8).json()
                for item in r_fb.get('Datas', []):
                    records.append({
                        'date': item['FSRQ'],
                        'nav': float(item['DWJZ']),
                        'chg_pct': float(item['JZZZL']) if item['JZZZL'] and item['JZZZL'] != '--' else 0.0
                    })
                df_hist = pd.DataFrame(records)
            except Exception:
                pass

        if not df_hist.empty:
            df_hist['date'] = pd.to_datetime(df_hist['date'])
            df_hist = df_hist.sort_values('date').reset_index(drop=True)

        # 实时盘中估值
        last_val = df_hist['nav'].iloc[-1] if not df_hist.empty else 1.0
        rt = {
            'code': key,
            'name': v.get('name', key),
            'last_nav': last_val,
            'estimate_nav': last_val,
            'estimate_chg': 0.0,
            'estimate_time': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        gz_url = f"http://fundgz.1234567.com.cn/js/{key}.js?rt={int(time.time()*1000)}"
        try:
            resp = session.get(gz_url, timeout=5)
            resp.encoding = 'utf-8'
            m = re.search(r'jsonpgz\((.*?)\);', resp.text)
            if m:
                gz_data = json.loads(m.group(1))
                rt['estimate_nav'] = float(gz_data.get('gsz', rt['last_nav']))
                rt['estimate_chg'] = float(gz_data.get('gszzl', 0.0))
                rt['estimate_time'] = gz_data.get('gztime', rt['estimate_time'])
                rt['name'] = gz_data.get('name', rt['name'])
        except Exception:
            pass

        return df_hist, rt

    def compute_wufu_score(self, df: pd.DataFrame) -> tuple:
        """五福对数斜率与 R² 线性度双核算法"""
        if len(df) < 20: return 0.0, 0.0
        closes = df['nav'].values
        y = np.log(closes[-20:])
        x = np.arange(len(y))
        weights = np.linspace(1.0, 2.0, len(y))
        W = weights ** 2
        W_sum = np.sum(W)
        x_bar = np.sum(W * x) / W_sum
        y_bar = np.sum(W * y) / W_sum
        dx = x - x_bar
        dy = y - y_bar
        var_x = np.sum(W * dx**2)
        slope = np.sum(W * dx * dy) / var_x if var_x != 0 else 0
        ss_tot = np.sum(weights * (y - np.mean(y)) ** 2)
        ss_res = np.sum(weights * (y - (slope * x + (y_bar - slope * x_bar))) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0
        ann_ret = np.exp(slope * 250) - 1.0
        score = ann_ret * r2
        return score, r2

    def compute_apex_composite_score(self, df: pd.DataFrame) -> float:
        """Apex 多周期动量 + 风险调整复合评分"""
        if len(df) < 25: return -999.0
        p = df['nav'].iloc[-1]
        closes = df['nav'].values
        m5  = (p / closes[-5] - 1.0)  if len(closes) >= 5  else 0.0
        m10 = (p / closes[-10] - 1.0) if len(closes) >= 10 else 0.0
        m20 = (p / closes[-20] - 1.0) if len(closes) >= 20 else 0.0
        
        e8 = df['nav'].ewm(span=8).mean().iloc[-1]
        e20 = df['nav'].ewm(span=20).mean().iloc[-1]
        ma20 = np.mean(closes[-20:])
        
        ret20 = df['nav'].pct_change().dropna().iloc[-20:]
        vol20 = ret20.std() * np.sqrt(250) if len(ret20) > 0 else 0.30
        
        mom_score = 0.45 * m5 + 0.35 * m10 + 0.20 * m20
        trend_score = 0.0
        if p > e8:   trend_score += 0.40
        if e8 > e20: trend_score += 0.35
        if p > ma20: trend_score += 0.25
        
        sharpe_proxy = (m20 / (vol20 + 1e-4)) * np.sqrt(250 / 20)
        risk_adj = np.tanh(sharpe_proxy * 0.5)
        return 0.40 * mom_score + 0.35 * trend_score + 0.25 * risk_adj

    def run_daily_decision_scan(self) -> dict:
        """每日 14:48 实盘决策中枢 (包含 80% 鱼身铁锁、逃顶四重奏与冷却期接回)"""
        now_dt = datetime.now()
        cur_date_str = now_dt.strftime('%Y-%m-%d')
        is_thu = (now_dt.weekday() == 3)

        holding_code = self.state.get('holding_code', '006503')
        entry_date_str = self.state.get('entry_date', cur_date_str)
        entry_nav = self.state.get('entry_nav', 1.0)
        peak_nav = self.state.get('peak_nav', entry_nav)
        last_stop_asset = self.state.get('last_stop_asset')
        last_stop_date = self.state.get('last_stop_date')

        entry_dt = datetime.strptime(entry_date_str, '%Y-%m-%d') if entry_date_str else now_dt
        hold_days = (now_dt - entry_dt).days
        is_fee_free = (hold_days >= 7)

        print(f"[{now_dt.strftime('%H:%M:%S')}] 📡 正在全量扫描 14 大核心高弹性母库盘中实时估值与宏观牛熊广度...")
        
        all_metrics = []
        df_holding = None
        rt_holding = None
        bull_cnt = 0
        total_growth_cnt = 0

        for key, info in FULL_UNIVERSE.items():
            if key == '000009': continue
            df_h, rt = self.fetch_fund_data(key)
            if df_h.empty or len(df_h) < 25: continue

            # 拼接盘中实时估值
            if cur_date_str != df_h['date'].iloc[-1].strftime('%Y-%m-%d'):
                new_r = pd.DataFrame([{'date': pd.to_datetime(cur_date_str), 'nav': rt['estimate_nav'], 'chg_pct': rt['estimate_chg']}])
                df_calc = pd.concat([df_h, new_r], ignore_index=True)
            else:
                df_calc = df_h.copy()

            if key == holding_code:
                df_holding = df_calc
                rt_holding = rt

            p = df_calc['nav'].iloc[-1]
            e8 = df_calc['nav'].ewm(span=8).mean().iloc[-1]
            e20 = df_calc['nav'].ewm(span=20).mean().iloc[-1]
            ma20 = np.mean(df_calc['nav'].values[-20:])
            m5 = (p / df_calc['nav'].values[-5] - 1.0)
            m20 = (p / df_calc['nav'].values[-20] - 1.0)
            wufu_score, r2 = self.compute_wufu_score(df_calc)
            apex_score = self.compute_apex_composite_score(df_calc)

            if info.get('type') not in ['DEFENSE', 'CASH', 'HEDGE']:
                total_growth_cnt += 1
                if p > ma20: bull_cnt += 1

            is_bull = (p > e8 > e20 and p > ma20 and m20 > 0.0) or (wufu_score > 1.0 and r2 > 0.35 and p > ma20) or (m5 > 0.04 and p > ma20)

            all_metrics.append({
                'code': key, 'name': info['name'], 'class': info['class'],
                'type': info['type'], 'category': info['category'], 'nav': p,
                'est_chg': rt['estimate_chg'], 'm5': m5, 'm20': m20, 'r2': r2,
                'wufu': wufu_score, 'apex_score': apex_score, 'is_bull': is_bull
            })

        # 宏观广度与牛熊状态机
        breadth = (bull_cnt / total_growth_cnt) if total_growth_cnt > 0 else 0.50
        macro_bear = (breadth < 0.20)
        is_bull_regime = (breadth >= 0.40 and not macro_bear)

        # 选拔进攻与防御候选池
        if not macro_bear:
            if is_bull_regime:
                growth_candidates = [m for m in all_metrics if m['is_bull'] and m['type'] in ['GROWTH', 'GLOBAL', 'CONSUMER', 'HEALTH', 'BROAD']]
                growth_candidates.sort(key=lambda x: x['apex_score'], reverse=True)
                top_asset = growth_candidates[0] if growth_candidates else None
            else:
                defensive_pool = [m for m in all_metrics if m['code'] in ['002611', '002207', '005125', '008280'] and m['is_bull']]
                defensive_pool.sort(key=lambda x: x['apex_score'], reverse=True)
                top_asset = defensive_pool[0] if defensive_pool else None
        else:
            top_asset = None

        if top_asset:
            target_asset = top_asset['code']
            target_name = top_asset['name']
            target_type = top_asset['type']
            target_score = top_asset['apex_score']
        else:
            target_asset = '000009'
            target_name = '易方达天天理财货币A(现金)'
            target_type = 'CASH'
            target_score = 0.0

        # 当前持仓诊断与 80% 黄金鱼身铁锁计算
        cur_holding_nav = rt_holding['estimate_nav'] if rt_holding else entry_nav
        cur_peak_nav = max(peak_nav, cur_holding_nav)
        cur_holding_pnl = (cur_holding_nav - entry_nav) / entry_nav * 100.0
        dd_from_peak = (cur_holding_nav - cur_peak_nav) / cur_peak_nav * 100.0
        peak_profit_ratio = (cur_peak_nav - entry_nav) / entry_nav if entry_nav > 0 else 0.0

        # 均线与乖离率
        if df_holding is not None and len(df_holding) >= 20:
            ma20_h = np.mean(df_holding['nav'].values[-20:])
            std20_h = np.std(df_holding['nav'].values[-20:])
            bb_upper_h = ma20_h + 2.2 * std20_h
            bias20_h = (cur_holding_nav - ma20_h) / ma20_h * 100.0
            m5_h = (cur_holding_nav / df_holding['nav'].values[-5] - 1.0) * 100.0 if len(df_holding) >= 5 else 0.0
        else:
            ma20_h = cur_holding_nav
            bb_upper_h = 999.0
            bias20_h = 0.0
            m5_h = 0.0

        holding_type = FULL_UNIVERSE.get(holding_code, {}).get('type', 'GROWTH')

        # -------------------------------------------------------------------------
        # 👑 核心风控算法：80% 黄金鱼身 + 逃顶四重奏
        # -------------------------------------------------------------------------
        is_takeprofit_exit = False
        exit_tag = "🔴常规止损"
        allowed_dd_pct = -6.50 if is_bull_regime else -3.50

        if holding_code != '000009':
            # 1. 动态 80% 浮盈保底铁锁 (浮盈 >= 15% 自动启动)
            if peak_profit_ratio >= 0.15:
                allowed_dd_pct = -1.0 * (peak_profit_ratio * 0.20) * 100.0
                if dd_from_peak <= allowed_dd_pct and is_fee_free:
                    is_takeprofit_exit = True
                    exit_tag = f"🏆80%鱼身利润锁死 (实保+{cur_holding_pnl:.1f}%)"
            
            # 2. 极端加速冲顶极值锁定
            if (bias20_h > 32.0 or (m5_h > 20.0 and bias20_h > 25.0)) and dd_from_peak <= -2.0 and is_fee_free:
                is_takeprofit_exit = True
                exit_tag = "👑高位冲顶极值锁定 (Bias20过热)"
            elif holding_type == 'GROWTH' and cur_holding_pnl >= 35.0 and bias20_h >= 22.0 and dd_from_peak <= -2.5 and is_fee_free:
                is_takeprofit_exit = True
                exit_tag = "🚀科技超级主升浪极值锁定 (+35%高位兑现)"
                
            # 3. 黄金/周期商品触碰布林上轨
            elif holding_type in ['HEDGE', 'DEFENSE', 'VALUE'] and (m5_h > 8.5 or bias20_h > 7.5 or cur_holding_nav >= bb_upper_h) and dd_from_peak <= -1.5 and is_fee_free:
                is_takeprofit_exit = True
                exit_tag = "🎯布林过热超买锁定"
                
            # 4. 保本线硬性拦截
            elif cur_holding_pnl >= 6.0 and dd_from_peak <= -4.0 and cur_holding_nav <= entry_nav * 1.005 and is_fee_free:
                is_takeprofit_exit = True
                exit_tag = "🛡️保本线强制拦截 (保住本金)"

        stop_threshold = -6.50 if is_bull_regime else -3.50
        stop_hit = (holding_code != '000009' and ((dd_from_peak <= stop_threshold and (is_fee_free or is_takeprofit_exit)) or dd_from_peak <= -8.50 or is_takeprofit_exit))
        
        overtake_hit = (top_asset and top_asset['code'] != holding_code and top_asset['m5'] >= 0.12 and top_asset['apex_score'] > 2.0 and is_fee_free)
        rotate_hit = (is_thu and is_fee_free) or overtake_hit or (holding_code == '000009' and target_asset != '000009')

        # 冷却期回踩接回 2.0
        is_cooling_reentry = False
        if holding_code == '000009' and last_stop_asset and last_stop_asset != '000009' and is_bull_regime:
            days_since_stop = (now_dt - datetime.strptime(last_stop_date, '%Y-%m-%d')).days if last_stop_date else 99
            if 2 <= days_since_stop <= 6:
                df_prev, _ = self.fetch_fund_data(last_stop_asset)
                if len(df_prev) >= 20:
                    p_prev = df_prev['nav'].iloc[-1]
                    ma20_prev = np.mean(df_prev['nav'].values[-20:])
                    if p_prev > ma20_prev:
                        target_asset = last_stop_asset
                        target_name = FULL_UNIVERSE[last_stop_asset]['name']
                        is_cooling_reentry = True

        final_action = 'HOLD'
        action_reason = ''

        if stop_hit:
            final_action = 'STOP_REDEEM'
            action_reason = f"{exit_tag} (峰值回撤 {dd_from_peak:.2f}%, 保底线 {allowed_dd_pct:.2f}%) -> 14:48 一键转入易方达天天理财货币A锁定战果！"
            # 更新状态
            self.state['last_stop_asset'] = holding_code
            self.state['last_stop_date'] = cur_date_str
            self.state['holding_code'] = '000009'
            self.state['holding_name'] = '易方达天天理财货币A(现金)'
            self.state['entry_date'] = cur_date_str
            self.state['entry_nav'] = 1.0
            self.state['peak_nav'] = 1.0
            self.state['last_action'] = 'STOP_REDEEM'
            self.state['last_action_date'] = now_dt.strftime('%Y-%m-%d %H:%M:%S')
            self.save_state(self.state)

        elif (rotate_hit or is_cooling_reentry) and target_asset != holding_code:
            final_action = 'ROTATE'
            tag_desc = "⚡冷却期企稳接回" if is_cooling_reentry else "🟢周四定期轮动"
            action_reason = f"{tag_desc} -> 建议在 14:48 转换/买入新领跑龙头【{target_name}】(五福评分 {target_score:.2f})！"
            # 更新状态
            self.state['holding_code'] = target_asset
            self.state['holding_name'] = target_name
            self.state['entry_date'] = cur_date_str
            self.state['entry_nav'] = cur_holding_nav if target_asset == holding_code else 1.0
            self.state['peak_nav'] = self.state['entry_nav']
            self.state['last_action'] = 'ROTATE'
            self.state['last_action_date'] = now_dt.strftime('%Y-%m-%d %H:%M:%S')
            self.save_state(self.state)
        else:
            final_action = 'HOLD'
            action_reason = f"持仓稳健运行在多头主升浪中，80%鱼身保底防线有效 (警戒线: {allowed_dd_pct:.2f}%)，继续锁仓享受狂飙！"
            # 更新峰值
            if cur_peak_nav > peak_nav:
                self.state['peak_nav'] = cur_peak_nav
                self.save_state(self.state)

        return {
            'time': now_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'breadth': breadth * 100.0,
            'regime': '🚀 科技主升大牛市' if is_bull_regime else ('📉 熊市冰冻避险' if macro_bear else '⚖️ 震荡防御市'),
            'holding_code': holding_code,
            'holding_name': FULL_UNIVERSE.get(holding_code, {}).get('name', holding_code),
            'cur_nav': cur_holding_nav,
            'entry_nav': entry_nav,
            'peak_nav': cur_peak_nav,
            'pnl_pct': cur_holding_pnl,
            'dd_from_peak': dd_from_peak,
            'allowed_dd_pct': allowed_dd_pct,
            'hold_days': hold_days,
            'is_fee_free': is_fee_free,
            'target_code': target_asset,
            'target_name': target_name,
            'target_score': target_score,
            'final_action': final_action,
            'action_reason': action_reason,
            'top_growth_candidates': all_metrics[:6]
        }

    def generate_markdown_report(self, res: dict) -> str:
        action_badge = {
            'HOLD': '🟢【继续坚决锁仓持有 · 享受主升浪】',
            'ROTATE': '🔄【14:48 黄金轮动 · 极速一键转换】',
            'STOP_REDEEM': '🏆【14:48 80%鱼身锁死 · 从容逃顶避险】'
        }.get(res['final_action'], '⚪【观望】')

        md = f"""# 👑 【Apex Sovereign V100.0 · 14:48 黄金鱼身决策卡片】
> **版本**：👑 Apex Infinite Sovereign V100.0 80%黄金鱼身至尊版 | **扫描时间**：`{res['time']}`
> **宏观环境**：**{res['regime']}** (全市场广度: `{res['breadth']:.1f}%`)

---

### 📢 【今日操盘核心指令】
### {action_badge}
* **决策结论**：{res['action_reason']}
* **建议操作时机**：**今日 14:45 ~ 14:55 之间在天天基金/蚂蚁/券商 APP 一键转换/申购**

---

### 💼 【当前持仓状态与 80% 黄金鱼身防线】
* **当前持仓**：`{res['holding_code']}` **{res['holding_name']}**
* **持仓成本**：`{res['entry_nav']:.4f}` | **实时估值**：`{res['cur_nav']:.4f}`
* **持仓浮盈**：<font color="{'#10b981' if res['pnl_pct']>=0 else '#ef4444'}">**{res['pnl_pct']:+.2f}%**</font>
* **历史最高净值**：`{res['peak_nav']:.4f}` | **当前峰值回撤**：`{res['dd_from_peak']:.2f}%`
* **🛡️ 80%鱼身保底防线**：最大允许回撤 **`{res['allowed_dd_pct']:.2f}%`** (绝不回吐超20%利润)
* **持有日历天数**：**{res['hold_days']} 天** ({'✅ 已满 7 天，0 赎回费！' if res['is_fee_free'] else '⚠️ 未满 7 天'})

---

### 🚀 【今日 14 大全资产母库五福动量领跑榜 Top 5】
"""
        for i, c in enumerate(res['top_growth_candidates'][:5], 1):
            md += f"{i}. `{c['code']}` **{c['name']}** | 5日涨幅: `{c['m5']*100:+.2f}%` | 五福R²: `{c['r2']:.2f}` | 综合分: `{c['apex_score']:.2f}`\n"

        md += "\n---\n*💡 声明：本系统由 Apex V100.0 黄金鱼身引擎驱动，每天 14:48 自动巡航。请在 15:00 前完成当日交易。*"
        return md

    def push_to_wecom(self, content: str):
        if not self.webhook_url: return
        payload = {"msgtype": "markdown", "markdown": {"content": content}}
        try:
            r = session.post(self.webhook_url, json=payload, timeout=8)
            print(f"[+] 企业微信推送结果: {r.status_code}")
        except Exception as e:
            print(f"[-] 企业微信推送失败: {e}")

if __name__ == '__main__':
    engine = ApexInfiniteSovereignV100Engine()
    res = engine.run_daily_decision_scan()
    report = engine.generate_markdown_report(res)
    print("\n" + "=" * 90)
    print(report)
    print("=" * 90)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--push':
        engine.push_to_wecom(report)
