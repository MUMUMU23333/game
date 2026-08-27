# -*- coding: utf-8 -*-
"""
================================================================================
量化策略全天候全自动执行与企业微信推送总调度器 (本地双保险引擎)
================================================================================
"""
import os
import sys
import time
import subprocess
from datetime import datetime

# 修复编码
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
    log(f"🚀 正在触发策略: {script_path} ...")
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
            log(f"✅ {script_path} 执行完成并成功推送！(耗时: {cost_s:.1f}s)")
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
    log("================================================================================")
    log("🏛️ 开始执行全量量化策略 14:48 尾盘黄金决策巡检 (本地双保险引擎)...")
    log("================================================================================")
    
    tasks = [
        ("五福 5.2 动量策略", os.path.join("quant_strategies", "wufu_5_2", "wufu_5_2_local_bot.py"), ["--force"]),
        ("七星量化动量策略", os.path.join("quant_strategies", "seven_stars", "local_etf_quant_bot.py"), ["--now"]),
        ("科创-银行轮动 (DTB-Apex)", "chinext_bank_strategy_notifier.py", ["--push"]),
        ("场外公募基金轮动 (006503)", "fund_rotation_notifier.py", [])
    ]
    
    results = []
    for name, path, args in tasks:
        success, cost = run_script(path, args)
        results.append((name, success, cost))
    
    log("--------------------------------------------------------------------------------")
    log("📊 全量策略执行汇总报告:")
    for name, success, cost in results:
        status_icon = "✅ 成功" if success else "❌ 异常"
        log(f"  - {name:<25}: {status_icon} (耗时: {cost:.1f}s)")
    log("================================================================================")
    log("🎉 全量策略巡检与决策推送完毕！")

if __name__ == "__main__":
    main()
