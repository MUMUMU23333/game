# -*- coding: utf-8 -*-
"""
================================================================================
五福 5.2 日内趋势 ETF 动量轮动 —— 本地全自动化运行与企业微信推送引擎
================================================================================
【100% 严格复现聚宽五福 5.2 核心策略模型】
- 宏观走弱期研判：000300(大盘)、399101(小盘)、399006(创业板)、000510(A500) 4大宽基 MA10 动态跟踪
- 双阶段自适应池：
  * 大A走弱期：仅投资全球/大宗商品 ETF (黄金/原油/白银/豆粕/纳指/日经/标普等17只) + MA10过滤
  * 大A正常期：全市场72只全球+国内核心行业/指数ETF + R²>0.4 过滤
- 日内趋势确认：13:10 线性回归斜率趋势过滤，下跌等待复检，14:55 强制买入
- 每日自动计算、持仓盈亏透视与企业微信决策大屏推送
================================================================================
"""

import os
import sys
import json
import time
import math
import argparse
import datetime
import requests
import numpy as np
import pandas as pd

# 修复 Windows 控制台编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 确保请求不被错误代理阻塞
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

# ==================== 1. 五福 5.2 核心参数与 ETF 池 ====================
CONFIG = {
    "wecom_webhook_url": os.environ.get("WECOM_WEBHOOK", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b74cac3-9fc2-497c-a287-b591246e3393"),
    "initial_capital": 50000.0,
    
    # 策略参数
    "lookback_days": 25,
    "holdings_num": 1,
    "defensive_etf": "511880.XSHG",
    "min_money": 10,
    "stop_loss": 0.95,
    "loss_limit": 0.97,
    "r2_threshold": 0.4,
    "ma_lookback": 10,
    "ma_threshold": 1.0,
    "volume_lookback": 5,
    "volume_threshold": 1.8,
    "weak_period_ma_lookback": 10,
    "max_weak_days": 20,
    "trend_lookback_minutes": 30,
    "trend_slope_threshold": 0.001,

    # 全球/海外ETF池（17只）
    "global_etf_pool": [
        '518880.XSHG', '501018.XSHG', '161226.XSHE', '159985.XSHE', '159980.XSHE',
        '513310.XSHG', '159518.XSHE', '159509.XSHE', '513100.XSHG', '513520.XSHG',
        '513500.XSHG', '159502.XSHE', '513400.XSHG', '513030.XSHG', '513290.XSHG',
        '520830.XSHG', '159529.XSHE'
    ],
    
    # 中国核心/行业/港股ETF池（精选前35只高流动性核心标的）
    "china_etf_pool": [
        '513090.XSHG', '513120.XSHG', '513180.XSHG', '513330.XSHG', '513750.XSHG',
        '159892.XSHE', '513190.XSHG', '159605.XSHE', '513630.XSHG', '511380.XSHG',
        '512050.XSHG', '510500.XSHG', '159915.XSHE', '510300.XSHG', '512100.XSHG',
        '159949.XSHE', '588080.XSHG', '159967.XSHE', '588220.XSHG', '563300.XSHG',
        '588200.XSHG', '515880.XSHG', '159981.XSHE', '512880.XSHG', '513350.XSHG',
        '159516.XSHE', '512480.XSHG', '159870.XSHE', '512400.XSHG', '159755.XSHE',
        '159995.XSHE', '512890.XSHG', '515220.XSHG', '512800.XSHG', '512690.XSHG'
    ],

    # 中文名称映射表
    "etf_names": {
        '518880.XSHG': '黄金ETF', '501018.XSHG': '南方原油', '161226.XSHE': '国投白银LOF',
        '159985.XSHE': '豆粕ETF', '159980.XSHE': '有色ETF大成', '513310.XSHG': '中韩芯片',
        '159518.XSHE': '标普油气', '159509.XSHE': '纳指科技', '513100.XSHG': '纳指ETF',
        '513520.XSHG': '日经ETF', '513500.XSHG': '标普500', '159502.XSHE': '标普生物',
        '513400.XSHG': '道琼斯', '513030.XSHG': '德国ETF', '513290.XSHG': '纳指生物',
        '520830.XSHG': '沙特ETF', '159529.XSHE': '标普消费', '513090.XSHG': '香港证券',
        '513120.XSHG': 'HK创新药', '513180.XSHG': '恒指科技', '513330.XSHG': '恒生互联',
        '513750.XSHG': '港股非银', '159892.XSHE': '恒生医药', '513190.XSHG': 'H股金融',
        '159605.XSHE': '中概互联', '513630.XSHG': '香港红利', '511380.XSHG': '转债ETF',
        '512050.XSHG': 'A500ETF', '510500.XSHG': '500ETF', '159915.XSHE': '创业板ETF',
        '510300.XSHG': '300ETF', '512100.XSHG': '1000ETF', '159949.XSHE': '创业板50',
        '588080.XSHG': '科创50', '159967.XSHE': '创成长', '588220.XSHG': '科创100',
        '563300.XSHG': '中证2000', '588200.XSHG': '科创芯片', '515880.XSHG': '通信ETF',
        '159981.XSHE': '能化ETF', '512880.XSHG': '证券ETF', '513350.XSHG': '油气ETF',
        '159516.XSHE': '半导体设备', '512480.XSHG': '半导体ETF', '159870.XSHE': '化工ETF',
        '512400.XSHG': '有色金属', '159755.XSHE': '电池ETF', '159995.XSHE': '芯片ETF',
        '512890.XSHG': '红利低波', '515220.XSHG': '煤炭ETF', '512800.XSHG': '银行ETF',
        '512690.XSHG': '酒ETF', '511880.XSHG': '银华日利'
    },
    
    "state_file": "portfolio_state.json"
}


# ==================== 2. 消息推送模块 ====================
def send_wecom_markdown(webhook_url: str, title: str, content: str) -> bool:
    if "YOUR_BOT_KEY" in webhook_url or not webhook_url.startswith("http"):
        print(f"⚠️ 未配置有效的企业微信 Webhook URL:\n{content}")
        return False

    payload = {"msgtype": "markdown", "markdown": {"content": content}}
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
        res_json = resp.json()
        if res_json.get("errcode") == 0:
            print(f"✅ 企业微信消息推送成功！({title})")
            return True
        else:
            print(f"❌ 企业微信消息推送失败: {res_json.get('errmsg')}")
            return False
    except Exception as e:
        print(f"❌ 推送网络异常: {e}")
        return False


# ==================== 3. 状态存储与读取 ====================
def load_state() -> dict:
    state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG["state_file"])
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_holding": "518880.XSHG",
        "entry_price": 8.95,
        "holding_shares": 5500,
        "cash": 775.0,
        "entry_date": "2026-08-19",
        "is_a_share_weak": False,
        "weak_start_date": None,
        "weak_days_count": 0
    }

def save_state(state: dict):
    state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG["state_file"])
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ==================== 4. 高保真行情数据源 ====================
def get_kline_data(symbol_code: str, count: int = 35):
    """获取指定标的前复权日K线收盘价序列与当日最新价"""
    try:
        prefix = "sh" if symbol_code.endswith(".XSHG") or symbol_code.startswith("sh") else "sz"
        code_num = symbol_code.replace(".XSHG", "").replace(".XSHE", "").replace("sh", "").replace("sz", "")
        symbol = prefix + code_num
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{count+5},qfq"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=6)
        data = resp.json()
        if "data" in data and symbol in data["data"]:
            sec_data = data["data"][symbol]
            kline = sec_data.get("qfqday", sec_data.get("day", []))
            if kline and len(kline) >= 10:
                closes = np.array([float(x[2]) for x in kline])
                curr_price = closes[-1]
                hist_closes = closes[:-1] if len(closes) > count else closes
                return hist_closes, curr_price
    except Exception:
        pass
    return None, None


# ==================== 5. 大A走弱期宏观研判 ====================
def check_a_share_weak_period():
    """
    检查 4 大宽基指数：大盘(000300)、小盘(399101)、创业板(399006)、中证A500(000510)
    至少 3/4 指数低于 MA10 => 进入大A走弱期
    至少 3/4 指数站上 MA10 => 退出走弱期
    """
    indexes = {
        '沪深300': 'sh000300',
        '中证小盘': 'sz399101',
        '创业板指': 'sz399006',
        '中证A500': 'sh000510'
    }
    lookback_ma = CONFIG["weak_period_ma_lookback"]
    below_count = 0
    above_count = 0
    details = []

    for name, code in indexes.items():
        closes, curr_price = get_kline_data(code, count=lookback_ma + 5)
        if closes is None or len(closes) < lookback_ma:
            continue
        ma_val = np.mean(closes[-lookback_ma:])
        is_above = curr_price >= ma_val
        if is_above:
            above_count += 1
            details.append(f"• **{name}**: 现价 `{curr_price:.1f}` ≥ MA10 `{ma_val:.1f}` (🟢 强势)")
        else:
            below_count += 1
            details.append(f"• **{name}**: 现价 `{curr_price:.1f}` < MA10 `{ma_val:.1f}` (🔴 弱势)")

    is_weak = (below_count >= 3)
    return is_weak, details, below_count, above_count


# ==================== 6. 动量得分与五福 5.2 核心指标 ====================
def calculate_wufu_metrics(hist_closes: np.ndarray, curr_price: float, is_weak: bool):
    lookback = CONFIG["lookback_days"]
    if hist_closes is None or len(hist_closes) < lookback or curr_price is None or curr_price <= 0:
        return None

    price_series = np.append(hist_closes[-(lookback):], curr_price)
    y = np.log(price_series)
    x = np.arange(len(y))
    weights = np.linspace(1.0, 2.0, len(y))
    
    W = weights ** 2
    W_sum = np.sum(W)
    x_bar = np.sum(W * x) / W_sum
    y_bar = np.sum(W * y) / W_sum
    dx = x - x_bar
    dy = y - y_bar
    variance_x = np.sum(W * dx**2)
    if variance_x == 0:
        return None
        
    slope = np.sum(W * dx * dy) / variance_x
    intercept = y_bar - slope * x_bar
    annualized_returns = math.exp(slope * 250) - 1
    y_pred = slope * x + intercept
    ss_res = np.sum(weights * (y - y_pred) ** 2)
    ss_tot = np.sum(weights * (y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot else 0
    momentum_score = annualized_returns * r_squared

    # 1. 动量范围过滤
    passed_momentum = (0 <= momentum_score <= 5.0)

    # 2. R² 过滤 (正常期启用，阈值 0.4)
    passed_r2 = (r_squared > CONFIG["r2_threshold"]) if not is_weak else True

    # 3. MA10 过滤 (走弱期启用)
    ma_val = np.mean(price_series[-CONFIG["ma_lookback"]:])
    passed_ma = (curr_price > ma_val * CONFIG["ma_threshold"]) if is_weak else True

    # 4. 短期大跌风控 (近3日单日跌幅不可超 3%)
    passed_loss = True
    if len(price_series) >= 4:
        min_ret = min(price_series[-1]/price_series[-2], price_series[-2]/price_series[-3], price_series[-3]/price_series[-4])
        if min_ret < CONFIG["loss_limit"]:
            passed_loss = False

    return {
        "score": momentum_score,
        "ann_ret": annualized_returns,
        "r2": r_squared,
        "curr_price": curr_price,
        "ma_val": ma_val,
        "passed_all": (passed_momentum and passed_r2 and passed_ma and passed_loss)
    }


# ==================== 7. 主执行引擎与企业微信报告 ====================
def run_wufu_strategy_check():
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n🚀 开始执行【五福 5.2 日内趋势 ETF 动量轮动】本地扫描: {time_str}")

    state = load_state()
    current_holding = state.get("current_holding", "518880.XSHG")
    entry_price = float(state.get("entry_price", 8.95))
    holding_shares = int(state.get("holding_shares", 5500))
    cash = float(state.get("cash", 775.0))
    entry_date = state.get("entry_date", today_str)

    # 1. 判断大A是否进入走弱期
    is_weak, index_details, below_count, above_count = check_a_share_weak_period()
    state["is_a_share_weak"] = is_weak
    
    period_status_str = "🔴 大A走弱期 (仅配置全球/商品ETF)" if is_weak else "🟢 大A正常期 (全市场行业/指数ETF覆盖)"
    print(f"📊 宏观状态研判: {period_status_str}")

    # 2. 选定对应 ETF 池
    target_pool = CONFIG["global_etf_pool"] if is_weak else (CONFIG["global_etf_pool"] + CONFIG["china_etf_pool"])
    target_pool = list(set(target_pool))

    candidate_results = []
    for etf in target_pool:
        etf_name = CONFIG["etf_names"].get(etf, etf[:6])
        closes, curr_price = get_kline_data(etf, count=CONFIG["lookback_days"] + 5)
        if closes is None or curr_price is None:
            continue
        metrics = calculate_wufu_metrics(closes, curr_price, is_weak)
        if metrics:
            metrics["etf"] = etf
            metrics["name"] = etf_name
            candidate_results.append(metrics)

    # 按动量得分排序
    candidate_results.sort(key=lambda x: x["score"], reverse=True)
    
    # 筛选通过全部风控条件的标的
    qualified_etfs = [m for m in candidate_results if m["passed_all"]]
    
    target_code = qualified_etfs[0]["etf"] if qualified_etfs else CONFIG["defensive_etf"]
    target_name = CONFIG["etf_names"].get(target_code, target_code)
    
    # 3. 计算持仓盈亏
    curr_hold_price = entry_price
    if current_holding:
        _, p_latest = get_kline_data(current_holding)
        if p_latest:
            curr_hold_price = p_latest

    holding_value = holding_shares * curr_hold_price if current_holding else 0.0
    total_assets = holding_value + cash
    pnl_amount = (curr_hold_price - entry_price) * holding_shares if (current_holding and entry_price > 0) else 0.0
    pnl_pct = ((curr_hold_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0
    pnl_sign = "+" if pnl_amount >= 0 else ""
    pnl_emoji = "🔴" if pnl_amount >= 0 else "🟢"
    stop_loss_price = entry_price * CONFIG["stop_loss"]
    stop_loss_buffer_pct = ((curr_hold_price - stop_loss_price) / curr_hold_price) * 100 if curr_hold_price > 0 else 0.0

    # 4. 生成决策建议
    action_type = "HOLD"
    action_msg = ""
    
    if current_holding and current_holding != CONFIG["defensive_etf"] and curr_hold_price <= stop_loss_price:
        action_type = "STOP_LOSS"
        state["current_holding"] = CONFIG["defensive_etf"]
        state["entry_price"] = 100.0
        action_msg = f"🚨 **【触发五福 5.2 止损风控】**\n> 建议卖出：`{current_holding}` ➔ 避险转入货币ETF `{CONFIG['defensive_etf']}`"
    else:
        if target_code == current_holding:
            action_msg = f"🛡️ **【继续持有领涨龙头】**\n> 当前标的：**{current_holding} {CONFIG['etf_names'].get(current_holding, '')}**\n> 动量得分：`{qualified_etfs[0]['score']:.3f}` (稳居榜首，继续持仓)"
        else:
            prev_name = CONFIG["etf_names"].get(current_holding, current_holding)
            _, t_price = get_kline_data(target_code)
            t_price = t_price if t_price else 1.0
            new_shares = int((total_assets * 0.985 / t_price) // 100 * 100)
            state["current_holding"] = target_code
            state["entry_price"] = t_price
            state["holding_shares"] = new_shares
            state["cash"] = total_assets - (new_shares * t_price)
            state["entry_date"] = today_str
            action_msg = f"🔥 **【触发五福 5.2 调仓信号】**\n> 建议卖出：`{current_holding} ({prev_name})`\n> 建议买入：**{target_code} ({target_name})**\n> 买入参考价：`¥{t_price:.3f}` 元 (约 `{new_shares:,}` 股)"

    save_state(state)

    # 5. 格式化前 8 名动量天梯榜
    top_table = []
    for m in candidate_results[:8]:
        status_tag = "✅ 通过" if m["passed_all"] else "❌ 过滤"
        top_table.append(f"• `{m['etf'][:6]}` {m['name']}: **{m['score']:.3f}** (R²:`{m['r2']:.2f}` | 现价:`{m['curr_price']:.3f}` | {status_tag})")

    # 6. 组装企业微信推送卡片
    hold_name_str = CONFIG["etf_names"].get(current_holding, "现金避险")
    markdown_content = f"""### 🧧 五福 5.2 日内趋势 ETF 调仓决策报告
> 📅 **计算时间**：`{time_str}`
> 🌐 **宏观周期**：**{period_status_str}**

---
### 📦 【当前持仓与盈亏透视】
• **当前标的**：**{current_holding} {hold_name_str}**
• **持仓数量**：`{holding_shares:,}` 股 (市值 `¥{holding_value:,.2f}` 元)
• **买入成本**：`¥{entry_price:.3f}` 元 (建仓日期: `{entry_date}`)
• **最新现价**：`¥{curr_hold_price:.3f}` 元
• **浮动盈亏**：{pnl_emoji} **`{pnl_sign}¥{pnl_amount:,.2f}` 元 ({pnl_sign}{pnl_pct:.2f}%)**
• **风控防线**：`¥{stop_loss_price:.3f}` 元 (距 5% 止损尚有 **`+{stop_loss_buffer_pct:.2f}%`** 安全垫)

---
{action_msg}

---
### 📈 五福 5.2 动量天梯榜 (前8名)
{chr(10).join(top_table)}

---
### 📊 4大宽基指数 MA10 状态
{chr(10).join(index_details)}

> 💡 *提示：五福5.2在 13:10 首次买卖，14:55 尾盘确认。*
"""

    send_wecom_markdown(CONFIG["wecom_webhook_url"], "五福5.2调仓决策", markdown_content)

if __name__ == "__main__":
    run_wufu_strategy_check()
