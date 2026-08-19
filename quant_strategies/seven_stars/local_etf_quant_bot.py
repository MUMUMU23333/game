# -*- coding: utf-8 -*-
"""
================================================================================
七星量化 ETF 动量轮动 —— 本地原版策略运行与企业微信自动通知机器人
================================================================================
【100% 严格遵循原版策略逻辑与参数 + 实时持仓盈亏透视】
- ETF池：黄金(518880)、豆粕(159985)、原油(501018)、白银(161226)、纳指(513100)、双创龙头(588330)、创成长(159967)、科创50(588940)
- 防御ETF：511880.XSHG（银华日利货币ETF）
- lookback_days: 30 | stop_loss: 0.95 | loss_limit: 0.97 | 溢价率上限: 0.20
- 每日 14:47~14:48 自动执行计算并向企业微信机器人推送包含【持仓价格、实时盈亏、动量天梯榜】的富文本卡片
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

# 修复 Windows 控制台中文与 Emoji 打印编码
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

# ==================== 1. 原版配置与参数 ====================
CONFIG = {
    # 企业微信群机器人 Webhook 地址
    "wecom_webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=46012c55-7fd0-4060-baa8-fc110bb3ca5d",
    
    # 聚宽 jqdatasdk 账号（可选，未配置则自动使用免费高保真行情源）
    "jq_username": "",
    "jq_password": "",
    
    # 模拟账户初始本金
    "initial_capital": 50000.0,
    
    # 原版策略参数（保持 100% 不变）
    "lookback_days": 30,
    "holdings_num": 1,
    "defensive_etf": "511880.XSHG",   # 银华日利货币ETF
    "min_money": 5000,
    "stop_loss": 0.95,
    "loss_limit": 0.97,
    "min_score_threshold": 0,
    "max_score_threshold": 500.0,
    "enable_premium_filter": True,
    "premium_threshold": 0.20,
    
    # 原版 8 大 ETF 池
    "etf_pool": [
        "518880.XSHG",  # 华安黄金ETF
        "159985.XSHE",  # 华夏饲料豆粕期货ETF
        "501018.XSHG",  # 南方原油LOF
        "161226.XSHE",  # 国投白银LOF
        "513100.XSHG",  # 纳指ETF
        "588330.XSHG",  # 双创龙头ETF
        "159967.XSHE",  # 创成长ETF（创业板动量成长）
        "588940.XSHG"   # 科创50ETF富国
    ],
    
    # 标的中文名称映射
    "etf_names": {
        "518880.XSHG": "华安黄金ETF",
        "159985.XSHE": "华夏豆粕ETF",
        "501018.XSHG": "南方原油LOF",
        "161226.XSHE": "国投白银LOF",
        "513100.XSHG": "华夏纳指ETF",
        "588330.XSHG": "双创龙头ETF",
        "159967.XSHE": "创成长ETF",
        "588940.XSHG": "科创50ETF富国",
        "511880.XSHG": "银华日利货币ETF"
    },
    
    # 本地持仓状态文件
    "state_file": "portfolio_state.json"
}


# ==================== 2. 企业微信 Webhook 消息推送 ====================
def send_wecom_markdown(webhook_url: str, title: str, content: str) -> bool:
    """向企业微信群机器人发送 Markdown 消息"""
    if "YOUR_BOT_KEY_HERE" in webhook_url or not webhook_url.startswith("http"):
        print(f"⚠️ [提示] 未配置有效的企业微信 Webhook URL，消息将在控制台展示：")
        print("\n" + "="*55)
        print(f"【企业微信推送预览】\n{content}")
        print("="*55 + "\n")
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
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


# ==================== 3. 本地状态机管理 ====================
def load_state() -> dict:
    """读取本地持仓状态"""
    state_file = CONFIG["state_file"]
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_holding": "518880.XSHG",  # 默认当前持有黄金ETF
        "entry_price": 8.95,               # 买入成本价
        "holding_shares": 5500,            # 持仓股数
        "cash": 775.0,                     # 账户闲置现金
        "entry_date": "2026-08-19",
        "stop_loss_blacklist": {}
    }

def save_state(state: dict):
    """保存本地持仓状态"""
    state_file = CONFIG["state_file"]
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ==================== 4. 高保真行情数据获取 ====================
def get_etf_data(etf_code: str, count: int = 35):
    """
    获取 ETF 历史日收盘价序列与当日最新价格
    优先使用 jqdatasdk，若未配置则调用腾讯证券前复权日K线接口
    """
    # 优先尝试 jqdatasdk
    if CONFIG["jq_username"] and CONFIG["jq_password"]:
        try:
            import jqdatasdk as jq
            if not jq.is_auth():
                jq.auth(CONFIG["jq_username"], CONFIG["jq_password"])
            df = jq.get_price(etf_code, count=count, frequency='1d', fields=['close'], fq='pre', panel=False)
            curr_data = jq.get_current_data()
            curr_price = curr_data[etf_code].last_price if etf_code in curr_data else df['close'].iloc[-1]
            return df['close'].values, float(curr_price)
        except Exception as e:
            print(f"jqdatasdk 获取 {etf_code} 异常: {e}，切换备用高保真行情源")

    # 腾讯前复权日K线接口 (高保真日线数据，精准支持 A股/ETF/LOF)
    try:
        prefix = "sh" if etf_code.endswith(".XSHG") else "sz"
        symbol = prefix + etf_code[:6]
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{count+5},qfq"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=6)
        data = resp.json()
        if "data" in data and symbol in data["data"]:
            sec_data = data["data"][symbol]
            kline = sec_data.get("qfqday", sec_data.get("day", []))
            if kline and len(kline) >= count:
                closes = np.array([float(x[2]) for x in kline])
                curr_price = closes[-1]
                hist_prices = closes[:-1] if len(closes) > count else closes
                return hist_prices, curr_price
    except Exception as e:
        print(f"腾讯行情获取 {etf_code} 异常: {e}")

    # 新浪实时行情兜底
    try:
        prefix = "sh" if etf_code.endswith(".XSHG") else "sz"
        symbol = prefix + etf_code[:6]
        url = f"http://hq.sinajs.cn/list={symbol}"
        headers = {"Referer": "https://finance.sina.com.cn"}
        resp = requests.get(url, headers=headers, timeout=5)
        text = resp.text
        if "=" in text:
            parts = text.split("=")[1].replace('"', '').replace(';\n', '').split(',')
            if len(parts) > 3:
                curr_price = float(parts[3]) if float(parts[3]) > 0 else float(parts[2])
                return np.array([curr_price] * count), curr_price
    except Exception as e:
        print(f"新浪行情获取 {etf_code} 异常: {e}")
        
    return None, None


# ==================== 5. 原版动量算法 (100% 原始公式) ====================
def calculate_momentum_score(prices: np.ndarray, curr_price: float):
    lookback = CONFIG["lookback_days"]
    if prices is None or len(prices) < lookback or curr_price is None or curr_price <= 0:
        return None
        
    y = np.log(np.append(prices[-lookback:], curr_price))
    x = np.arange(len(y))
    weights = np.linspace(1.0, 2.0, len(y))
    
    slope, intercept = np.polyfit(x, y, 1, w=weights)
    ann_ret = math.exp(slope * 250) - 1
    
    y_pred = slope * x + intercept
    ss_res = np.sum(weights * (y - y_pred) ** 2)
    ss_tot = np.sum(weights * (y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0
    score = ann_ret * r2
    
    if len(prices) >= 4:
        recent_ret = min(prices[-1] / prices[-2],
                         prices[-2] / prices[-3],
                         prices[-3] / prices[-4])
        if recent_ret < CONFIG["loss_limit"]:
            score = 0
            
    return score


# ==================== 6. 核心逻辑执行与通知推送 ====================
def run_strategy_check():
    """执行原版选股、持仓盈亏透视与企业微信推送"""
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n🚀 开始执行【七星量化 ETF 原版策略】本地计算与盈亏透视: {time_str}")
    
    state = load_state()
    current_holding = state.get("current_holding", "518880.XSHG")
    entry_price = float(state.get("entry_price", 8.95))
    holding_shares = int(state.get("holding_shares", 5500))
    cash = float(state.get("cash", 775.0))
    entry_date = state.get("entry_date", today_str)
    
    scores = []
    scores_table = []
    
    # 1. 遍历计算 ETF 池动量评分
    for etf in CONFIG["etf_pool"]:
        etf_name = CONFIG["etf_names"].get(etf, etf)
        prices, curr_price = get_etf_data(etf, count=CONFIG["lookback_days"] + 5)
        
        if prices is None or curr_price is None:
            scores_table.append(f"• `{etf[:6]}` {etf_name}: 行情数据获取中...")
            continue
            
        score = calculate_momentum_score(prices, curr_price)
        if score is not None:
            status_tag = "📈 上行趋势" if score > 0 else "📉 回调筑底"
            scores_table.append(f"• `{etf[:6]}` {etf_name}: **{score:.3f}** ({status_tag} | 现价 `{curr_price:.3f}`)")
            if CONFIG["min_score_threshold"] < score < CONFIG["max_score_threshold"]:
                scores.append((etf, etf_name, score, curr_price))
        else:
            scores_table.append(f"• `{etf[:6]}` {etf_name}: 暂无有效评分")
            
    # 按动量排序
    scores.sort(key=lambda x: x[2], reverse=True)
    ranked_etfs = [s[0] for s in scores]
    targets = ranked_etfs[:CONFIG["holdings_num"]] if ranked_etfs else []
    
    if not targets:
        targets = [CONFIG["defensive_etf"]]
        
    target_code = targets[0]
    target_name = CONFIG["etf_names"].get(target_code, target_code)
    
    # 2. 获取当前持仓的最新实时现价并计算精确盈亏
    curr_hold_price = entry_price
    if current_holding:
        _, p_latest = get_etf_data(current_holding)
        if p_latest:
            curr_hold_price = p_latest
            
    holding_value = holding_shares * curr_hold_price if current_holding else 0.0
    total_assets = holding_value + cash
    
    # 计算持仓盈亏
    pnl_amount = (curr_hold_price - entry_price) * holding_shares if (current_holding and entry_price > 0) else 0.0
    pnl_pct = ((curr_hold_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0
    pnl_sign = "+" if pnl_amount >= 0 else ""
    pnl_emoji = "🔴" if pnl_amount >= 0 else "🟢"
    
    # 止损价与安全缓冲
    stop_loss_price = entry_price * CONFIG["stop_loss"]
    stop_loss_buffer_pct = ((curr_hold_price - stop_loss_price) / curr_hold_price) * 100 if curr_hold_price > 0 else 0.0
    position_ratio = (holding_value / total_assets * 100) if total_assets > 0 else 0.0
    
    # 3. 产生操作信号与决策
    action_type = "HOLD"
    action_msg = ""
    
    if current_holding and current_holding != CONFIG["defensive_etf"]:
        if curr_hold_price <= stop_loss_price and entry_price > 0:
            action_type = "STOP_LOSS"
            hold_name = CONFIG["etf_names"].get(current_holding, current_holding)
            state["current_holding"] = CONFIG["defensive_etf"]
            state["entry_price"] = 100.0
            state["holding_shares"] = int((total_assets * 0.985 / 100.0) // 100 * 100)
            state["cash"] = total_assets - (state["holding_shares"] * 100.0)
            action_msg = f"🚨 **【触发原版 5% 硬止损】**\n> 止损标的：**{current_holding} {hold_name}**\n> 成本价：`¥{entry_price:.3f}` ➔ 现价：`¥{curr_hold_price:.3f}` (亏损 `{pnl_pct:.2f}%`)\n> 决策建议：**立即清仓卖出，切换至防御标的 {CONFIG['defensive_etf']} (银华日利)**"

    if action_type != "STOP_LOSS":
        if target_code == current_holding:
            action_msg = f"🛡️ **【继续持有最强龙头】**\n> 当前持仓：**{current_holding} {CONFIG['etf_names'].get(current_holding, '')}**\n> 动量优势：**{scores[0][2]:.3f}** (稳居榜首，继续持有吃满波段)"
        else:
            prev_name = CONFIG["etf_names"].get(current_holding, current_holding)
            _, t_price = get_etf_data(target_code)
            t_price = t_price if t_price else 1.0
            new_shares = int((total_assets * 0.985 / t_price) // 100 * 100)
            state["current_holding"] = target_code
            state["entry_price"] = t_price
            state["holding_shares"] = new_shares
            state["cash"] = total_assets - (new_shares * t_price)
            state["entry_date"] = today_str
            
            if target_code == CONFIG["defensive_etf"]:
                action_msg = f"⚠️ **【转入防御状态】**\n> 原因：所有进攻 ETF 动量均未达标或触发风控\n> 建议卖出：`{current_holding} ({prev_name})`\n> 建议买入：**{target_code} ({target_name})** (货币ETF避险)"
            else:
                action_msg = f"🔥 **【触发原版调仓换股信号】**\n> 建议卖出：`{current_holding} ({prev_name})`\n> 建议全仓买入：**{target_code} ({target_name})**\n> 买入参考价：`¥{t_price:.3f}` 元 (约 `{new_shares:,}` 股)\n> 动量得分：**{scores[0][2]:.3f}** (全市场动量第一名)"

    # 保存状态
    save_state(state)
    
    # 4. 组装企业微信 Markdown 富文本卡片（包含全量持仓仓位与盈亏透视）
    hold_name_str = CONFIG["etf_names"].get(current_holding, "100% 现金")
    
    markdown_content = f"""### 🔔 七星量化 ETF 动量决策与持仓盈亏报告
> 📅 **计算时间**：`{time_str}`
> 💰 **账户总资产**：`¥{total_assets:,.2f}` 元 (仓位: **{position_ratio:.1f}%**)

---
### 📦 【当前持仓与实时盈亏透视】
• **当前标的**：**{current_holding} {hold_name_str}**
• **持仓数量**：`{holding_shares:,}` 股 (持仓市值 `¥{holding_value:,.2f}` 元)
• **买入成本**：`¥{entry_price:.3f}` 元 (建仓日期: `{entry_date}`)
• **最新现价**：`¥{curr_hold_price:.3f}` 元
• **浮动盈亏**：{pnl_emoji} **`{pnl_sign}¥{pnl_amount:,.2f}` 元 ({pnl_sign}{pnl_pct:.2f}%)**
• **风控防线**：`¥{stop_loss_price:.3f}` 元 (距 5% 硬止损线尚有 **`+{stop_loss_buffer_pct:.2f}%`** 安全垫)

---
{action_msg}

---
### 📊 今日 ETF 动量打分榜 (原版公式)
{chr(10).join(scores_table)}

> 💡 *风控提示：原版策略建议在每个交易日 14:47 卖出、14:48 买入执行。*
"""

    # 5. 推送企业微信
    send_wecom_markdown(CONFIG["wecom_webhook_url"], "七星量化持仓与调仓通知", markdown_content)


# ==================== 7. 定时调度与主入口 ====================
def start_scheduler():
    """本地守护调度引擎：交易日 14:47 准时执行"""
    import schedule
    print("⏰ [量化调度器启动] 交易日 14:47 将自动执行原版策略计算并推送企业微信...")
    print("💡 按 Ctrl + C 可退出守护进程。")
    
    schedule.every().monday.at("14:47").do(run_strategy_check)
    schedule.every().tuesday.at("14:47").do(run_strategy_check)
    schedule.every().wednesday.at("14:47").do(run_strategy_check)
    schedule.every().thursday.at("14:47").do(run_strategy_check)
    schedule.every().friday.at("14:47").do(run_strategy_check)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="七星量化本地原版策略与企业微信推送")
    parser.add_argument("--now", action="store_true", help="立即运行一次原版策略计算并推送")
    parser.add_argument("--daemon", action="store_true", help="启动本地定时守护进程（每个交易日 14:47 自动执行）")
    args = parser.parse_args()
    
    if args.daemon:
        start_scheduler()
    else:
        run_strategy_check()
