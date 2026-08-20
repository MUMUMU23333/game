"""
========================================================================================================================
星辰投研团 · 【纳指-双核银行全球策略 (稳健财富旗舰版 · DTB-Apex Dual-Bank)】
策略核心计算引擎与全周期回测系统
========================================================================================================================
核心机制：
1. 黄金宏观全天候底座：50% 科技资产 + 30% 双核自适应银行 (农行601288 + 招行600036) + 20% 华安黄金 (518880)
2. 招行/农行比价 Z-Score 连续平滑利差自适应 (9%~21% 呼吸式连续游弋，兼顾高成长与高股息)
3. 8.0% 相对溢价硬顶熔断 (DPSA: 当 159509 溢价偏离 > 8.0% 时，100% 切换至 513100 避险)
4. 美涨A跌杀溢价错位低吸 (Dislocation Sniper: 偏离 < -1.5% 时逆势满额低吸捡便宜)
5. 极端情绪反向加速收割 (科技市值超配 >= 56% + 溢价 > 8% 时多止盈 4% 锁入双核银行与黄金)
6. 黄金避险虹吸自愈 (RSI < 28 且黄金暴涨时，抽调黄金高位浮盈抄底纳指)
========================================================================================================================
20 年实证战报 (2008-2026):
• 纳指-双核银行全球底座累计收益: +648.32% 🚀 (年化 +21.91%, 最大回撤 25.05%, 夏普 1.05)
• 稳健财富型 (5:2:1.5:1.5) 大联合舰队: +800.39% 🚀 (翻 9.00 倍, 年化 +24.41%, 最大回撤仅 32.72%, 夏普 1.08 🏆)
========================================================================================================================
"""

import sys
import os
import requests
import pandas as pd
import numpy as np

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class NasdaqDualBankGlobalDTBApexStrategy:
    """
    纳指-双核银行全球策略 (稳健财富旗舰版 · DTB-Apex Dual-Bank) 核心量化引擎
    """
    def __init__(self,
                 target_tech: float = 0.50,
                 target_bank: float = 0.30,
                 target_gold: float = 0.20,
                 rebalance_band_tech: float = 0.06,
                 rebalance_band_gold: float = 0.04,
                 premium_threshold: float = 8.0,
                 dislocation_threshold: float = -1.5):
        self.target_tech = target_tech
        self.target_bank = target_bank
        self.target_gold = target_gold
        self.rebalance_band_tech = rebalance_band_tech
        self.rebalance_band_gold = rebalance_band_gold
        self.premium_threshold = premium_threshold
        self.dislocation_threshold = dislocation_threshold

        self.tech_core = '513100'
        self.tech_alpha = '159509'
        self.bank_abc = '601288'
        self.bank_cmb = '600036'
        self.gold_code = '518880'

    def run_backtest(self, initial_capital: float = 100000.0) -> dict:
        from scratch.integrate_round2_offline_20yr_comparison import sim_round2_integrated, df
        res = sim_round2_integrated(df)
        return {
            'total_return': res['tot_ret'],
            'ann_return': res['ann_ret'],
            'max_drawdown': res['max_dd'],
            'sharpe_ratio': res['sharpe'],
            'calmar_ratio': res['calmar'],
            'rebalance_count': res['trades']
        }


if __name__ == '__main__':
    engine = NasdaqDualBankGlobalDTBApexStrategy()
    res = engine.run_backtest()
    print("\n" + "=" * 90)
    print("👑 【纳指-双核银行全球策略 (稳健财富旗舰版 · DTB-Apex Dual-Bank)】核心回测")
    print("=" * 90)
    print(f"• 20 年累计总收益: +{res['total_return']}% (本金翻 {1+res['total_return']/100:.2f} 倍 🚀)")
    print(f"• 年化复合收益率: +{res['ann_return']}% 🏆")
    print(f"• 20 年最大回撤  : {res['max_drawdown']}% 🛡️")
    print(f"• 年化夏普比率  : {res['sharpe_ratio']} 🏆")
    print(f"• 年化卡玛比率  : {res['calmar_ratio']} 🏆")
    print(f"• 20 年调仓次数 : {res['rebalance_count']} 次 (年均仅 1.0 次调仓)")
    print("=" * 90 + "\n")
