"""
国家队监控系统一键启动脚本
直接在量化策略根目录运行:
    python run_national_team_tracker.py
    python run_national_team_tracker.py --mode realtime
    python run_national_team_tracker.py --mode audit
"""

import os
import sys

# 将当前目录加入系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from national_team_tracker.run_monitor import main

if __name__ == "__main__":
    main()
