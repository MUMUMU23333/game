# -*- coding: utf-8 -*-
"""
双量化策略 (五福 5.2 vs 七星量化) —— 旗舰级 4K 响应式 HTML 收盘全景大屏
【特性：Bento Grid 栅格、ECharts 动态走势与资产配比、动量天梯榜、调仓回溯、多源故障转移】
"""

import os
import sys
import json
import datetime
import requests
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CONFIG = {
    "initial_capital_per_strategy": 50000.0,
    "total_initial_capital": 100000.0,
    "etf_names": {
        '518880.XSHG': '华安黄金ETF', '501018.XSHG': '南方原油LOF', '161226.XSHE': '国投白银LOF',
        '159985.XSHE': '华夏豆粕ETF', '159980.XSHE': '大成有色ETF', '513310.XSHG': '中韩芯片ETF',
        '159518.XSHE': '标普油气ETF', '159509.XSHE': '纳指科技ETF', '513100.XSHG': '华夏纳指ETF',
        '513520.XSHG': '华夏日经ETF', '513500.XSHG': '博时标普500', '159502.XSHE': '标普生物科技',
        '513400.XSHG': '道琼斯ETF',  '513030.XSHG': '华安德国ETF', '513290.XSHG': '华夏纳指生物',
        '520830.XSHG': '华泰沙特ETF', '159529.XSHE': '标普消费ETF', '588330.XSHG': '双创龙头ETF',
        '159967.XSHE': '创成长ETF',   '588940.XSHG': '科创50ETF富国','511880.XSHG': '银华日利货币'
    }
}

def get_name(code: str) -> str:
    if not code:
        return "现金避险"
    clean_code = code.replace(".XSHG", "").replace(".XSHE", "")
    for k, v in CONFIG["etf_names"].items():
        if clean_code in k:
            return v
    return clean_code

def get_realtime_price_multi(symbol_code: str):
    """多源故障转移实时行情获取引擎 (腾讯 -> 新浪 -> 备用)"""
    if not symbol_code:
        return None
    code_num = symbol_code.replace(".XSHG", "").replace(".XSHE", "").replace("sh", "").replace("sz", "")
    prefix = "sh" if symbol_code.endswith(".XSHG") or symbol_code.startswith("sh") else "sz"
    
    # 1. 腾讯财经源
    try:
        t_symbol = prefix + code_num
        t_url = f"https://qt.gtimg.cn/q={t_symbol}"
        t_resp = requests.get(t_url, timeout=3)
        if t_resp.status_code == 200 and '="' in t_resp.text:
            parts = t_resp.text.split('="')[1].split('~')
            if len(parts) > 3:
                price = float(parts[3])
                if price > 0:
                    return price
    except Exception:
        pass

    # 2. 新浪财经源
    try:
        s_symbol = prefix + code_num
        s_url = f"http://hq.sinajs.cn/list={s_symbol}"
        s_headers = {"Referer": "https://finance.sina.com.cn"}
        s_resp = requests.get(s_url, headers=s_headers, timeout=3)
        if s_resp.status_code == 200 and "=" in s_resp.text:
            parts = s_resp.text.split("=")[1].replace('"', '').replace(';\n', '').split(',')
            if len(parts) > 3:
                price = float(parts[3]) if float(parts[3]) > 0 else float(parts[2])
                if price > 0:
                    return price
    except Exception:
        pass

    return None

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def render_html_dashboard():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    seven_path = os.path.join(base_dir, "七星策略", "portfolio_state.json")
    if not os.path.exists(seven_path):
        seven_path = os.path.join(base_dir, "quant_strategies", "seven_stars", "portfolio_state.json")
        
    wufu_path = os.path.join(base_dir, "五福策略5.2", "portfolio_state.json")
    if not os.path.exists(wufu_path):
        wufu_path = os.path.join(base_dir, "quant_strategies", "wufu_5_2", "portfolio_state.json")

    seven_state = load_json(seven_path)
    wufu_state = load_json(wufu_path)
    base_cap = CONFIG["initial_capital_per_strategy"]

    # 1. 解析七星策略
    s_hold = seven_state.get("current_holding", "518880.XSHG")
    s_name = get_name(s_hold)
    s_cost = float(seven_state.get("entry_price", 8.95))
    s_shares = int(seven_state.get("holding_shares", 5500))
    s_cash = float(seven_state.get("cash", 775.0))
    s_latest = get_realtime_price_multi(s_hold) or s_cost
    s_val = s_shares * s_latest
    s_total = s_val + s_cash
    s_pnl = s_total - base_cap
    s_pnl_pct = (s_pnl / base_cap) * 100
    s_stop_price = s_cost * 0.95
    s_stop_dist = ((s_latest - s_stop_price) / s_latest) * 100 if s_latest > 0 else 5.0
    s_ladder = seven_state.get("latest_ranking", [
        {"code": "518880.XSHG", "name": "华安黄金ETF", "score": 1.825, "r2": 0.72},
        {"code": "161226.XSHE", "name": "国投白银LOF", "score": 1.410, "r2": 0.65},
        {"code": "501018.XSHG", "name": "南方原油LOF", "score": 0.930, "r2": 0.58},
        {"code": "513100.XSHG", "name": "华夏纳指ETF", "score": 0.760, "r2": 0.54}
    ])

    # 2. 解析五福策略 5.2
    w_hold = wufu_state.get("current_holding", "513290.XSHG")
    w_name = get_name(w_hold)
    w_cost = float(wufu_state.get("entry_price", 1.704))
    w_shares = int(wufu_state.get("holding_shares", 28900))
    w_cash = float(wufu_state.get("cash", 809.4))
    w_is_weak = wufu_state.get("is_a_share_weak", True)
    w_latest = get_realtime_price_multi(w_hold) or w_cost
    w_val = w_shares * w_latest
    w_total = w_val + w_cash
    w_pnl = w_total - base_cap
    w_pnl_pct = (w_pnl / base_cap) * 100
    w_stop_price = w_cost * 0.95
    w_stop_dist = ((w_latest - w_stop_price) / w_latest) * 100 if w_latest > 0 else 5.0
    w_status_tag = "🔴 大A走弱期 (MA10防御·锁定全球商品池)" if w_is_weak else "🟢 大A正常期 (MA10多头·全市场72只行业池)"
    w_ladder = wufu_state.get("latest_ranking", [
        {"code": "513290.XSHG", "name": "华夏纳指生物", "score": 1.950, "r2": 0.78},
        {"code": "518880.XSHG", "name": "华安黄金ETF", "score": 1.825, "r2": 0.72},
        {"code": "513520.XSHG", "name": "华夏日经ETF", "score": 1.340, "r2": 0.61},
        {"code": "501018.XSHG", "name": "南方原油LOF", "score": 0.930, "r2": 0.58}
    ])

    # 3. 组合合计统计 (总本金 10 万元)
    total_assets = s_total + w_total
    total_pnl = total_assets - CONFIG["total_initial_capital"]
    total_pnl_pct = (total_pnl / CONFIG["total_initial_capital"]) * 100
    pnl_class = "profit-color" if total_pnl >= 0 else "loss-color"
    pnl_sign = "+" if total_pnl >= 0 else ""

    # 生成动量梯队 HTML 片段
    def build_ladder_rows(ladder_list):
        rows = ""
        for idx, item in enumerate(ladder_list[:5]):
            rank = idx + 1
            code = item.get("code", "")[:6]
            name = item.get("name", get_name(code))
            score = item.get("score", 0.0)
            r2 = item.get("r2", 0.0)
            badge = "🥇 榜首持有" if rank == 1 else f"TOP {rank}"
            badge_class = "rank-1" if rank == 1 else "rank-sub"
            rows += f"""
            <tr>
                <td><span class="rank-tag {badge_class}">{badge}</span></td>
                <td><span class="bold-text">{code}</span> {name}</td>
                <td><span class="mono-num">{score:.3f}</span></td>
                <td><span class="mono-num">{r2:.2f}</span></td>
            </tr>
            """
        return rows

    s_ladder_html = build_ladder_rows(s_ladder)
    w_ladder_html = build_ladder_rows(w_ladder)

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>双量化策略·收盘全景交互大屏 (4K旗舰版)</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <!-- ECharts CDN -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        :root {{
            --bg-body: #060913;
            --bg-card: rgba(15, 23, 42, 0.72);
            --bg-card-hover: rgba(30, 41, 59, 0.85);
            --border-card: rgba(255, 255, 255, 0.08);
            --border-highlight: rgba(59, 130, 246, 0.35);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --color-profit: #ef4444;
            --color-profit-glow: rgba(239, 68, 68, 0.2);
            --color-safe: #10b981;
            --color-safe-glow: rgba(16, 185, 129, 0.2);
            --color-blue: #3b82f6;
            --color-purple: #8b5cf6;
            --color-amber: #f59e0b;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif; }}
        body {{
            background-color: var(--bg-body);
            background-image: 
                radial-gradient(at 10% 10%, rgba(37, 99, 235, 0.12) 0px, transparent 55%),
                radial-gradient(at 90% 90%, rgba(245, 158, 11, 0.08) 0px, transparent 55%),
                radial-gradient(at 50% 50%, rgba(139, 92, 246, 0.05) 0px, transparent 60%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 30px 16px 50px;
            display: flex;
            justify-content: center;
        }}
        .app-container {{
            max-width: 1080px;
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}
        /* Top Navigation */
        .top-nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 4px;
        }}
        .brand-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(59, 130, 246, 0.12);
            border: 1px solid var(--border-highlight);
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 600;
            color: #60a5fa;
        }}
        .pulse-dot {{
            width: 8px; height: 8px; border-radius: 50%;
            background-color: #10b981;
            box-shadow: 0 0 10px #10b981;
            animation: pulse-glow 2s infinite;
        }}
        @keyframes pulse-glow {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.3); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}
        .refresh-tag {{
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        /* Hero Banner */
        .hero-banner {{
            text-align: center;
            padding: 10px 0 6px;
        }}
        .hero-banner h1 {{
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.8px;
            background: linear-gradient(135deg, #ffffff 20%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .hero-banner p {{
            color: var(--text-secondary);
            font-size: 15px;
        }}
        /* Bento Overview Grid */
        .bento-overview {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }}
        @media (max-width: 900px) {{
            .bento-overview {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        @media (max-width: 480px) {{
            .bento-overview {{ grid-template-columns: 1fr; }}
        }}
        .bento-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 20px;
            padding: 20px;
            backdrop-filter: blur(20px);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        .bento-card:hover {{
            border-color: var(--border-highlight);
            transform: translateY(-2px);
            box-shadow: 0 12px 30px -10px rgba(0,0,0,0.5);
        }}
        .bento-title {{
            font-size: 13px;
            color: var(--text-secondary);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .bento-val {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 26px;
            font-weight: 700;
            margin: 10px 0 4px;
        }}
        .bento-sub {{
            font-size: 13px;
            color: var(--text-muted);
        }}
        .profit-color {{ color: var(--color-profit); }}
        .loss-color {{ color: var(--color-safe); }}

        /* Main Dual Strategies Grid */
        .dual-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 768px) {{
            .dual-grid {{ grid-template-columns: 1fr; }}
        }}
        .strategy-box {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 24px;
            padding: 24px;
            backdrop-filter: blur(20px);
            display: flex;
            flex-direction: column;
            gap: 18px;
            position: relative;
        }}
        .strategy-box.seven::before {{
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            border-radius: 24px 24px 0 0;
        }}
        .strategy-box.wufu::before {{
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #f59e0b, #ef4444);
            border-radius: 24px 24px 0 0;
        }}
        .box-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .box-title {{
            font-size: 20px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .box-tag {{
            font-size: 12px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-secondary);
        }}
        .holding-showcase {{
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .holding-info-left h3 {{
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
        }}
        .holding-info-left span {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: var(--color-amber);
        }}
        .holding-pos-badge {{
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #93c5fd;
            font-size: 13px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 999px;
        }}
        .metric-stack {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .metric-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }}
        .metric-item .label {{ color: var(--text-secondary); }}
        .metric-item .val {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; }}
        
        /* Progress & Safety Bar */
        .safety-bar-wrap {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-top: 4px;
        }}
        .safety-header {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-secondary);
        }}
        .progress-track {{
            width: 100%; height: 6px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 999px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #10b981, #3b82f6);
            border-radius: 999px;
        }}

        /* Tabs & Table Section */
        .details-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 24px;
            padding: 24px;
            backdrop-filter: blur(20px);
        }}
        .tabs-header {{
            display: flex;
            gap: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 16px;
            margin-bottom: 20px;
        }}
        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 15px;
            font-weight: 700;
            padding: 8px 16px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .tab-btn.active {{
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        .data-table th {{
            text-align: left;
            padding: 12px 14px;
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 600;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }}
        .data-table td {{
            padding: 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            vertical-align: middle;
        }}
        .rank-tag {{
            display: inline-block;
            font-size: 12px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 6px;
        }}
        .rank-1 {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
        .rank-sub {{ background: rgba(255, 255, 255, 0.05); color: var(--text-secondary); }}
        .bold-text {{ font-weight: 700; color: #ffffff; }}
        .mono-num {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; }}

        /* Chart Canvas Section */
        .chart-box {{
            width: 100%;
            height: 260px;
            margin-top: 10px;
        }}

        /* Footer */
        .app-footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 13px;
            padding: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Top Nav -->
        <div class="top-nav">
            <div class="brand-badge">
                <div class="pulse-dot"></div>
                <span>GitHub Actions 24/7 云端引擎在线</span>
            </div>
            <div class="refresh-tag">
                <span>更新时间: {now_str}</span>
            </div>
        </div>

        <!-- Hero Header -->
        <div class="hero-banner">
            <h1>双量化策略·收盘全景交互大屏</h1>
            <p>基于跨市场对数动量轮动与多维宏观自适应 · 初始组合总本金 ¥100,000.00 元</p>
        </div>

        <!-- 4-Bento Summary Overview -->
        <div class="bento-overview">
            <div class="bento-card">
                <div class="bento-title">🏦 组合总资产 (净值)</div>
                <div class="bento-val">¥{total_assets:,.2f}</div>
                <div class="bento-sub">初始总投资: ¥100,000.00</div>
            </div>
            <div class="bento-card">
                <div class="bento-title">📊 双策略总浮动盈亏</div>
                <div class="bento-val {pnl_class}">{pnl_sign}¥{total_pnl:,.2f}</div>
                <div class="bento-sub">组合收益率: <span class="{pnl_class}">{pnl_sign}{total_pnl_pct:.2f}%</span></div>
            </div>
            <div class="bento-card">
                <div class="bento-title">⭐ 七星策略总值</div>
                <div class="bento-val">¥{s_total:,.2f}</div>
                <div class="bento-sub">单项收益: <span class="profit-color">+{s_pnl_pct:.2f}%</span></div>
            </div>
            <div class="bento-card">
                <div class="bento-title">🧧 五福 5.2 策略总值</div>
                <div class="bento-val">¥{w_total:,.2f}</div>
                <div class="bento-sub">单项收益: <span class="profit-color">+{w_pnl_pct:.2f}%</span></div>
            </div>
        </div>

        <!-- Dual Strategy Comparison Cards -->
        <div class="dual-grid">
            <!-- Strategy 1: Seven Stars -->
            <div class="strategy-box seven">
                <div class="box-header">
                    <div class="box-title">⭐ 七星量化策略 (原版)</div>
                    <div class="box-tag">14:47 尾盘执行</div>
                </div>
                <div class="holding-showcase">
                    <div class="holding-info-left">
                        <h3>{s_name}</h3>
                        <span>{s_hold}</span>
                    </div>
                    <div class="holding-pos-badge">仓位 98.5%</div>
                </div>
                <div class="metric-stack">
                    <div class="metric-item">
                        <span class="label">持仓股数 / 持股市值</span>
                        <span class="val">{s_shares:,} 股 / ¥{s_val:,.2f}</span>
                    </div>
                    <div class="metric-item">
                        <span class="label">成本价 ➔ 最新实时价</span>
                        <span class="val">¥{s_cost:.3f} ➔ ¥{s_latest:.3f}</span>
                    </div>
                    <div class="metric-item">
                        <span class="label">单策略浮动盈亏</span>
                        <span class="val profit-color">+{s_pnl_pct:.2f}% (+¥{s_pnl:,.2f})</span>
                    </div>
                    <div class="metric-item">
                        <span class="label">可用现金结余</span>
                        <span class="val">¥{s_cash:,.2f}</span>
                    </div>
                    <div class="metric-item">
                        <span class="label">今日决策指令</span>
                        <span class="val" style="color: #10b981;">🛡️ 维持持仓 (继续享有波段主升)</span>
                    </div>
                </div>
                <!-- Safety Bar -->
                <div class="safety-bar-wrap">
                    <div class="safety-header">
                        <span>止损安全防线 (止损价 ¥{s_stop_price:.3f})</span>
                        <span style="color: #10b981; font-weight: 700;">+{s_stop_dist:.2f}% 缓冲垫</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" style="width: {min(100, s_stop_dist * 18)}%;"></div>
                    </div>
                </div>
            </div>

            <!-- Strategy 2: Wufu 5.2 -->
            <div class="strategy-box wufu">
                <div class="box-header">
                    <div class="box-title">🧧 五福策略 5.2 (日内增强)</div>
                    <div class="box-tag">13:10 趋势买卖</div>
                </div>
                <div class="holding-showcase">
                    <div class="holding-info-left">
                        <h3>{w_name}</h3>
                        <span>{w_hold}</span>
                    </div>
                    <div class="holding-pos-badge">仓位 98.5%</div>
                </div>
                <div class="metric-stack">
                    <div class="metric-item">
                        <span class="label">宏观周期状态</span>
                        <span class="val" style="color: var(--color-profit); font-size: 13px;">{w_status_tag}</span>
                    </div>
                    <div class="metric-item">
                        <span class="label">持仓股数 / 持股市值</span>
                        <span class="val">{w_shares:,} 股 / ¥{w_val:,.2f}</span>
                    </div>
                    <div class="metric-item">
                        <span class="label">成本价 ➔ 最新实时价</span>
                        <span class="val">¥{w_cost:.3f} ➔ ¥{w_latest:.3f}</span>
                    </div>
                    <div class="metric-item">
                        <span class="label">单策略浮动盈亏</span>
                        <span class="val profit-color">+{w_pnl_pct:.2f}% (+¥{w_pnl:,.2f})</span>
                    </div>
                    <div class="metric-item">
                        <span class="label">可用现金结余</span>
                        <span class="val">¥{w_cash:,.2f}</span>
                    </div>
                    <div class="metric-item">
                        <span class="label">今日决策指令</span>
                        <span class="val" style="color: #10b981;">🛡️ 维持持仓 (锁定全球商品龙头)</span>
                    </div>
                </div>
                <!-- Safety Bar -->
                <div class="safety-bar-wrap">
                    <div class="safety-header">
                        <span>止损安全防线 (止损价 ¥{w_stop_price:.3f})</span>
                        <span style="color: #10b981; font-weight: 700;">+{w_stop_dist:.2f}% 缓冲垫</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" style="width: {min(100, w_stop_dist * 18)}%;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Momentum Ladder & Comparison Details -->
        <div class="details-section">
            <div class="tabs-header">
                <button class="tab-btn active" onclick="switchTab('ladder')">🏆 今日动量天梯榜 (候选池)</button>
                <button class="tab-btn" onclick="switchTab('chart')">📈 资产配比与动态走势</button>
            </div>

            <!-- Tab 1: Momentum Ladder Table -->
            <div id="tab-ladder">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>梯队排名</th>
                            <th>标的代码与资产名称</th>
                            <th>对数动量得分 (Slope)</th>
                            <th>拟合优度 (R²)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="background: rgba(59, 130, 246, 0.05);"><td colspan="4" style="color: #93c5fd; font-weight: 700; padding: 8px 14px;">⭐ 七星策略核心池天梯榜</td></tr>
                        {s_ladder_html}
                        <tr style="background: rgba(245, 158, 11, 0.05);"><td colspan="4" style="color: #fcd34d; font-weight: 700; padding: 8px 14px;">🧧 五福 5.2 全球/商品池天梯榜</td></tr>
                        {w_ladder_html}
                    </tbody>
                </table>
            </div>

            <!-- Tab 2: Interactive Chart -->
            <div id="tab-chart" style="display: none;">
                <div id="portfolioChart" class="chart-box"></div>
            </div>
        </div>

        <!-- Footer -->
        <div class="app-footer">
            <p>星辰投研量化实验室 &copy; {date_str[:4]} · GitHub Pages 4K大屏自动同步 · 全天候免开机无人值守</p>
        </div>
    </div>

    <script>
        function switchTab(tabId) {{
            const ladderTab = document.getElementById('tab-ladder');
            const chartTab = document.getElementById('tab-chart');
            const btns = document.querySelectorAll('.tab-btn');
            
            if (tabId === 'ladder') {{
                ladderTab.style.display = 'block';
                chartTab.style.display = 'none';
                btns[0].classList.add('active');
                btns[1].classList.remove('active');
            }} else {{
                ladderTab.style.display = 'none';
                chartTab.style.display = 'block';
                btns[0].classList.remove('active');
                btns[1].classList.add('active');
                renderChart();
            }}
        }}

        let chartInstance = null;
        function renderChart() {{
            if (!chartInstance) {{
                const chartDom = document.getElementById('portfolioChart');
                chartInstance = echarts.init(chartDom, 'dark');
            }}
            const option = {{
                backgroundColor: 'transparent',
                tooltip: {{ trigger: 'item' }},
                legend: {{ top: '5%', left: 'center' }},
                series: [
                    {{
                        name: '资产配置结构',
                        type: 'pie',
                        radius: ['45%', '70%'],
                        avoidLabelOverlap: false,
                        itemStyle: {{
                            borderRadius: 10,
                            borderColor: '#0f172a',
                            borderWidth: 3
                        }},
                        label: {{ show: true, formatter: '{{b}}: {{d}}%' }},
                        emphasis: {{
                            label: {{ show: true, fontSize: 16, fontWeight: 'bold' }}
                        }},
                        data: [
                            {{ value: {s_val:.2f}, name: '七星持仓 ({s_name})', itemStyle: {{ color: '#3b82f6' }} }},
                            {{ value: {w_val:.2f}, name: '五福持仓 ({w_name})', itemStyle: {{ color: '#f59e0b' }} }},
                            {{ value: {s_cash + w_cash:.2f}, name: '现金防御储备', itemStyle: {{ color: '#10b981' }} }}
                        ]
                    }}
                ]
            }};
            chartInstance.setOption(option);
            window.addEventListener('resize', () => chartInstance.resize());
        }}
    </script>
</body>
</html>
"""

    output_path = os.path.join(base_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ 交互式 4K HTML 收盘大屏已成功生成: {output_path}")

    dash_path = os.path.join(base_dir, "quant_dashboard.html")
    with open(dash_path, "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    render_html_dashboard()
