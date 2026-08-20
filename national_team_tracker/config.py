"""
系统配置模块：标的池、异动阈值与预警参数配置
"""

import os
from typing import Dict, List

# ==========================================
# 1. 核心监控标的池 (6大关键板块：沪深300/中证500/中证1000/创业板/科创50/大金融)
# ==========================================
ETF_UNIVERSE: Dict[str, Dict[str, str]] = {
    # --- 1. 沪深300 主力军团 (国家队护盘第一核心) ---
    "510300": {"name": "华泰柏瑞沪深300ETF", "market": "SH", "category": "沪深300", "weight": 1.0},
    "510310": {"name": "易方达沪深300ETF",   "market": "SH", "category": "沪深300", "weight": 0.9},
    "159919": {"name": "嘉实沪深300ETF",     "market": "SZ", "category": "沪深300", "weight": 0.8},

    # --- 2. 中证500 中盘中坚 (流动性承接) ---
    "510500": {"name": "南方中证500ETF",     "market": "SH", "category": "中证500",  "weight": 0.9},

    # --- 3. 中证1000 小盘弹性 (微盘股/流动性救急) ---
    "512100": {"name": "南方中证1000ETF",    "market": "SH", "category": "中证1000", "weight": 0.9},

    # --- 4. 创业板 核心成长 ---
    "159915": {"name": "易方达创业板ETF",     "market": "SZ", "category": "创业板",   "weight": 0.8},

    # --- 5. 科创50 硬科技前沿 ---
    "588000": {"name": "华夏科创50ETF",      "market": "SH", "category": "科创50",   "weight": 0.8},

    # --- 6. 大金融/证券/银行 (救市拉升情绪与高股息底仓) ---
    "512880": {"name": "国泰证券ETF",         "market": "SH", "category": "大金融(证券)", "weight": 0.9},
    "512800": {"name": "华宝银行ETF",         "market": "SH", "category": "大金融(银行)", "weight": 0.8},
    "510230": {"name": "国泰金融ETF",         "market": "SH", "category": "大金融(综合)", "weight": 0.8},
}

# ==========================================
# 2. T+0 盘中异动监测阈值配置 (基于 3 年历史回测寻优更新)
# ==========================================
INTRADAY_CONFIG = {
    # 扫描间隔 (秒)
    "SCAN_INTERVAL_SEC": 15,
    
    # 分钟级爆量倍数阈值 (回测寻优最佳: 1.8x ~ 2.2x 兼顾高胜率与灵敏度)
    "VOLUME_BURST_RATIO": 2.0,
    
    # 瞬间脉冲拉升阈值 (3分钟内价格上涨幅度 >= 0.4%)
    "PULSE_PRICE_RISE_PCT": 0.4,
    
    # 尾盘防守关键时间段 (14:00 - 15:00) 敏感度倍率提升
    "TAIL_HOUR_START": "14:00",
    "TAIL_HOUR_SENSITIVITY": 1.25,
    
    # 单笔大单预警阈值 (万元)
    "LARGE_ORDER_THRESHOLD_WAN": 2500,
    
    # 综合异动评分达到多少触发红色预警 (0 - 100)
    "ALERT_SCORE_THRESHOLD": 60,
}

# ==========================================
# 3. T+1 官方份额审计参数 (基于 3 年历史回测寻优更新)
# ==========================================
SHARE_AUDIT_CONFIG = {
    # 单日真金白银救市认定门槛 (单只 ETF 净流入金额，单位：亿元)
    "HEAVY_INFLOW_THRESHOLD_YI": 10.0,
    
    # 中度净流入门槛 (单位：亿元)
    "MEDIUM_INFLOW_THRESHOLD_YI": 2.5,
    
    # 全市场多宽基总净流入告警线 (单位：亿元)
    "TOTAL_INFLOW_ALERT_YI": 20.0,
    
    # 历史回溯天数
    "LOOKBACK_DAYS": 30,
}

# ==========================================
# 4. 通知与报告输出配置
# ==========================================
NOTIFIER_CONFIG = {
    # 是否启用控制台彩色表格打印
    "ENABLE_CONSOLE_LOG": True,
    
    # 是否自动生成 HTML 交互报告
    "ENABLE_HTML_REPORT": True,
    "HTML_REPORT_PATH": os.path.join(os.path.dirname(__file__), "reports", "national_team_report.html"),
    
    # Webhook 推送配置 (若需使用可填入 Webhook URL)
    "WEBHOOK_TYPE": None,  # 可选: "feishu", "dingtalk", "wecom", None
    "WEBHOOK_URL": "",
}
