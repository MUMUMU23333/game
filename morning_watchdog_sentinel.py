# -*- coding: utf-8 -*-
"""
================================================================================
👑 早盘 09:29 看门狗守望哨兵 (Dead Man's Switch Watchdog)
================================================================================
职责:
  每个交易日北京时间 09:29:00 准点巡检。
  检测 09:26:00 主调度器是否已成功发出今日早盘决策卡。
  若检测到任何策略尚未推送（云端排队延迟 / 本地进程受阻 / 网络抖动），
  看门狗哨兵将以第一优先级毫秒级强行接管、立即补漏并向企微发出自愈告警！
================================================================================
"""
import os
import sys
import json
import subprocess
from datetime import datetime

# 修复编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(CURRENT_FILE_DIR, "godking_ultimate_notifier.py")):
    REPO_DIR = CURRENT_FILE_DIR
else:
    DEFAULT_REPO = r"C:\Users\Administrator\Desktop\量化策略源代码"
    if os.path.exists(os.path.join(DEFAULT_REPO, "godking_ultimate_notifier.py")):
        REPO_DIR = DEFAULT_REPO
    else:
        REPO_DIR = CURRENT_FILE_DIR

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [Watchdog] {msg}")

def is_today_pushed(cache_file):
    if not os.path.exists(cache_file):
        return False
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            ts = data.get('timestamp', '')
            today_str = datetime.now().strftime('%Y-%m-%d')
            return ts.startswith(today_str)
    except Exception as e:
        log(f"读取缓存文件 {cache_file} 失败: {e}")
        return False

def trigger_emergency_push(script_name, args):
    log(f"🚨 触发紧急自愈补偿: {script_name} {' '.join(args)} ...")
    cmd = [sys.executable, os.path.join(REPO_DIR, script_name)] + args
    try:
        res = subprocess.run(
            cmd,
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=90,
            encoding='utf-8',
            errors='replace'
        )
        if res.returncode == 0:
            log(f"✅ 紧急补偿成功: {script_name}")
            return True
        else:
            log(f"❌ 紧急补偿异常: {script_name}, 错误: {res.stderr[:200]}")
            return False
    except Exception as e:
        log(f"❌ 运行异常: {script_name}, {e}")
        return False

def run_watchdog():
    # 1. 交易日熔断检测
    try:
        sys.path.insert(0, REPO_DIR)
        from trade_day_guard import is_trade_day
        if not is_trade_day():
            log("今日非交易日，看门狗守望哨兵休眠。")
            return
    except Exception:
        pass

    log("=" * 70)
    log(f"🐕 开始执行早盘 09:29 看门狗健康巡检 (Dead Man's Switch)...")
    log(f"📁 策略工作区: {REPO_DIR}")
    log("=" * 70)

    godking_cache = os.path.join(REPO_DIR, ".godking_ultimate_morning_cache.json")
    chinext_cache = os.path.join(REPO_DIR, ".chinext_bank_push_cache.json")

    # 检查神王体早盘
    godking_ok = is_today_pushed(godking_cache)
    # 检查科创-银行早盘
    chinext_ok = is_today_pushed(chinext_cache)

    missing_tasks = []
    if not godking_ok:
        log("⚠️ 警报: 检测到【终极神王体 · 89矛早盘雷达】今日尚未完成推送！")
        missing_tasks.append(("godking_ultimate_notifier.py", ["--morning", "--push", "--force"]))
    else:
        log("✅ 巡检通过: 【终极神王体 · 89矛早盘雷达】已成功交付。")

    if not chinext_ok:
        log("⚠️ 警报: 检测到【科创-银行轮动 (V5.9 Apex-Master)】今日尚未完成推送！")
        missing_tasks.append(("chinext_bank_strategy_notifier.py", ["--push", "--force"]))
    else:
        log("✅ 巡检通过: 【科创-银行轮动 (V5.9 Apex-Master)】已成功交付。")

    if not missing_tasks:
        log("🎉 全量早盘策略健康巡检 100% 达标，主调度器表现完美，无需介入！")
        log("=" * 70)
        return

    # 存在缺失任务，启动紧急自愈介入
    log(f"🚨 启动紧急自愈程序，共有 {len(missing_tasks)} 项任务需要即刻补漏...")
    for script, args in missing_tasks:
        trigger_emergency_push(script, args)

    log("🏁 看门狗自愈补偿执行完毕。")
    log("=" * 70)

if __name__ == "__main__":
    run_watchdog()
