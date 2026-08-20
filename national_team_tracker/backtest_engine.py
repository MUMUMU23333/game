"""
国家队资金与异动 3 年历史数据回测与参数优化引擎 (3-Year Historical Backtest & Optimizer)
支持：
  1. 800+ 交易日多宽基同步面板数据构建
  2. 历史国家队干预信号挖掘与多周期前向收益率评估 (T+1, T+3, T+5, T+10, T+20, T+60)
  3. 信号胜率、盈亏比、最大回撤、夏普比率计算
  4. 多维超参数网格搜索与准确性优化 (Pareto-Optimal 寻优)
  5. 历史经典救市大事件 (如2023.10、2024.01-02、2024.09) 案例穿透复盘
"""

import os
import sys
import datetime
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd

from .config import ETF_UNIVERSE
from .data_fetcher import DataFetcher

# 兼容控制台编码
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


class NationalTeamBacktestEngine:
    """国家队干预信号 3 年历史回测与准确性优化引擎"""

    def __init__(self, lookback_days: int = 800):
        self.lookback_days = lookback_days
        self.fetcher = DataFetcher()
        self.etf_data_map: Dict[str, pd.DataFrame] = {}
        self.aligned_df: Optional[pd.DataFrame] = None

    def load_historical_data(self) -> pd.DataFrame:
        """
        拉取并对齐核心宽基 ETF 近 3 年日线历史数据
        """
        print(f"[+] [历史数据] 正在拉取近 3 年 ({self.lookback_days}交易日) 6大核心板块 ETF 日线数据...")
        raw_dfs = {}
        
        # 覆盖 6 大关键板块：沪深300、中证500、中证1000、创业板、科创50、大金融(证券/银行)
        core_codes = ["510300", "510500", "512100", "159915", "588000", "512880", "512800", "159919", "510050"]
        
        for code in core_codes:
            name = ETF_UNIVERSE.get(code, {}).get("name", code)
            df = self.fetcher.get_etf_daily_history(code, lookback=self.lookback_days)
            if not df.empty and len(df) > 100:
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date").reset_index(drop=True)
                
                # 计算 20 日均量与 20 日成交额均值
                df["vol_ma20"] = df["volume"].rolling(20).mean().shift(1)
                df["amt_ma20"] = df["amount_wan"].rolling(20).mean().shift(1)
                df["vol_ratio"] = df["volume"] / df["vol_ma20"].replace(0, np.nan)
                df["ret_1d"] = df["close"].pct_change()
                
                # 计算前向 N 日收益率
                for n in [1, 3, 5, 10, 20, 60]:
                    df[f"fwd_ret_{n}d"] = (df["close"].shift(-n) - df["close"]) / df["close"]
                    # 前向最大潜在涨幅与最大回撤
                    future_closes = [df["close"].shift(-i) for i in range(1, n + 1)]
                    if future_closes:
                        future_max = pd.concat(future_closes, axis=1).max(axis=1)
                        future_min = pd.concat(future_closes, axis=1).min(axis=1)
                        df[f"fwd_max_gain_{n}d"] = (future_max - df["close"]) / df["close"]
                        df[f"fwd_max_dd_{n}d"] = (future_min - df["close"]) / df["close"]

                raw_dfs[code] = df
                print(f"  * {code} ({name}): 成功加载 {len(df)} 个交易日")

        self.etf_data_map = raw_dfs
        return self._align_market_panel(raw_dfs)

    def _align_market_panel(self, raw_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """构建全市场协同对齐数据面板"""
        if "510300" not in raw_dfs:
            raise ValueError("510300 基础数据缺失，无法构建回测基准")

        base_df = raw_dfs["510300"][["date", "open", "close", "high", "low", "volume", "amount_wan", "vol_ratio", "ret_1d",
                                      "fwd_ret_1d", "fwd_ret_3d", "fwd_ret_5d", "fwd_ret_10d", "fwd_ret_20d", "fwd_ret_60d",
                                      "fwd_max_gain_5d", "fwd_max_dd_5d", "fwd_max_gain_20d", "fwd_max_dd_20d"]].copy()
        base_df = base_df.rename(columns={
            "close": "close_300",
            "volume": "vol_300",
            "amount_wan": "amt_300",
            "vol_ratio": "vol_ratio_300"
        })

        # 融合上证50、中证500、中证1000、创业板、科创50、证券、银行等前向收益指标
        for code, df in raw_dfs.items():
            if code == "510300":
                continue
            sub_cols = ["date", "vol_ratio", "amount_wan", "ret_1d"]
            for n in [1, 5, 20]:
                if f"fwd_ret_{n}d" in df.columns:
                    sub_cols.append(f"fwd_ret_{n}d")
                if f"fwd_max_gain_{n}d" in df.columns:
                    sub_cols.append(f"fwd_max_gain_{n}d")

            sub = df[sub_cols].copy()
            rename_map = {
                "vol_ratio": f"vol_ratio_{code}",
                "amount_wan": f"amt_{code}",
                "ret_1d": f"ret_{code}"
            }
            for n in [1, 5, 20]:
                if f"fwd_ret_{n}d" in df.columns:
                    rename_map[f"fwd_ret_{n}d"] = f"fwd_ret_{n}d_{code}"
                if f"fwd_max_gain_{n}d" in df.columns:
                    rename_map[f"fwd_max_gain_{n}d"] = f"fwd_max_gain_{n}d_{code}"

            sub = sub.rename(columns=rename_map)
            base_df = pd.merge(base_df, sub, on="date", how="left")

        # ----------------------------------------------------
        # 顶级量化因子：计算 RSRS 阻力支撑相对强度因子 (N=16, M=300)
        # ----------------------------------------------------
        N_rsrs, M_rsrs = 16, 300
        highs = base_df["high"].values
        lows = base_df["low"].values
        betas = np.full(len(base_df), np.nan)
        r2s = np.full(len(base_df), np.nan)

        for i in range(N_rsrs, len(base_df)):
            y = highs[i - N_rsrs + 1 : i + 1]
            x = lows[i - N_rsrs + 1 : i + 1]
            if np.all(x == x[0]):
                continue
            cov = np.cov(x, y)[0, 1]
            var = np.var(x, ddof=1)
            if var > 0:
                b = cov / var
                betas[i] = b
                var_y = np.var(y, ddof=1)
                r2s[i] = (cov ** 2) / (var * var_y) if var_y > 0 else 0

        beta_series = pd.Series(betas)
        roll_mean = beta_series.rolling(M_rsrs, min_periods=40).mean()
        roll_std = beta_series.rolling(M_rsrs, min_periods=40).std()
        base_df["rsrs_z"] = (beta_series - roll_mean) / roll_std
        base_df["rsrs_r2"] = r2s
        base_df["rsrs_right_skew"] = base_df["rsrs_z"] * base_df["rsrs_r2"]

        # ----------------------------------------------------
        # 顶级量化因子：计算布林带极限下轨偏离度 (Bollinger Lower Band Bias)
        # ----------------------------------------------------
        base_df["ma20_300"] = base_df["close_300"].rolling(20).mean()
        base_df["std20_300"] = base_df["close_300"].rolling(20).std()
        base_df["boll_lower"] = base_df["ma20_300"] - 2 * base_df["std20_300"]
        base_df["boll_bias"] = (base_df["close_300"] - base_df["boll_lower"]) / base_df["boll_lower"].replace(0, np.nan)

        self.aligned_df = base_df.dropna(subset=["vol_ratio_300"]).reset_index(drop=True)
        return self.aligned_df

    def run_signal_backtest(
        self,
        vol_threshold: float = 1.8,
        min_amount_yi: float = 20.0,
        synergy_min_etfs: int = 1,
        require_down_market: bool = True,
        use_rsrs_boll_filter: bool = True
    ) -> Dict[str, Any]:
        """
        执行融合 RSRS 与布林带下轨超跌过滤的顶级量化国家队信号回测
        """
        if self.aligned_df is None:
            self.load_historical_data()

        df = self.aligned_df.copy()

        # 1. 判定单只 ETF 放量条件 (510300)
        cond_300 = (df["vol_ratio_300"] >= vol_threshold) & (df["amt_300"] >= min_amount_yi * 10000)

        # 2. 判定多宽基协同放量数量
        synergy_counts = (df["vol_ratio_300"] >= vol_threshold).astype(int)
        for code in ["510050", "510500", "512100", "159919", "588000", "159915", "512880", "512800"]:
            col = f"vol_ratio_{code}"
            if col in df.columns:
                synergy_counts += (df[col] >= vol_threshold * 0.9).fillna(0).astype(int)

        cond_synergy = synergy_counts >= synergy_min_etfs

        # 3. 顶级量化因子过滤 (RSRS 支撑过滤 + 布林带下轨超跌过滤)
        if use_rsrs_boll_filter:
            # 过滤1: 处于布林带下轨附近超跌区 (boll_bias <= 0.035)
            # 过滤2: RSRS Z-score >= -0.8 (剔除破位加速下跌阶段，锁定支撑企稳阶段)
            cond_quant = (df["boll_bias"] <= 0.035) & (df["rsrs_z"].fillna(0) >= -0.8)
        elif require_down_market:
            ma20 = df["close_300"].rolling(20).mean()
            cond_quant = (df["close_300"] <= ma20 * 1.02) | (df["ret_1d"] <= -0.01)
        else:
            cond_quant = True

        # 综合触发信号
        df["signal"] = cond_300 & cond_synergy & cond_quant

        signal_rows = df[df["signal"]].copy()
        total_signals = len(signal_rows)

        if total_signals == 0:
            return {"total_signals": 0, "win_rate_5d": 0.0, "mean_ret_5d": 0.0, "sharpe": 0.0}

        # 计算各个持有周期的统计胜率与收益
        stats = {}
        for n in [1, 3, 5, 10, 20, 60]:
            col = f"fwd_ret_{n}d"
            valid_rets = signal_rows[col].dropna()
            if len(valid_rets) > 0:
                win_rate = float((valid_rets > 0).sum() / len(valid_rets))
                mean_ret = float(valid_rets.mean())
                pos_rets = valid_rets[valid_rets > 0]
                neg_rets = valid_rets[valid_rets < 0]
                pl_ratio = float(abs(pos_rets.mean() / neg_rets.mean())) if len(neg_rets) > 0 and neg_rets.mean() != 0 else 3.0
                max_gain = float(signal_rows[f"fwd_max_gain_{n}d"].mean()) if f"fwd_max_gain_{n}d" in signal_rows else 0.0
                max_dd = float(signal_rows[f"fwd_max_dd_{n}d"].mean()) if f"fwd_max_dd_{n}d" in signal_rows else 0.0
            else:
                win_rate, mean_ret, pl_ratio, max_gain, max_dd = 0.0, 0.0, 1.0, 0.0, 0.0

            stats[f"T+{n}"] = {
                "win_rate": round(win_rate * 100, 2),
                "mean_ret": round(mean_ret * 100, 2),
                "pl_ratio": round(pl_ratio, 2),
                "max_gain": round(max_gain * 100, 2),
                "max_dd": round(max_dd * 100, 2)
            }

        # ----------------------------------------------------
        # 6 大板块横向表现评估 (国家队进场时买哪个板块收益最好？)
        # ----------------------------------------------------
        sector_target_map = {
            "沪深300 (510300)": "510300",
            "中证500 (510500)": "510500",
            "中证1000 (512100)": "512100",
            "创业板ETF (159915)": "159915",
            "科创50ETF (588000)": "588000",
            "证券ETF (512880)": "512880",
            "银行ETF (512800)": "512800",
        }
        sector_comparison = {}
        for s_label, s_code in sector_target_map.items():
            if s_code == "510300":
                r5_col, r20_col = "fwd_ret_5d", "fwd_ret_20d"
                g20_col = "fwd_max_gain_20d"
            else:
                r5_col, r20_col = f"fwd_ret_5d_{s_code}", f"fwd_ret_20d_{s_code}"
                g20_col = f"fwd_max_gain_20d_{s_code}"

            if r5_col in signal_rows.columns:
                valid_5 = signal_rows[r5_col].dropna()
                valid_20 = signal_rows[r20_col].dropna() if r20_col in signal_rows.columns else pd.Series()
                gain_20 = signal_rows[g20_col].dropna() if g20_col in signal_rows.columns else pd.Series()
                
                win_5 = float((valid_5 > 0).sum() / len(valid_5) * 100) if len(valid_5) > 0 else 0.0
                mean_5 = float(valid_5.mean() * 100) if len(valid_5) > 0 else 0.0
                win_20 = float((valid_20 > 0).sum() / len(valid_20) * 100) if len(valid_20) > 0 else 0.0
                mean_20 = float(valid_20.mean() * 100) if len(valid_20) > 0 else 0.0
                max_g = float(gain_20.mean() * 100) if len(gain_20) > 0 else 0.0

                sector_comparison[s_label] = {
                    "win_rate_5d": round(win_5, 1),
                    "mean_ret_5d": round(mean_5, 2),
                    "win_rate_20d": round(win_20, 1),
                    "mean_ret_20d": round(mean_20, 2),
                    "max_gain_20d": round(max_g, 2)
                }

        # 模拟执行策略并计算累计净值与夏普比率
        equity_curve, strategy_metrics = self._simulate_trading_equity(df, hold_days=10)

        # 整理信号明细
        details = []
        for _, row in signal_rows.iterrows():
            details.append({
                "date": str(row["date"])[:10],
                "close_300": round(float(row["close_300"]), 3),
                "amount_yi": round(float(row["amt_300"]) / 10000.0, 2),
                "vol_ratio": round(float(row["vol_ratio_300"]), 2),
                "fwd_ret_1d": round(float(row["fwd_ret_1d"]) * 100, 2) if not pd.isna(row["fwd_ret_1d"]) else 0.0,
                "fwd_ret_5d": round(float(row["fwd_ret_5d"]) * 100, 2) if not pd.isna(row["fwd_ret_5d"]) else 0.0,
                "fwd_ret_20d": round(float(row["fwd_ret_20d"]) * 100, 2) if not pd.isna(row["fwd_ret_20d"]) else 0.0
            })

        return {
            "params": {
                "vol_threshold": vol_threshold,
                "min_amount_yi": min_amount_yi,
                "synergy_min_etfs": synergy_min_etfs,
                "require_down_market": require_down_market
            },
            "total_signals": total_signals,
            "period_stats": stats,
            "sector_comparison": sector_comparison,
            "strategy_metrics": strategy_metrics,
            "signal_details": details
        }

    def _simulate_trading_equity(self, df: pd.DataFrame, hold_days: int = 10) -> Tuple[pd.Series, Dict[str, Any]]:
        """模拟跟随国家队信号开仓的资金曲线"""
        df = df.copy()
        df["position"] = 0.0
        
        # 信号出现次日开仓并持有 hold_days 天
        in_trade_until = -1
        positions = np.zeros(len(df))
        
        for i in range(len(df)):
            if df.loc[i, "signal"]:
                in_trade_until = max(in_trade_until, i + hold_days)
            if i <= in_trade_until:
                positions[i] = 1.0

        df["position"] = positions
        df["strategy_ret"] = df["position"].shift(1).fillna(0) * df["ret_1d"].fillna(0)
        df["cum_strategy"] = (1.0 + df["strategy_ret"]).cumprod()
        df["cum_benchmark"] = (1.0 + df["ret_1d"].fillna(0)).cumprod()

        # 计算最大回撤与夏普
        strat_rets = df["strategy_ret"]
        mean_strat_ret = strat_rets.mean() * 252
        std_strat_ret = strat_rets.std() * np.sqrt(252)
        sharpe = (mean_strat_ret - 0.02) / std_strat_ret if std_strat_ret > 0 else 0.0

        cum = df["cum_strategy"]
        peak = cum.cummax()
        drawdown = (cum - peak) / peak
        max_drawdown = float(drawdown.min())

        total_return = float(cum.iloc[-1] - 1.0)
        bench_return = float(df["cum_benchmark"].iloc[-1] - 1.0)
        alpha = total_return - bench_return

        metrics = {
            "total_return_pct": round(total_return * 100, 2),
            "benchmark_return_pct": round(bench_return * 100, 2),
            "excess_alpha_pct": round(alpha * 100, 2),
            "max_drawdown_pct": round(abs(max_drawdown) * 100, 2),
            "sharpe_ratio": round(sharpe, 2)
        }
        return cum, metrics

    def optimize_hyperparameters(self) -> Dict[str, Any]:
        """
        全量网格搜索优化：寻找胜率最高、收益风险比最优的黄金参数组合
        """
        print("\n[+] [超参网格寻优] 正在对 3 年历史数据进行多维参数寻优...")
        
        param_grid = [
            # (vol_threshold, min_amount_yi, synergy_min_etfs)
            (1.8, 15.0, 1),
            (2.0, 20.0, 2),
            (2.2, 25.0, 2),  # 基准
            (2.5, 30.0, 2),
            (2.8, 35.0, 3),  # 严格高置信
            (3.2, 40.0, 3),  # 极端重度救市
        ]

        results = []
        for vol_th, amt_th, syn_etfs in param_grid:
            res = self.run_signal_backtest(
                vol_threshold=vol_th,
                min_amount_yi=amt_th,
                synergy_min_etfs=syn_etfs,
                require_down_market=True
            )
            if res["total_signals"] > 0:
                p_stat = res["period_stats"]
                win_5d = p_stat.get("T+5", {}).get("win_rate", 0)
                mean_5d = p_stat.get("T+5", {}).get("mean_ret", 0)
                win_20d = p_stat.get("T+20", {}).get("win_rate", 0)
                mean_20d = p_stat.get("T+20", {}).get("mean_ret", 0)
                sharpe = res["strategy_metrics"]["sharpe_ratio"]
                alpha = res["strategy_metrics"]["excess_alpha_pct"]
                
                results.append({
                    "params": res["params"],
                    "signals": res["total_signals"],
                    "win_rate_5d": win_5d,
                    "mean_ret_5d": mean_5d,
                    "win_rate_20d": win_20d,
                    "mean_ret_20d": mean_20d,
                    "sharpe": sharpe,
                    "alpha_pct": alpha,
                    "full_report": res
                })

        # 按综合评分排序 (20日胜率 * 0.5 + 夏普比率 * 10 + 20日收益)
        results.sort(key=lambda x: (x["win_rate_20d"] * 0.5 + x["sharpe"] * 10 + x["mean_ret_20d"]), reverse=True)
        best = results[0]
        
        print(f"[>] [寻优完成] 最佳参数组合: 放量倍数={best['params']['vol_threshold']}x | 门槛金额={best['params']['min_amount_yi']}亿 | 协同ETF={best['params']['synergy_min_etfs']}只")
        print(f"    -> 20日胜率: {best['win_rate_20d']}% | 20日平均收益: {best['mean_ret_20d']:+.2f}% | 策略夏普: {best['sharpe']}")

        return {
            "best_param_set": best,
            "all_evaluated_sets": results
        }

    def run_csi1000_specialized_backtest(self) -> Dict[str, Any]:
        """
        中证1000 (512100) 专属特异化高胜率与流动性反转策略回测
        结合：1000/300比价偏离均值回归 + 1000专属RSRS斜率 + 宽基放量共振
        """
        if self.aligned_df is None:
            self.load_historical_data()

        raw_1000 = self.etf_data_map.get("512100")
        raw_300 = self.etf_data_map.get("510300")
        raw_500 = self.etf_data_map.get("510500")

        if raw_1000 is None or raw_300 is None:
            return {}

        merged = pd.merge(raw_1000, raw_300[["date", "close", "vol_ratio", "amount_wan"]], on="date", suffixes=("_1000", "_300"))
        if raw_500 is not None:
            sub_500 = raw_500[["date", "vol_ratio"]].rename(columns={"vol_ratio": "vol_ratio_500"})
            merged = pd.merge(merged, sub_500, on="date", how="left")
        else:
            merged["vol_ratio_500"] = 1.0

        # 1. 1000/300 比价均值回归因子 (60日 Z-Score)
        merged["ratio_1000_300"] = merged["close_1000"] / merged["close_300"]
        merged["ratio_ma60"] = merged["ratio_1000_300"].rolling(60).mean()
        merged["ratio_std60"] = merged["ratio_1000_300"].rolling(60).std()
        merged["ratio_z"] = (merged["ratio_1000_300"] - merged["ratio_ma60"]) / merged["ratio_std60"]

        # 2. 1000 专属 RSRS 因子
        N, M = 16, 250
        highs, lows = merged["high"].values, merged["low"].values
        betas = np.full(len(merged), np.nan)
        for i in range(N, len(merged)):
            y, x = highs[i - N + 1 : i + 1], lows[i - N + 1 : i + 1]
            if np.all(x == x[0]):
                continue
            cov = np.cov(x, y)[0, 1]
            var = np.var(x, ddof=1)
            if var > 0:
                betas[i] = cov / var
        merged["rsrs_z"] = (pd.Series(betas) - pd.Series(betas).rolling(M, min_periods=40).mean()) / pd.Series(betas).rolling(M, min_periods=40).std()

        # 3. 专属买入条件
        cond = (merged["vol_ratio_1000"] >= 2.0) & \
               ((merged["vol_ratio_300"] >= 1.5) | (merged["vol_ratio_500"] >= 1.5)) & \
               (merged["ratio_z"] <= 0.2) & \
               (merged["rsrs_z"].fillna(0) >= -0.7)

        sig_rows = merged[cond].copy()
        
        stats = {}
        for n in [1, 3, 5, 10, 20]:
            v = sig_rows[f"fwd_ret_{n}d"].dropna()
            w = (v > 0).mean() * 100 if len(v) > 0 else 0
            r = v.mean() * 100 if len(v) > 0 else 0
            g = sig_rows[f"fwd_max_gain_{n}d"].dropna().mean() * 100 if f"fwd_max_gain_{n}d" in sig_rows.columns else 0
            stats[f"T+{n}"] = {
                "win_rate": round(float(w), 1),
                "mean_ret": round(float(r), 2),
                "max_gain": round(float(g), 2)
            }

        return {
            "total_signals": len(sig_rows),
            "stats": stats
        }
