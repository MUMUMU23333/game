# -*- coding: utf-8 -*-
"""
================================================================================
终极神王体 · 70矛主板种业神皇版 早盘 09:26 决策雷达调度器 (本地双保险引擎)
================================================================================
触发时间: 每个交易日北京时间 09:26:00 准点触发
核心职责:
  1. 集合竞价 09:25:00 撮合结束后，精准提取官方开盘价与竞价量能；
  2. 诊断昨日挂起买单的 4 类集合竞价开盘形态，提供【方案 B 次日开盘买入实操指引卡】；
  3. 监测昨日持仓标的隔夜浮盈浮亏与 70 矛全域早盘高开异动 TOP 5；
  4. 留足 4 分钟从容决策时间 (09:26 ~ 09:30)，准点推送企业微信。
================================================================================
"""
import os
import sys
import time
import subprocess
from datetime import datetime

# 修复 Windows 控制台编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def run_script(script_path, args=None):
    full_path = os.path.join(BASE_DIR, script_path)
    cmd = [sys.executable, full_path]
    if args:
        cmd.extend(args)
    log(f"🚀 正在触发早盘策略: {script_path} ...")
    start_t = time.time()
    try:
        res = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=90,
            encoding='utf-8',
            errors='replace'
        )
        cost_s = time.time() - start_t
        if res.returncode == 0:
            log(f"✅ {script_path} 早盘雷达执行完成并成功推送！(耗时: {cost_s:.1f}s)")
            if res.stdout:
                # 打印最后几行摘要
                lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
                for l in lines[-4:]:
                    log(f"   [输出] {l}")
            return True, cost_s
        else:
            log(f"⚠️ {script_path} 执行返回警告 (耗时: {cost_s:.1f}s):\n{res.stderr[:300]}")
            return False, cost_s
    except subprocess.TimeoutExpired:
        cost_s = time.time() - start_t
        log(f"⏳ {script_path} 执行超时 (超过 90 秒)")
        return False, cost_s
    except Exception as e:
        cost_s = time.time() - start_t
        log(f"❌ {script_path} 异常: {e}")
        return False, cost_s

def main():
    # 🛑 交易日休市熔断守卫：非交易日不运行、不计算、不推送
    try:
        from trade_day_guard import guard_and_exit_if_not_trade_day
        guard_and_exit_if_not_trade_day("终极神王体 09:26 早盘决策雷达")
    except Exception as e:
        log(f"⚠️ [交易日守卫警告] {e}")

    log("================================================================================")
    log("🌅 开始执行【终极神王体 · 苍穹七十矛神皇版】早盘 09:26 开盘态势决策雷达 (本地引擎)...")
    log("================================================================================")
    
    tasks = [
        ("终极神王体 · 70矛早盘雷达", "godking_ultimate_notifier.py", ["--morning", "--push"]),
        ("科创-银行轮动 (V5.9 Apex-Master)", "chinext_bank_strategy_notifier.py", ["--push"]),
    ]
    
    results = []
    for name, path, args in tasks:
        success, cost = run_script(path, args)
        results.append((name, success, cost))
    
    log("--------------------------------------------------------------------------------")
    log("📊 早盘策略执行汇总:")
    for name, success, cost in results:
        status_icon = "✅ 成功" if success else "❌ 异常"
        log(f"  - {name:<25}: {status_icon} (耗时: {cost:.1f}s)")
    log("================================================================================")
    log("🎉 早盘 09:26 态势速查卡已全部准点推送完毕！")

if __name__ == "__main__":
    main()
