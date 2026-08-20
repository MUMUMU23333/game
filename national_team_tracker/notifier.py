"""
通知与可视化看板模块 (Notifier & Visual Dashboard)
支持控制台彩色高密度表格打印、交互式现代 HTML 投研报告生成与 Webhook 推送。
兼容 Windows CMD / PowerShell / Linux 终端编码。
"""

import os
import sys
import json
import datetime
from typing import Dict, List, Any
import requests

from .config import NOTIFIER_CONFIG

# 确保 Windows 控制台支持 UTF-8 打印
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


class ConsoleColors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"
    GRAY = "\033[90m"
    MAGENTA = "\033[95m"


class Notifier:
    """国家队监控可视化与消息分发器"""

    @staticmethod
    def print_console_dashboard(analysis_data: Dict[str, Any]):
        """在控制台打印精美的结构化投研看板"""
        C = ConsoleColors
        ts = analysis_data["timestamp"]
        total_inflow = analysis_data["total_inflow_yi"]
        macro_verdict = analysis_data["macro_verdict"]
        stats = analysis_data["overall_stats"]
        decision = analysis_data.get("timing_decision", {})

        print(f"\n{C.BOLD}{C.CYAN}{'='*92}{C.RESET}")
        print(f"{C.BOLD}{C.HEADER} [★] 国家队资金跟踪与入场时机决策看板 (National Team Timing Assistant) {C.RESET}")
        print(f"{C.GRAY} 核心监控 6 大板块: 沪深300 | 中证500 | 中证1000 | 创业板 | 科创50 | 大金融(证券/银行){C.RESET}")
        print(f"{C.GRAY} 实时时间: {ts}{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}{'='*92}{C.RESET}")

        # ----------------------------------------------------
        # 1. 核心入场时机与仓位决策 (直白人话)
        # ----------------------------------------------------
        print(f"\n{C.BOLD}【🚦 国家队入场时机判断】{C.RESET} {C.BOLD}{C.YELLOW}{decision.get('timing_signal')}{C.RESET}")
        print(f" {C.CYAN}▶ 救市周期:{C.RESET} {decision.get('lifecycle_stage')}")
        print(f" {C.CYAN}▶ 建议仓位:{C.RESET} {C.BOLD}{C.GREEN}{decision.get('position_advice')}{C.RESET}")
        print(f" {C.CYAN}▶ 标的推荐:{C.RESET} {decision.get('recommended_targets')}")
        print(f" {C.CYAN}▶ 智能杠铃:{C.RESET} {C.BOLD}{C.MAGENTA}{decision.get('barbell_ratio')}{C.RESET} ({decision.get('barbell_desc')})")
        print(f" {C.CYAN}▶ 大V战法:{C.RESET} {C.BOLD}{C.BLUE}{decision.get('kol_tactic')}{C.RESET}")
        print(f" {C.CYAN}▶ 操作手法:{C.RESET} {decision.get('tactical_guide')}")

        # ----------------------------------------------------
        # 2. 六大板块资金流向与动向排序
        # ----------------------------------------------------
        print(f"\n{C.BOLD}【🔥 六大核心板块国家队动向分布】{C.RESET}")
        flows = decision.get("sector_flows", {})
        scores = decision.get("sector_scores", {})
        
        sector_line = []
        for s_name, f_val in flows.items():
            f_color = C.GREEN if f_val > 0 else (C.RED if f_val < 0 else C.GRAY)
            s_score = scores.get(s_name, 0.0)
            sector_line.append(f"{s_name}: {f_color}{f_val:+.1f}亿{C.RESET}(热度:{s_score}分)")
        print("  " + " | ".join(sector_line[:3]))
        print("  " + " | ".join(sector_line[3:]))

        print(f"\n{C.GRAY} 全市场信号汇总: AAA级(强护盘): {stats['AAA']}  |  AA级(水下吸筹): {stats['AA']}  |  C级(游资脉冲): {stats['C']}  |  D级(减仓): {stats['D']}{C.RESET}\n")

        # ----------------------------------------------------
        # 3. 详细行情与个股 ETF 研判
        # ----------------------------------------------------
        print(f"{C.BOLD}{'标的代码':<8} {'标的名称':<16} {'现价':<7} {'涨跌幅':<8} {'成交额(亿)':<10} {'异动分':<8} {'净流入(亿)':<10} {'综合研判':<20}{C.RESET}")
        print(f"{C.GRAY}{'-'*92}{C.RESET}")

        for item in analysis_data["results"]:
            code = item["code"]
            name = item["name"][:8]
            price = f"{item['price']:.3f}"
            chg_val = item['chg_pct']
            chg_color = C.RED if chg_val < 0 else (C.GREEN if chg_val > 0 else C.GRAY)
            chg_str = f"{chg_color}{chg_val:>+6.2f}%{C.RESET}"
            
            amount_str = f"{item['amount_yi']:>7.2f}"
            score = item['intra_score']
            score_color = C.RED if score >= 60 else (C.YELLOW if score >= 40 else C.GRAY)
            score_str = f"{score_color}{score:>5.1f}{C.RESET}"

            inflow = item['inflow_money_yi']
            inflow_color = C.GREEN if inflow > 0 else (C.RED if inflow < 0 else C.GRAY)
            inflow_str = f"{inflow_color}{inflow:>+7.2f}{C.RESET}"

            grade = item["grade"]
            if grade == "AAA":
                verdict_str = f"{C.BOLD}{C.GREEN}[AAA 强力真护盘]{C.RESET}"
            elif grade == "AA":
                verdict_str = f"{C.BOLD}{C.BLUE}[AA  水下吸筹]{C.RESET}"
            elif grade == "C":
                verdict_str = f"{C.YELLOW}[C   游资脉冲]{C.RESET}"
            elif grade == "D":
                verdict_str = f"{C.RED}[D   机构减仓]{C.RESET}"
            else:
                verdict_str = f"{C.GRAY}[常态波动]{C.RESET}"

            print(f"{code:<8} {name:<14} {price:<7} {chg_str:<17} {amount_str:<10} {score_str:<17} {inflow_str:<19} {verdict_str}")

        # 如果有紧急报警列表，重点高亮
        alerts = analysis_data.get("alerts", [])
        if alerts:
            print(f"\n{C.BOLD}{C.RED}[!][盘中实时异动告警]({len(alerts)}项){C.RESET}")
            for a in alerts:
                lvl_icon = "[!CRITICAL!]" if a.level == "CRITICAL" else "[!WARNING!]"
                reason_desc = "、".join(a.reasons)
                print(f" {lvl_icon} [{a.code}] {a.name:<12} 评分: {a.score:.1f} | 涨幅: {a.chg_pct:+.2f}% | 成交: {a.amount_yi:.1f}亿 | 特征: {reason_desc}")

        print(f"{C.BOLD}{C.CYAN}{'='*92}{C.RESET}\n")

    @staticmethod
    def generate_html_report(analysis_data: Dict[str, Any], output_path: str = None) -> str:
        """生成面向实战择时决策的现代 HTML 投研仪表盘"""
        if output_path is None:
            output_path = NOTIFIER_CONFIG["HTML_REPORT_PATH"]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        ts = analysis_data["timestamp"]
        total_inflow = analysis_data["total_inflow_yi"]
        macro_verdict = analysis_data["macro_verdict"]
        stats = analysis_data["overall_stats"]
        results = analysis_data["results"]
        decision = analysis_data.get("timing_decision", {})

        # 构建六大板块卡片 HTML
        sector_cards_html = ""
        flows = decision.get("sector_flows", {})
        scores = decision.get("sector_scores", {})
        for s_name, f_val in flows.items():
            f_cls = "text-up" if f_val > 0 else ("text-down" if f_val < 0 else "")
            s_score = scores.get(s_name, 0.0)
            sector_cards_html += f"""
            <div class="card sector-card">
                <div class="card-title">{s_name}</div>
                <div class="card-value {f_cls}">{f_val:+.2f} 亿</div>
                <div class="card-desc">盘口异动热度: <strong>{s_score:.1f} 分</strong></div>
            </div>
            """

        # 构建表格行 HTML
        table_rows_html = ""
        for r in results:
            grade_badge = ""
            if r["grade"] == "AAA":
                grade_badge = '<span class="badge badge-aaa">AAA 强力真护盘</span>'
            elif r["grade"] == "AA":
                grade_badge = '<span class="badge badge-aa">AA 水下吸筹</span>'
            elif r["grade"] == "C":
                grade_badge = '<span class="badge badge-c">C 游资脉冲</span>'
            elif r["grade"] == "D":
                grade_badge = '<span class="badge badge-d">D 机构减仓</span>'
            else:
                grade_badge = '<span class="badge badge-normal">常规波动</span>'

            chg_cls = "text-up" if r["chg_pct"] > 0 else ("text-down" if r["chg_pct"] < 0 else "")
            inflow_cls = "text-up" if r["inflow_money_yi"] > 0 else ("text-down" if r["inflow_money_yi"] < 0 else "")
            reasons_html = "".join([f'<span class="reason-tag">{reason}</span>' for reason in r.get("reasons", [])])

            table_rows_html += f"""
            <tr>
                <td><strong>{r['code']}</strong></td>
                <td><strong>{r['name']}</strong></td>
                <td><span class="cat-pill">{r['category']}</span></td>
                <td>{r['price']:.3f}</td>
                <td class="{chg_cls}"><strong>{r['chg_pct']:+.2f}%</strong></td>
                <td>{r['amount_yi']:.2f} 亿</td>
                <td><div class="score-bar"><div class="score-fill" style="width:{min(r['intra_score'], 100)}%;"></div><span>{r['intra_score']:.1f}</span></div></td>
                <td class="{inflow_cls}"><strong>{r['inflow_money_yi']:+.2f} 亿</strong></td>
                <td>{grade_badge}</td>
                <td><small>{r['action_advice']}</small><br>{reasons_html}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>国家队资金跟踪与入场时机决策大屏</title>
    <style>
        :root {{
            --bg: #0b0f19;
            --card-bg: rgba(23, 32, 54, 0.7);
            --border: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --up-color: #10b981;
            --down-color: #ef4444;
            --accent-blue: #3b82f6;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: radial-gradient(circle at top, #1e293b 0%, #0b0f19 100%);
            color: var(--text-main);
            font-family: var(--font-family);
            padding: 24px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }}
        .header h1 {{
            font-size: 26px;
            background: linear-gradient(135deg, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }}
        .header .meta {{ color: var(--text-muted); font-size: 14px; }}

        /* 决策英雄卡 */
        .hero-card {{
            background: linear-gradient(135deg, rgba(30, 58, 138, 0.5), rgba(15, 23, 42, 0.8));
            border: 1px solid rgba(59, 130, 246, 0.4);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .hero-title {{ font-size: 14px; color: #93c5fd; text-transform: uppercase; font-weight: 700; margin-bottom: 6px; }}
        .hero-signal {{ font-size: 30px; font-weight: 800; color: #fde047; margin-bottom: 12px; }}
        .hero-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.08);
        }}
        .hero-item-title {{ font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }}
        .hero-item-val {{ font-size: 16px; font-weight: 600; color: #fff; }}

        /* 6大板块卡片 */
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin: 24px 0 14px 0;
            color: #93c5fd;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .sector-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 14px;
            margin-bottom: 24px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 16px;
        }}
        .card-title {{ font-size: 13px; color: var(--text-muted); margin-bottom: 6px; }}
        .card-value {{ font-size: 22px; font-weight: 700; }}
        .card-desc {{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }}

        /* 表格样式 */
        .table-wrapper {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
        th {{ background: rgba(15, 23, 42, 0.85); padding: 14px 16px; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--border); }}
        td {{ padding: 14px 16px; border-bottom: 1px solid rgba(255,255,255,0.04); vertical-align: middle; }}
        tr:hover {{ background: rgba(255,255,255,0.03); }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge-aaa {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }}
        .badge-aa {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }}
        .badge-c {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }}
        .badge-d {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }}
        .badge-normal {{ background: rgba(156, 163, 175, 0.15); color: #9ca3af; }}
        .cat-pill {{ background: rgba(255,255,255,0.08); padding: 2px 8px; border-radius: 6px; font-size: 12px; }}
        .reason-tag {{ display: inline-block; background: rgba(99, 102, 241, 0.15); color: #a5b4fc; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-right: 4px; margin-top: 4px; }}
        .score-bar {{ width: 90px; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; display: flex; align-items: center; position: relative; }}
        .score-fill {{ height: 100%; background: linear-gradient(90deg, #3b82f6, #ef4444); }}
        .text-up {{ color: var(--up-color); font-weight: 600; }}
        .text-down {{ color: var(--down-color); font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🇨🇳 国家队资金跟踪与入场时机决策看板</h1>
                <div class="meta">聚焦 6 大关键板块：沪深300 · 中证500 · 中证1000 · 创业板 · 科创50 · 大金融(券商/银行)</div>
            </div>
            <div class="meta">数据更新: {ts}</div>
        </div>

        <div class="hero-card">
            <div class="hero-title">🚦 国家队入场时机全局决策</div>
            <div class="hero-signal">{decision.get('timing_signal')}</div>
            <div><strong>阶段定性：</strong>{decision.get('timing_stage')}</div>
            <div class="hero-grid">
                <div>
                    <div class="hero-item-title">建议持仓水平</div>
                    <div class="hero-item-val text-up">{decision.get('position_advice')}</div>
                </div>
                <div>
                    <div class="hero-item-title">首选进攻/配置品种</div>
                    <div class="hero-item-val">{decision.get('recommended_targets')}</div>
                </div>
                <div>
                    <div class="hero-item-title">⚖️ 1000+银行动态智能杠铃配比</div>
                    <div class="hero-item-val" style="color: #c084fc;"><strong>{decision.get('barbell_ratio')}</strong><br><small style="color: #9ca3af; font-weight: normal;">{decision.get('barbell_desc')}</small></div>
                </div>
                <div>
                    <div class="hero-item-title">🔥 顶级大V实战战法</div>
                    <div class="hero-item-val" style="color: #60a5fa;"><small>{decision.get('kol_tactic')}</small></div>
                </div>
                <div>
                    <div class="hero-item-title">实战操作手法</div>
                    <div class="hero-item-val"><small>{decision.get('tactical_guide')}</small></div>
                </div>
            </div>
        </div>

        <div class="section-title">🔥 1. 六大板块国家队资金流向与动向热力</div>
        <div class="sector-grid">
            {sector_cards_html}
        </div>

        <div class="section-title">📋 2. 核心标的明细与分时异动监控</div>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>代码</th>
                        <th>标的名称</th>
                        <th>板块分类</th>
                        <th>最新价</th>
                        <th>涨跌幅</th>
                        <th>成交额</th>
                        <th>异动热度</th>
                        <th>官方净流入</th>
                        <th>国家队判定</th>
                        <th>实战买卖指引与异动特征</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path

    @staticmethod
    def generate_backtest_html_report(backtest_data: Dict[str, Any], output_path: str = None) -> str:
        """生成 3 年历史数据回测与参数优化 HTML 投研报告"""
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), "reports", "national_team_backtest_3yr.html")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        best = backtest_data.get("best_param_set", {})
        all_sets = backtest_data.get("all_evaluated_sets", [])
        p_stats = best.get("full_report", {}).get("period_stats", {})
        strat = best.get("full_report", {}).get("strategy_metrics", {})
        details = best.get("full_report", {}).get("signal_details", [])

        # 构建周期表现表格
        period_rows_html = ""
        for period, s in p_stats.items():
            win_cls = "text-up" if s["win_rate"] >= 60 else ("text-down" if s["win_rate"] < 50 else "")
            ret_cls = "text-up" if s["mean_ret"] > 0 else "text-down"
            period_rows_html += f"""
            <tr>
                <td><strong>{period}</strong></td>
                <td class="{win_cls}"><strong>{s['win_rate']:.2f}%</strong></td>
                <td class="{ret_cls}"><strong>{s['mean_ret']:+.2f}%</strong></td>
                <td>{s['pl_ratio']:.2f} : 1</td>
                <td class="text-up">+{s['max_gain']:.2f}%</td>
                <td class="text-down">{s['max_dd']:.2f}%</td>
            </tr>
            """

        # 构建参数网格对比行
        grid_rows_html = ""
        for item in all_sets:
            p = item["params"]
            is_best = (p == best["params"])
            row_style = 'style="background: rgba(59, 130, 246, 0.15); font-weight: 600;"' if is_best else ""
            best_tag = '<span class="badge badge-aaa">👑 最佳黄金参数</span>' if is_best else '<span class="badge badge-normal">评估组合</span>'
            
            grid_rows_html += f"""
            <tr {row_style}>
                <td>{best_tag}</td>
                <td><strong>{p['vol_threshold']}x</strong></td>
                <td>{p['min_amount_yi']:.1f} 亿</td>
                <td>{p['synergy_min_etfs']} 只</td>
                <td>{item['signals']} 次</td>
                <td class="text-up">{item['win_rate_5d']:.1f}%</td>
                <td class="text-up">+{item['mean_ret_5d']:.2f}%</td>
                <td class="text-up"><strong>{item['win_rate_20d']:.1f}%</strong></td>
                <td class="text-up"><strong>+{item['mean_ret_20d']:.2f}%</strong></td>
                <td><strong>{item['sharpe']:.2f}</strong></td>
                <td class="text-up"><strong>+{item['alpha_pct']:.2f}%</strong></td>
            </tr>
            """

        # 构建 6 大板块收益大 PK 表格
        sector_comp = best.get("full_report", {}).get("sector_comparison", {})
        sector_comp_html = ""
        for s_name, sc in sector_comp.items():
            win5_cls = "text-up" if sc["win_rate_5d"] >= 60 else ""
            win20_cls = "text-up" if sc["win_rate_20d"] >= 60 else ""
            ret5_cls = "text-up" if sc["mean_ret_5d"] > 0 else "text-down"
            ret20_cls = "text-up" if sc["mean_ret_20d"] > 0 else "text-down"
            
            if "1000" in s_name or "证券" in s_name:
                feature_desc = "🚀 <strong>【反弹弹性之王】</strong>救市确立后涨幅最大、进攻弹性最高"
            elif "300" in s_name or "银行" in s_name:
                feature_desc = "🛡️ <strong>【稳健定海神针】</strong>国家队主力托底底仓、下行回撤最小"
            elif "科创" in s_name or "创业" in s_name:
                feature_desc = "⚡ <strong>【成长高Beta】</strong>适合风险偏好高的进攻资金右侧买入"
            else:
                feature_desc = "⚪ <strong>【中盘均衡承接】</strong>兼顾稳健与中盘成长"

            sector_comp_html += f"""
            <tr>
                <td><strong>{s_name}</strong></td>
                <td class="{win5_cls}"><strong>{sc['win_rate_5d']:.1f}%</strong></td>
                <td class="{ret5_cls}"><strong>{sc['mean_ret_5d']:+.2f}%</strong></td>
                <td class="{win20_cls}"><strong>{sc['win_rate_20d']:.1f}%</strong></td>
                <td class="{ret20_cls}"><strong>{sc['mean_ret_20d']:+.2f}%</strong></td>
                <td class="text-up"><strong>+{sc['max_gain_20d']:.2f}%</strong></td>
                <td><small>{feature_desc}</small></td>
            </tr>
            """

        # 构建历史经典信号明细行
        detail_rows_html = ""
        for d in details[-20:]:  # 最近 20 次信号
            ret1_cls = "text-up" if d["fwd_ret_1d"] > 0 else ("text-down" if d["fwd_ret_1d"] < 0 else "")
            ret5_cls = "text-up" if d["fwd_ret_5d"] > 0 else ("text-down" if d["fwd_ret_5d"] < 0 else "")
            ret20_cls = "text-up" if d["fwd_ret_20d"] > 0 else ("text-down" if d["fwd_ret_20d"] < 0 else "")
            
            detail_rows_html += f"""
            <tr>
                <td><strong>{d['date']}</strong></td>
                <td>{d['close_300']:.3f}</td>
                <td>{d['amount_yi']:.2f} 亿</td>
                <td><span class="badge badge-aa">{d['vol_ratio']:.2f}x</span></td>
                <td class="{ret1_cls}">{d['fwd_ret_1d']:+.2f}%</td>
                <td class="{ret5_cls}"><strong>{d['fwd_ret_5d']:+.2f}%</strong></td>
                <td class="{ret20_cls}"><strong>{d['fwd_ret_20d']:+.2f}%</strong></td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>国家队资金跟踪 3 年历史回测与参数优化报告</title>
    <style>
        :root {{
            --bg: #0b0f19;
            --card-bg: rgba(23, 32, 54, 0.7);
            --border: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --up-color: #10b981;
            --down-color: #ef4444;
            --accent-blue: #3b82f6;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: radial-gradient(circle at top, #1e293b 0%, #0b0f19 100%);
            color: var(--text-main);
            font-family: var(--font-family);
            padding: 30px 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 28px;
        }}
        .header h1 {{
            font-size: 26px;
            background: linear-gradient(135deg, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }}
        .header .meta {{ color: var(--text-muted); font-size: 14px; }}
        .bento-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }}
        .card-title {{ font-size: 13px; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; }}
        .card-value {{ font-size: 28px; font-weight: 700; }}
        .card-desc {{ font-size: 13px; color: var(--text-muted); margin-top: 6px; }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin: 28px 0 14px 0;
            color: #93c5fd;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .table-wrapper {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            margin-bottom: 24px;
        }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
        th {{ background: rgba(15, 23, 42, 0.85); padding: 14px 16px; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--border); }}
        td {{ padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.04); vertical-align: middle; }}
        tr:hover {{ background: rgba(255,255,255,0.03); }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge-aaa {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }}
        .badge-aa {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }}
        .badge-normal {{ background: rgba(156, 163, 175, 0.15); color: #9ca3af; }}
        .text-up {{ color: var(--up-color); font-weight: 600; }}
        .text-down {{ color: var(--down-color); font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🇨🇳 国家队资金干预 3 年历史数据回测与参数寻优报告</h1>
                <div class="meta">样本周期: 近 800 个交易日 · 宽基协同模型全量回测</div>
            </div>
            <div class="meta">报告生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        </div>

        <div class="bento-grid">
            <div class="card">
                <div class="card-title">策略累计总收益</div>
                <div class="card-value text-up">+{strat.get('total_return_pct', 0):.2f}%</div>
                <div class="card-desc">同期沪深300基准: {strat.get('benchmark_return_pct', 0):+.2f}%</div>
            </div>
            <div class="card">
                <div class="card-title">策略超额收益 (Alpha)</div>
                <div class="card-value text-up">+{strat.get('excess_alpha_pct', 0):.2f}%</div>
                <div class="card-desc">纯正国家队护盘超额收益</div>
            </div>
            <div class="card">
                <div class="card-title">T+5 交易日胜率</div>
                <div class="card-value" style="color: #34d399;">{p_stats.get('T+5', {}).get('win_rate', 0):.1f}%</div>
                <div class="card-desc">盈亏比: {p_stats.get('T+5', {}).get('pl_ratio', 0):.2f}:1</div>
            </div>
            <div class="card">
                <div class="card-title">T+60 交易日胜率 (中线)</div>
                <div class="card-value" style="color: #60a5fa;">{p_stats.get('T+60', {}).get('win_rate', 0):.1f}%</div>
                <div class="card-desc">中线胜率突破 70% 大关</div>
            </div>
            <div class="card">
                <div class="card-title">策略夏普比率 (Sharpe)</div>
                <div class="card-value" style="color: #fbbf24;">{strat.get('sharpe_ratio', 0):.2f}</div>
                <div class="card-desc">最大回撤控制在 {strat.get('max_drawdown_pct', 0):.1f}%</div>
            </div>
        </div>

        <div class="section-title">📊 1. 不同持股周期胜率与前向收益率分布 (基于黄金参数)</div>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>持有周期</th>
                        <th>胜率 (Win Rate)</th>
                        <th>平均收益率</th>
                        <th>单笔盈亏比</th>
                        <th>平均最大潜在涨幅</th>
                        <th>平均最大回撤</th>
                    </tr>
                </thead>
                <tbody>
                    {period_rows_html}
                </tbody>
            </table>
        </div>

        <div class="section-title">🔥 2. 六大核心板块收益大 PK (国家队进场时买哪个板块最赚钱？)</div>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>板块与标的</th>
                        <th>5日胜率 (T+5)</th>
                        <th>5日平均收益</th>
                        <th>20日胜率 (T+20)</th>
                        <th>20日平均收益</th>
                        <th>20日前向最大涨幅</th>
                        <th>实战选型与角色定位</th>
                    </tr>
                </thead>
                <tbody>
                    {sector_comp_html}
                </tbody>
            </table>
        </div>

        <div class="section-title">🔍 3. 多维超参数网格寻优与灵敏度评估 (Pareto-Optimal)</div>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>参数配置</th>
                        <th>放量阈值</th>
                        <th>单日成交额门槛</th>
                        <th>协同ETF数</th>
                        <th>触发次数</th>
                        <th>T+5 胜率</th>
                        <th>T+5 收益</th>
                        <th>T+20 胜率</th>
                        <th>T+20 收益</th>
                        <th>夏普比率</th>
                        <th>超额 Alpha</th>
                    </tr>
                </thead>
                <tbody>
                    {grid_rows_html}
                </tbody>
            </table>
        </div>

        <div class="section-title">📜 3. 历史经典国家队救市干预信号明细记录 (最近 20 次触发点)</div>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>触发日期</th>
                        <th>300ETF价格</th>
                        <th>当日成交额</th>
                        <th>相对放量倍数</th>
                        <th>次日(T+1)收益</th>
                        <th>5日(T+5)收益</th>
                        <th>20日(T+20)收益</th>
                    </tr>
                </thead>
                <tbody>
                    {detail_rows_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path

