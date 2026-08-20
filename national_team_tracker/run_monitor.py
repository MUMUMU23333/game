"""
国家队监控系统统一运行入口 (CLI Entrypoint)
支持模式：
  --mode scan      : 执行一次即时盘中扫描与双重确认审计 (默认)
  --mode realtime  : 启动盘中实时高频轮询雷达 (按秒级刷新)
  --mode audit     : 专门执行 T+1 官方交易所份额审计
  --mode report    : 生成并导出交互式 HTML 投研报告
"""

import sys
import time
import argparse
import webbrowser
from typing import Optional

from .fusion_engine import FusionEngine
from .notifier import Notifier
from .config import INTRADAY_CONFIG, NOTIFIER_CONFIG


def run_once_scan(generate_report: bool = True):
    """执行一次完整的市场扫描与判定"""
    engine = FusionEngine()
    analysis_data = engine.run_composite_analysis()
    
    # 控制台打印
    Notifier.print_console_dashboard(analysis_data)
    
    # 生成 HTML 报告
    if generate_report:
        report_file = Notifier.generate_html_report(analysis_data)
        print(f"📊 [报告已就绪] 交互式 HTML 看板已生成至: {report_file}")
    
    return analysis_data


def run_realtime_monitor(interval_sec: int = 15):
    """启动盘中实时轮询监控循环"""
    engine = FusionEngine()
    print(f"🚀 [国家队雷达启动] 实时高频异动扫描已激活 (轮询间隔: {interval_sec}秒, 按 Ctrl+C 退出)...")
    
    try:
        round_count = 1
        while True:
            print(f"\n--- 🔄 第 {round_count} 轮实时扫描 ---")
            analysis_data = engine.run_composite_analysis()
            Notifier.print_console_dashboard(analysis_data)
            
            # 定期更新 HTML 报告
            Notifier.generate_html_report(analysis_data)
            
            round_count += 1
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\n🛑 [国家队雷达] 用户手动终止监控。")


def run_official_audit():
    """专门审计 T+1 官方份额数据"""
    from .share_auditor import ShareAuditor
    auditor = ShareAuditor()
    audit_data = auditor.audit_today_inflow()
    
    print("\n=======================================================")
    print(f"🇨🇳 官方交易所宽基 ETF 份额与资金变动审计报告 ({audit_data['date']})")
    print("=======================================================")
    print(f"宏观态势: {audit_data['macro_verdict']}")
    print(f"总净流入: {audit_data['total_inflow_yi']:+.2f} 亿元\n")
    
    print(f"{'代码':<8} {'标的名称':<16} {'最新份额(亿份)':<14} {'份额变动':<10} {'净买入金额(亿)':<12} {'操作定性'}")
    print("-" * 75)
    for row in audit_data["details"]:
        print(f"{row['code']:<8} {row['name']:<14} {row['current_shares_yi']:>10.2f}     {row['delta_shares_yi']:>+8.2f}   {row['inflow_money_yi']:>+10.2f}    {row['action']}")
    print("=======================================================\n")


def run_backtest_mode(open_browser: bool = False):
    """执行 3 年历史数据全量回测与参数寻优"""
    from .backtest_engine import NationalTeamBacktestEngine
    engine = NationalTeamBacktestEngine(lookback_days=800)
    opt_results = engine.optimize_hyperparameters()
    
    # 渲染 HTML 回测报告
    report_file = Notifier.generate_backtest_html_report(opt_results)
    print(f"\n📈 [3年回测报告就绪] 交互式回测与参数寻优大屏已生成至: {report_file}")
    
    if open_browser:
        webbrowser.open(report_file)


def main():
    parser = argparse.ArgumentParser(description="国家队资金跟踪与盘中异动监控系统")
    parser.add_argument(
        "--mode",
        choices=["scan", "realtime", "audit", "report", "backtest"],
        default="scan",
        help="运行模式: scan(单次扫描), realtime(实时轮询), audit(官方份额审计), report(生成HTML报告), backtest(3年历史回测寻优)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=INTRADAY_CONFIG["SCAN_INTERVAL_SEC"],
        help="实时监控轮询间隔 (秒)"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="生成报告后是否自动在浏览器中打开"
    )

    args = parser.parse_args()

    if args.mode == "scan":
        data = run_once_scan(generate_report=True)
        if args.open:
            webbrowser.open(NOTIFIER_CONFIG["HTML_REPORT_PATH"])
    elif args.mode == "realtime":
        run_realtime_monitor(interval_sec=args.interval)
    elif args.mode == "audit":
        run_official_audit()
    elif args.mode == "report":
        data = run_once_scan(generate_report=True)
        webbrowser.open(NOTIFIER_CONFIG["HTML_REPORT_PATH"])
    elif args.mode == "backtest":
        run_backtest_mode(open_browser=args.open)


if __name__ == "__main__":
    main()
