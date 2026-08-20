# 🇨🇳 国家队资金跟踪与盘中异动监控系统 (National Team Capital Tracker)

> 本系统融合 **GitHub 热门项目 `national-team-position`（纯份额物理审计）** 与 **`etf-three-factor`（三因子异动加权）** 的核心思想，打造从 **T+0 盘中毫秒级异动雷达** 到 **T+1 交易所官方结算份额确认** 的双重确认量化系统。

---

## 🌟 核心特性与架构

```
┌────────────────────────────────────────────────────────┐
│                   双阶段双重确认机制                    │
└────────────────────────────────────────────────────────┘
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
【T+0 盘中异动雷达】                    【T+1 交易所官方份额审计】
• 分钟级爆量脉冲 (Volume Spike)         • 官方总份额剥离 (Share Delta)
• 3~5分钟急拉托底 (Momentum)            • 剔除净值行情涨跌噪音
• 14:00 尾盘防守加权                     • 精确核算真金白银净流入 (亿元)
• 买卖5档深度失衡 (托单识别)             • 区分净增持 vs 宽基结构轮动
       │                                       │
       └───────────────────┬───────────────────┘
                           ▼
               【双阶段交叉判定与量化评级】
  🟢 AAA级: 放量急拉 + 巨额净申购 (真金白银强力护盘 · 坚决跟随)
  🔵 AA级 : 盘面平稳 + 持续净申购 (水下隐蔽潜伏增持 · 左侧布局)
  🟡 C级  : 盘中爆量 + 份额未变动 (游资量化情绪脉冲 · 严禁追高)
  🔴 D级  : 冲高放量 + 份额大赎回 (主力阶段性高抛减仓 · 风控离场)
```

---

## 🚀 快速启动

在本项目根目录下，直接执行以下命令：

### 1. 执行一次全盘即时扫描与双重确认审计（默认推荐）
```bash
python run_national_team_tracker.py
```
*扫描当前市场宽基 ETF，输出控制台彩色投研看板，并自动在 `reports/` 目录下生成交互式 HTML 报告。*

### 2. 启动盘中实时轮询监控雷达（自动秒级刷新）
```bash
python run_national_team_tracker.py --mode realtime --interval 15
```
*实时捕捉盘中 510300、510050、510500、512100、560510 等标的的急拉托底、爆量脉冲。*

### 3. 执行 T+1 官方交易所份额审计
```bash
python run_national_team_tracker.py --mode audit
```
*调取上交所与深交所官方结算总份额，核算单日及区间内各宽基 ETF 的确切净流入金额。*

### 4. 执行 3 年历史数据全量回测与超参网格寻优
```bash
python run_national_team_tracker.py --mode backtest --open
```
*在 800+ 交易日真实行情中回测国家队干预信号，评估 T+1/T+5/T+20/T+60 胜率与夏普比率，并自动生成 HTML 回测大屏。*

### 5. 生成并在浏览器中打开 HTML 投研仪表盘
```bash
python run_national_team_tracker.py --mode report --open
```

---

## 📁 目录结构说明

```
national_team_tracker/
├── config.py                 # 标的池配置、预警阈值、通知通道
├── data_fetcher.py           # 实时行情抓取、分时K线、交易所官方份额拉取 (AKShare/HTTP)
├── intraday_scanner.py       # T+0 盘中异动雷达 (爆量脉冲、急拉托底、尾盘突击、折溢价异常)
├── share_auditor.py          # T+1 官方份额审计 (真实净申赎测算、大额资金流入、轮动识别)
├── fusion_engine.py          # 信号交叉融合打分引擎 (AAA~D 评级判定)
├── notifier.py               # 终端高亮看板 (Rich Table)、HTML 交互式报告渲染、Webhook 告警
├── run_monitor.py            # CLI 运行主逻辑
├── requirements.txt          # 依赖清单
└── README.md                 # 完整使用说明
```

---

## 💡 如何将信号接入你的量化策略代码？

例如在你的 `backtest_5_2.py` 或实盘策略中直接调用：

```python
from national_team_tracker.fusion_engine import FusionEngine

# 初始化引擎
engine = FusionEngine()
analysis = engine.run_composite_analysis()

# 获取 AAA级 强护盘标的
aaa_signals = [item for item in analysis["results"] if item["grade"] == "AAA"]

if len(aaa_signals) > 0 or analysis["total_inflow_yi"] >= 30.0:
    print("🚨 触发国家队强力托底保护信号，提升策略仓位乘数至 1.2x，禁止开空对冲！")
```
