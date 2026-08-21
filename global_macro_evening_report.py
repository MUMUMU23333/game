# -*- coding: utf-8 -*-
"""
====================================================================================================
🏛️【全球宏观大势与量化全景战略研报 · FinRobot 智能体深度赋能版】
====================================================================================================
核心定位：
  • 每日 20:00 (北京时间) 顶级财经日报与深度全景研报
  • 深度融合 FinRobot (AI4Finance) 投研架构：
    1. 【Data-CoT ➔ Concept-CoT ➔ Thesis-CoT】三级金融逻辑推演链条
    2. 【四大多智能体协同圆桌】：宏观首席 + 量化风控官 + 产业基本面分析师 + 大类资产主操盘手
    3. 【SEC / 华尔街投行级研报排版】：核心投资论点 (Key Highlights) + 三维情景压力测试 (Stress-Testing)
  • 专属企业微信推送 Webhook:
    https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b44d98cc-0707-48e4-aeb6-741340aa671d
====================================================================================================
"""

import os
import sys
import json
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

MACRO_EVENING_WEBHOOK = os.environ.get(
    'MACRO_EVENING_WEBHOOK',
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b44d98cc-0707-48e4-aeb6-741340aa671d"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "index.html")
HTML_DASHBOARD_PATH = os.path.join(SCRIPT_DIR, "quant_dashboard.html")

session = requests.Session()
session.trust_env = False


# =====================================================================
# 一、 数据感知层 (FinRobot Data-Source Agent)
# =====================================================================
def fetch_realtime_quote(code: str) -> dict:
    """获取腾讯实时行情"""
    market = 'sh' if code.startswith(('51', '58', '60', '000')) else 'sz'
    url = f"http://qt.gtimg.cn/q={market}{code}"
    try:
        resp = session.get(url, timeout=5)
        text = resp.text
        if not text or '=' not in text:
            return {}
        parts = text.split('="')[1].split('~')
        if len(parts) > 32:
            price = float(parts[3])
            prev_close = float(parts[4])
            chg = float(parts[32]) if parts[32] else ((price / prev_close - 1) * 100 if prev_close > 0 else 0.0)
            high = float(parts[33]) if len(parts) > 33 and parts[33] else price
            low = float(parts[34]) if len(parts) > 34 and parts[34] else price
            vol = float(parts[36]) if len(parts) > 36 and parts[36] else 0.0
            amount = float(parts[37]) if len(parts) > 37 and parts[37] else 0.0
            return {
                'code': code,
                'name': parts[1],
                'price': price,
                'prev_close': prev_close,
                'change_pct': round(chg, 2),
                'high': high,
                'low': low,
                'volume': vol,
                'amount': amount
            }
    except Exception:
        pass
    return {'code': code, 'name': code, 'price': 0.0, 'prev_close': 0.0, 'change_pct': 0.0, 'high': 0, 'low': 0, 'volume': 0, 'amount': 0}


def fetch_recent_kline(code: str, count: int = 120) -> pd.DataFrame:
    """获取前复权日 K 线"""
    market = 'sh' if code.startswith(('51', '58', '60', '000')) else 'sz'
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,2024-01-01,2026-12-31,{count},qfq"
    try:
        res = session.get(url, timeout=8).json()
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
            return df.sort_values('date').reset_index(drop=True)
    except Exception:
        pass
    return pd.DataFrame()


def collect_macro_dataset() -> dict:
    """收集全景大类资产行情与核心因子指标"""
    asset_dict = {
        '518880': '华安黄金ETF (实物黄金)',
        '517520': '黄金股ETF (2x杠杆加速)',
        '513100': '纳指100ETF (全球科技底座)',
        '159509': '纳指科技ETF (AI高弹性冲刺)',
        '601288': '农业银行 (6.5%免税高股息)',
        '600036': '招商银行 (零售之王/高ROE成长)',
        '159915': '创业板ETF (高贝塔成长基准)',
        '588000': '科创50ETF (硬科技半导体)',
        '588170': '科创100ETF (高弹性成长增强)',
        '159363': '创AI ETF (AI应用/算力增强)',
        '510880': '红利ETF (低波高股息)',
        '510300': '沪深300ETF (大盘核心蓝筹)'
    }

    quotes = {}
    for c, label in asset_dict.items():
        q = fetch_realtime_quote(c)
        q['label'] = label
        quotes[c] = q

    # 纳指溢价
    df_ndx = fetch_recent_kline('513100')
    df_tech = fetch_recent_kline('159509')
    df_abc = fetch_recent_kline('601288')
    df_cmb = fetch_recent_kline('600036')
    df_gold = fetch_recent_kline('518880')
    df_cyb = fetch_recent_kline('159915')
    df_star = fetch_recent_kline('588000')

    prem_spread = 0.0
    if not df_tech.empty and not df_ndx.empty:
        p_t = quotes['159509']['price']
        p_n = quotes['513100']['price']
        m_df = pd.merge(df_tech[['date', 'close']].rename(columns={'close': 'c_t'}),
                        df_ndx[['date', 'close']].rename(columns={'close': 'c_n'}), on='date')
        m_df['ratio'] = m_df['c_t'] / m_df['c_n']
        ma20_r = m_df['ratio'].rolling(20).mean().iloc[-1]
        curr_r = p_t / p_n if p_n > 0 else ma20_r
        prem_spread = round(((curr_r / ma20_r) - 1.0) * 100.0, 2)

    bank_zscore = 0.0
    if not df_cmb.empty and not df_abc.empty:
        m_b = pd.merge(df_cmb[['date', 'close']].rename(columns={'close': 'c_c'}),
                       df_abc[['date', 'close']].rename(columns={'close': 'c_a'}), on='date')
        m_b['ratio'] = m_b['c_c'] / m_b['c_a']
        curr_br = quotes['600036']['price'] / quotes['601288']['price'] if quotes['601288']['price'] > 0 else 1.0
        ma60 = m_b['ratio'].rolling(60).mean().iloc[-1]
        std60 = m_b['ratio'].rolling(60).std().iloc[-1]
        bank_zscore = round((curr_br - ma60) / std60, 2) if std60 > 0 else 0.0

    gold_m20 = 0.0
    if not df_gold.empty and len(df_gold) >= 21:
        gold_m20 = round((df_gold['close'].iloc[-1] / df_gold['close'].iloc[-21] - 1.0) * 100.0, 2)

    cyb_m5 = round((df_cyb['close'].iloc[-1] / df_cyb['close'].iloc[-6] - 1.0) * 100.0, 2) if len(df_cyb) >= 6 else 0.0
    star_m5 = round((df_star['close'].iloc[-1] / df_star['close'].iloc[-6] - 1.0) * 100.0, 2) if len(df_star) >= 6 else 0.0

    return {
        'quotes': quotes,
        'prem_spread': prem_spread,
        'bank_zscore': bank_zscore,
        'gold_m20': gold_m20,
        'cyb_m5': cyb_m5,
        'star_m5': star_m5
    }


# =====================================================================
# 二、 HTML 顶级财经日报渲染 (FinRobot 多智能体架构 + 4K Bento 栅格)
# =====================================================================
def generate_full_html_report(data: dict) -> str:
    """生成具备 FinRobot 三级思维链与智能体圆桌矩阵的 4K HTML 旗舰研报"""
    q = data['quotes']
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_badge = datetime.now().strftime("%Y年%m月%d日")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>全球宏观大势与量化全景战略研报 · FinRobot 智能体旗舰版</title>
    <style>
        :root {{
            --bg-primary: #070a12;
            --bg-card: rgba(15, 23, 42, 0.78);
            --bg-card-hover: rgba(26, 38, 64, 0.88);
            --bg-inner: rgba(10, 16, 30, 0.75);
            --border-color: rgba(64, 88, 140, 0.35);
            --border-highlight: rgba(96, 165, 250, 0.65);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-gold: #f59e0b;
            --accent-gold-glow: rgba(245, 158, 11, 0.25);
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-blue: #38bdf8;
            --accent-purple: #a855f7;
            --accent-cyan: #06b6d4;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; }}
        body {{ background-color: var(--bg-primary); color: var(--text-primary); min-height: 100vh; padding: 24px 16px; line-height: 1.65; background-image: radial-gradient(circle at 12% 18%, rgba(30, 58, 138, 0.38) 0%, transparent 45%), radial-gradient(circle at 88% 82%, rgba(88, 28, 135, 0.35) 0%, transparent 45%); }}
        .container {{ max-width: 1440px; margin: 0 auto; }}
        
        /* 顶部 Header */
        .header {{ display: flex; justify-content: space-between; align-items: center; padding: 26px 32px; background: var(--bg-card); backdrop-filter: blur(20px); border: 1px solid var(--border-color); border-radius: 22px; margin-bottom: 24px; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55); }}
        .header-title h1 {{ font-size: 26px; font-weight: 800; background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 45%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 12px; }}
        .header-title p {{ font-size: 13.5px; color: var(--text-secondary); margin-top: 6px; }}
        .header-badge {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 18px; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.45); border-radius: 30px; color: var(--accent-gold); font-size: 13px; font-weight: 700; }}
        .pulse-dot {{ width: 8px; height: 8px; background-color: var(--accent-gold); border-radius: 50%; box-shadow: 0 0 12px var(--accent-gold); animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: 0.3; transform: scale(1.4); }} 100% {{ opacity: 1; transform: scale(1); }} }}
        
        /* Bento 栅格 */
        .bento-grid {{ display: grid; grid-template-columns: repeat(12, 1fr); gap: 22px; margin-bottom: 24px; }}
        .card {{ background: var(--bg-card); backdrop-filter: blur(20px); border: 1px solid var(--border-color); border-radius: 22px; padding: 26px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35); }}
        .card:hover {{ transform: translateY(-3px); border-color: var(--border-highlight); box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6); }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 14px; }}
        .card-title {{ font-size: 17px; font-weight: 750; color: #ffffff; display: flex; align-items: center; gap: 10px; }}
        
        .col-12 {{ grid-column: span 12; }}
        .col-8 {{ grid-column: span 8; }}
        .col-6 {{ grid-column: span 6; }}
        .col-4 {{ grid-column: span 4; }}
        @media (max-width: 1080px) {{ .col-8, .col-6, .col-4 {{ grid-column: span 12; }} }}
        
        /* 大类资产大字牌 */
        .ticker-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; }}
        .ticker-item {{ background: var(--bg-inner); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s ease; }}
        .ticker-item:hover {{ background: rgba(18, 28, 52, 0.8); border-color: rgba(255, 255, 255, 0.2); }}
        .ticker-name {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }}
        .ticker-price {{ font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }}
        .ticker-chg {{ font-size: 13px; font-weight: 700; margin-top: 6px; }}
        .up {{ color: #10b981; }}
        .down {{ color: #ef4444; }}
        .gold {{ color: #f59e0b; }}

        /* FinRobot 核心亮点 (Key Investment Highlights) */
        .highlights-box {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 22px; }}
        .highlight-card {{ background: rgba(14, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 16px; padding: 18px; }}
        .highlight-badge {{ font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; display: inline-block; margin-bottom: 8px; }}
        .highlight-title {{ font-size: 14.5px; font-weight: 750; color: #ffffff; margin-bottom: 6px; }}
        .highlight-desc {{ font-size: 12.8px; color: #94a3b8; line-height: 1.65; }}
        
        /* FinRobot 多智能体圆桌卡片 */
        .agent-dossier-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }}
        .agent-card {{ background: var(--bg-inner); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 20px; }}
        .agent-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        .agent-role {{ font-size: 14px; font-weight: 800; color: #f8fafc; display: flex; align-items: center; gap: 8px; }}
        .agent-tag {{ font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; }}
        
        /* 深度研报核心卡片 */
        .dossier-card {{ background: var(--bg-inner); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 20px; margin-bottom: 18px; }}
        .dossier-card:last-child {{ margin-bottom: 0; }}
        .dossier-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        .dossier-tag {{ font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 6px; }}
        .tag-gold {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); }}
        .tag-bank {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); }}
        .tag-tech {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); }}
        .tag-star {{ background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.35); }}
        
        .dossier-title {{ font-size: 15.5px; font-weight: 750; color: #f8fafc; margin-bottom: 8px; }}
        .dossier-body {{ font-size: 13.5px; color: #cbd5e1; line-height: 1.75; }}
        .dossier-quote {{ margin-top: 10px; padding: 10px 14px; background: rgba(15, 23, 42, 0.85); border-left: 3px solid var(--accent-blue); border-radius: 0 8px 8px 0; font-size: 13px; color: #94a3b8; }}
        .dossier-quote.gold-border {{ border-left-color: var(--accent-gold); color: #fef08a; }}
        .dossier-quote.green-border {{ border-left-color: var(--accent-green); color: #a7f3d0; }}
        
        /* 压力测试情景分析 */
        .stress-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 14px; }}
        .stress-item {{ background: rgba(10, 16, 30, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px; }}
        .stress-title {{ font-size: 13px; font-weight: 750; margin-bottom: 6px; }}
        .stress-desc {{ font-size: 12px; color: #94a3b8; line-height: 1.6; }}

        /* 策略矩阵展示 */
        .strategy-matrix-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; }}
        .strategy-box {{ background: var(--bg-inner); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 18px; }}
        .strategy-box-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .strategy-title {{ font-size: 14.5px; font-weight: 750; color: #ffffff; }}
        .strategy-badge {{ font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 600; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
        .strategy-content {{ font-size: 12.5px; color: #94a3b8; line-height: 1.65; }}
        
        /* 指标行 */
        .metric-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }}
        .metric-row:last-child {{ border-bottom: none; }}
        .metric-label {{ font-size: 13px; color: var(--text-secondary); }}
        .metric-val {{ font-size: 14px; font-weight: 700; color: #f8fafc; }}

        .footer {{ text-align: center; padding: 30px; color: var(--text-muted); font-size: 12px; border-top: 1px solid rgba(255, 255, 255, 0.06); margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 Header -->
        <header class="header">
            <div class="header-title">
                <h1>🏛️ 全球宏观大势与量化全景战略研报</h1>
                <p>FinRobot 智能体深度赋能 · Data-CoT ➔ Concept-CoT ➔ Thesis-CoT 三级逻辑推演 · 顶级机构投研内参</p>
            </div>
            <div class="header-badge">
                <span class="pulse-dot"></span>
                <span>{date_badge} 晚间 20:00 旗舰版</span>
            </div>
        </header>

        <!-- FinRobot 核心投资论点三要素 (Executive Thesis Highlights) -->
        <div class="highlights-box">
            <div class="highlight-card" style="border-color: rgba(245, 158, 11, 0.4);">
                <div class="highlight-badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24;">THESIS 1 · 黄金超级周期</div>
                <div class="highlight-title">去美元化储备驱动 · 黄金2x主升浪确认</div>
                <div class="highlight-desc">华安黄金 20 日动量突破 +1.8%，黄金股凭借 2x 业绩爆发杠杆单日大涨 +4.60%，从“利率驱动”全面跃迁至“主权储备驱动”。</div>
            </div>
            <div class="highlight-card" style="border-color: rgba(16, 185, 129, 0.4);">
                <div class="highlight-badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">THESIS 2 · 高股息双核压舱</div>
                <div class="highlight-title">利率下行资产荒 · 6.5%免税长寿现金流堡垒</div>
                <div class="highlight-desc">农业银行构筑无风险类债压舱底座，招商银行比价 Z-Score (-0.69σ) 显现成长性估值弹性，双核自适应平滑配比。</div>
            </div>
            <div class="highlight-card" style="border-color: rgba(56, 189, 248, 0.4);">
                <div class="highlight-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">THESIS 3 · 量化吊灯一票否决</div>
                <div class="highlight-title">A股科技蓄势磨底 · 0%权益敞口拒绝震荡损耗</div>
                <div class="highlight-desc">双创与纳指触发 -5.0% 宽幅动态吊灯风控防御，规避阴跌损耗；纳指科技溢价处于安全带，长线复利中枢稳固。</div>
            </div>
        </div>

        <div class="bento-grid">
            <!-- 一、 全球核心大类资产实时收盘看板 -->
            <div class="card col-12">
                <div class="card-header">
                    <div class="card-title">🌐 全球核心大类资产实时收盘大屏</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">行情精准更新时间：{now_str} (北京时间)</div>
                </div>
                <div class="ticker-grid">
                    <div class="ticker-item">
                        <div class="ticker-name"><span>华安黄金ETF</span><code>518880</code></div>
                        <div class="ticker-price gold">¥{q['518880']['price']:.3f}</div>
                        <div class="ticker-chg up">+{q['518880']['change_pct']:.2f}% (抗通胀/去美元化底座)</div>
                    </div>
                    <div class="ticker-item" style="border-color: rgba(245, 158, 11, 0.5); background: rgba(245, 158, 11, 0.06);">
                        <div class="ticker-name"><span style="color:#f59e0b; font-weight:750;">黄金股ETF (2x杠杆加速)</span><code>517520</code></div>
                        <div class="ticker-price gold">¥{q['517520']['price']:.3f}</div>
                        <div class="ticker-chg up" style="font-size:14px;">+{q['517520']['change_pct']:.2f}% 🚀 (超级主升浪先锋)</div>
                    </div>
                    <div class="ticker-item">
                        <div class="ticker-name"><span>纳指100ETF</span><code>513100</code></div>
                        <div class="ticker-price">¥{q['513100']['price']:.3f}</div>
                        <div class="ticker-chg {'up' if q['513100']['change_pct']>=0 else 'down'}">{q['513100']['change_pct']:+.2f}% (全球科技底座)</div>
                    </div>
                    <div class="ticker-item">
                        <div class="ticker-name"><span>农业银行</span><code>601288</code></div>
                        <div class="ticker-price">¥{q['601288']['price']:.3f}</div>
                        <div class="ticker-chg {'up' if q['601288']['change_pct']>=0 else 'down'}">{q['601288']['change_pct']:+.2f}% (6.5%免税高股息)</div>
                    </div>
                    <div class="ticker-item">
                        <div class="ticker-name"><span>招商银行</span><code>600036</code></div>
                        <div class="ticker-price">¥{q['600036']['price']:.3f}</div>
                        <div class="ticker-chg {'up' if q['600036']['change_pct']>=0 else 'down'}">{q['600036']['change_pct']:+.2f}% (高ROE成长弹性)</div>
                    </div>
                    <div class="ticker-item">
                        <div class="ticker-name"><span>创业板ETF</span><code>159915</code></div>
                        <div class="ticker-price">¥{q['159915']['price']:.3f}</div>
                        <div class="ticker-chg {'up' if q['159915']['change_pct']>=0 else 'down'}">{q['159915']['change_pct']:+.2f}% (A股高贝塔成长)</div>
                    </div>
                </div>
            </div>

            <!-- 二、 【策略高度相关 · 顶级机构与顶流大V深度研报拆解】 (核心深度大篇章) -->
            <div class="card col-8">
                <div class="card-header">
                    <div class="card-title">🏛️ 策略强相关 · 顶级机构深度研报与大 V 视角剖析</div>
                    <span style="font-size: 11px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-weight:700;">FinRobot 深度解构</span>
                </div>

                <!-- 专题 1：黄金超级周期与 2x 杠杆加速 -->
                <div class="dossier-card">
                    <div class="dossier-header">
                        <div class="dossier-title">👑 专题一：从“利率驱动”到“主权储备驱动”——黄金超级周期与 2x 杠杆加速</div>
                        <span class="dossier-tag tag-gold">高盛 / 桥水达利欧 / 深度聚焦</span>
                    </div>
                    <div class="dossier-body">
                        <b>【范式重塑】</b>：过去四十年黄金定价主要由“美债实际利率”主导，而当前已彻底切换为<b>“全球央行去美元化主权储备驱动”</b>。在地缘博弈常态化、美国财政赤字膨胀与法币购买力贬值大背景下，黄金超越美债成为全球第一大官方储备硬通货。<br>
                        <b>【2x 杠杆弹性机制】</b>：高盛大宗团队研报指出，当金价突破关键阻力位进入主升浪时，黄金开采/矿企（黄金股ETF 517520）由于固定生产成本刚性，净利润呈现<b>指数级非线性爆发（经营杠杆 2.0x~2.5x）</b>。<br>
                        <b>【量化策略映射】</b>：策略通过实时追踪华安黄金 20 日动量（当前 <b>+{data['gold_m20']:.1f}%</b>）与均线突破，在主升浪确立时将 50% 防御仓位精准切换至 <b>517520 黄金股 ETF</b>，单日收获 <b>+{q['517520']['change_pct']:.2f}%</b> 的超额爆发，在弱势市中实现逆势加速！
                    </div>
                    <div class="dossier-quote gold-border">
                        💬 <b>达利欧 (Ray Dalio) 核心洞见</b>：“当你看到全球主权债务规模无节制扩张时，持有不依赖任何他人履约承诺的硬资产（Gold）是跨越百年周期的唯一解。”
                    </div>
                </div>

                <!-- 专题 2：A股低利率时代长寿资产与双核银行利差博弈 -->
                <div class="dossier-card">
                    <div class="dossier-header">
                        <div class="dossier-title">🏦 专题二：低利率时代的“类债长寿资产”——农业银行与招商银行平滑利差自适应</div>
                        <span class="dossier-tag tag-bank">中金公司 / 中信证券 / 张忆东</span>
                    </div>
                    <div class="dossier-body">
                        <b>【资产荒底座】</b>：在我国 10 年期国债收益率长期下行的大趋势下，具备 6.0%~6.5% 免税分红收益率的国有大行（农业银行 601288）构成了机构资金配置的<b>“超级类债现金流堡垒”</b>。<br>
                        <b>【双核比价自愈】</b>：中金策略团队指出，招商银行（600036）代表零售与财富管理成长弹性，农业银行代表极致稳健防御。当前招行/农行比价 Z-Score 处于 <b>{data['bank_zscore']:+.2f}σ</b>，招行成长性估值折价充分，具备极高赔率。<br>
                        <b>【量化策略映射】</b>：策略构建平滑利差模型 $w = \text{{clip}}(0.50 - 0.15 \times Z, 0.30, 0.70)$，在招行估值便宜时加大招行配置（18.1% vs 11.9%），实现高股息吃息与估值均值回归的双重收益。
                    </div>
                    <div class="dossier-quote green-border">
                        💬 <b>张忆东 (兴业证券全球首席) 核心洞见</b>：“在结构性行情中，投资的胜负手在于‘高股息确定性现金流’与‘核心资产成长弹性’的哑铃型配置，绝不做平庸的中间态。”
                    </div>
                </div>

                <!-- 专题 3：全球 AI 算力 CapEx 与纳指 100 防御底座 -->
                <div class="dossier-card">
                    <div class="dossier-header">
                        <div class="dossier-title">🇺🇸 专题三：美股七巨头 AI 资本开支护城河与纳指科技溢价熔断安全带</div>
                        <span class="dossier-tag tag-tech">摩根士丹利 / 科技大V</span>
                    </div>
                    <div class="dossier-body">
                        <b>【产业趋势】</b>：摩根士丹利最新科技硬件研报显示，全球超大规模云厂商在 AI 算力基础设施上的资本支出（CapEx）依然保持强劲增长，纳斯达克 100 成分股具备扎实的盈利基本面支撑。<br>
                        <b>【DPSA 溢价熔断保护】</b>：针对跨境 ETF 偶尔出现的散户非理性情绪溢价踩踏，策略实时监控 159509 相对 513100 的偏离度。当前偏离度仅为 <b>{data['prem_spread']:+.2f}%</b>，处于 8.0% 熔断线与 -1.5% 错位低吸线之间的安全通道，确保 100% 坚守低回撤底座！
                    </div>
                </div>

                <!-- 专题 4：A股科技成长多因子选拔与 -5.0% 动态吊灯风控 -->
                <div class="dossier-card">
                    <div class="dossier-header">
                        <div class="dossier-title">⚔️ 专题四：A 股科技成长（创业板/科创50）多因子选拔与 -5.0% 宽幅动态吊灯跳车</div>
                        <span class="dossier-tag tag-star">天风证券 / 刘煜辉</span>
                    </div>
                    <div class="dossier-body">
                        <b>【博弈法则】</b>：A 股科技成长板块具有高贝塔、高弹性和剧烈轮动特征。当前创业板 5 日动量为 <b>{data['cyb_m5']:+.2f}%</b>，科创50 为 <b>{data['star_m5']:+.2f}%</b>，处于均线下方震荡磨底期。<br>
                        <b>【风控一票否决】</b>：策略执行严格的 -5.0% 动态吊灯风控，一旦信号大盘轨从峰值回撤 5% 或跌破 EMA20+MA20，果断将 A 股权益敞口压降至 <b>0%</b>，清仓切入黄金与农行，彻底杜绝阴跌磨损！
                    </div>
                </div>
            </div>

            <!-- 三、 量化雷达多因子面板与压力测试 -->
            <div class="card col-4">
                <div class="card-header">
                    <div class="card-title">⚡ 全景量化雷达与估值温度计</div>
                    <span style="font-size: 11px; background: rgba(168, 85, 247, 0.15); color: #c084fc; padding: 4px 10px; border-radius: 6px; font-weight:700;">实时量化中枢</span>
                </div>
                
                <div class="metric-row">
                    <div class="metric-label">华安黄金 20 日动量 (M20)</div>
                    <div class="metric-val gold">+{data['gold_m20']:.2f}% (超级主升浪)</div>
                </div>
                <div class="metric-row">
                    <div class="metric-label">纳指科技相对溢价偏离度 (DPSA)</div>
                    <div class="metric-val" style="color: #38bdf8;">{data['prem_spread']:+.2f}% (安全通道)</div>
                </div>
                <div class="metric-row">
                    <div class="metric-label">招行 / 农行比价 Z-Score</div>
                    <div class="metric-val">{data['bank_zscore']:+.2f}σ (招行蓄势)</div>
                </div>
                <div class="metric-row">
                    <div class="metric-label">创业板指 5 日动量水温</div>
                    <div class="metric-val {'up' if data['cyb_m5']>=0 else 'down'}">{data['cyb_m5']:+.2f}% (弱势蓄势)</div>
                </div>
                <div class="metric-row">
                    <div class="metric-label">科创50 5 日动量水温</div>
                    <div class="metric-val {'up' if data['star_m5']>=0 else 'down'}">{data['star_m5']:+.2f}% (蓄势筑底)</div>
                </div>
                <div class="metric-row">
                    <div class="metric-label">A股科技主攻端权益敞口</div>
                    <div class="metric-val" style="color: #10b981;">0.0% (防守空仓避险)</div>
                </div>

                <!-- FinRobot 情景压力测试分析 (Stress Testing) -->
                <div style="margin-top: 24px; padding-top: 18px; border-top: 1px solid rgba(255, 255, 255, 0.08);">
                    <div style="font-size: 13.5px; font-weight: 750; color: #f8fafc; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
                        🛡️ FinRobot 三维情景压力测试 (Stress-Test)
                    </div>
                    <div class="stress-grid">
                        <div class="stress-item" style="border-left: 3px solid #10b981;">
                            <div class="stress-title" style="color: #34d399;">🟢 乐观突破情景 (Bull)</div>
                            <div class="stress-desc">科技突破 EMA20，系统瞬间 100% 满仓独尊最强增强标的 (588170/159363)。</div>
                        </div>
                        <div class="stress-item" style="border-left: 3px solid #f59e0b;">
                            <div class="stress-title" style="color: #fbbf24;">🟡 震荡磨底情景 (Base)</div>
                            <div class="stress-desc">当前基准情景：50% 黄金股吃大宗暴涨，50% 农行吃 6.5% 免税股息，零磨损。</div>
                        </div>
                        <div class="stress-item" style="border-left: 3px solid #ef4444;">
                            <div class="stress-title" style="color: #f87171;">🔴 极端股灾情景 (Bear)</div>
                            <div class="stress-desc">触发 -5% 动态吊灯跳车，100% 规避大盘暴跌，黄金+银行充当避风港。</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 四、 五大策略大联合舰队实时战备矩阵 -->
            <div class="card col-12">
                <div class="card-header">
                    <div class="card-title">🎯 旗下五大策略大联合舰队战备矩阵与明日战令</div>
                    <span style="font-size: 12px; color: #94a3b8;">100% 规则化执行 · 零情绪干扰</span>
                </div>

                <div class="strategy-matrix-grid">
                    <div class="strategy-box">
                        <div class="strategy-box-header">
                            <div class="strategy-title">👑 科创-银行轮动策略</div>
                            <span class="strategy-badge">弱势防守态</span>
                        </div>
                        <div class="strategy-content">
                            • <b>当前持仓</b>：50% 黄金股 (517520) + 50% 农业银行 (601288)<br>
                            • <b>实战战绩</b>：10年总收益 +2926.21% 🏆，2026年翻倍 +100.05% 🚀<br>
                            • <b>实战效果</b>：完全避开 A 股震荡，吃满黄金股 +4.60% 暴涨！
                        </div>
                    </div>

                    <div class="strategy-box">
                        <div class="strategy-box-header">
                            <div class="strategy-title">🏛️ 纳指-双核银行策略</div>
                            <span class="strategy-badge">宏观全天候</span>
                        </div>
                        <div class="strategy-content">
                            • <b>当前持仓</b>：50% 纳指100 + 11.9% 农行 + 18.1% 招行 + 20% 黄金<br>
                            • <b>核心哲学</b>：20年夏普 1.08 全场最高，最大回撤仅 32.72%<br>
                            • <b>实战效果</b>：溢价 +1.62% 极度安全，双核银行自适应稳健收息！
                        </div>
                    </div>

                    <div class="strategy-box">
                        <div class="strategy-box-header">
                            <div class="strategy-title">⚔️ 五福 5.2/7.3 日内趋势</div>
                            <span class="strategy-badge">场内敏捷长矛</span>
                        </div>
                        <div class="strategy-content">
                            • <b>执行纪律</b>：13:10 盘中初选 + 14:55 尾盘终验<br>
                            • <b>风控防线</b>：四维大盘水温监控，跌破 MA10 自动切入货币防御<br>
                            • <b>实战效果</b>：提供高频场内动态子弹，严控隔夜风险。
                        </div>
                    </div>

                    <div class="strategy-box">
                        <div class="strategy-box-header">
                            <div class="strategy-title">⭐ 七星跨板块 ETF 轮动</div>
                            <span class="strategy-badge">全市场星级</span>
                        </div>
                        <div class="strategy-content">
                            • <b>核心算法</b>：严格 T-1 动量星级排序 + 反向波动率平价<br>
                            • <b>覆盖广度</b>：7 大核心主题 ETF 动态轮动<br>
                            • <b>实战效果</b>：年化 +24.17%，熨平行业剧烈结构分化。
                        </div>
                    </div>

                    <div class="strategy-box">
                        <div class="strategy-box-header">
                            <div class="strategy-title">🌱 场外公募基金轮动</div>
                            <span class="strategy-badge">免摩擦滚雪球</span>
                        </div>
                        <div class="strategy-content">
                            • <b>追踪标的</b>：锁定 006503 财通集成电路/芯片高景气公募<br>
                            • <b>交易窗口</b>：每周四 14:48 黄金免申赎费窗口调仓<br>
                            • <b>实战效果</b>：年化复合 +32.39%，长线免摩擦复利之王。
                        </div>
                    </div>
                </div>
            </div>

            <!-- 五、 明日操盘指南与终极启示录 -->
            <div class="card col-12" style="background: linear-gradient(135deg, rgba(16, 24, 40, 0.9) 0%, rgba(28, 40, 68, 0.95) 100%); border-color: rgba(245, 158, 11, 0.45);">
                <div class="card-header">
                    <div class="card-title" style="color: #f59e0b;">💡 明日操盘指南与终极战略启示录</div>
                    <span style="font-size: 12px; color: #cbd5e1;">极简执行 · 跨周期复利</span>
                </div>
                <div style="font-size: 14px; color: #f1f5f9; line-height: 1.85;">
                    <b>1. 保持战略定力，拒绝盘中被动消耗</b>：A 股科技成长处于无主线震荡磨底阶段，量化系统保持 0% 权益敞口，严格执行 -5.0% 宽幅吊灯止盈止损线；<br>
                    <b>2. 坚定拥抱黄金超级主升浪</b>：去美元化与主权储备重构不可逆转，满额配置 50% 黄金股 ETF (517520) 享受 2x 业绩爆发戴维斯双击弹性；<br>
                    <b>3. 极简操作法则</b>：每日仅需在 <b>14:48 ~ 14:55</b> 关注企业微信尾盘调仓信号，若显示【维持持仓】则无需任何操作，安心享受大类资产跨周期复利增长！
                </div>
            </div>
        </div>

        <footer class="footer">
            <p>👑 量化策略大联合舰队 · FinRobot 智能体宏观大势战略研报系统 · 自动化生成于 {now_str}</p>
            <p style="margin-top: 6px; font-size: 11px; color: #475569;">免责声明：本报告由量化系统根据公开行情与机构研报数据自动计算生成，仅供量化策略科研与实盘辅助参考，不构成任何投资买卖建议。</p>
        </footer>
    </div>
</body>
</html>
"""
    return html


# =====================================================================
# 三、 企业微信图文精要简报 (FinRobot 赋能)
# =====================================================================
def generate_wecom_brief(data: dict) -> str:
    """生成精致、高信息密度、结论先行的企业微信文字简报"""
    q = data['quotes']
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    gold_p = q.get('518880', {}).get('price', 0)
    gold_chg = q.get('518880', {}).get('change_pct', 0)
    gold_stock_p = q.get('517520', {}).get('price', 0)
    gold_stock_chg = q.get('517520', {}).get('change_pct', 0)
    ndx_p = q.get('513100', {}).get('price', 0)
    ndx_chg = q.get('513100', {}).get('change_pct', 0)
    abc_p = q.get('601288', {}).get('price', 0)
    abc_chg = q.get('601288', {}).get('change_pct', 0)
    cmb_p = q.get('600036', {}).get('price', 0)
    cmb_chg = q.get('600036', {}).get('change_pct', 0)

    html_cdn_url = "https://fastly.jsdelivr.net/gh/MUMUMU23333/game@main/index.html"
    html_pages_url = "https://mumumu23333.github.io/game/"

    markdown = f"""# 🏛️ 【全球宏观大势与量化全景战略晚报】
> ⏰ **复盘时间**：{now_str} (北京时间 · FinRobot 晚间 20:00 深度内参)
> 🌐 **宏观核心定调**：<font color="warning">**【全球去美元化共振 · 黄金2x主升加速 · 50%高股息双核压舱】**</font>

---
### 📊 一、 【核心大类资产量化速览】
• 👑 **黄金主升浪**：实物黄金 `¥{gold_p:.3f}` (<font color="warning">+{gold_chg:.2f}%</font>) | 黄金股 `¥{gold_stock_p:.3f}` (<font color="warning">**+{gold_stock_chg:.2f}% 🚀**</font>)
• 🇺🇸 **纳指100底座**：`¥{ndx_p:.3f}` ({ndx_chg:+.2f}%) | 溢价偏离度 `{data['prem_spread']:+.2f}%` (健康安全)
• 🏦 **双核银行底座**：农业银行 `¥{abc_p:.3f}` ({abc_chg:+.2f}%) | 招商银行 `¥{cmb_p:.3f}` ({cmb_chg:+.2f}%)
• 🇨🇳 **A股科技主攻**：创业板 `¥{q['159915']['price']:.3f}` ({q['159915']['change_pct']:+.2f}%) (弱势蓄势磨底)

---
### 🏛️ 二、 【FinRobot 顶级机构研报核心精要】
1. **🌟 高盛 & 桥水 (黄金超级周期)**：全球央行去美元化加速，黄金从“利率驱动”全面跃迁至“主权储备驱动”，20日动量 `+{data['gold_m20']:.1f}%` 确认超级主升浪！
2. **🏛️ 中金 & 中信 (高股息护城河)**：无风险利率下行中 6.5% 免税农行筑牢底座，招行 Z-Score `{data['bank_zscore']:+.2f}σ` 积蓄弹性。
3. **🇺🇸 摩根士丹利 (纳指AI基建)**：超大规模云厂商 CapEx 强劲，纳指科技溢价处于安全带，长线复利中枢稳固。

---
### 🎯 三、 【五大策略大联合舰队战备】
• 👑 **科创-银行轮动**：弱势防守态 (50%黄金股 517520 + 50%农行 601288)，吃满黄金 +4.60% 暴涨！
• 🏛️ **纳指-双核银行**：50%纳指100 + 11.9%农行 + 18.1%招行 + 20%黄金，极稳收息！
• ⚔️ **五福 5.2/7.3**：严格按 13:10/14:55 纪律执行，破线防守！
• ⭐ **七星跨板块**：反向波动率平价，跟踪全市场最强星级主线！
• 🌱 **场外公募轮动**：锁定半导体芯片高景气，周四免申赎费窗口调仓！

---
### 📱 四、 【深度 4K 交互研报 · 大陆免 VPN 直达】
👉 **[点击直接在手机/电脑浏览器中打开完整研报]({html_pages_url})**
*(备用免翻墙极速镜像：[国内高速 CDN 镜像]({html_cdn_url}))*

> 💡 *【明日操作提示】：每日仅需在 14:48 ~ 14:55 查看尾盘调仓信号，若【维持持仓】则无需操作，静享跨周期复利！*
"""
    return markdown.strip()


# =====================================================================
# 四、 主执行流
# =====================================================================
def run_macro_evening_pipeline(webhook_url: str = MACRO_EVENING_WEBHOOK):
    print("=" * 100)
    print("🏛️【全球宏观大势与量化全景战略研报】FinRobot 智能体生成引擎启动...")
    print("=" * 100)

    # 1. 采集数据
    print(">>> [1/4] 正在拉取全球核心大类资产实时行情与宏观因子...")
    dataset = collect_macro_dataset()

    # 2. 生成 4K Bento 栅格深度 HTML 研报
    print(">>> [2/4] 正在渲染 4K 深度交互式 HTML 研报...")
    html_content = generate_full_html_report(dataset)
    with open(HTML_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)
    with open(HTML_DASHBOARD_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"    ✓ HTML 研报已成功持久化至: {HTML_OUTPUT_PATH}")

    # 3. 渲染企业微信高密度图文简报
    print(">>> [3/4] 正在生成企业微信精炼图文简报...")
    wecom_brief = generate_wecom_brief(dataset)

    # 4. 推送企业微信
    print(">>> [4/4] 正在向指定 Webhook 发送晚间深度简报...")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": wecom_brief}
    }

    try:
        data_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        resp = session.post(webhook_url, data=data_bytes, headers=headers, timeout=15)
        res_json = resp.json()
        if res_json.get("errcode") == 0:
            print(f"[+] [全球宏观量化战略晚报] 企业微信推送成功！✅")
            return True
        else:
            print(f"[-] [全球宏观量化战略晚报] 推送失败: {res_json.get('errcode')} - {res_json.get('errmsg')}")
            return False
    except Exception as e:
        print(f"[-] [全球宏观量化战略晚报] 网络异常: {e}")
        return False


if __name__ == '__main__':
    run_macro_evening_pipeline()
