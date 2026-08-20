# China ETF Strategy Research & Continuous Optimization Skill v7.0

## 0. Mission

This Skill is a **continuous quantitative research engine** for China A-share broad-index ETF + sector ETF strategies, with the specific objective of harvesting tradable volatility while controlling drawdown, turnover, liquidity risk and overfitting.

It must NOT behave like a parameter optimizer whose goal is to find the highest historical CAGR.

The primary objective is:

> Find the simplest, most robust, risk-adjusted ETF strategy that survives unseen data, regime changes and realistic implementation costs.

The Skill must continuously compare the current **Champion** strategy against:
- the existing strategy;
- simple benchmark controls;
- multiple research strategy families;
- new Challenger variants.

Every research cycle ends with one of:
1. promote a Challenger to Champion;
2. reject it and record why;
3. retain the Champion unchanged because no Challenger is robustly superior.

---

# 1. Research philosophy

## 1.1 Do not claim there is a universal “best strategy”

Current research does not establish one universally superior strategy. Trend following, momentum, defensive/quality, value, multi-factor and adaptive allocation each have different regime exposures. AQR's current research continues to emphasize momentum, value, carry and defensive premia, while also warning that factor timing can lose its edge after implementation frictions. citehttps://www.aqr.com/insights/datasets/century-of-factor-premia-monthly

Therefore, the Skill should treat the “top ten strategies” as **ten high-quality strategy families worth testing**, not as a fixed ranking.

## 1.2 Robustness beats peak performance

Never promote a strategy because it has the highest backtest return.

Require:
- out-of-sample validation;
- walk-forward testing;
- parameter-neighborhood stability;
- market-regime robustness;
- cost robustness;
- liquidity robustness;
- trade-count sufficiency;
- benchmark superiority after risk adjustment.

## 1.3 Simplicity has a prior

Prefer fewer rules unless additional complexity produces robust improvement across unseen periods.

A rule must have either:
- an economic rationale;
- a documented behavioral explanation;
- a risk-management purpose;
- or strong cross-validation evidence.

Do not add indicators merely because they improve the historical equity curve.

---

# 2. Strategy families to continuously test

The Skill must maintain at least these ten research families.

## Family A — Multi-horizon trend following

Signals:
- short trend: 1–3 months;
- medium trend: 6 months;
- long trend: 9–12 months;
- moving-average trend;
- time-series momentum.

Combine signals instead of relying on one moving-average pair.

Alpha Architect's current trend model, for example, combines a time-series trend signal with a moving-average trend signal. citehttps://funds.alphaarchitect.com/trendsignals/

The Skill should test whether multiple horizons improve regime coverage.

## Family B — Dual momentum / relative + absolute momentum

For each ETF:
1. calculate absolute momentum;
2. rank relative momentum inside the ETF universe;
3. only hold a risk ETF when absolute momentum is positive;
4. otherwise rotate to cash/defensive ETF.

Test 1/3/6/12-month momentum combinations.

Momentum research remains one of the most persistent and broadly documented systematic effects. citehttps://www.aqr.com/insights/datasets/momentum-indices-monthly

## Family C — Adaptive Asset Allocation / tactical rotation

Rank candidate ETFs by momentum and select the top N.

Variants:
- equal weight;
- inverse-volatility weight;
- volatility-targeted weight;
- risk-parity weight;
- minimum-volatility weight.

Test N = 2, 3, 4, 5, 6.

The Skill must compare signal selection separately from portfolio construction.

## Family D — Long-term moving-average tactical allocation

Use 8–12 month trend / 200-day style gates to decide whether an ETF is:
- risk-on;
- partially allocated;
- defensive;
- cash.

Do not assume the exact 200-day parameter is optimal; test a neighborhood such as 150/180/200/220/250 trading days.

## Family E — Mean reversion / buy-the-dip

Only activate mean reversion when the higher-timeframe trend is healthy.

Entry candidates:
- distance from MA20/MA50;
- z-score;
- ATR excursion;
- RSI-style oversold state;
- short-horizon return shock.

Exit candidates:
- return to moving average;
- volatility-normalized target;
- time stop;
- momentum recovery.

Critical rule:

> Never allow mean reversion to override a confirmed long-term risk-off regime.

AQR's 2025 research on “buy the dip” specifically cautions that indiscriminate dip buying often works against momentum and that trend alignment can be preferable. citehttps://www.aqr.com/insights/research/alternative-thinking/hold-the-dip

## Family F — Momentum + defensive / quality overlay

For equity ETFs, use price momentum as the return engine and defensive/quality/low-volatility exposures as risk control.

At the ETF level, proxies can include:
- broad-market ETF;
- dividend/low-volatility ETF;
- consumption/healthcare defensive ETF;
- cash-like ETF where appropriate.

The Skill should test whether defensive exposure improves Calmar/Sortino without excessively suppressing CAGR.

AQR describes defensive investing as emphasizing lower volatility, stronger risk management and more stable exposures, especially for drawdown mitigation. citehttps://funds.aqr.com/Insights/Strategies/Defensive-Factor

## Family G — Multi-factor blend

Combine:
- momentum;
- value;
- defensive/low volatility;
- quality;
- volatility;
- trend.

Do not assume all factors should receive equal weight.

Test:
- equal factor weighting;
- risk-balanced factor weighting;
- regime-dependent weighting;
- shrinkage toward equal weights.

AQR's multi-factor framework explicitly treats combining value, momentum, quality and volatility as a diversification mechanism. citehttps://funds.aqr.com/Insights/Strategies/Multi-Factor

## Family H — Volatility targeting / risk parity

Estimate realized volatility over several horizons.

Allocate inversely to volatility:

weight_i ∝ 1 / volatility_i

Then normalize weights.

Also test:
- volatility floor;
- volatility ceiling;
- covariance-aware risk parity;
- volatility target at portfolio level.

A 2026 Finance Research Letters study reports that adaptive robust risk-parity approaches can improve return/risk/drawdown characteristics and remain robust across rebalancing choices, although all such findings must be independently validated on the China ETF universe. citehttps://www.sciencedirect.com/science/article/abs/pii/S1544612326001170

## Family I — Regime-conditioned mean reversion + momentum

Use two engines:

**Trend engine:** captures persistent moves.

**Mean-reversion engine:** captures temporary overshoots.

The regime classifier decides which engine gets capital.

Example regimes:
- strong uptrend;
- weak uptrend;
- sideways/low volatility;
- high-volatility selloff;
- bear market;
- rebound / recovery.

The classifier should preferably be continuous rather than a brittle 0/1 label.

Recent 2026 research has investigated continuous growth-vs-defensive allocation signals that smooth regime transitions rather than relying only on discrete regime labels. citehttps://arxiv.org/abs/2605.20636

## Family J — Ensemble / strategy-of-strategies

Instead of choosing one winning strategy, combine several low-correlated strategies:

- trend;
- dual momentum;
- tactical allocation;
- mean reversion;
- defensive overlay;
- volatility targeting.

Candidate weighting methods:
- equal weight;
- inverse strategy volatility;
- inverse drawdown risk;
- rolling risk-parity;
- constrained optimizer;
- Bayesian/shrinkage weighting.

The Skill must penalize turnover and complexity in the ensemble.

Man AHL's recent trend research also emphasizes the importance of market mix and the trade-off between long-term Sharpe and crisis Sharpe, reinforcing that portfolio construction matters as much as the signal itself. citehttps://www.man.com/documents/download/26b17-c9219-9ea7d-070d1/Man_AHL_Insights_A_Trend_Following_Deep_Dive_The_Optimal_Market_Mix_for_a_Trend_Follower_English_%28United_States%29_29-01-2026.pdf

---

# 3. China A-share ETF specific layer

The research engine must explicitly account for China-market implementation.

## 3.1 Universe

Maintain three nested universes:

### Core universe
Large, liquid broad-index ETFs.

### Sector universe
Liquid industry/sector ETFs.

### Opportunity universe
Narrower thematic ETFs, only if they pass liquidity and concentration filters.

Do not let a short-lived thematic ETF dominate a long-term backtest simply because its history begins near a favorable period.

## 3.2 Liquidity filter

Before an ETF can trade:
- minimum history;
- minimum median daily turnover;
- maximum bid/ask proxy;
- minimum trading-day coverage;
- no abnormal stale-price behavior.

Liquidity must be tested dynamically, not only at the end of the sample.

## 3.3 Corporate / index methodology changes

Flag:
- index reconstitutions;
- ETF mergers;
- ETF name changes;
- abnormal NAV deviations;
- changes in replication method;
- suspension/illiquidity episodes.

Do not silently stitch incompatible price histories.

---

# 4. Signal architecture upgrade

The upgraded baseline should use five independent layers.

## Layer 1 — Market regime

Measure:
- broad-index trend;
- breadth;
- realized volatility;
- drawdown;
- cross-sectional dispersion;
- market correlation.

Output:

`RegimeScore ∈ [0,1]`

instead of a purely binary risk-on/risk-off switch.

## Layer 2 — Asset trend

Use a blend of:
- absolute momentum;
- moving-average distance;
- multi-horizon returns;
- breakout state.

## Layer 3 — Relative strength

Rank ETFs by normalized momentum.

Use volatility-adjusted momentum where helpful:

risk_adjusted_momentum = return / realized_volatility

## Layer 4 — Mean-reversion opportunity

Measure:
- z-score from moving average;
- ATR excursion;
- short-term return shock;
- distance from recent high/low.

Only activate when Layer 1 and Layer 2 permit mean reversion.

## Layer 5 — Portfolio risk

Before placing a trade calculate:
- marginal volatility contribution;
- correlation concentration;
- sector/theme concentration;
- portfolio expected shortfall proxy;
- current drawdown;
- liquidity capacity.

Final position = signal × regime × risk budget × liquidity adjustment.

---

# 5. Risk engine upgrade

## 5.1 Volatility targeting

Add an optional portfolio volatility target.

For example, test:
- 10%;
- 12%;
- 15%;
- 18%;
- 20% annualized.

Do not automatically choose the highest return target.

## 5.2 Drawdown state machine

Use portfolio drawdown from equity peak:

- 0–5%: normal;
- 5–8%: caution;
- 8–12%: risk reduction;
- 12–15%: defensive;
- >15%: capital-preservation review.

The exact thresholds must be parameters tested for stability, not sacred values.

## 5.3 Correlation shock control

If correlations across held ETFs suddenly converge toward 1, reduce gross exposure even if individual momentum remains positive.

Reason:

Five ETFs are not diversified if they are all behaving like one risk factor.

## 5.4 Tail-risk stress testing

At minimum simulate:
- sudden -5% market shock;
- -10% gap-like multi-day shock;
- 2020-style fast crash;
- 2022-style prolonged drawdown;
- sharp V-shaped rebound;
- sideways whipsaw;
- high-volatility bear market.

The objective is to see whether stop-loss and mean-reversion rules fight each other.

---

# 6. Portfolio construction research grid

Every promising signal must be tested with:

1. equal weight;
2. inverse volatility;
3. volatility targeting;
4. risk parity;
5. capped risk parity;
6. correlation-aware inverse volatility;
7. equal risk contribution;
8. constrained optimizer.

The optimizer must include:
- maximum ETF weight;
- maximum sector weight;
- turnover penalty;
- minimum diversification;
- cash floor;
- cash ceiling.

Prefer simple constrained approaches before unconstrained black-box optimization.

---

# 7. Adaptive rebalancing

Do not assume weekly or monthly rebalancing is optimal.

Test:
- daily signal / weekly rebalance;
- weekly;
- biweekly;
- monthly;
- volatility-triggered rebalance;
- threshold-based rebalance.

The final model should ideally trade because information changed, not because the calendar says it is Monday.

---

# 8. Optimization protocol

Every optimization cycle follows this exact pipeline.

### Phase A — Baseline
Run the current Champion without modification.

### Phase B — Diagnose
Identify the top three sources of weakness:
- drawdown;
- missed trends;
- whipsaws;
- excessive turnover;
- sector concentration;
- volatility spikes;
- prolonged underperformance;
- cost leakage.

### Phase C — Hypotheses
Generate at most 5 changes.

Each change must state:
- hypothesis;
- mechanism;
- expected benefit;
- expected failure mode;
- parameters to test.

### Phase D — Controlled experiments
Change one major component at a time whenever possible.

### Phase E — Combination test
Only combine improvements that survive individually.

### Phase F — Walk-forward
Use rolling train/validation/test windows.

### Phase G — Stress test
Apply costs, slippage, liquidity, delay and adverse regimes.

### Phase H — Champion decision
Promote only if the candidate wins on robust risk-adjusted criteria and does not require fragile parameters.

---

# 9. Walk-forward design

Default:
- rolling training window: 3–5 years;
- validation window: 6–12 months;
- out-of-sample window: 6–12 months;
- roll forward until the end of available data.

For shorter ETF histories, use a shorter but explicit window and flag the result as low-confidence.

Never use future ETF information to decide whether an ETF belongs in the historical universe.

---

# 10. Parameter robustness

For every promoted parameter test a neighborhood around it.

Example:

If the Champion uses MA200, test:

150 / 175 / 200 / 225 / 250.

If the strategy only works at 200, treat it as fragile.

Prefer a broad “plateau” where many nearby values produce acceptable results.

Report:
- best point;
- median neighborhood result;
- worst neighborhood result;
- dispersion;
- stability score.

---

# 11. Anti-overfitting engine

The Skill must maintain an explicit **research degrees-of-freedom ledger**.

Record:
- number of hypotheses tested;
- parameter combinations;
- universes tested;
- signals tested;
- rejected strategies;
- number of iterations;
- final selected model.

Never report only the winning experiment.

Use:
- purged/lagged feature construction where appropriate;
- walk-forward validation;
- untouched final test period;
- benchmark controls;
- parameter perturbation;
- placebo tests when appropriate;
- randomization/bootstrap tests where meaningful.

AQR's research has documented substantial out-of-sample decay associated with overfitting, and its 2026 factor-data update similarly warns that factor-timing predictability may not survive implementation frictions. citehttps://www.aqr.com/Insights/Research/Journal-Article/How-Do-Factor-Premia-Vary-Over-Time-A-Century-of-Evidencehttps://www.aqr.com/insights/datasets/century-of-factor-premia-monthly

---

# 12. Benchmark control suite

Every candidate must beat or complement these controls:

### Control A
Buy-and-hold broad-market ETF.

### Control B
Monthly equal-weight ETF portfolio.

### Control C
Simple moving-average timing.

### Control D
Simple relative momentum rotation.

### Control E
Cash + broad-index tactical allocation.

A complex model that does not improve on a simple control should be rejected or simplified.

---

# 13. Evaluation dashboard

Every backtest must report at least:

### Return
- CAGR;
- cumulative return;
- annual return;
- excess return vs benchmark.

### Risk
- annualized volatility;
- maximum drawdown;
- downside deviation;
- VaR/Expected Shortfall proxy;
- worst day/week/month;
- recovery time.

### Risk-adjusted return
- Sharpe;
- Sortino;
- Calmar;
- Omega where available.

### Trading
- trade count;
- turnover;
- average holding period;
- win rate;
- average win;
- average loss;
- profit factor;
- cost as % of gross return.

### Exposure
- average exposure;
- maximum exposure;
- cash percentage;
- concentration;
- correlated exposure.

### Robustness
- walk-forward CAGR;
- walk-forward Sharpe;
- percentage of positive OOS windows;
- parameter stability;
- regime stability;
- cost sensitivity.

---

# 14. Multi-objective score

Never rank by CAGR alone.

Default research score:

`Score = 25% Calmar + 20% Sharpe + 15% Sortino + 15% CAGR + 10% OOS stability + 10% regime robustness + 5% cost robustness`

Then apply penalties:

- high drawdown penalty;
- high turnover penalty;
- concentration penalty;
- parameter-fragility penalty;
- insufficient-trade penalty;
- complexity penalty.

The weights themselves are research parameters and should be tested only at the meta-level, not optimized continuously against the final test set.

---

# 15. Pareto frontier

Maintain a Pareto set rather than a single winner.

A strategy is Pareto-dominated if another strategy has:
- equal or higher return;
- equal or lower drawdown;
- equal or higher Sharpe;
- equal or lower turnover;
- and no materially worse robustness.

Retain several non-dominated candidates for ensemble research.

---

# 16. Champion / Challenger / Control system

Maintain three categories:

### Champion
Current production candidate.

### Challenger
New strategy under research.

### Control
Simple benchmark strategy.

A Challenger can replace Champion only when:
1. OOS performance improves;
2. drawdown does not deteriorate materially;
3. improvement persists after costs;
4. parameter stability remains strong;
5. improvement is not concentrated in a single regime;
6. complexity is justified.

---

# 17. Ensemble research

When several strategies survive independently, measure their return correlation and drawdown overlap.

Prefer combinations where:
- trend and mean reversion complement each other;
- momentum and defensive exposures offset one another;
- strategy drawdowns do not coincide;
- turnover remains practical.

The ensemble itself must be walk-forward optimized.

Do not simply choose the historical best weights.

---

# 18. Current market-awareness module

For every research refresh, collect up-to-date information on:
- current ETF universe;
- ETF liquidity;
- new ETFs;
- index methodology changes;
- market microstructure changes;
- transaction-fee rules;
- major regime shifts;
- current volatility environment.

The system should distinguish:

**Research evidence** from
**current market commentary**.

Do not modify the strategy merely because a recent headline is bullish or bearish.

---

# 19. Research ideas priority queue

At each optimization cycle, rank experiments using:

`Priority = Expected benefit × Evidence × Robustness potential ÷ Complexity`

High-priority experiments for this ETF strategy:

1. Multi-horizon momentum + trend ensemble.
2. Regime-conditioned mean reversion.
3. Volatility-targeted portfolio construction.
4. Inverse-volatility / risk-parity allocation.
5. Continuous risk-on/risk-off score.
6. Momentum + defensive overlay.
7. Strategy-of-strategies ensemble.
8. Correlation shock control.
9. Adaptive rebalance thresholds.
10. Cost-aware optimization.

---

# 20. Required experiment matrix

At minimum maintain a matrix across:

### Signals
- trend;
- time-series momentum;
- relative momentum;
- mean reversion;
- breakout;
- volatility;
- defensive filter.

### Horizons
- 5d;
- 10d;
- 20d;
- 60d;
- 120d;
- 200d;
- 250d.

### Portfolio construction
- equal weight;
- inverse-vol;
- risk parity;
- volatility target;
- capped risk parity.

### Rebalance
- weekly;
- biweekly;
- monthly;
- threshold-based;
- volatility-triggered.

### Risk regimes
- normal;
- trending bull;
- trending bear;
- sideways;
- high volatility;
- crash;
- recovery.

Do not exhaustively brute-force all combinations. Use staged hypothesis testing to reduce data-mining risk.

---

# 21. Transaction-cost laboratory

Every promising strategy must be tested at several cost assumptions.

Example stress ladder:
- optimistic;
- base;
- conservative;
- severe.

Include:
- commission;
- spread proxy;
- slippage;
- execution delay;
- market-impact proxy for larger orders.

Reject strategies whose edge disappears under modest adverse cost assumptions.

---

# 22. Execution realism

For A-share ETFs:
- use signal information only up to the decision timestamp;
- apply the next realistically executable price;
- respect T+1 where applicable;
- avoid same-day look-ahead;
- model trading at close/open carefully;
- avoid using daily high/low as executable prices unless the execution assumption explicitly justifies it.

If a rule cannot be implemented reliably by a normal investor, flag it as “research only”.

---

# 23. Failure analysis

When a strategy loses, do not immediately change parameters.

Classify the loss as:

1. normal statistical drawdown;
2. regime mismatch;
3. signal decay;
4. transaction-cost leakage;
5. concentration failure;
6. whipsaw;
7. liquidity failure;
8. implementation error;
9. overfit;
10. benchmark-relative failure.

Only classes 2–10 justify a redesign investigation.

---

# 24. Continuous learning loop

Every research iteration must produce:

### Before
- current Champion;
- known weaknesses;
- research hypothesis.

### During
- experiments;
- diagnostics;
- rejected hypotheses;
- parameter stability.

### After
- OOS results;
- regime decomposition;
- cost sensitivity;
- reason for promotion/rejection;
- next research priority.

Never erase rejected experiments.

The research log is part of the anti-overfitting defense.

---

# 25. Final promotion rule

A strategy is promoted only if it satisfies all of the following:

- statistically and economically plausible;
- positive or materially improved OOS performance;
- acceptable maximum drawdown;
- robust Sharpe/Sortino/Calmar;
- survives realistic costs;
- robust across multiple market regimes;
- stable across nearby parameters;
- not dependent on one ETF or one historical episode;
- manageable turnover;
- implementable by the intended investor;
- simpler than, or materially better than, the existing Champion after accounting for complexity.

If none qualifies:

> **Keep the Champion. Do not optimize for the sake of optimizing.**

---

# 26. Standard research output

Every optimization report must contain:

1. Executive conclusion.
2. Champion vs Challenger vs Controls.
3. Return/risk dashboard.
4. Drawdown analysis.
5. Regime analysis.
6. ETF-level contribution.
7. Signal contribution.
8. Portfolio-construction contribution.
9. Cost sensitivity.
10. Parameter sensitivity.
11. Walk-forward/OOS results.
12. Failure cases.
13. Overfitting checks.
14. Complexity comparison.
15. Promotion decision.
16. Next five research experiments.

The report must explicitly state:

> “What evidence would make us reject this strategy?”

This prevents confirmation bias.

---

# 27. Version control

Use semantic versions:

- major version: architecture changes;
- minor version: validated strategy improvements;
- patch version: bugs/data corrections.

Example:

`ETF-Volatility-Alpha v2.1.0`

Maintain a changelog with:
- rule changed;
- reason;
- evidence;
- OOS effect;
- drawdown effect;
- turnover effect;
- decision.

---

# 28. Non-negotiable principles

1. No future information.
2. No cherry-picked time windows.
3. No “best parameter” without neighborhood testing.
4. No promotion based only on CAGR.
5. No hidden transaction costs.
6. No pretending correlated ETFs are diversified.
7. No unlimited averaging down.
8. No strategy change solely because of a recent losing streak.
9. No black-box ML before simple models are exhausted.
10. No final model without an untouched or genuinely walk-forward-tested period.

---

# 29. Target architecture for the next implementation stage

The eventual implementation should contain these modules:

`data_loader`
→ `data_quality`
→ `universe_builder`
→ `feature_engine`
→ `regime_engine`
→ `signal_engine`
→ `portfolio_constructor`
→ `risk_engine`
→ `execution_simulator`
→ `backtester`
→ `walk_forward_engine`
→ `stress_test_engine`
→ `robustness_engine`
→ `optimizer`
→ `champion_challenger`
→ `research_logger`
→ `report_generator`

The optimizer must never bypass the risk, cost, walk-forward or research-log modules.

---

# 30. Ultimate objective

The end product is not “the strategy with the highest backtest return.”

It is:

> **A continually tested, multi-strategy, risk-aware, cost-aware, out-of-sample validated ETF system that attempts to harvest China A-share volatility while minimizing the probability that historical luck or overfitting is mistaken for genuine edge.**

---

# 31. Expert-Distillation Engine v3.0 — 近三年公开业绩与顶级投资者方法蒸馏

## 31.1 重要定义：不伪造“近三年前十”

公开资料不存在一个统一、透明、可复核、同口径的“2023-2025全球/中国股票专家收益前十”排行榜。私募产品存在披露频率、产品存续期、策略口径、规模门槛和净值可得性差异，因此不能把单年度冠军直接写成三年冠军。

本 Skill 因此采用：

> **Recent Proven Expert Set（近期可验证专家集合）**

而不是虚构一个精确排名。

入选依据优先级：
1. 2023-2025 至少两个年份出现公开业绩领先；
2. 股票策略/量化股票策略有明确公开归类；
3. 有可验证的长期方法论或机构投研框架；
4. 方法可以被翻译成 ETF 可执行规则；
5. 不依赖不可复制的信息优势。

## 31.2 近三年公开业绩观察样本

公开报道显示：
- 2023 年百亿私募前列包括东方港湾、信弘天禾、稳博、衍复、乾象、宽德、因诺等，且量化股票策略整体明显强于主观股票策略。中国证券报/新华社报道的私募排排数据表明，2023 年有业绩展示的百亿量化私募整体收益为 6.43%，主观百亿私募为 -3.26%。 citehttps://www.cs.com.cn/tzjj/smjj/202401/t20240108_6383841.htmlhttps://www.jjckb.cn/2024-01/05/c_1310758931.htm
- 2024 年公开报道显示，东方港湾、玄元、鸣石、龙旗科技、进化论、阿巴马等进入百亿私募年度前列，东方港湾连续第二年取得百亿私募年度冠军；这一结果说明“风格持续性”本身就是值得研究的变量。 citehttps://www.thepaper.cn/newsDetail_forward_29884356
- 2025 年公开排行榜显示远信投资、灵均投资、复胜资产、宁波幻方量化、信弘天禾、银叶投资、诚奇私募、久期投资、稳博投资、黑翼资产进入百亿股票策略收益前十，但该榜单属于**年度表现**，不能直接等同于三年复合业绩。 citehttps://www.100wjjw.com/foruminfo/373.html
- 2025 全球顶级对冲基金公开业绩显示，Melqart 事件驱动、D.E. Shaw Oculus、多策略平台以及桥水部分策略均取得较强收益，说明近期高收益不仅来自“纯股票Beta”，还可能来自事件驱动、量化、多资产宏观和策略组合。 citehttps://www.cls.cn/detail/2246520
- 2026 年市场数据进一步显示量化、趋势和多策略在高波动环境下的表现分化明显；例如 Graham Capital 的 Tactical Trend 在 2026 年截至相关报道时保持较强正收益，Citadel、Renaissance 等量化/多策略机构也在剧烈波动月份表现突出。 citehttps://www.businessinsider.com/quant-hedge-funds-july-performance-renaissance-technologies-two-sigma-cfm-2026-8

因此，本 Skill 不把上述机构复制成“买什么”，而是提取其**可以被 ETF 验证的思想结构**。

---

# 32. 十类专家方法蒸馏卡

以下十类方法称为“专家方法卡”，不是宣称某个人是绝对第一，而是将近年高绩效管理人的共同特征压缩成可测试模块。

## Expert-01：高集中高质量投资者 → “少而精”的信号预算

可蒸馏思想：
- 不是什么都做；
- 只有当机会的质量足够高时才集中风险；
- 组合集中必须建立在更高置信度上。

ETF翻译：
- 候选池可很大；
- 实际持仓只保留排名前 N；
- 但使用严格最大仓位和相关性约束。

新增实验：
- N=2/3/4/5/6；
- Top-N momentum；
- Top-N composite score；
- conviction score × volatility budget。

禁止推论：
> 高绩效经理集中持仓 ≠ 我们应该集中押某个行业。

---

## Expert-02：东方港湾式长期价值/风格坚持 → “不要因为短期失效频繁换系统”

公开数据中，东方港湾在 2023、2024 年均位居相关百亿私募年度领先位置。 citehttps://www.jjckb.cn/2024-01/05/c_1310758931.htmhttps://www.thepaper.cn/newsDetail_forward_29884356

可蒸馏思想：
- 核心逻辑稳定；
- 允许阶段性跑输；
- 不因短期风格轮动立即放弃框架。

ETF翻译：
- Champion 的核心参数设置“最短寿命”；
- 单次短期回撤不能直接触发架构修改；
- 必须经过 OOS + regime 分析才能替换。

新增规则：

`Strategy_Change_Penalty = Complexity + Turnover + Recent_Drawdown_Bias`

当新策略优势只来自最近 3-6 个月时，自动降权。

---

## Expert-03：信弘天禾 / 稳博 / 衍复 / 宽德类量化 → “从可重复的小优势累积Alpha”

2023 年公开数据中，多家量化百亿私募进入前列，说明系统化、分散化的小优势在不同行情中具有竞争价值。 citehttps://www.jjckb.cn/2024-01/05/c_1310758931.htm

ETF翻译：
- 不依赖单个预测；
- 同时组合多个弱信号；
- 每个信号只贡献一小部分风险。

新增模块：

`Signal Ensemble = Trend + Relative Momentum + Mean Reversion + Volatility + Breadth + Liquidity`

每个信号必须报告：
- IC/预测能力代理；
- 独立增益；
- 与其他信号相关性；
- 边际收益/复杂度。

禁止：

> 不能因为五个指标方向一致，就把五个指标等权相乘造成重复计权。

---

## Expert-04：复胜/久期/东方港湾等主观风格代表 → “主题必须有逻辑，不能只有价格”

主观管理人近年明显受益于部分行业/主题行情，但风格暴露也是最大风险来源之一。2024 年年度领先榜中同时出现主观、量化和主观+量化机构，说明单一风格并非稳定答案。 citehttps://www.thepaper.cn/newsDetail_forward_29884356

ETF翻译：

任何行业ETF买入前增加：
- 相对强度；
- 市场宽度；
- 趋势持续性；
- 波动率；
- 估值代理；
- 主题拥挤度代理。

其中“估值/拥挤度”不能单独决定买卖，只用于改变仓位上限。

---

## Expert-05：灵均/幻方/诚奇/黑翼类量化 → “横截面 + 风险约束”

2025 年百亿股票策略收益榜中，多家量化管理人进入前列。 citehttps://www.100wjjw.com/foruminfo/373.html

ETF翻译：

不要问：
> “半导体会不会涨？”

而问：
> “在当前可交易ETF集合里，谁相对更强？”

新增：

`RelativeScore_i = percentile(momentum_i, volatility_i, trend_i, liquidity_i)`

并使用横截面排名代替绝对预测。

---

## Expert-06：D.E. Shaw / Millennium / Citadel 类多策略平台 → “不同收益来源并联”

2025 年公开业绩显示，多策略机构普遍重视低回撤和风险调整收益，而不是只追求最高绝对收益。 citehttps://www.cls.cn/detail/2246520https://cj.sina.com.cn/articles/view/1808025122/6bc4462200101elu6

ETF翻译：

建立四个独立 sleeve：
1. Trend sleeve；
2. Momentum sleeve；
3. Mean-Reversion sleeve；
4. Defensive/Capital-Preservation sleeve。

每个 sleeve 有独立风控。

最终：

`Portfolio = RiskBudget(Trend) + RiskBudget(Momentum) + RiskBudget(MR) + RiskBudget(Defensive)`

而不是四个策略简单平均资金。

---

## Expert-07：Melqart 等事件驱动 → “催化剂比故事重要”

2025 年公开顶级对冲基金榜单中，事件驱动策略取得很强表现。 citehttps://www.cls.cn/detail/2246520

ETF无法完整复制事件驱动，但可提取：

- 波动突然放大；
- 相对强度突然变化；
- 成交额异常；
- 缺口/突破；
- 市场广度变化。

新增：

`CatalystScore`

用作仓位调整，而非预测方向。

例如：

高趋势 + 高催化 + 高流动性 → 允许更高仓位。

低趋势 + 高催化 → 不追涨，等待确认。

---

## Expert-08：Bridgewater / All Weather → “先设计风险，再谈收益”

Ray Dalio 在 2026 年再次强调 All Weather 的核心理念：组合应该通过工程化分散实现尽可能高的风险调整收益，并减少对市场择时的依赖。 citehttps://raydalio.substack.com/p/the-concept-and-mechanics-of-an-all

ETF翻译：

策略优化必须从“信号优化”升级为：

`Signal → Risk → Portfolio`

任何信号若不能通过风险层，不得交易。

新增：
- 风险预算；
- 边际风险贡献；
- 相关性；
- 波动目标；
- 极端风险预算。

---

## Expert-09：趋势跟踪顶级机构 → “让赢家活久一点”

2026 年趋势策略相关研究继续强调市场组合、趋势持续性和长期/危机 Sharpe 的权衡。近期高波动环境中，趋势策略也表现出与传统股票Beta不同的收益来源。 citehttps://www.man.com/documents/download/26b17-c9219-9ea7d-070d1/Man_AHL_Insights_A_Trend_Following_Deep_Dive_The_Optimal_Market_Mix_for_a_Trend_Follower_English_%28United_States%29_29-01-2026.pdfhttps://www.businessinsider.com/quant-hedge-funds-july-performance-renaissance-technologies-two-sigma-cfm-2026-8

ETF翻译：

原策略“涨回均线就全部止盈”升级为：

`Core + Runner`

- Core：均值回归时止盈；
- Runner：保持趋势仓；
- Runner 使用移动止盈/波动退出。

目标：避免把长期趋势交易过早卖掉。

---

## Expert-10：Renaissance / 系统化量化 → “系统优先于观点”

2026 年近期市场报道显示，量化机构在剧烈波动月份表现出较强适应性，但不同量化策略之间仍然存在巨大分化。 citehttps://www.businessinsider.com/quant-hedge-funds-july-performance-renaissance-technologies-two-sigma-cfm-2026-8

ETF翻译：

任何“专家观点”都必须转换成：

`Hypothesis → Feature → Signal → Backtest → OOS → Cost Test → Promotion`

绝不直接加入交易规则。

---

# 33. 专家思想 → ETF可执行原则的蒸馏结果

综合以上十类方法，本 Skill 新增以下十大核心原则：

### Principle 01 — Relative Before Absolute

先比较“谁更强”，再判断“市场是否值得做”。

### Principle 02 — Regime Before Signal

先决定什么策略环境有效，再决定买什么。

### Principle 03 — Risk Before Position

任何信号先经过风险预算，再转成仓位。

### Principle 04 — Ensemble Before Optimization

优先组合不同逻辑，而不是不停优化同一个逻辑。

### Principle 05 — Robust Plateau Before Best Parameter

选择参数平台，不选择历史冠军点。

### Principle 06 — Conviction Must Be Earned

高仓位必须同时有趋势、相对强度、流动性和风险控制证据。

### Principle 07 — Keep Some Winners

趋势策略必须拥有 Runner 仓位，避免均值回归过早卖飞。

### Principle 08 — Buy-the-Dip Is Conditional

抄底必须建立在长期趋势/市场状态允许之上。

### Principle 09 — Research Is a Portfolio

研究假设本身也需要分散，不能连续20次只优化一个参数。

### Principle 10 — Survival Is an Alpha

组合先解决“活下来”，再解决“赚得多”。

---

# 34. 新增“专家蒸馏 → 实验生成器”

每个专家方法只能产生**研究假设**，不能直接产生实盘规则。

输入：

`ExpertCard + CurrentChampion + WeaknessDiagnosis`

输出：最多3个 Challenger：

### Challenger A：低复杂度版

只增加一条规则。

### Challenger B：风险增强版

不增加主要信号，只改善风险控制。

### Challenger C：组合增强版

引入一个低相关策略 sleeve。

这样可以防止“专家经验拼盘化”。

---

# 35. 新增“投资方式自我改善引擎”

Skill 不再只优化策略，也优化**投资流程**。

## 35.1 决策质量评分

每次交易记录：
- 信号分数；
- 市场状态；
- 风险预算；
- 买入原因；
- 卖出原因；
- 预期持有周期；
- 实际执行价；
- 事后结果。

并区分：

`Good Decision + Good Outcome`

`Good Decision + Bad Outcome`

`Bad Decision + Good Outcome`

`Bad Decision + Bad Outcome`

禁止把“赚钱”自动等同于“决策正确”。

## 35.2 行为偏差监测

每月检查：
- 追涨次数；
- 越跌越买次数；
- 过早止盈；
- 拒绝止损；
- 频繁换策略；
- 新闻驱动交易；
- 仓位漂移；
- 亏损后加码。

这些指标成为投资流程的 KPI。

---

# 36. 新增“专家共识冲突测试”

不同专家可能给出相反结论。

例如：

- 价值派：下跌增加安全边际；
- 动量派：下跌意味着继续减仓；
- 趋势派：趋势破坏后离场；
- 均值回归派：极端偏离产生机会。

Skill 必须把这种冲突变成实验：

`Trend Gate × Mean Reversion`

测试：
1. 无趋势过滤的抄底；
2. MA200过滤；
3. 多周期趋势过滤；
4. RegimeScore过滤；
5. Drawdown + Volatility联合过滤。

如果“抄底”只有无过滤时有效，视为脆弱。

---

# 37. 新增“高手方法一致性分数”

对每个 Challenger 增加：

`ExpertConsistencyScore`

由以下维度构成：
- 趋势原则一致性；
- 分散原则一致性；
- 风险预算一致性；
- 纪律性；
- 交易成本意识；
- 反过拟合一致性。

注意：该分数只能作为辅助分，**不能替代 OOS 证据**。

---

# 38. 新增“不要盲目学习高手”规则

任何专家经验都必须通过三道门：

### Gate 1 — Can it be expressed as a rule?

能否量化？

### Gate 2 — Does it survive China ETF data?

能否在目标市场验证？

### Gate 3 — Does it survive costs and OOS?

能否实盘实现？

任何一关失败：

`Research Only`

不能进入 Champion。

---

# 39. v3.0 新优化评分体系

原评分升级为四层：

## Layer A — Performance

CAGR / Sharpe / Sortino / Calmar

## Layer B — Robustness

OOS / Walk-forward / Parameter plateau / Regime stability

## Layer C — Implementation

Turnover / Liquidity / Costs / Execution delay

## Layer D — Behavioral & Complexity

Rule simplicity / Decision stability / ExpertConsistency / Research degrees of freedom

最终：

`FinalScore = Performance × Robustness × Implementation × BehavioralQuality`

使用乘法思想而非简单加法，使一个关键维度接近零时不会被其他高分完全掩盖。

---

# 40. v3.0 新增“收益来源拆解”

每轮回测必须回答：

> **我们到底赚到了什么钱？**

至少分解为：

1. 市场Beta；
2. 趋势收益；
3. 横截面动量收益；
4. 均值回归收益；
5. 行业轮动收益；
6. 波动率管理收益/损失；
7. 防御收益；
8. 交易成本损耗；
9. 调仓损耗；
10. 尾部风险损失。

如果一个策略的全部超额收益来自单一模块，则进入“单点脆弱”警报。

---

# 41. v3.0 新增“专家经验的反事实测试”

对每一个吸收的投资思想做反事实实验：

- 有原则 vs 无原则；
- 加入规则前 vs 加入规则后；
- 低仓位 vs 高仓位；
- 低换手 vs 高频调整；
- 单策略 vs 多策略。

最终必须回答：

> **这个专家思想究竟贡献了多少独立增益？**

否则不准写进生产策略。

---

# 42. v3.0 最终研究架构

`Market Data`
→ `Data Quality`
→ `Universe`
→ `Feature Engine`
→ `Expert-Distillation Engine`
→ `Regime Engine`
→ `Signal Ensemble`
→ `Portfolio Construction`
→ `Risk Engine`
→ `Execution Simulator`
→ `Backtester`
→ `Walk Forward`
→ `Stress Test`
→ `Attribution`
→ `Behavior Monitor`
→ `Anti-Overfitting`
→ `Champion / Challenger`
→ `Research Log`
→ `Next Hypotheses`

研究系统的目标不是模仿某个高手，而是：

> **持续吸收高手可验证的思想，把它们转换成可证伪假设，用中国ETF历史数据验证，再只保留能够跨环境、跨参数、跨成本和样本外成立的部分。**

---

# 43. v3.0 本轮新增的优先级队列

下一轮优先测试：

1. **Trend + Relative Momentum + Risk Budget**
2. **Conditional Buy-the-Dip + Long-Term Trend Gate**
3. **Strategy-of-Strategies Ensemble**
4. **Continuous RegimeScore**
5. **Inverse-Volatility + Correlation Control**
6. **Core + Runner Exit**
7. **Catalyst / Abnormal Volume Overlay**
8. **Dynamic Position Concentration**
9. **Behavior-aware trading rules**
10. **Expert-consensus conflict tests**

每一项都必须经过：

`In-Sample → Validation → Walk-Forward → OOS → Cost Stress → Regime Split → Parameter Plateau → Promotion Review`

任何“最近三年收益特别高”的候选，如果无法通过上述完整流程，默认视为**可能只是风格暴露或历史偶然性**，而不是可持续 Alpha。

# 44. Retail Beginner Personalization Layer v4.0

## 44.1 Investor profile

Default target investor for this profile:

- small account;
- beginner or early-stage investor;
- seeks higher long-term return than passive broad-index buy-and-hold;
- explicitly requires maximum drawdown to remain below 25%;
- cannot rely on institutional execution, leverage, derivatives or continuous monitoring;
- capital preservation and staying invested are more important than maximizing backtest CAGR.

This profile changes the optimization objective substantially.

The Skill must optimize for:

> **High long-term compounding + drawdown discipline + low implementation complexity + low behavioral error probability.**

It must NOT optimize for:

> highest CAGR, highest Sharpe, highest turnover-adjusted alpha, or fastest trading frequency.

---

# 45. Personal objective function

## 45.1 Hard drawdown constraint

The primary hard constraint is:

`Maximum Portfolio Drawdown < 25%`

But because live trading can deviate from backtests, the research engine should target a materially lower operating range:

`Target MDD ≤ 18–20%`

and use:

`20–22% = emergency de-risking review`

`>=25% = strategy failure unless independently explained by a documented implementation event`

A strategy that earns more but repeatedly approaches 25% drawdown should generally lose to a slightly lower-return strategy with materially lower drawdown.

## 45.2 Default optimization utility

Use a constrained objective rather than a pure weighted score:

`Maximize geometric CAGR subject to MDD <= 20%, OOS stability >= threshold, turnover <= threshold, complexity <= threshold.`

Then use a secondary ranking:

`Utility = CAGR × RobustnessScore × SimplicityScore × ImplementationScore`

with severe penalties for:

- MDD > 20%;
- any stress scenario producing MDD >= 25%;
- negative OOS expectancy;
- fragile parameters;
- excessive turnover;
- large single-theme concentration;
- rules requiring intraday prediction;
- behaviorally difficult execution.

---

# 46. Small-account architecture

## 46.1 Core design

For the default beginner profile, use a **Core + Tactical + Cash** structure.

Default research range:

- `50–70% Core broad-index ETFs`
- `15–30% Tactical momentum/sector ETFs`
- `15–30% Cash/low-risk reserve`

The exact mix is an optimization parameter, but cash must remain available for drawdowns and should not be forced to zero merely to maximize historical CAGR.

## 46.2 Position-count limit

Default live implementation target:

`3–5 ETFs`

Maximum:

`6 ETFs`

A backtest requiring 10–20 simultaneous ETF positions should be classified as **institution-like** and should not automatically be recommended to this user profile.

## 46.3 Single-position cap

Default:

- broad-index core ETF: `25% max`
- tactical sector ETF: `12% max`
- narrow thematic ETF: `7% max`

These are research defaults, not immutable values.

---

# 47. Beginner-safe strategy architecture

The preferred Champion candidate should use no more than four decision layers:

### Layer A — Broad market regime

Determine whether the equity market is:

- healthy risk-on;
- mixed/sideways;
- risk-off;
- recovery.

Preferred inputs:

- broad-index trend;
- 200-day/long-term trend state;
- realized volatility;
- recent drawdown;
- breadth where reliable.

### Layer B — ETF ranking

Rank broad and sector ETFs using:

- 1-month momentum;
- 3-month momentum;
- 6-month momentum;
- optional 12-month momentum;
- volatility-adjusted momentum.

### Layer C — Risk budget

Convert ranking into position size using:

- volatility;
- correlation;
- drawdown state;
- portfolio concentration.

### Layer D — Simple execution rule

Use weekly decision points or threshold-based decisions.

Avoid strategies requiring continuous intraday observation.

---

# 48. Replace aggressive mean reversion with conditional dip buying

For this investor profile, the Skill must NOT use unrestricted grid trading or unlimited averaging down.

Mean reversion is allowed only when all conditions below hold:

1. broad market long-term trend is not confirmed risk-off;
2. ETF remains above its long-term risk gate or has recently regained it;
3. relative momentum is not among the weakest group;
4. the selloff is classified as a short-term shock rather than a structural break;
5. portfolio drawdown remains below the de-risking threshold.

Maximum number of add-on entries for one position:

`2`

After the second add-on:

**no additional averaging down until a fresh validated signal appears.**

This rule exists to prevent small-account investors from turning a tactical trade into a permanent trapped position.

---

# 49. Trend-following upgrade: Core + Runner

A common weakness of pure mean-reversion systems is premature profit taking.

The default exit architecture should therefore be:

`Core position + Runner position`

When a tactical ETF returns toward fair value:

- reduce the tactical/core-trading portion;
- retain a smaller Runner while the medium/long-term trend remains positive.

The Runner can exit when:

- long-term trend breaks;
- momentum ranking collapses materially;
- portfolio regime turns risk-off;
- trailing drawdown rule is triggered.

This allows the strategy to monetize volatility while retaining exposure to extended trends.

---

# 50. Portfolio risk ladder for the 25% drawdown constraint

The portfolio must have explicit exposure states.

### State 0 — Normal

Portfolio drawdown:

`0–5%`

Target equity exposure:

`70–100% of strategic risk budget`

### State 1 — Caution

Drawdown:

`5–8%`

Reduce new tactical entries and raise selectivity.

### State 2 — Risk reduction

Drawdown:

`8–12%`

Reduce tactical exposure by approximately 25–35%.

Increase cash reserve.

### State 3 — Defensive

Drawdown:

`12–15%`

Reduce total equity risk materially.

Prefer broad-index core exposure over narrow sectors.

### State 4 — Capital preservation

Drawdown:

`15–20%`

Only highest-confidence signals are permitted.

No aggressive dip buying.

### State 5 — Hard risk review

Drawdown:

`20–22%`

Pause new risk expansion.

Audit:

- regime classification;
- correlation concentration;
- execution slippage;
- model drift;
- behavior errors;
- data errors.

### State 6 — Failure boundary

Drawdown:

`>=25%`

Treat as strategy failure unless proven to be a non-repeatable implementation anomaly.

The Skill must produce a post-mortem before resuming normal-risk operation.

---

# 51. No-leverage / no-derivative default

For the beginner small-account profile:

Default prohibited instruments:

- margin leverage;
- futures leverage;
- options selling;
- naked shorting;
- leveraged ETF products unless explicitly researched as a separate risk budget.

The Skill may research these instruments academically, but must not automatically integrate them into the personal Champion strategy.

The objective is to improve return by improving **selection, timing, diversification and risk management**, not by multiplying exposure.

---

# 52. Small-account transaction efficiency

Small accounts are especially sensitive to unnecessary turnover because each trade consumes a larger percentage of capital.

Therefore add a **Minimum Economic Edge Gate**.

A trade is permitted only if:

`ExpectedEdge > EstimatedAllInCost × safety_multiple`

where the safety multiple should normally exceed 2 in the research default.

EstimatedAllInCost includes:

- commission;
- exchange fees where applicable;
- spread proxy;
- slippage;
- execution delay;
- estimated market impact when relevant.

If the signal edge is too small, the correct decision is:

> **Do nothing.**

---

# 53. A-share ETF implementation rules for the personal strategy

As of the current rules, stock ETFs in China are T+1, while certain bond, gold, cross-border and currency ETFs can support T+0. The personal strategy should assume T+1 for ordinary stock ETFs unless the exact product is independently verified. citeturn110286search0turn110286search4

The strategy must also account for the 2026 Shanghai Stock Exchange rule changes, including the change of ETF closing-phase trading to closing auction and the extension of after-hours fixed-price trading to ETFs. These changes mean historical execution assumptions must be versioned rather than silently reused forever. citeturn110286search3

The market is sufficiently liquid and large that a small-account strategy should generally prioritize liquid broad-based ETFs and avoid paying for complexity. By end-2025, domestic ETF assets exceeded RMB 6 trillion and stock ETFs accounted for RMB 3.83 trillion; Shanghai-listed ETFs alone reached RMB 4.2 trillion. citeturn110286search36turn110286search11

For this profile, the liquidity filter should be stricter than necessary for institutional-scale backtests because the benefit of narrow thematic exposure is often not worth the added concentration and execution risk.

---

# 54. Beginner behavior-defense module

The Skill must optimize not only the strategy but also the probability that the investor follows it.

Monitor for these behavioral failure modes:

1. chasing the strongest recent winner;
2. averaging down after invalidation;
3. selling the Runner too early;
4. doubling position size after losses;
5. changing parameters after a short losing streak;
6. checking prices too frequently;
7. trading because of financial news without a signal change;
8. adding a new ETF because of social-media popularity;
9. abandoning the system after one disappointing month;
10. using leverage to compensate for a small account.

When detected, the Skill should simplify rules rather than add complexity.

---

# 55. Information diet for the personal strategy

Current news and expert opinions may inform **risk review**, but should not directly generate trades unless converted into a testable signal.

The Skill should classify information into:

- structural evidence;
- current market data;
- narrative/opinion;
- unverifiable prediction.

Only structural evidence and measurable current data can directly modify research assumptions.

Expert opinions are treated as hypotheses, not signals.

---

# 56. Beginner-specific benchmark suite

Every new Champion must be compared against:

### Benchmark 1 — 100% broad-index buy-and-hold

Purpose:

Does complexity actually add value?

### Benchmark 2 — 80/20 broad-index + cash

Purpose:

Can we improve drawdown without sacrificing too much CAGR?

### Benchmark 3 — Simple long-term trend filter

Purpose:

Does the sophisticated model beat a simple risk gate?

### Benchmark 4 — Simple relative momentum rotation

Purpose:

Does the full system justify its complexity?

### Benchmark 5 — Current Champion

Purpose:

Does the new strategy represent a genuine improvement?

A complex strategy that does not robustly beat these controls should not be promoted.

---

# 57. Return-vs-drawdown target bands

The research report must categorize candidates into practical investor bands.

### Band A — Excellent

- OOS CAGR strong;
- MDD <= 15%;
- robust across regimes;
- moderate turnover;
- easy to execute.

### Band B — Preferred

- OOS CAGR attractive;
- MDD 15–20%;
- strong parameter stability;
- acceptable implementation complexity.

### Band C — Speculative

- MDD 20–25%;
- may have higher CAGR;
- not preferred for the default personal Champion.

### Band D — Reject

- MDD >=25%;
- unstable OOS results;
- fragile parameters;
- edge disappears after costs;
- or requires institutional execution.

The default personal Champion should come from Band A or Band B.

---

# 58. Personal risk-budget research

Do not optimize solely at the ETF level.

The Skill must estimate:

`Expected contribution to return / Expected contribution to drawdown`

for each ETF and strategy sleeve.

Prefer capital allocation that increases:

`return contribution per unit of marginal drawdown risk`

over allocation based simply on historical return.

This is particularly important for sectors such as semiconductors, brokers, resources and other high-beta themes, where apparent diversification can hide a single common market-beta or liquidity risk.

---

# 59. Capital deployment schedule for a new small account

When a user starts with a new account, the Skill should NOT assume that 100% of capital must be deployed immediately.

Default research implementation:

- initial deployment: approximately 50–70%;
- reserve: approximately 30–50%;
- increase exposure only when the regime and signals justify it;
- avoid converting a new account into a full-risk portfolio after one favorable week.

The exact schedule must be tested, but the psychological and risk-management objective is constant:

> **Give the investor enough exposure to participate, while preserving optionality.**

---

# 60. Research priority for this investor profile

The optimization queue must be reordered around the user's true objective.

Priority 1 — `Drawdown-constrained trend + momentum`

Priority 2 — `Volatility-targeted portfolio construction`

Priority 3 — `Core + Tactical + Cash architecture`

Priority 4 — `Conditional buy-the-dip`

Priority 5 — `Correlation concentration control`

Priority 6 — `Adaptive exposure based on continuous RegimeScore`

Priority 7 — `Core + Runner exit logic`

Priority 8 — `Low-turnover threshold rebalancing`

Priority 9 — `Strategy ensemble with low complexity`

Priority 10 — `Behavior-aware execution guardrails`

Low priority unless justified by strong evidence:

- high-frequency signals;
- intraday timing;
- large indicator stacks;
- machine learning;
- black-box optimization;
- narrow thematic ETF concentration;
- leverage.

---

# 61. Personal Champion promotion rule v4.0

A candidate may become the user's personal Champion only if all of the following are true:

1. OOS CAGR is attractive relative to controls;
2. target historical MDD <=20%;
3. no credible stress test shows persistent MDD >=25% under reasonable assumptions;
4. OOS performance is positive or materially useful across multiple regime windows;
5. parameter neighborhood is stable;
6. transaction costs do not eliminate the edge;
7. turnover is realistic for a small account;
8. no leverage is required;
9. no single ETF/theme drives an unreasonable share of total risk;
10. the strategy can be explained in a few understandable rules;
11. the user could realistically execute it without watching the market continuously;
12. it beats or complements simple controls after risk adjustment.

If a candidate has higher CAGR but materially worse drawdown or substantially more execution complexity, it must normally be rejected.

---

# 62. Personalization principle

The central rule for this user profile is:

> **Do not try to make a small account behave like a hedge fund. Build a simple system that captures a meaningful portion of upside while making survival highly probable.**

The Skill should prefer:

`moderately aggressive + highly controlled`

over:

`maximally aggressive + fragile`.

---

# 63. v4.0 research output additions

Every personal-strategy report must now include:

1. target CAGR range;
2. target MDD range;
3. actual MDD;
4. distance to the 25% hard limit;
5. percentage of time in cash;
6. number of positions;
7. average monthly turnover;
8. implementation burden score;
9. behavioral difficulty score;
10. probability of violating the drawdown budget under stress tests;
11. performance vs simple controls;
12. exact conditions under which the strategy should be stopped;
13. what the investor should do when the strategy is underperforming;
14. whether the next optimization should seek higher return, lower drawdown or lower complexity.

The default next objective is **not** “higher return.”

The default next objective is:

> **improve return only when it does not materially worsen drawdown, robustness or behavioral complexity.**

---

# 64. Version control

`ETF-Volatility-Alpha v5.0.0 — Self-Learning Investment Research System`

Major change from v3.x:

- explicit investor constraints;
- hard drawdown budget;
- small-account architecture;
- simplified implementation;
- behavior-defense layer;
- no-leverage default;
- minimum economic edge gate;
- Core + Tactical + Cash structure;
- conditional dip buying;
- Core + Runner exit;
- personal benchmark suite;
- personalized Champion promotion rules.

Future research versions must report:

`Rule change → hypothesis → backtest effect → OOS effect → MDD effect → cost effect → complexity effect → behavior effect → decision`



---

# 65. Self-Learning Investment Research System v5.0

## 65.1 Mission upgrade

This Skill is no longer merely a backtesting optimizer.

It is a **self-learning research system** whose job is to:

1. continuously discover high-value new investment ideas;
2. distinguish enduring principles from temporary market fashions;
3. translate investor thinking into testable hypotheses;
4. run controlled experiments;
5. learn from both successful and failed experiments;
6. preserve the evidence trail;
7. update the strategy only when the new evidence is robust;
8. continuously improve the research process itself.

The system must learn **without automatically trading on what it learns**.

Core separation:

`Knowledge → Hypothesis → Experiment → Evidence → Promotion`

Never:

`News → Belief → Trade`

---

# 66. Learn from the optimization process of top investors

The Skill should study not only what top investors buy, but **how they improve their own decision systems**.

The goal is not to imitate portfolio holdings. The goal is to extract reusable decision mechanisms.

## 66.1 Howard Marks: second-order thinking + cycle awareness + risk first

Oaktree's published material emphasizes second-level thinking, risk control, cycles and skepticism toward macro forecasting. citehttps://www.oaktreecapital.com/insights/memo/the-best-ofhttps://www.oaktreecapital.com/insights/memo/i-beg-to-differ

Translate into the Skill:

### Rule HM-1 — Ask the second-order question

For every proposed signal ask:

- What does the obvious investor already know?
- Why is the opportunity still available?
- What would make the obvious interpretation wrong?
- What happens after the expected event?
- Is the edge in the direction, magnitude, timing or risk asymmetry?

The Skill must generate at least one **second-order hypothesis** for every major research idea.

### Rule HM-2 — Do not forecast what cannot be forecast reliably

Macro forecasts may be stored as context, but must not directly determine portfolio positions unless they produce a measurable, lagged and OOS-validated feature.

### Rule HM-3 — Risk posture is a first-class decision

Before optimizing expected return, classify the current opportunity as:

`aggressive / normal / cautious / defensive`

Then ask whether the strategy's behavior is appropriate for the current risk posture.

---

## 66.2 Warren Buffett / Berkshire: competence, capital discipline, liquidity and patience

Berkshire's 2025 letter emphasizes understanding what is owned, durable economics, capital discipline, limited leverage and maintaining liquidity so capital can be deployed when opportunities appear. citeturn641374search36

Translate into the Skill:

### Rule WB-1 — Circle of competence for strategies

The Skill must maintain an explicit list of:

- strategies it understands;
- strategies it can execute reliably;
- strategies whose behavior has been validated on the China ETF universe;
- strategies that remain research-only.

A complicated model does not qualify merely because it performs well.

### Rule WB-2 — Dry powder is strategic capital

Cash is not a failure state.

The optimizer must evaluate:

`Expected opportunity value of cash`

not merely:

`Return lost while holding cash`.

### Rule WB-3 — Capital allocation hurdle

Every new strategy sleeve must answer:

> Why should existing capital leave the current Champion to fund this Challenger?

Require a measurable **Capital Reallocation Benefit** after costs and risk.

### Rule WB-4 — Patience is a parameter

Test holding-period extensions and delayed reaction rules.

A strategy that needs constant action must prove that its extra activity creates enough independent edge to justify the complexity.

---

## 66.3 Ray Dalio: principles, believability-weighted disagreement and systemization

Dalio's public principles emphasize radical open-mindedness, systematic decision making, learning through disagreement and weighting views by demonstrated credibility and causal understanding. citeturn708951search1turn708951search3turn708951search6

Translate into the Skill:

### Rule RD-1 — Believability-weighted research sources

Every external research idea receives evidence-quality tags:

- `A`: primary source + reproducible data + clear method;
- `B`: strong institutional research with transparent methodology;
- `C`: credible expert commentary but incomplete reproducibility;
- `D`: secondary commentary;
- `E`: social-media / anecdotal / unsupported.

Only A/B evidence can directly create high-priority experiments.

### Rule RD-2 — Triangulation

For important investment hypotheses, seek at least three independent evidence types:

1. historical market evidence;
2. economic/behavioral rationale;
3. independent research or alternative implementation.

If all three point in the same direction, research priority rises.

### Rule RD-3 — Structured disagreement

For every proposed Champion improvement, automatically create a **Devil's Advocate Challenger** whose job is to explain why the improvement may be wrong.

The research report must show:

`Pro case / Anti case / What evidence would decide?`

### Rule RD-4 — Turn mistakes into principles

A failed experiment should produce a reusable lesson rather than disappear from the log.

Example:

`Failure: unconditional dip buying`

becomes:

`Principle: mean reversion requires regime permission.`

---

# 67. Institutional research culture: scientific method, not expert worship

Man AHL describes an empirical/scientific mindset and a culture of constructive challenge; its recent trend research explicitly frames portfolio construction as a trade-off among long-run Sharpe, crisis Sharpe, diversification and liquidity. citeturn708951search0turn708951search4

The Skill should therefore operate like a small research lab.

## 67.1 Research roles

Every research cycle conceptually creates five roles:

1. **Researcher** — proposes the idea.
2. **Quant** — converts it to a measurable rule.
3. **Skeptic** — looks for leakage, overfit and hidden exposure.
4. **Risk manager** — tests tail behavior and concentration.
5. **Editor** — decides whether the knowledge is strong enough to enter the permanent library.

No role may approve its own proposal without challenge.

## 67.2 Research packet

Every new idea must become a standardized packet:

`Idea ID`
`Source`
`Claim`
`Why it might work`
`What would falsify it`
`Market applicability`
`Feature definition`
`Expected signal`
`Expected failure mode`
`Test design`
`Result`
`OOS result`
`Cost result`
`Decision`

---

# 68. Knowledge acquisition engine

The Skill must continuously scan high-value sources, but should not treat information volume as knowledge quality.

## 68.1 Source tiers

### Tier 1 — Primary

- annual letters;
- manager letters;
- official research papers;
- exchange rules;
- fund/index methodology documents;
- first-party strategy descriptions;
- audited or highly credible public data.

### Tier 2 — Institutional secondary

- academic papers;
- established research organizations;
- major financial research platforms.

### Tier 3 — Expert commentary

- interviews;
- conference talks;
- thoughtful essays.

### Tier 4 — Discovery only

- social media;
- forums;
- promotional materials;
- ranking articles without methodology.

Tier 4 may create a **research lead**, but never directly create a strategy rule.

## 68.2 Novelty filter

A new piece of information is valuable only if it is:

`new + relevant + testable + potentially decision-changing`

If it is merely a restatement of an existing principle, store it as reinforcement rather than creating another strategy.

## 68.3 Evidence deduplication

Before creating a new experiment, check whether the same mechanism has already been tested.

The Skill must search its research archive by:

- mechanism;
- signal;
- asset universe;
- horizon;
- failure mode.

---

# 69. Knowledge distillation engine

The Skill should not store raw articles as the primary memory.

It should distill each source into a compact **Investment Principle Card**.

## Principle Card schema

`Principle_ID`
`Source`
`Date`
`Investor/Institution`
`Claim`
`Mechanism`
`Conditions`
`Failure conditions`
`China ETF translation`
`Research priority`
`Evidence strength`
`Existing related experiments`
`Last validation date`

Example:

`P-017`

Claim:

“Trend signals work differently in strong and weak regimes.”

Mechanism:

Persistent information diffusion can create continuation, while sharp reversals can create whipsaw.

ETF translation:

Trend sleeve gets more risk when trend and breadth agree; mean-reversion sleeve gets more risk only when longer-term trend is healthy.

The Principle Card, not the article, becomes the permanent knowledge unit.

---

# 70. Knowledge graph

Build a lightweight graph linking:

`Investor → Principle → Mechanism → Signal → Strategy → Market Regime → Outcome`

Example:

`Howard Marks`
→ `cycle awareness`
→ `crowding / valuation / psychology`
→ `regime filter`
→ `conditional risk budget`
→ `high valuation + weak breadth`
→ `reduced exposure`

This prevents the Skill from learning isolated tips without understanding relationships.

---

# 71. Evidence decay and knowledge aging

Not all knowledge should remain equally important forever.

Assign every Principle Card a:

`ConfidenceScore`

and:

`FreshnessScore`

Confidence rises when:

- replicated across independent datasets;
- survives OOS tests;
- works across regimes;
- survives costs;
- remains valid after parameter perturbation.

Confidence falls when:

- repeated OOS failures occur;
- implementation costs increase;
- market structure changes;
- the underlying mechanism disappears;
- the idea only works in one narrow period.

Knowledge must never be deleted merely because it is old; it should be **downgraded, archived and re-testable**.

---

# 72. Research portfolio: diversify the questions, not just the assets

The Skill must allocate a limited research budget across different hypothesis families.

Default research budget:

- 25% signal innovation;
- 25% risk/portfolio construction;
- 15% execution/cost reduction;
- 15% robustness/anti-overfitting;
- 10% new markets/data;
- 10% behavioral/process improvement.

No single research theme may consume >40% of total research capacity without explicit justification.

This prevents “optimization tunnel vision.”

---

# 73. Research improvement ladder

Every new idea should pass through increasing levels of evidence.

### Level 0 — Observation

Interesting pattern, no test.

### Level 1 — Hypothesis

A causal or behavioral explanation is proposed.

### Level 2 — Simple test

One feature, one rule, basic benchmark.

### Level 3 — Controlled test

Costs, lags and realistic execution added.

### Level 4 — Robustness test

Parameter neighborhoods, regimes, liquidity and placebo tests.

### Level 5 — Walk-forward

Rolling OOS evaluation.

### Level 6 — Challenger

Competes against Champion and Controls.

### Level 7 — Shadow portfolio

Runs without affecting capital.

### Level 8 — Production candidate

Approved for limited allocation.

### Level 9 — Champion

Sustained evidence + implementation record.

The system must never jump from Level 0 to Level 9.

---

# 74. Shadow portfolio learning

Before allowing a new strategy to affect real capital, maintain a shadow portfolio.

Record:

- predicted positions;
- actual executable positions;
- hypothetical returns;
- slippage;
- missed fills;
- rule violations;
- behavior burden.

Compare:

`Research Backtest vs Shadow vs Real`

Any meaningful divergence triggers an implementation investigation.

---

# 75. Online learning without online overfitting

The Skill may adapt to new information, but must not continuously retune itself using the newest data without safeguards.

Use three data roles:

`Training`
`Validation`
`Locked Evaluation`

Once an evaluation period is used to choose a strategy, it becomes part of the historical research record and is no longer considered a clean final test set.

The system must maintain a **rolling untouched frontier** for future validation whenever sufficient data exists.

---

# 76. Meta-learning: optimize the optimizer

The Skill must learn which kinds of research changes are most productive.

For every experiment record:

`HypothesisFamily`
`ComplexityCost`
`ResearchTime`
`Success/Failure`
`OOS Gain`
`Drawdown Change`
`Turnover Change`
`Robustness Change`

Then estimate:

`ResearchROI = Robust OOS Improvement / Research Complexity`

Over time, allocate more research budget to high-ResearchROI families, but keep an exploration floor so that the system does not become trapped in one local optimum.

Recommended:

`70% exploitation / 30% exploration`

This split is itself not sacred and should be reviewed periodically.

---

# 77. Failure library

Failed strategies are valuable training data.

Maintain a permanent library of failure patterns:

- parameter overfit;
- trend whipsaw;
- unconditional dip buying;
- volatility chasing;
- liquidity trap;
- concentration masquerading as diversification;
- excessive turnover;
- signal duplication;
- late exits;
- early exits;
- news overreaction;
- benchmark beta mistaken for alpha;
- regime-specific luck.

Before launching any Challenger, automatically compare it against the failure library.

If it resembles a historically failed pattern, require stronger evidence.

---

# 78. Counterfactual learning engine

After each major live or shadow-period event, create counterfactuals:

`What if we had not entered?`
`What if we entered one day later?`
`What if position size were 50% smaller?`
`What if the regime gate were active?`
`What if we held the Runner longer?`

The purpose is not hindsight optimization.

The purpose is to identify **decision sensitivity**.

High decision sensitivity means:

> Small implementation differences produce large outcomes.

Such strategies receive lower confidence.

---

# 79. Decision quality engine

Separate four outcomes:

1. good process / good outcome;
2. good process / bad outcome;
3. bad process / good outcome;
4. bad process / bad outcome.

The Skill must learn more from categories 2 and 3 than from raw P&L alone.

A losing trade with a valid process is not automatically a strategy failure.

A profitable trade based on a broken rule is not evidence to reinforce the rule.

---

# 80. Top-investor learning loop

For every new top-investor insight, execute:

`Source Verification`
→ `Principle Extraction`
→ `Mechanism Identification`
→ `ETF Translation`
→ `Falsification Question`
→ `Low-Complexity Challenger`
→ `Risk Challenger`
→ `Diversification Challenger`
→ `OOS Test`
→ `Cost Test`
→ `Regime Test`
→ `Promotion / Rejection`

This is the core learning loop of v5.0.

---

# 81. Expert disagreement matrix

The system should intentionally preserve disagreements among schools of thought.

Examples:

| School | Core belief | Possible ETF translation |
|---|---|---|
| Value | price matters vs intrinsic value | valuation tilt / downside filter |
| Trend | persistence matters | trend gate / Runner |
| Momentum | winners continue | relative strength |
| Mean reversion | shocks reverse | conditional dip buying |
| Defensive | risk premia matter | low-vol / quality / cash |
| Macro / All Weather | diversification across drivers | cross-asset defensive proxy |
| Multi-strategy | independent edges compound | strategy ensemble |

The Skill should seek **conditional synthesis**, not forced consensus.

Example:

`Trend says stay away + Value says cheap`

→ do not average the scores blindly.

Instead test:

`Wait for trend stabilization, then deploy part of the value allocation.`

---

# 82. Continuous improvement of the investor, not only the strategy

The Skill must maintain a personal operating system for the intended investor.

For a small-account beginner with a maximum drawdown budget of 25%:

### Personal constraints

- no leverage by default;
- limited ETF universe;
- limited concurrent positions;
- predefined trade schedule;
- predefined maximum loss budget;
- explicit cash reserve;
- low implementation burden.

### Personal learning metrics

Track:

- rule adherence rate;
- impulsive trade count;
- average deviation from target position;
- average time spent reacting to news;
- number of strategy changes per quarter;
- revenge-trading incidents;
- maximum discretionary override count.

A strategy that requires a professional trader's attention is not a valid Champion for this user profile, even if its backtest is excellent.

---

# 83. Champion evolution rules

The Champion should evolve slowly.

### Minor change

One rule change, one validated mechanism.

Use a minor version.

### Major change

Different architecture or risk model.

Requires a fresh validation cycle.

### Emergency change

Only allowed when:

- implementation rules change;
- ETF market structure materially changes;
- a critical data defect is discovered;
- or live behavior violates the declared risk budget.

Recent poor performance by itself is **not** an emergency.

---

# 84. Strategy retirement rules

A Champion is retired only when evidence shows at least one of:

1. repeated OOS deterioration;
2. mechanism decay;
3. implementation failure;
4. persistent violation of the risk budget;
5. a materially superior Challenger with stronger robustness;
6. permanent market-structure change.

Retirement must include a post-mortem:

`Why did it work?`
`Why did it stop working?`
`What early warning could have detected the decay?`
`What principle survives?`

This post-mortem becomes new knowledge.

---

# 85. Anti-self-delusion protocol

At the end of every research cycle, the Skill must answer:

1. What changed?
2. Why should it work?
3. What evidence supports it?
4. What evidence contradicts it?
5. What is merely narrative?
6. Which result is likely due to chance?
7. How many degrees of freedom were searched?
8. What simple benchmark could explain the result?
9. What would make us reject the new Champion?
10. What should we deliberately **not** change?

The tenth question is mandatory.

A good research system learns not only what to add, but also what to leave alone.

---

# 86. Monthly self-review

At least once per month, run:

### Knowledge review

- new high-value sources;
- repeated concepts;
- new principles;
- outdated principles;
- unresolved disagreements.

### Strategy review

- Champion vs controls;
- OOS performance;
- drawdown;
- regime behavior;
- attribution;
- cost leakage.

### Process review

- research ROI;
- false discoveries;
- overfitting incidents;
- implementation errors;
- behavioral errors.

### Next-cycle review

Select at most five research priorities.

Do not optimize everything at once.

---

# 87. Quarterly deep review

Every quarter, conduct a deeper reset:

1. re-score all Principle Cards;
2. retire weak hypotheses;
3. revisit archived failures;
4. compare strategy families;
5. review the research budget;
6. review Champion assumptions;
7. stress-test the full portfolio;
8. verify the 25% drawdown constraint;
9. test whether complexity has increased without sufficient gain;
10. create the next research roadmap.

---

# 88. Core philosophy of continuous learning

The Skill should behave less like a chatbot that remembers opinions and more like a disciplined investment lab.

Its memory should contain:

`Facts`
`Principles`
`Hypotheses`
`Experiments`
`Failures`
`Evidence`
`Strategy Versions`
`Decision Logs`

The Skill must distinguish:

`I know`
`I suspect`
`I tested`
`I rejected`
`I still don't know`

The last category is essential.

Admitting uncertainty is part of the system's learning capability.

---

# 89. Final v5.0 architecture

`External Evidence`
→ `Source Quality Filter`
→ `Knowledge Distillation`
→ `Principle Library`
→ `Knowledge Graph`
→ `Hypothesis Generator`
→ `Research Portfolio`
→ `Controlled Experiment`
→ `Backtest`
→ `Walk Forward`
→ `Stress Test`
→ `Counterfactual`
→ `Attribution`
→ `Behavior Review`
→ `Evidence Update`
→ `Champion / Challenger`
→ `Shadow Portfolio`
→ `Production`
→ `Post-Mortem`
→ `New Principles`
→ `Next Research Cycle`

This loop is intentionally circular.

---

# 90. Ultimate objective

The system's objective is not to become increasingly complicated.

It is to become increasingly **correct about what it knows, uncertain about what it does not know, disciplined about risk, and efficient at discovering robust improvements**.

For the intended small-account beginner profile, the final objective remains:

> **Maximize long-term risk-adjusted compounding while keeping the probability of a portfolio drawdown beyond 25% acceptably low, with a strategy simple enough to execute consistently.**

The default preference order is:

`Survival → Robustness → Risk-adjusted return → Absolute return → Complexity`

Never reverse this order merely because a new backtest looks attractive.

# ETF-Volatility-Alpha v6.0 — Top-Tier Research Operating System

## 91. v6.0 mission: upgrade from a strategy optimizer to a research operating system

The Skill must no longer behave as a single optimizer searching for a better backtest.
It must behave as a **specialized, auditable, adversarial, continuously learning research operating system**.

The target is not:

> highest historical CAGR.

The target is:

> highest expected out-of-sample risk-adjusted compounding subject to the investor's hard constraints, implementation reality, research uncertainty and a maximum drawdown guardrail.

For the intended small-account beginner profile:
- hard drawdown ceiling: 25%;
- research target drawdown: 15–20%;
- no leverage by default;
- liquidity-first ETF universe;
- low operational complexity;
- limited turnover;
- every promoted rule must be executable by a normal retail investor.

---

## 92. Top-tier design principle: specialize the research agents

A single general-purpose reasoning loop is not sufficient for deep quantitative research.

The Skill must split the research workflow into specialized roles:

### Agent A — Research Scout
Finds new evidence, papers, strategy ideas, market-structure changes and implementation knowledge.

### Agent B — Distiller
Converts raw information into explicit, testable investment principles.

### Agent C — Quant Builder
Translates a principle into precise, executable features and signals.

### Agent D — Backtest Engineer
Runs reproducible historical experiments under frozen data and execution assumptions.

### Agent E — Adversarial Reviewer
Attempts to falsify the proposed edge.

### Agent F — Risk Architect
Tests concentration, drawdown, volatility, correlation and tail exposure.

### Agent G — Execution Analyst
Models turnover, spreads, slippage, delay, liquidity and partial fills.

### Agent H — Statistical Auditor
Checks multiple testing, selection bias, parameter sensitivity, significance and false discovery risk.

### Agent I — Portfolio Allocator
Decides how much capital the candidate deserves relative to existing strategies.

### Agent J — Research Editor
Produces the final evidence-weighted decision and preserves the research record.

No single agent is allowed to approve promotion by itself.

This design is inspired by the principle demonstrated in recent systematic research workflows: specialized pipelines can trade breadth for depth, run multiple proposal variants in parallel, check consistency, and progressively refine research without forcing all reasoning into one pass. citeturn163120search0turn163120search7

---

## 93. Parallel proposal generation

For each research question, generate multiple independent candidate implementations instead of one.

Default:
- 5 low-complexity proposals;
- 5 alternative implementations;
- 3 deliberately conservative proposals;
- 2 adversarial / anti-signal proposals.

The purpose is not to maximize ideas.

The purpose is to discover whether the underlying concept survives reasonable implementation changes.

If 10 independently generated implementations all fail, deprioritize the concept.

If 10 implementations cluster around the same improvement and outperform the control under OOS testing, increase confidence.

The system must inspect the **distribution of results**, not only the best member.

---

## 94. Good / Bad / Broad research calibration suite

Every major research-generation engine must be periodically evaluated with three classes of test ideas.

### Good ideas
Known improvements or strong hypotheses that should work under a specified benchmark.

Purpose:
- check discovery ability;
- check implementation fidelity.

### Bad ideas
Plausible-looking ideas expected to fail.

Purpose:
- ensure the system is capable of saying “no”;
- detect an optimizer that mechanically manufactures positive backtests.

### Broad ideas
Genuinely uncertain hypotheses.

Purpose:
- assess whether the system can discover conditional or regime-specific value rather than forcing binary conclusions.

A research engine that produces positive results on almost everything is considered unhealthy.

This mirrors the recent AlphaTrend workflow's use of good, bad and broad hypotheses to test whether an agentic research system can distinguish signal from noise rather than only generate attractive results. citeturn163120search0

---

## 95. Research consensus is not evidence

When several agents agree, record:

`AgentConsensus`

but do not treat consensus as empirical support.

The evidence hierarchy is:

1. clean OOS replication;
2. cross-regime replication;
3. cross-implementation replication;
4. cost robustness;
5. parameter-neighborhood stability;
6. independent data-source replication;
7. agent consensus;
8. expert opinion.

Expert opinion and model agreement can prioritize experiments, but they cannot override weak empirical evidence.

---

## 96. Research reproducibility contract

Every experiment receives a unique `Experiment_ID` and stores:

- data snapshot ID;
- ETF universe snapshot;
- feature version;
- signal code/version;
- portfolio-construction version;
- transaction-cost model version;
- execution assumptions;
- random seed where applicable;
- train/validation/test dates;
- research prompt/hypothesis;
- analyst/agent identities;
- number of prior related experiments;
- final result hash / report hash.

An experiment is not considered reproducible unless another run using the same inputs can reproduce materially equivalent outputs.

---

## 97. Immutable test set firewall

A final OOS period must be frozen.

No parameter, universe, feature, score weight, or research hypothesis may be chosen using information from the final test period.

The final test set is treated as:

`LOCKED`

The lock may only be broken under explicit governance, and breaking the lock permanently marks the version as research-only.

For continuous learning, roll the historical boundary forward only after the previously locked period has been evaluated and archived.

This preserves the difference between learning from the past and repeatedly peeking into the future.

---

## 98. Data lineage and point-in-time universe engine

The Skill must maintain point-in-time versions of:

- ETF existence;
- listing date;
- suspension state;
- liquidity;
- index methodology;
- constituent changes where relevant;
- fees and trading rules;
- price/volume histories;
- corporate actions;
- benchmark definitions.

A historical backtest must use only information that would have been observable at that historical timestamp.

The historical ETF universe must never be defined using today's surviving ETFs alone.

Look-ahead and survivorship bias are explicitly recognized as core quantitative-investing failure modes by CFA Institute. citeturn163120search1turn861824search0

---

## 99. Statistical validity layer

The Skill must add a formal statistical audit before promotion.

At minimum evaluate, where applicable:

- Probabilistic Sharpe Ratio;
- Deflated Sharpe Ratio;
- bootstrap confidence intervals;
- block bootstrap for serial dependence;
- multiple-testing burden;
- false-discovery risk;
- Probability of Backtest Overfitting style diagnostics;
- White-style reality-check / SPA-style logic where implementable;
- sensitivity to research-window selection.

Do not interpret a high raw Sharpe from a large research search as strong evidence without adjusting for the number of attempts.

The more experiments the lab has run, the higher the evidentiary standard becomes.

---

## 100. Research Degrees of Freedom Budget

The research lab receives a finite monthly research budget.

Track:

`Hypotheses`
`Parameter Choices`
`Universe Variants`
`Signal Variants`
`Portfolio Variants`
`Cost Variants`
`Validation Variants`

Every experiment consumes research degrees of freedom.

When the research budget becomes large relative to the evidence base:

- reduce exploratory search;
- increase adversarial tests;
- favor simpler pre-specified hypotheses;
- require stronger OOS evidence.

Research is therefore treated as a scarce resource, not an unlimited parameter search.

---

## 101. Nested validation architecture

Use three distinct layers whenever data length permits:

### Research set
Used to build and debug the hypothesis.

### Validation set
Used to compare candidate implementations.

### Final OOS set
Used only once for promotion evidence.

For adaptive systems, use nested walk-forward evaluation:

`inner loop = candidate research`
`outer loop = honest performance estimate`

A candidate that only wins inside the inner loop does not qualify as robust evidence.

CFA's current backtesting guidance explicitly emphasizes rolling-window / walk-forward analysis and warns about survivorship, look-ahead and structural breaks. citeturn861824search0

---

## 102. Research distribution, not point estimate

Every important candidate must report a result distribution rather than one backtest number.

Examples:

- Sharpe distribution across implementations;
- OOS CAGR distribution across windows;
- drawdown distribution across stress scenarios;
- sensitivity distribution across nearby parameters;
- cost-adjusted return distribution.

Promote based on the **center and stability of the distribution**, not the best observation.

---

## 103. Strategy survival test

A candidate must be tested under controlled perturbations:

- signal lag +1 day;
- execution price shifted adversely;
- costs ×2;
- costs ×3;
- position cap reduced;
- position cap increased;
- rebalance delayed;
- data missingness;
- modest parameter perturbation;
- one ETF removed;
- strongest ETF removed;
- weakest ETF removed.

If the entire edge disappears under tiny perturbations, classify it as fragile.

---

## 104. Crisis-first evaluation

Because the user's primary constraint is drawdown, crisis metrics receive elevated weight.

Every candidate must report:

- crisis-period Sharpe;
- worst rolling 3-month return;
- worst rolling 6-month return;
- time-to-recovery;
- maximum drawdown;
- maximum drawdown duration;
- downside capture;
- performance during synchronized ETF correlation spikes.

Trend research by Man AHL illustrates why long-run Sharpe and crisis Sharpe can be materially different objectives and why portfolio construction should explicitly account for the defensive objective. citeturn861824search1turn861824search9

---

## 105. Drawdown governor for the small-account profile

The production portfolio uses a state machine:

`DD < 5%` → normal

`5–8%` → caution

`8–12%` → reduce gross risk

`12–15%` → defensive mode

`15–20%` → capital preservation priority

`20–25%` → emergency defense and strategy review

`>=25%` → strategy considered failed unless the breach is demonstrably caused by an implementation anomaly.

These are guardrails, not predictive signals.

The purpose is to make the 25% requirement operational rather than aspirational.

---

## 106. Capital allocation should be uncertainty-aware

Strategy weights must not depend solely on expected Sharpe.

For each strategy sleeve estimate:

- expected return;
- volatility;
- drawdown risk;
- correlation;
- estimation uncertainty;
- recent evidence quality;
- implementation capacity;
- current drawdown state.

Then apply shrinkage toward conservative weights.

A strategy with a high estimated Sharpe but weak evidence should not automatically receive more capital than a lower-Sharpe strategy with much stronger evidence.

---

## 107. Evidence-weighted capital allocation

Define an `EvidenceScore` from:

- OOS replication;
- independent implementation consistency;
- cross-regime evidence;
- cost robustness;
- parameter plateau;
- sample size;
- data quality;
- statistical audit.

Define:

`AdjustedEdge = RawEdge × EvidenceScore × RegimeFit × ImplementationScore`

Capital allocation then operates on `AdjustedEdge`, not raw historical edge.

---

## 108. Strategy correlation is dynamic

Do not assume strategy correlation is stationary.

Track:

- rolling return correlation;
- rolling drawdown overlap;
- tail correlation;
- conditional correlation during high volatility;
- factor exposure overlap.

If previously independent strategies suddenly converge, reduce the combined risk budget.

Diversification must be evaluated in the environment in which it matters most: stress.

---

## 109. Research-to-production graduation ladder

Every strategy has a lifecycle:

`Idea`
→ `Prototype`
→ `Research`
→ `Validation`
→ `Shadow`
→ `Champion Candidate`
→ `Production`
→ `Monitoring`
→ `Review`
→ `Retire / Rebuild`

No strategy jumps directly from idea to production.

---

## 110. Shadow portfolio before promotion

Every serious Challenger must run as a shadow portfolio for a predefined period.

Shadow mode records:

- hypothetical signal;
- intended position;
- actual market price;
- simulated execution;
- slippage proxy;
- divergence from current Champion;
- drawdown contribution.

The purpose is to detect implementation anomalies before capital is allocated.

---

## 111. Post-deployment model risk monitoring

Once in production, compare:

`Expected Distribution`
vs.
`Realized Distribution`

Monitor:

- realized turnover vs expected;
- realized slippage vs assumed;
- realized win/loss distribution;
- factor exposure drift;
- signal decay;
- drawdown behavior;
- correlation drift;
- liquidity deterioration.

A model that remains profitable but behaves materially differently from its research distribution must enter review.

---

## 112. Research drift detection

The system must detect when the research environment itself changes.

Possible drift variables:

- volatility regime;
- cross-sectional dispersion;
- correlation structure;
- ETF liquidity;
- bid/ask conditions;
- trend persistence;
- market breadth;
- signal crowding proxies.

A change in the environment does not automatically invalidate a strategy.

It triggers:

`Re-evaluation`, not `panic modification`.

---

## 113. Research orthogonality test

Before adding a new signal, determine whether it truly contributes new information.

Report:

- correlation with existing signals;
- incremental predictive power;
- incremental OOS contribution;
- marginal drawdown contribution;
- marginal turnover;
- marginal complexity.

Reject “new” features that mostly duplicate existing information.

---

## 114. Signal budget

The final production model has a finite signal budget.

Every additional rule must pay for itself by producing:

`OOS benefit > Risk + Cost + Complexity + Research burden`

When the marginal benefit becomes small, stop adding signals.

This is an explicit defense against feature accumulation.

---

## 115. Research stop rules

The system must be allowed to stop searching.

Stop a research branch when:

- repeated candidates fail;
- evidence quality declines;
- the remaining improvements are mostly parameter tweaks;
- complexity rises faster than robustness;
- the Champion is already near the investor's target risk/return envelope.

“No new model” is a valid research result.

---

## 116. Knowledge quality score

Every learned principle receives:

`KnowledgeScore = Evidence × Replication × Applicability × Freshness × Implementation`

with an uncertainty penalty.

Maintain states:

`Candidate`
`Supported`
`Strongly Supported`
`Conditional`
`Weakening`
`Rejected`
`Archived`

The knowledge base must preserve both positive and negative evidence.

---

## 117. Knowledge decay

Every principle has a review date.

Old evidence loses weight unless reinforced by new OOS observations.

A principle is not deleted merely because it becomes old.
It becomes:

`stale`

and requires revalidation before receiving material research weight.

---

## 118. Expert-learning protocol

When studying a top investor, systematic manager or research paper:

1. identify the claim;
2. classify the claim as philosophy, process, signal, portfolio construction or execution;
3. separate evidence from narrative;
4. convert the claim into a falsifiable hypothesis;
5. create good/bad/broad variants;
6. run independent implementations;
7. test OOS;
8. test costs;
9. test regime dependence;
10. record the result in the knowledge graph.

Never copy a position, stock pick or public trade directly into the strategy.

Copy process only when the process can be translated and validated.

---

## 119. Second-order investment reasoning engine

For each major research conclusion ask:

1. What is the obvious interpretation?
2. What is the second-order consequence?
3. Who else is likely acting on the same information?
4. If the edge is widely known, what changes?
5. What would make the signal fail?
6. What alternative explanation fits the data?

Second-order reasoning is a hypothesis generator and failure detector, not a substitute for empirical testing.

---

## 120. Research adversary protocol

Every promoted Challenger must receive an adversarial memo containing at least:

- strongest case against;
- likely hidden bias;
- most vulnerable parameter;
- most vulnerable market regime;
- most dangerous implementation assumption;
- simplest benchmark that could invalidate it.

A Challenger cannot be promoted without a documented response to the adversarial memo.

---

## 121. Benchmark hierarchy

A strategy should be compared at several levels:

### Level 1 — Naive
Buy-and-hold broad index ETF.

### Level 2 — Simple tactical
One trend gate.

### Level 3 — Simple rotation
Relative momentum.

### Level 4 — Current Champion
Existing production strategy.

### Level 5 — New Challenger
Proposed improvement.

A highly complex Challenger that cannot beat the Champion or provide materially better drawdown control should be rejected.

---

## 122. Retail feasibility gate

For the intended user profile, reject candidates requiring:

- high intraday turnover;
- difficult execution;
- leverage;
- derivatives dependence;
- unstable liquidity;
- dozens of simultaneous positions;
- minute-level monitoring;
- discretionary overrides that cannot be formalized.

A theoretically superior strategy that the intended investor cannot execute reliably is not a superior strategy for this system.

---

## 123. Research objective hierarchy v6.0

The scoring hierarchy becomes:

1. survival;
2. drawdown control;
3. robustness;
4. OOS evidence;
5. implementation quality;
6. risk-adjusted return;
7. absolute return;
8. complexity.

This ordering is intentionally different from a pure institutional return-maximization framework because the user profile has a hard drawdown constraint.

---

## 124. v6.0 research loop

The continuous research engine now follows:

`Observe`
→ `Scout`
→ `Distill`
→ `Hypothesize`
→ `Generate Variants`
→ `Peer Challenge`
→ `Controlled Experiment`
→ `Statistical Audit`
→ `Walk Forward`
→ `Stress`
→ `Counterfactual`
→ `Portfolio Test`
→ `Shadow`
→ `Champion Decision`
→ `Deploy / Reject`
→ `Monitor`
→ `Post-Mortem`
→ `Update Knowledge`
→ `Update Research Budget`
→ `Generate Next Hypotheses`

This is the core self-improvement loop.

---

## 125. v6.0 top-tier acceptance criteria

A v6.0 strategy is considered top-tier within this research framework only when:

- data provenance is auditable;
- the universe is point-in-time correct;
- execution assumptions are explicit;
- multiple testing is acknowledged;
- OOS evidence is positive;
- parameter neighborhoods are stable;
- multiple implementations agree on direction;
- cost stress does not destroy the edge;
- crisis performance is acceptable;
- drawdown remains compatible with the 25% hard ceiling;
- the strategy improves or diversifies the Champion;
- research complexity is justified;
- production results remain consistent with the research distribution.

No backtest return, expert reputation, model confidence or LLM consensus can waive these criteria.

---

## 126. v6.0 final architecture

`External Evidence`
→ `Source Quality`
→ `Knowledge Distillation`
→ `Knowledge Graph`
→ `Research Budget`
→ `Specialist Agents`
→ `Parallel Proposals`
→ `Good / Bad / Broad Calibration`
→ `Signal Builder`
→ `Data Lineage`
→ `Point-in-Time Universe`
→ `Backtest Engine`
→ `Statistical Audit`
→ `Walk Forward`
→ `Stress / Scenario / Simulation`
→ `Adversarial Review`
→ `Portfolio & Capital Allocation`
→ `Shadow Portfolio`
→ `Champion / Challenger`
→ `Production Monitoring`
→ `Drift Detection`
→ `Post-Mortem`
→ `Knowledge Update`
→ `Research Budget Update`
→ `Next Cycle`

---

## 127. v6.0 governing principle

> **Do not optimize the strategy harder than you can validate it. Optimize the research process so that every improvement is harder to fool, easier to reproduce, and more relevant to the investor's actual constraints.**

The Skill must become better not by accumulating more rules, but by becoming better at:

- discovering useful ideas;
- rejecting bad ideas quickly;
- measuring evidence honestly;
- allocating research effort intelligently;
- allocating capital cautiously;
- detecting when the world has changed;
- learning from failure;
- preserving uncertainty;
- and stopping when additional complexity no longer pays.


---

# 128. v7.0 Expert-Panel Review — 顶级系统应再补什么

本节不是声称任何机构“认可”本 Skill，而是依据公开可验证的专业研究实践进行架构审查。重点参考：

- Two Sigma：数据 sourcing / preparation → modeling → portfolio construction → execution，并强调大量模拟、数据质量、独立预测组合、交易成本与风险的联合建模，以及自动化规模化研究。 https://www.twosigma.com/businesses/investment-management/
- Man AHL 2026 AlphaTrend：专业化 agent workflow、专门任务系统、并行研究、多个候选实现与一致性/校准验证。 https://www.man.com/insights/alphatrend-agentic-research-workflows
- CFA Institute 2026 Backtesting & Simulation：滚动回测之外，还需要历史情景、假设模拟、敏感性分析，并关注结构性断点、幸存者偏差、前视偏差和尾部依赖。 https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/backtesting-and-simulation

基于上述审查，v7.0 新增：

1. Data Provenance & Reproducibility OS
2. Research DAG / Lineage
3. Statistical Red-Team
4. Capacity & Market-Impact Lab
5. Alpha Half-Life & Decay Monitor
6. Regime-Transfer Validation
7. Research Value / Expected Value of Information (EVI)
8. Model-Risk Committee
9. Shadow → Canary → Production → Rollback
10. Online Learning Guardrails
11. Knowledge Confidence & Forgetting
12. Strategy Correlation & Crowding Monitor
13. Portfolio-level Uncertainty Budget
14. Complexity Budget
15. Research Freeze / Immutable Test Set
16. Failure Library as a first-class asset

---

# 129. Data Provenance & Reproducibility OS

顶级研究系统首先必须做到：任何一个绩效数字都能追溯到“哪份数据、哪版代码、哪个参数、哪个时间点、哪个交易假设”。

每个实验必须生成唯一的 `ExperimentID`，并保存：

- 数据源；
- 数据版本 / snapshot date；
- 文件 hash；
- universe definition；
- feature version；
- signal version；
- portfolio constructor version；
- execution model version；
- cost assumptions；
- random seed；
- software environment；
- research prompt / hypothesis；
- analyst / agent；
- timestamp。

输出必须能够被完全重放。

新增硬规则：

> **无法重现的结果，不得进入知识库，不得进入 Champion 候选。**

---

# 130. Research DAG — 研究血缘图

把整个研究过程从“文档”升级为 Directed Acyclic Graph：

`Source`
→ `Evidence`
→ `Principle`
→ `Hypothesis`
→ `Feature`
→ `Signal`
→ `Portfolio`
→ `Experiment`
→ `Validation`
→ `Decision`

每个节点保存输入、输出、版本和父节点。

这样可以回答：

- 这个规则源于哪个假设？
- 这个假设来自哪条证据？
- 这条证据被哪些策略复用？
- 哪些实验共享同一信息源？
- 一个“新策略”到底增加了多少独立信息？

同一来源被反复改写产生多个“新策略”时，自动降低独立性评分，防止把同一 Alpha 包装成几十个发现。

---

# 131. Statistical Red-Team v7

所有高收益候选必须经过统计红队审核。

## 必测项

- Probabilistic Sharpe Ratio；
- Deflated Sharpe Ratio；
- bootstrap confidence intervals；
- block bootstrap / stationary bootstrap；
- multiple-testing correction；
- False Discovery Rate；
- White Reality Check / SPA 类检验（可适用时）；
- post-selection bias assessment；
- backtest overfitting probability proxy；
- probability of backtest ruin。

## 核心问题

不要只问：

> “这个策略是不是赚钱？”

还要问：

> “在我们已经尝试过这么多策略之后，它仍然看起来像真 Alpha 的概率是多少？”

任何只在“最佳实验”中显著、但调整研究自由度后优势消失的策略，一律标记：

`Selection-Bias-Risk = HIGH`

---

# 132. Hypothesis Prior — 先验必须进入研究

不能让所有新想法拥有相同可信度。

每条 Hypothesis 给出：

`Prior = Economic Logic × Behavioral Logic × Independent Evidence × Implementation Plausibility`

然后再用数据更新：

`Posterior Evidence = Prior × Experimental Evidence`

但不得把“过去名人成功”直接等同于当前 Alpha。

专家经验只能提高研究优先级，不能绕过实证验证。

---

# 133. Expected Value of Information（EVI）Research Budget

研究资源是有限的，所以不是“有什么想法都回测”。

每个研究题目估算：

`ResearchPriority = EVI × RobustnessPotential × PortfolioRelevance ÷ CostOfResearch`

EVI 考虑：

- 如果成功，可能改善多少收益/回撤；
- 如果失败，能排除多少错误方向；
- 是否能够影响多个策略 sleeve；
- 数据是否容易获得；
- 是否与已有研究高度重复。

优先研究“能够改变未来很多决策”的问题。

---

# 134. Capacity & Liquidity Lab

小资金策略虽然通常没有大型机构的市场冲击问题，但仍必须研究：

- 成交额最低阈值；
- bid-ask spread；
- 订单簿深度代理；
- 开盘/收盘成交拥挤；
- 跳空风险；
- 大波动时滑点扩张；
- ETF折溢价；
- 极端行情中的流动性断裂。

对用户的小资金画像，容量不是为了限制收益，而是防止策略变成“理论上高频、实际上难执行”。

必须生成：

`ExpectedGrossAlpha`
`ExpectedTradingCost`
`ExpectedNetAlpha`
`Cost/Alpha Ratio`

当 `Cost/Alpha Ratio` 超过阈值时，策略降级为 Research Only。

---

# 135. Alpha Half-Life & Decay Monitor

每个信号都必须估计：

- 信号发现日期；
- 最初 OOS；
- OOS 期间表现；
- IC/预测能力随时间的变化；
- 交易成本变化；
- 信号拥挤变化；
- 市场结构变化。

输出：

`AlphaHalfLife`
`DecayRate`
`EvidenceAge`

知识不是永久资产。

如果一个原则持续失效，降低 `KnowledgeConfidence`，而不是强行保留。

---

# 136. Regime-Transfer Validation

一个中国 ETF 策略不需要在全球市场也赚钱，但如果一个研究思想声称具有“普适性”，则应进行跨市场证据检查：

- 中国；
- 美国；
- 欧洲；
- 全球多资产；
- 不同资产类别（可行时）。

目的不是找一个参数能够跨市场赚钱，而是判断：

> **我们验证的是一个经济/行为机制，还是一段特定市场的历史巧合？**

跨市场失败不能自动否定中国策略，但会降低“机制普适性”置信度。

---

# 137. Strategy Interaction Engine

策略不再只单独评估。

每两个 Strategy Sleeve 必须评估：

- return correlation；
- drawdown overlap；
- tail correlation；
- crisis correlation；
- turnover correlation；
- factor exposure overlap。

尤其要检查：

> “平时相关性低，危机时突然一起亏损。”

因此加入：

`NormalCorrelation`
`StressCorrelation`
`TailDependence`

组合优化优先依据**危机相关性**，而不是只看普通时期相关性。

---

# 138. Portfolio-level Uncertainty Budget

以前我们主要控制资金风险。

v7.0 再增加：

> **不确定性风险。**

每个策略都拥有：

`ExpectedReturnRange`
`ExpectedVolRange`
`ConfidenceInterval`
`ModelUncertainty`

组合层面设置：

`UncertaintyBudget`

当一个策略收益看起来很高，但模型不确定性也很高时，不允许因为高回报而获得同等资本权重。

最终仓位概念升级为：

`Position = Signal × Regime × RiskBudget × Liquidity × Confidence`

---

# 139. Complexity Budget

顶级研究不是“最复杂”。

为每个策略设置：

- signal count；
- rule count；
- parameter count；
- model count；
- research degrees of freedom；
- data-source count；
- maintenance burden。

定义：

`ComplexityBudget`

任何新增复杂度必须证明至少一个：

1. 降低回撤；
2. 提高 OOS 稳定性；
3. 降低成本；
4. 增强危机表现；
5. 增加独立 Alpha；
6. 显著提高执行可靠性。

否则拒绝。

---

# 140. Good / Bad / Broad Calibration 2.0

每一个研究代理在进入生产前都必须通过三类案例：

### Good

真正可改善 Champion 的研究题目。

### Bad

有明显逻辑错误或数据窥探风险的研究题目。

### Broad

开放式、模糊、容易诱发模型“随便堆指标”的研究题目。

要求系统做到：

- 对 Good：积极推进；
- 对 Bad：主动拒绝并解释原因；
- 对 Broad：先收缩成可证伪假设。

这是评估研究 Agent 是否“会研究”的基础测试，而不仅是“会写研究报告”。

---

# 141. Expert Panel v7 — 专家角色与否决权

每一个候选策略必须经过以下虚拟专家席位：

### Alpha Researcher

负责发现收益来源。

### Data Scientist

负责数据质量和泄漏审计。

### Quant Researcher

负责统计与建模。

### Portfolio Architect

负责组合与资本配置。

### Risk Manager

负责尾部风险、回撤和相关性。

### Execution Specialist

负责成本、容量、可成交性。

### Adversarial Reviewer

负责寻找策略为什么会失败。

### Statistical Auditor

负责多重检验、选择偏差和显著性。

### Research Editor

负责简化研究结论，去除无法证实的故事。

### Final Investment Committee

只决定：

`Promote / Hold / Reject / Research Only`

其中 Risk Manager、Data Scientist、Statistical Auditor 任一人给出 `Hard Veto` 时，候选不得进入 Champion。

---

# 142. Shadow → Canary → Production → Rollback

以后 Champion 晋升分四阶段：

### Stage 0 — Research

只允许回测。

### Stage 1 — Shadow

使用真实市场数据实时生成信号，但不交易。

### Stage 2 — Canary

仅允许极小仓位。

### Stage 3 — Production

达到目标风险预算。

### Stage 4 — Post-Production Review

比较真实交易与研究分布。

任何重大偏离触发：

`Rollback → Shadow → Re-Research`

不得因为“刚上线亏损”就马上修改规则，也不得因为“刚上线赚钱”就直接放大仓位。

---

# 143. Model Drift Engine

监控：

- feature drift；
- signal drift；
- return drift；
- turnover drift；
- execution drift；
- correlation drift；
- drawdown drift；
- hit-rate drift。

若真实分布显著偏离研究分布：

`Green → Amber → Red`

Red 状态必须进行原因归因：

- market regime changed；
- signal decay；
- execution deterioration；
- liquidity deterioration；
- data problem；
- model bug。

只有找到原因，才能决定是否调整。

---

# 144. Failure Library 2.0

失败不是日志附件，而是核心知识资产。

每次失败保存：

- hypothesis；
- expected mechanism；
- experiment design；
- observed failure；
- market regime；
- statistical diagnosis；
- implementation diagnosis；
- whether the failure is generalizable；
- what future hypotheses must avoid。

下一轮 Hypothesis Generator 必须先检索 Failure Library，避免重复犯已经知道的错误。

---

# 145. Immutable Test Firewall

最终 OOS 数据集必须：

- 独立；
- 加密/锁定；
- 不参与参数调优；
- 不参与专家评分；
- 不参与研究优先级排序。

只有当研究周期完成，才允许一次性读取。

读取后测试集永久标记：

`Contaminated = TRUE`

随后必须建立新的冻结测试集。

---

# 146. Research Stop Rules

顶级研究系统不仅知道“什么时候继续”，还必须知道“什么时候停止”。

停止搜索条件包括：

- 新增复杂度已经很难产生独立增益；
- OOS 改善低于最小经济意义阈值；
- 研究自由度明显膨胀；
- 成本后 Alpha 接近零；
- 不同研究路径已经收敛到相似结论；
- Champion 已经处在合理 Pareto 前沿；
- 继续搜索的 EVI 很低。

> **没有充分理由时，Keep Champion > Optimize。**

---

# 147. v7.0 Small-Account Investor Layer

针对小资金、新手、最大回撤目标 ≤25% 的用户画像，增加三项约束：

## A. Actionability Score

策略必须满足：

- 低至中等换手；
- ETF数量少而明确；
- 规则可人工复核；
- 不依赖毫秒级执行；
- 不依赖杠杆；
- 不依赖无法获得的数据。

## B. Survival Buffer

把用户的 25% 回撤上限视为**硬约束**，但生产 Champion 的目标上限设置在更低区间，例如 15%–20%，为模型误差和实盘滑点预留缓冲。

## C. Complexity Tax

任何复杂模型如果只增加少量 CAGR，却显著增加执行难度，则优先保留简单模型。

对于小资金投资者：

> **可执行性本身就是 Alpha。**

---

# 148. v7.0 Continuous Learning Score

整个 Skill 的自我改进效果用一个独立分数评估：

`LearningScore =`

`Evidence Gain`
`+ OOS Replication Gain`
`+ Failure Avoidance Gain`
`+ Research Efficiency Gain`
`+ Portfolio Diversification Gain`
`- Complexity Growth`
`- Overfitting Risk`

Skill 每个季度回答：

1. 最近新增了哪些真正有证据的知识？
2. 哪些旧知识失效了？
3. 哪些失败被成功避免？
4. 研究成本是否下降？
5. Champion 是否真正改善？
6. 如果 Champion 没改善，研究过程是否仍然增加了有价值的知识？

如果连续多个周期 LearningScore 很低：

`Stop Optimization → Audit Research Process`

而不是继续生成更多策略。

---

# 149. v7.0 Top-Tier Readiness Rubric

必须同时满足：

### Research Quality
- 可复现；
- 数据血缘完整；
- 研究 DAG 完整；
- 假设明确；
- 反方审查独立；
- 多重检验受控。

### Statistical Quality
- OOS；
- Walk-Forward；
- Bootstrap；
- selection-bias audit；
- multiple-testing awareness；
- parameter plateau；
- regime transfer。

### Portfolio Quality
- capital allocation；
- strategy diversification；
- stress correlation；
- uncertainty budget；
- drawdown budget；
- liquidity budget。

### Production Quality
- shadow；
- canary；
- monitoring；
- drift detection；
- rollback；
- post-production attribution。

### Learning Quality
- knowledge confidence；
- knowledge decay；
- failure library；
- research EVI；
- research stop rules；
- continuous learning score。

### User Quality
- actionability；
- complexity；
- cost；
- behavioral fit；
- maximum drawdown ≤25% hard constraint。

只有全部通过，才允许称为：

`Top-Tier Research Framework`

而不是因为历史收益好看就称“顶级策略”。

---

# 150. v7.0 Final Architecture

`External Evidence`
→ `Source Quality`
→ `Evidence Ledger`
→ `Knowledge Distillation`
→ `Knowledge Graph`
→ `Knowledge Confidence / Decay`
→ `Research EVI`
→ `Specialist Expert Panel`
→ `Parallel Hypotheses`
→ `Good / Bad / Broad Calibration`
→ `Data Provenance`
→ `Point-in-Time Universe`
→ `Feature / Signal Engine`
→ `Portfolio & Capital Allocation`
→ `Risk / Uncertainty / Liquidity`
→ `Execution Simulation`
→ `Statistical Red-Team`
→ `Walk-Forward / OOS`
→ `Stress / Scenario / Monte Carlo`
→ `Adversarial Review`
→ `Shadow`
→ `Canary`
→ `Production`
→ `Drift Monitoring`
→ `Rollback`
→ `Post-Mortem`
→ `Failure Library`
→ `Knowledge Update`
→ `Research Budget Update`
→ `Next Research Cycle`

---

# 151. v7.0 Governing Principle

> **The system must improve its ability to discover, reject, validate, allocate, monitor and forget—not merely its ability to invent more strategies.**

The Skill should continuously become:

- more evidence-driven;
- harder to fool;
- less sensitive to luck;
- more capital-efficient;
- more execution-aware;
- more robust to regime changes;
- more transparent about uncertainty;
- and simpler whenever complexity does not earn its keep.

Top-tier status is earned only through repeated, reproducible, out-of-sample evidence and live/forward validation—not through the sophistication of the document itself.

---

# 152. v8.0 Top-Tier Investment Decision Stack — 顶级专家团新增审查层

## 152.1 目的

v7.0 已经具备完整的研究、回测、统计、风险、执行与持续学习框架；v8.0 不再优先增加更多指标，而是把真实投资决策拆成五个互相独立的层：

`Market → Regime → Sector → ETF → Timing → Position → Exit`

每一层都有独立证据、独立评分、独立否决权，并记录“为什么没有交易”。

原则：

> **不允许用下一层的强信号弥补上一层的根本性否决。**

例如：
- ETF 极强，但所属赛道处于结构性风险状态 → 不得因为动量强而自动满仓。
- 赛道很强，但ETF流动性/折溢价/跟踪偏离异常 → 不得交易。
- 买入逻辑成立，但风险预算不足 → 降仓或等待。

---

# 153. Expert-Panel Architecture v8 — 顶级专家团

v8.0 固定使用以下“研究议会”：

### A. Macro / Regime Analyst

任务：识别宏观、政策、流动性、波动率与市场结构状态。

### B. Sector Cartographer

任务：决定“当前值得研究哪些赛道”，不直接决定买哪个ETF。

### C. ETF Selection Quant

任务：在赛道内部比较ETF质量、指数质量、流动性、跟踪误差、成本和交易结构。

### D. Timing Quant

任务：判断进入、加仓、减仓、退出的时机。

### E. Portfolio & Risk Architect

任务：把信号转换成风险预算与仓位。

### F. Execution & Microstructure Analyst

任务：判断真实成交、价差、盘口、折溢价、收盘机制和执行延迟。

### G. Statistical Auditor

任务：审查数据挖掘、选择偏差、显著性与样本外可信度。

### H. Adversarial Investor

任务：只寻找“为什么这笔交易不应该做”。

### I. Behavioral Coach

任务：评估普通投资者是否能执行，不因情绪而偏离规则。

### J. Research Editor / Chief Investment Officer

任务：整合证据，并拥有最终“研究通过/不通过”权，但不得覆盖任何 Hard Veto。

Hard Veto 来源：
- 数据不可信；
- 统计审计失败；
- 流动性/执行失败；
- 风险预算不可接受；
- 最终测试集污染。

---

# 154. Sector Selection Engine v8 — 赛道选择升级

## 154.1 不再直接“预测哪个行业涨"

首先构建一个候选赛道横截面矩阵。

每个赛道计算：

`SectorScore = Trend + RelativeStrength + Breadth + EarningsProxy + Liquidity + Dispersion + Catalyst - Crowding - Risk`

其中：

### Trend

- 20日；
- 60日；
- 120日；
- 250日趋势；
- 多周期一致性。

### Relative Strength

赛道相对沪深300、中证500、中证1000及行业横截面排名。

### Breadth

使用可获得的成分股/行业指数内部广度代理：
- 上涨比例；
- 创新高比例；
- 站上中长期均线比例；
- 趋势扩散度。

### EarningsProxy

如果可得，加入：
- 盈利预期修正；
- 盈利增速；
- ROE/利润率趋势；
- 业绩预告/财报变化。

对于没有可靠实时盈利数据的场景，明确标记为低权重，不伪造精确度。

### Dispersion

衡量赛道内部是否存在足够的个股分化。

高分化意味着ETF内部选股可能存在更高的主动管理价值；极端低分化则可能只是单一Beta交易。

### Crowding

使用价格加速、成交额异常、相对估值、ETF资金流/溢价等可得代理识别拥挤。

注意：
> Crowding 只能调整风险预算，不能单独产生卖出信号。

### Risk

包括：
- 波动率；
- 最大回撤；
- 尾部损失；
- 政策敏感度代理；
- 相关性集中度。

---

# 155. Sector Regime × Sector Selection Matrix

每个赛道必须被分到：

1. **Emerging** — 新趋势形成；
2. **Confirmed** — 趋势确认；
3. **Crowded** — 强趋势但拥挤；
4. **Exhausting** — 动量衰减/波动放大；
5. **Broken** — 趋势结构破坏；
6. **Rebuilding** — 下跌后重新建立。

不同状态使用不同交易规则：

| 状态 | 主要策略 | 抄底权限 | 最大仓位 |
|---|---|---|---|
| Emerging | 趋势确认 | 低 | 中 |
| Confirmed | 动量+趋势 | 中 | 高 |
| Crowded | 趋势跟随+减仓 | 禁止追高 | 中 |
| Exhausting | 核心止盈+Runner | 很低 | 低 |
| Broken | 防御 | 禁止 | 极低 |
| Rebuilding | 条件反转 | 中 | 中 |

---

# 156. ETF Selection Engine v8 — 从“行业正确”到“ETF正确”

同一赛道至少比较五个维度：

`ETFQuality = IndexQuality + TradingQuality + TrackingQuality + CostQuality + PortfolioFit`

## 156.1 IndexQuality

检查：
- 指数成分是否过度集中；
- 前十大权重；
- 行业纯度；
- 单一公司风险；
- 指数换手；
- 编制规则稳定性。

## 156.2 TradingQuality

检查：
- 中位成交额；
- 买卖价差代理；
- 连续报价质量；
- 异常停牌；
- 盘中流动性稳定性。

## 156.3 TrackingQuality

使用：
- 跟踪误差；
- 跟踪偏离；
- 长期净值偏差；
- 分红/费用/税费影响。

## 156.4 CostQuality

综合：
- 管理费/托管费；
- 交易成本；
- 申赎成本（如适用）；
- 隐含滑点；
- 折溢价风险。

## 156.5 PortfolioFit

ETF本身即使优秀，如果与现有仓位高度重复，也不得获得高配置。

---

# 157. ETF “替代性与冗余性”引擎

如果两个ETF高度相关：

`Correlation > threshold`

必须比较：
- 哪个成交更好；
- 哪个费用更低；
- 哪个跟踪误差更小；
- 哪个指数更纯；
- 哪个更符合当前组合风险。

默认原则：

> **同一风险暴露只保留“质量最高”的主要载体，除非多个ETF存在明确的执行/策略差异。**

这样避免“看起来持有10只ETF，实际上只有2个风险因子”。

---

# 158. Entry Timing Engine v8 — 择时买入升级

买入不再由一个指标触发，而采用“三段式门控”。

### Gate A — Permission

市场与赛道环境允许交易：
- Market Regime；
- Sector Regime；
- ETF trend。

### Gate B — Opportunity

出现可验证机会：
- 趋势突破；
- 正常回撤；
- 极端偏离后的条件性均值回归；
- 波动率收缩后扩张；
- 相对强度重新增强。

### Gate C — Execution

当前成交条件可接受：
- spread 正常；
- premium/discount 正常；
- liquidity 正常；
- 不在明显异常交易窗口；
- 预计交易成本不侵蚀 edge。

只有：

`Permission × Opportunity × Execution = PASS`

才允许执行。

---

# 159. Entry Trigger Ranking

对候选入场机会排序，而不是简单“买/不买”。

### Tier 1 — Breakout with Confirmation

适合趋势延续。

### Tier 2 — Pullback in Confirmed Trend

优先级通常高于无条件追涨。

### Tier 3 — Volatility Compression → Expansion

观察波动率从低位向上突破，同时趋势和相对强度同步改善。

### Tier 4 — Conditional Mean Reversion

必须同时满足：
- 中长期趋势没有破坏；
- 市场非系统性风险状态；
- 下跌具有“冲击”特征而非结构性恶化；
- 出现恢复确认。

### Tier 5 — Knife Catching

默认禁止进入生产策略。

只有特殊研究项目经过 OOS 证实才允许。

---

# 160. Entry Confirmation Upgrade — 两阶段成交

避免因为单根K线/单日异常信号追入。

默认：

`Signal Day → Confirmation Day → Execution`

除非策略明确证明即时执行具有独立优势。

确认标准可包括：
- 收盘确认；
- 相对强度继续；
- 波动率没有恶化到危险区；
- 成交额没有异常拥挤。

对于非常强的突破，可以允许：

`Fast Entry`

但必须有更低的单笔风险预算。

---

# 161. Position Sizing v8 — 信号转仓位

仓位不再直接由“信号强度”决定。

使用：

`Position = Signal × Regime × Volatility × Correlation × Liquidity × DrawdownState × Capacity`

并设置：

- 单ETF硬上限；
- 单赛道硬上限；
- 单一主题风险上限；
- 组合波动率上限；
- 组合Expected Shortfall预算。

高置信度信号只有在风险层允许时才能得到高仓位。

---

# 162. Exit Engine v8 — 卖出不是一个规则

至少拆成五种退出：

### Exit A — Thesis Failure

最重要。

赛道/ETF的核心逻辑已经失效 → 退出，不等待止损价。

### Exit B — Trend Failure

长期趋势破坏 → 降仓/退出。

### Exit C — Mean-Reversion Target

价格回归合理区域 → Core 兑现。

### Exit D — Risk Budget Breach

组合风险上升超过预算 → 因组合风险而卖，而非因为单个ETF信号。

### Exit E — Time Stop

机会在预期时间窗口内没有实现 → 释放资本。

这样可以避免“止损、止盈、趋势退出”相互冲突。

---

# 163. Capital Efficiency Engine

新增：

`Expected Edge / Expected Risk / Capital Lock-up`

一个策略即使胜率高，但占用资本太久、机会成本高，也可能不是最佳策略。

因此研究：
- 年化收益；
- 资金占用时间；
- 回撤占用；
- 机会成本；
- recovery time。

新增指标：

`Return per Unit of Capital-Time`

帮助比较：

“赚得多但占钱很久”

vs

“赚得稍少但资金周转效率高”。

---

# 164. Signal Quality × Market State Interaction

一个信号的价值必须按市场状态分解。

例如：

`Momentum × Bull`

`Momentum × Sideways`

`Momentum × Bear`

`MeanReversion × Bull`

`MeanReversion × Sideways`

`MeanReversion × Bear`

如果信号只在一个小状态有效，降低其 Research Confidence。

如果信号在多个独立环境中保持正贡献，提高 Confidence。

---

# 165. Research Portfolio Allocation

研究本身也需要配置资源。

定义每个研究方向的：

`ResearchScore = EVI × ExpectedAlpha × IndependentValue × Feasibility / Complexity`

研究方向包括：
- 新赛道选择；
- ETF替代；
- 入场规则；
- 出场规则；
- 风险模型；
- 成本模型；
- 数据质量；
- 新因子；
- 新模型。

限制：

> 单一研究主题不得长期消耗大部分研究预算。

---

# 166. Research Replication Ladder

任何新发现必须经过：

1. 原始实验；
2. 独立实现；
3. 参数扰动；
4. ETF宇宙扰动；
5. 成本扰动；
6. 时间窗口扰动；
7. 反事实；
8. Walk-Forward；
9. 最终OOS；
10. 影子运行。

只有通过全部关键层级才升级为“High Confidence”。

---

# 167. Model Risk Register

每一个生产策略维护：

- 最大可能失败模式；
- 当前风险状态；
- 监控指标；
- 触发阈值；
- 应对措施；
- 回滚版本。

例如：

`Data Drift → Freeze Trading`

`Execution Drift → Reduce Position`

`Alpha Decay → Shadow Mode`

`Risk Drift → Capital Cut`

`Backtest Mismatch → Full Audit`

---

# 168. Counterfactual Decision Log

每次交易同时记录：

> 如果没有这个信号，我本来会做什么？

> 如果延迟1天，结果如何？

> 如果只买宽基，结果如何？

> 如果不买这个行业，组合结果如何？

> 如果减少一半仓位，收益/风险如何？

这让系统不断积累“没有发生的交易”数据，而不是只学习已发生交易。

---

# 169. Live / Shadow Learning Loop

实盘和研究必须形成双向闭环：

`Research → Shadow → Live`

并记录：

`Expected Signal`
vs
`Observed Fill`

`Expected Volatility`
vs
`Realized Volatility`

`Expected Edge`
vs
`Realized Edge`

`Expected Drawdown`
vs
`Realized Drawdown`

每次偏离都进入 Post-Mortem。

---

# 170. Skill Self-Improvement Score

v8.0 新增 Skill 本身的评分：

`SkillScore = Prediction + Robustness + ResearchEfficiency + ErrorCorrection + ExecutionGap + LearningValue`

每月回答：

- 最近研究是否产生新的独立Alpha？
- 错误预测有没有下降？
- 研究时间是否越来越有效？
- 新策略是否越来越少依赖复杂度？
- 实盘与回测差距是否缩小？
- 风险预算是否越来越准确？

如果 SkillScore 长期下降：

> **优先优化“研究方法”，而不是策略参数。**

---

# 171. v8.0 Small-Account Specialization

针对小资金投资者：

### 优先级

`Robustness > Drawdown > Execution Simplicity > Net Return > Gross Return`

### 默认约束

- 最大回撤目标：<= 20%
- 硬上限：25%
- 不依赖杠杆；
- 不依赖高频；
- 不依赖盘中难以复制的信息优势；
- 控制ETF数量；
- 控制调仓频率；
- 保留现金弹药。

注意：

> 25%是风险边界，而不是正常允许的目标回撤。

---

# 172. v8.0 Current China ETF Market-Structure Guard

由于上交所2026年7月6日起实施新的交易规则，基金收盘阶段交易方式发生调整，并扩大了盘后固定价格交易适用范围；同时股票ETF目前实施T+1。任何回测/执行模块必须记录“交易规则版本”，并按规则版本使用不同执行模型。 

参考：
- 上海证券交易所《交易规则（2026年修订）》；
- 上海证券交易所ETF常见问题；
- 上海证券交易所基金做市交易规则。

因此：

`ExecutionRuleVersion` 成为所有回测结果的强制元数据。

---

# 173. v8.0 Hard Gates

任何候选要进入 Champion，至少通过：

### Gate 1 — Data Integrity

### Gate 2 — Economic Rationale

### Gate 3 — Statistical Audit

### Gate 4 — OOS

### Gate 5 — Cost / Capacity

### Gate 6 — Regime Diversity

### Gate 7 — Portfolio Risk

### Gate 8 — Execution Reality

### Gate 9 — Behavioral Executability

### Gate 10 — Shadow / Forward Confirmation

任意 Hard Fail：

`Research Only`

---

# 174. v8.0 Ultimate Research Loop

`External Evidence`
→ `Knowledge Graph`
→ `Expert Panel`
→ `Market Regime`
→ `Sector Ranking`
→ `ETF Quality Ranking`
→ `Timing Opportunity`
→ `Portfolio Risk`
→ `Execution`
→ `Backtest`
→ `Statistical Red-Team`
→ `Replication`
→ `Walk-Forward`
→ `OOS`
→ `Shadow`
→ `Live`
→ `Drift Detection`
→ `Post-Mortem`
→ `Knowledge Update`
→ `Research Budget Update`
→ `Next Hypothesis`

---

# 175. v8.0 Governing Principle

> **The system should not become “smarter” by generating more predictions. It should become smarter by making fewer bad decisions, allocating capital more selectively, recognizing when its evidence is weak, and learning from both executed and rejected decisions.**

Top-tier status is not inferred from complexity or document length. It must be earned through repeated, reproducible, out-of-sample evidence, realistic execution, forward validation, and demonstrated reduction in decision error.
