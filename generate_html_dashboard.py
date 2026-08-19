# -*- coding: utf-8 -*-
"""
双量化策略 (五福 5.2 vs 七星量化) —— 交互式 HTML 收盘全景大屏生成器
【零额外费用，完全通过 GitHub Pages 免费托管，企微一键点击直达】
"""

import os
import sys
import json
import datetime
import requests

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

def get_realtime_price(symbol_code: str):
    if not symbol_code:
        return None
    try:
        prefix = "sh" if symbol_code.endswith(".XSHG") or symbol_code.startswith("sh") else "sz"
        code_num = symbol_code.replace(".XSHG", "").replace(".XSHE", "").replace("sh", "").replace("sz", "")
        symbol = prefix + code_num
        url = f"http://hq.sinajs.cn/list={symbol}"
        headers = {"Referer": "https://finance.sina.com.cn"}
        resp = requests.get(url, headers=headers, timeout=5)
        text = resp.text
        if "=" in text:
            parts = text.split("=")[1].replace('"', '').replace(';\n', '').split(',')
            if len(parts) > 3:
                p = float(parts[3]) if float(parts[3]) > 0 else float(parts[2])
                return p
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
    date_str = datetime.datetime.now().strftime("%Y年%m月%d日")
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

    # 1. 七星策略
    s_hold = seven_state.get("current_holding", "518880.XSHG")
    s_name = get_name(s_hold)
    s_cost = float(seven_state.get("entry_price", 8.95))
    s_shares = int(seven_state.get("holding_shares", 5500))
    s_cash = float(seven_state.get("cash", 775.0))
    s_latest = get_realtime_price(s_hold) or s_cost
    s_val = s_shares * s_latest
    s_total = s_val + s_cash
    s_pnl = s_total - base_cap
    s_pnl_pct = (s_pnl / base_cap) * 100
    s_stop_dist = ((s_latest - s_cost * 0.95) / s_latest) * 100 if s_latest > 0 else 5.0

    # 2. 五福策略 5.2
    w_hold = wufu_state.get("current_holding", "518880.XSHG")
    w_name = get_name(w_hold)
    w_cost = float(wufu_state.get("entry_price", 8.95))
    w_shares = int(wufu_state.get("holding_shares", 5500))
    w_cash = float(wufu_state.get("cash", 775.0))
    w_is_weak = wufu_state.get("is_a_share_weak", True)
    w_latest = get_realtime_price(w_hold) or w_cost
    w_val = w_shares * w_latest
    w_total = w_val + w_cash
    w_pnl = w_total - base_cap
    w_pnl_pct = (w_pnl / base_cap) * 100
    w_stop_dist = ((w_latest - w_cost * 0.95) / w_latest) * 100 if w_latest > 0 else 5.0
    w_status_tag = "大A走弱期 (全球商品池)" if w_is_weak else "大A正常期 (全市场行业池)"

    # 3. 组合合计
    total_assets = s_total + w_total
    total_pnl = total_assets - CONFIG["total_initial_capital"]
    total_pnl_pct = (total_pnl / CONFIG["total_initial_capital"]) * 100
    pnl_class = "profit" if total_pnl >= 0 else "loss"
    pnl_sign = "+" if total_pnl >= 0 else ""

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>双量化策略·收盘全景对比大屏</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #0a0f1d;
            --card-bg: rgba(20, 29, 51, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-glow: rgba(59, 130, 246, 0.15);
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
            --profit-red: #ef4444;
            --profit-bg: rgba(239, 68, 68, 0.12);
            --safe-green: #10b981;
            --safe-bg: rgba(16, 185, 129, 0.12);
            --gold: #f59e0b;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', system-ui, -apple-system, sans-serif; }}
        body {{
            background-color: var(--bg-base);
            background-image: 
                radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(245, 158, 11, 0.1) 0px, transparent 50%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px 16px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 900px;
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .header {{
            text-align: center;
            padding: 20px 0 10px;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 9999px;
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #60a5fa;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 12px;
        }}
        .header h1 {{
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .header p {{
            color: var(--text-sub);
            font-size: 14px;
        }}
        /* Summary Hero Card */
        .summary-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 24px;
            backdrop-filter: blur(16px);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .summary-item {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .summary-label {{
            font-size: 13px;
            color: var(--text-sub);
            font-weight: 600;
            text-transform: uppercase;
        }}
        .summary-value {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 24px;
            font-weight: 700;
        }}
        .profit {{ color: var(--profit-red); }}
        .loss {{ color: var(--safe-green); }}

        /* Strategies Grid */
        .strategies-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 768px) {{
            .strategies-grid {{ grid-template-columns: 1fr; }}
        }}
        .strategy-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 24px;
            backdrop-filter: blur(16px);
            display: flex;
            flex-direction: column;
            gap: 16px;
            position: relative;
            overflow: hidden;
        }}
        .strategy-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        }}
        .strategy-card.wufu::before {{
            background: linear-gradient(90deg, #f59e0b, #ef4444);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .card-title {{
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .time-tag {{
            font-size: 12px;
            padding: 2px 8px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-sub);
        }}
        .holding-box {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 14px;
            padding: 16px;
        }}
        .holding-name {{
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 4px;
        }}
        .holding-code {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: var(--gold);
        }}
        .metrics-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }}
        .metric-label {{
            color: var(--text-sub);
        }}
        .metric-val {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
        }}
        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            background: var(--safe-bg);
            color: var(--safe-green);
        }}
        /* Table Section */
        .table-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 24px;
            backdrop-filter: blur(16px);
        }}
        .table-title {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 16px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px 14px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        th {{
            color: var(--text-sub);
            font-weight: 600;
            font-size: 13px;
        }}
        td {{
            font-family: 'JetBrains Mono', monospace;
        }}
        .footer {{
            text-align: center;
            padding: 16px 0;
            font-size: 12px;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="badge">🤖 GitHub Actions 24/7 免开机云端驱动</div>
            <h1>双量化策略·收盘全景横向对比大屏</h1>
            <p>数据更新时间：{now_str} | 基准初始本金：¥100,000.00 元</p>
        </div>

        <!-- Summary Hero -->
        <div class="summary-card">
            <div class="summary-item">
                <span class="summary-label">组合当前总资产</span>
                <span class="summary-value">¥{total_assets:,.2f}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">双策略合计浮动盈亏</span>
                <span class="summary-value {pnl_class}">{pnl_sign}¥{total_pnl:,.2f} ({pnl_sign}{total_pnl_pct:.2f}%)</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">当前运作状态</span>
                <span class="summary-value" style="font-size: 18px; color: var(--safe-green); display: flex; align-items: center; gap: 6px;">
                    🟢 运行健康 (无需调仓)
                </span>
            </div>
        </div>

        <!-- Strategy Grid -->
        <div class="strategies-grid">
            <!-- Seven Stars -->
            <div class="strategy-card">
                <div class="card-header">
                    <div class="card-title">⭐ 七星量化策略</div>
                    <div class="time-tag">每日 14:47 执行</div>
                </div>
                <div class="holding-box">
                    <div class="holding-name">{s_name}</div>
                    <div class="holding-code">{s_hold} (仓位: 98.5%)</div>
                </div>
                <div class="metrics-list">
                    <div class="metric-row">
                        <span class="metric-label">持仓股数 / 市值</span>
                        <span class="metric-val">{s_shares:,} 股 / ¥{s_val:,.2f}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">买入成本 ➔ 最新价</span>
                        <span class="metric-val">¥{s_cost:.3f} ➔ ¥{s_latest:.3f}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">单策略收益 (本金5万)</span>
                        <span class="metric-val profit">+{s_pnl_pct:.2f}% (+¥{s_pnl:,.2f})</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">账户总资产 (含现金)</span>
                        <span class="metric-val">¥{s_total:,.2f}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">风控止损安全垫</span>
                        <span class="status-pill">🛡️ 距止损 +{s_stop_dist:.2f}%</span>
                    </div>
                </div>
            </div>

            <!-- Wufu 5.2 -->
            <div class="strategy-card wufu">
                <div class="card-header">
                    <div class="card-title">🧧 五福策略 5.2</div>
                    <div class="time-tag">每日 13:10 执行</div>
                </div>
                <div class="holding-box">
                    <div class="holding-name">{w_name}</div>
                    <div class="holding-code">{w_hold} (仓位: 98.5%)</div>
                </div>
                <div class="metrics-list">
                    <div class="metric-row">
                        <span class="metric-label">宏观周期研判</span>
                        <span class="metric-val" style="color: var(--profit-red); font-size: 12px;">{w_status_tag}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">持仓股数 / 市值</span>
                        <span class="metric-val">{w_shares:,} 股 / ¥{w_val:,.2f}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">买入成本 ➔ 最新价</span>
                        <span class="metric-val">¥{w_cost:.3f} ➔ ¥{w_latest:.3f}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">单策略收益 (本金5万)</span>
                        <span class="metric-val profit">+{w_pnl_pct:.2f}% (+¥{w_pnl:,.2f})</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">账户总资产 (含现金)</span>
                        <span class="metric-val">¥{w_total:,.2f}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">风控止损安全垫</span>
                        <span class="status-pill">🛡️ 距止损 +{w_stop_dist:.2f}%</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Comparative Table -->
        <div class="table-card">
            <div class="table-title">📋 核心指标横向深度对照表</div>
            <table>
                <thead>
                    <tr>
                        <th>对比维度</th>
                        <th>⭐ 七星量化策略</th>
                        <th>🧧 五福策略 5.2</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>当前持仓标的</td>
                        <td style="color: #60a5fa;">{s_hold[:6]} {s_name}</td>
                        <td style="color: #f59e0b;">{w_hold[:6]} {w_name}</td>
                    </tr>
                    <tr>
                        <td>单策略本金 / 市值</td>
                        <td>¥50,000 / ¥{s_val:,.2f}</td>
                        <td>¥50,000 / ¥{w_val:,.2f}</td>
                    </tr>
                    <tr>
                        <td>单策略盈亏 (金额/比例)</td>
                        <td class="profit">+¥{s_pnl:,.2f} (+{s_pnl_pct:.2f}%)</td>
                        <td class="profit">+¥{w_pnl:,.2f} (+{w_pnl_pct:.2f}%)</td>
                    </tr>
                    <tr>
                        <td>今日收盘操作指示</td>
                        <td><span class="status-pill">🛡️ 维持持仓</span></td>
                        <td><span class="status-pill">🛡️ 维持持仓</span></td>
                    </tr>
                    <tr>
                        <td>风控防线阈值</td>
                        <td>5% 绝对止损 (回撤预警)</td>
                        <td>5% 绝对止损 (回撤预警)</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>星辰投研量化实验室 &copy; {date_str[:4]} · GitHub Pages 实时大屏托管</p>
        </div>
    </div>
</body>
</html>
"""

    output_path = os.path.join(base_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ 交互式 HTML 收盘大屏已成功生成: {output_path}")

    # 同时复制一份为 dashboard.html
    dash_path = os.path.join(base_dir, "dashboard.html")
    with open(dash_path, "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    render_html_dashboard()
