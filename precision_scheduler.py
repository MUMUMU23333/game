# -*- coding: utf-8 -*-
"""
================================================================================
精准时钟调度器：用于 GitHub Actions 提前预热与准点对齐发射
================================================================================
"""
import sys
import time
import argparse
from datetime import datetime, timezone, timedelta

# 修复 Windows 控制台编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def get_beijing_now():
    """获取当前精准北京时间 (UTC+8)"""
    utc_now = datetime.now(timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    return utc_now.astimezone(beijing_tz)

def wait_until_target_beijing_time(target_hour: int, target_minute: int, target_second: int = 0, max_wait_seconds: int = 2400):
    """
    等待直到指定的北京时间 (HH:MM:SS)
    - 若当前时间早于目标时间：执行精准倒计时 sleep
    - 若当前时间已过目标时间：立即返回执行，不作等待
    - 若等待时间超过 max_wait_seconds：安全退出等待，直接执行
    """
    now = get_beijing_now()
    target_dt = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)
    
    delta_seconds = (target_dt - now).total_seconds()
    
    if delta_seconds <= 0:
        print(f"⏰ [时钟调度] 当前北京时间 {now.strftime('%H:%M:%S')} 已到达/超过目标时间 {target_hour:02d}:{target_minute:02d}:{target_second:02d}，立即触发执行！")
        return
    
    if delta_seconds > max_wait_seconds:
        print(f"⚠️ [时钟调度] 距离目标时间还有 {delta_seconds/60:.1f} 分钟，超过最大安全等待上限 ({max_wait_seconds/60:.1f}分钟)，立即执行！")
        return
        
    print(f"⏳ [时钟调度] 提前预热就绪！当前北京时间: {now.strftime('%H:%M:%S.%f')[:-3]}")
    print(f"🎯 [时钟调度] 目标发射时间: {target_hour:02d}:{target_minute:02d}:{target_second:02d} (需精准等待 {delta_seconds:.1f} 秒)")
    
    # 倒计时等待（大块 sleep + 毫秒微调）
    while True:
        curr_now = get_beijing_now()
        remain = (target_dt - curr_now).total_seconds()
        if remain <= 0.05:  # 提前 50ms 唤醒就绪
            break
        if remain > 10:
            time.sleep(remain - 5)
        elif remain > 1:
            time.sleep(0.5)
        else:
            time.sleep(0.01)
            
    final_now = get_beijing_now()
    print(f"🚀 [时钟调度] 倒计时结束！当前精准时间: {final_now.strftime('%H:%M:%S.%f')[:-3]} ➔ 准时发射！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Precision Beijing Time Scheduler")
    parser.add_argument("--target", type=str, default="14:48", help="目标北京时间 HH:MM (例如 14:48)")
    parser.add_argument("--now", action="store_true", help="跳过等待立即执行")
    args = parser.parse_args()

    if args.now:
        print("⏩ [时钟调度] 收到 --now 指令，跳过等待立即执行！")
        sys.exit(0)

    try:
        parts = args.target.split(":")
        th = int(parts[0])
        tm = int(parts[1])
        ts = int(parts[2]) if len(parts) > 2 else 0
        wait_until_target_beijing_time(th, tm, ts)
    except Exception as e:
        print(f"⚠️ [时钟调度] 解析目标时间失败: {e}，默认立即执行！")
