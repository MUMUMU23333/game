# -*- coding: utf-8 -*-
"""
================================================================================
量化策略全天候全自动执行与企业微信推送总调度器 (本地双保险引擎)
================================================================================
"""
import os
import sys
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
    try:
        res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='replace')
        if res.returncode == 0:
            log(f"✅ {script_path} 执行完成并成功推送！")
        else:
            log(f"⚠️ {script_path} 执行返回警告: {res.stderr[:200]}")
    except Exception as e:
        log(f"❌ {script_path} 异常: {e}")

def main():
    log("================================================================================")
    log("🏛️ 开始执行全量量化策略 14:48 尾盘黄金决策巡检...")
    log("================================================================================")
    
    # 1. 五福 5.2 动量策略 (尾盘强推)
    run_script(os.path.join("quant_strategies", "wufu_5_2", "wufu_5_2_local_bot.py"), ["--force"])
    
    # 2. 七星量化策略 (原版动量)
    run_script(os.path.join("quant_strategies", "seven_stars", "local_etf_quant_bot.py"), ["--now"])
    
    # 3. 科创-银行轮动策略 (DTB-Apex)
    run_script("chinext_bank_strategy_notifier.py", ["--push"])
    
    # 4. 场外公募基金轮动策略 (006503 / Apex V100)
    run_script("fund_rotation_notifier.py")
    
    log("🎉 全量策略执行与决策推送完毕！")

if __name__ == "__main__":
    main()
