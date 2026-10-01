# -*- coding: utf-8 -*-
"""
====================================================================================================
🏛️ MUMUMU23333的机器人 · 企业微信全能量化 AI 掌上中枢 (WebSocket 双向交互旗舰版)
====================================================================================================
功能列表：
1. 【持仓透视】：查持仓 / 仓位 / 资产
2. 【量化战令】：跑五福 / 跑七星 / 生成晚报 / 尾盘巡检 (14:48)
3. 【量化诊断】：诊断 <股票/ETF> / 查 <代码> / 分析 <标的> (多空评分、支撑阻力位、均线排列)
4. 【财报排雷】：排雷 <股票名称/代码> (五维财务穿透：现金流、商誉、研发资本化)
5. 【多因子选股】：选股 动量 / 选股 高股息 / 选股 破净
6. 【实时盯盘预警】：
   - 盯盘 <代码/名称> 突破 <价格> (如: 盯盘 黄金股ETF 突破 2.30)
   - 盯盘 <代码/名称> 跌破 <价格> (如: 盯盘 黄金 跌破 9.40)
   - 查盯盘 / 清空盯盘
7. 【桌面快照与状态】：看桌面 / 截图 / 电脑状态 / 系统
8. 【代码维护】：更新代码 / git pull
====================================================================================================
"""
import os
import sys
import re
import json
import time
import asyncio
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Any

# 修复 Windows 控制台编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import psutil
import requests
from wecom_aibot_sdk import WSClient, WSClientOptions, generate_req_id

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCH_FILE = os.path.join(BASE_DIR, ".price_watchlist.json")

# 官方机器人凭据
BOT_ID = "aibQ2P8Xz3wHWcVD9t-7OR_oGca8D1D797R"
SECRET = "dI8wtTDpngK9iFgBrvnErmbRynLjBWkKNiD93TiMBnd"

ws_client = WSClient(WSClientOptions(
    bot_id=BOT_ID,
    secret=SECRET
))

# 引入量化工具库
from quant_assistant_tools import (
    diagnose_symbol,
    get_screener_top_stocks,
    get_financial_audit_report,
    get_system_hardware_status,
    execute_git_pull,
    search_stock_code,
    get_quote_and_kline
)


# =====================================================================
# 一、 盯盘预警引擎 (Price Watcher Engine)
# =====================================================================
def load_watchlist() -> List[Dict[str, Any]]:
    if os.path.exists(WATCH_FILE):
        try:
            with open(WATCH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_watchlist(items: List[Dict[str, Any]]):
    with open(WATCH_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_watch_target(text: str, chat_id: str = "") -> str:
    """
    解析盯盘指令:
    - 盯盘 517520 突破 2.30
    - 盯盘 黄金 跌破 9.40
    """
    m = re.search(r"盯盘\s*(\S+)\s*(突破|跌破|>=|<=|>|<)\s*([0-9.]+)", text)
    if not m:
        return "⚠️ 盯盘格式不正确。\n正确示例：\n• `盯盘 517520 突破 2.30`\n• `盯盘 华安黄金 跌破 9.40`"

    symbol_str, op_str, target_price_str = m.group(1), m.group(2), m.group(3)
    code = search_stock_code(symbol_str)
    if not code:
        return f"⚠️ 未能识别标的【{symbol_str}】，请提供 6 位数字代码。"

    target_price = float(target_price_str)
    condition = "ABOVE" if op_str in ["突破", ">", ">="] else "BELOW"
    
    quote, _ = get_quote_and_kline(code)
    name = quote.get("name", code)
    curr_price = quote.get("price", 0.0)

    items = load_watchlist()
    item_id = f"{code}_{condition}_{target_price}"
    items = [i for i in items if i.get("id") != item_id]

    items.append({
        "id": item_id,
        "code": code,
        "name": name,
        "condition": condition,
        "target_price": target_price,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "chat_id": chat_id,
        "active": True
    })
    save_watchlist(items)

    cond_text = f"突破 (>= ¥{target_price:.3f})" if condition == "ABOVE" else f"跌破 (<= ¥{target_price:.3f})"
    return f"""🎯 【实时盯盘预警已设置成功】
────────────────────────
• 标的名称：{name} ({code})
• 当前现价：¥{curr_price:.3f}
• 监控条件：当价格 {cond_text} 时自动微信报警
• 巡检频率：15 秒 / 次 高频巡检中"""


def get_watchlist_status() -> str:
    items = load_watchlist()
    active_items = [i for i in items if i.get("active", True)]
    if not active_items:
        return "ℹ️ 当前没有正在监控的盯盘任务。\n发送 `盯盘 黄金股 突破 2.30` 即可添加！"

    lines = ["📋 【当前活跃盯盘监控清单】", "────────────────────────"]
    for idx, it in enumerate(active_items):
        op = "突破 >=" if it['condition'] == "ABOVE" else "跌破 <="
        lines.append(f"{idx+1}. **{it['name']}** ({it['code']}): {op} ¥{it['target_price']:.3f} | 设置于 {it['created_at'][11:]}")
    lines.append("\n💡 发送 `清空盯盘` 可一键取消所有监控。")
    return "\n".join(lines)


def clear_watchlist() -> str:
    save_watchlist([])
    return "✅ 已清空所有盯盘监控任务！"


# 独立盯盘后台巡检线程
def price_watcher_loop():
    print("[*] 实时价格盯盘巡检引擎已启动 (15s 周期)...")
    while True:
        try:
            items = load_watchlist()
            active_items = [i for i in items if i.get("active", True)]
            if active_items:
                for it in active_items:
                    code = it["code"]
                    target = it["target_price"]
                    cond = it["condition"]
                    quote, _ = get_quote_and_kline(code)
                    curr = quote.get("price", 0.0)
                    if curr <= 0: continue

                    triggered = False
                    if cond == "ABOVE" and curr >= target:
                        triggered = True
                    elif cond == "BELOW" and curr <= target:
                        triggered = True

                    if triggered:
                        it["active"] = False
                        save_watchlist(items)
                        op_str = f"突破 ¥{target:.3f}" if cond == "ABOVE" else f"跌破 ¥{target:.3f}"
                        alert_msg = f"""🚨 【价格异动紧急预警提醒】
────────────────────────
• 标的名称：{it['name']} ({code})
• 预警触发：现价已 {op_str}！
• 当前最新价：¥{curr:.3f} ({quote.get('change_pct', 0.0):+.2f}%)
• 触发时间：{datetime.now().strftime('%H:%M:%S')}

💡 请及时打开证券账户或结合策略战令进行操作！"""
                        try:
                            webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b74cac3-9fc2-497c-a287-b591246e3393"
                            requests.post(webhook_url, json={"msgtype": "markdown", "markdown": {"content": alert_msg}}, timeout=5)
                        except Exception:
                            pass
        except Exception as e:
            pass
        time.sleep(15)

# 启动盯盘线程
threading.Thread(target=price_watcher_loop, daemon=True).start()


# =====================================================================
# 二、 持仓与策略执行
# =====================================================================
def query_current_holdings() -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 0. 科创-银行轮动 (V5.9 14大长矛全域平铺版)
    sb_file = os.path.join(BASE_DIR, ".star_bank_state.json")
    sb_hold = "100% 科创100ETF (588170)"
    sb_status = "🌟 多头全域共振顶格 (100% 进攻)"
    if os.path.exists(sb_file):
        try:
            with open(sb_file, "r", encoding="utf-8") as f:
                sb_data = json.load(f)
                weights = sb_data.get("target_weights", {})
                sb_status = sb_data.get("stage_desc", sb_status)
                if weights:
                    from chinext_bank_strategy_notifier import ASSET_NAMES as SB_NAMES
                    parts = [f"{w:.0f}% {SB_NAMES.get(c, c)} ({c})" for c, w in weights.items()]
                    sb_hold = " + ".join(parts)
        except Exception:
            pass

    # 0.1 双轨独立：科创-个股龙头增强 (V1.0 Alpha-Master)
    alpha_file = os.path.join(BASE_DIR, ".star_stock_alpha_state.json")
    alpha_hold = "100% 科创100ETF (588170)"
    if os.path.exists(alpha_file):
        try:
            with open(alpha_file, "r", encoding="utf-8") as f:
                alpha_data = json.load(f)
                a_weights = alpha_data.get("target_weights", {})
                if a_weights:
                    from star_stock_alpha_master_notifier import ASSET_NAMES as ALPHA_NAMES
                    parts = [f"{w:.0f}% {ALPHA_NAMES.get(c, c)} ({c})" for c, w in a_weights.items()]
                    alpha_hold = " + ".join(parts)
        except Exception:
            pass

    # 1. 五福 5.2
    wufu_file = os.path.join(BASE_DIR, "quant_strategies", "wufu_5_2", "portfolio_state.json")
    wufu_hold = "100% 纳指生物ETF (513290)"
    if os.path.exists(wufu_file):
        try:
            with open(wufu_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                h = data.get("current_holding", "513290.XSHG").split(".")[0]
                if h == "513290": wufu_hold = "100% 纳指生物ETF (513290)"
                elif h == "518880": wufu_hold = "100% 华安黄金ETF (518880)"
        except Exception:
            pass

    # 2. 七星量化
    seven_file = os.path.join(BASE_DIR, "quant_strategies", "seven_stars", "portfolio_state.json")
    seven_hold = "100% 华安黄金ETF (518880)"
    if os.path.exists(seven_file):
        try:
            with open(seven_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                h = data.get("current_holding", "518880.XSHG").split(".")[0]
                if h == "518880": seven_hold = "100% 华安黄金ETF (518880)"
                elif h == "501018": seven_hold = "100% 南方原油LOF (501018)"
        except Exception:
            pass

    # 3. 场外公募双星
    fund_file = os.path.join(BASE_DIR, ".fund_rotation_state.json")
    fund_hold = "100% 前海开源金银珠宝A/C (002207)"
    if os.path.exists(fund_file):
        try:
            with open(fund_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                fund_hold = f"100% {data.get('holding_name', '前海开源金银珠宝')} ({data.get('holding_code', '002207')})"
        except Exception:
            pass

    return f"""📱 【全量量化舰队 · 当前实盘穿透持仓】
⏰ 查询时间：{now_str}
🛡️ 宏观定调：【黄金大宗 + 农业银行双核避险 + 纳指生物先锋进攻】

────────────────────────
🎯 旗下核心策略实时持仓清单：
1. 🏛️ 科创-银行轮动 (V5.9 14大长矛基准)：
   👉 {sb_hold}
   (10年战绩：累计 +357.5万倍 · 卡玛 22.36 👑)

2. 🚀 科创-个股龙头增强 (V1.0 Alpha-Master 双轨版)：
   👉 {alpha_hold}
   (10年战绩：累计 +855.0亿倍 · 夏普 5.55 · 卡玛 78.08 👑)

3. ⚔️ 五福 5.2/7.3 日内趋势：
   👉 {wufu_hold}
   (今日动作：14:55 止盈黄金，满仓纳指生物)

4. ⭐ 七星跨板块 ETF 轮动：
   👉 {seven_hold}
   (实盘战绩：2026年累计 +414.36%)

5. 📊 场外公募双星杠铃 (8.5 巅峰大圆满)：
   👉 {fund_hold}
   (实盘战绩：10年累计 +2593.58% · 翻27倍)

────────────────────────
💰 8 万元黄金铁三角实盘穿透汇总：
• 👑 黄金资产：¥40,000 (50.0%)
• 🏦 农业银行：¥20,000 (25.0%)
• 🧬 纳指生物：¥20,000 (25.0%)"""


def run_strategy_sync(script_name: str, args: list, task_title: str) -> str:
    start_t = time.time()
    try:
        full_path = os.path.join(BASE_DIR, script_name)
        cmd = [sys.executable, full_path] + args
        res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
        cost_s = time.time() - start_t
        if res.returncode == 0:
            return f"✅ [{task_title}] 执行成功！(耗时 {cost_s:.1f}s)\n最新研报/战令已自动同步并推送到群聊！"
        else:
            return f"⚠️ [{task_title}] 返回警告:\n{res.stderr[:200]}"
    except Exception as e:
        return f"❌ [{task_title}] 异常: {e}"


def get_help_menu() -> str:
    return """🤖 【MUMUMU23333的机器人 · 全能量化掌上中枢】

您可以在微信里直接给我发以下指令：
────────────────────────
📊 【持仓与策略战令】
• 【查持仓】/【仓位】：立即查看 5 大策略实盘穿透持仓
• 【跑个股增强】/【双轨】：执行科创-个股龙头增强 (10年855亿倍 Alpha-Master)
• 【跑科创】/【科创轮动】：执行科创-银行轮动 (V5.9 14大长矛全域平铺版)
• 【跑五福】/【五福】：立即执行五福 5.2 动量策略
• 【跑七星】/【七星】：立即执行七星跨板块 ETF 轮动
• 【生成晚报】/【态势】：生成全球宏观大势与 4K Bento 研报
• 【尾盘巡检】/【全量】：触发 14:48 全量策略战令总巡检

🔍 【智能投研与排雷】
• 【诊断 黄金股ETF】/【诊断 601288】：多空评分、支撑阻力位
• 【排雷 茅台】/【排雷 宁德时代】：财报五维深度穿透体检
• 【选股 动量】/【选股 高股息】：筛选全市场领跑龙头

⚡ 【实时盯盘预警 (免盯盘)】
• 【盯盘 517520 突破 2.30】：价格突破自动微信报警
• 【盯盘 黄金 跌破 9.40】：价格跌破自动微信报警
• 【查盯盘】/【清空盯盘】：管理当前监控任务

🖥️ 【电脑控制与运维】
• 【电脑状态】/【硬件】：查看 CPU/内存/磁盘占用
• 【更新代码】/【git pull】：一键拉取最新 GitHub 策略
• 【ping】：检测电脑在线与响应状态"""


# =====================================================================
# 三、 消息路由与分发处理
# =====================================================================
async def on_message_text(frame):
    try:
        body = getattr(frame, "body", {}) or {}
        content = ""
        if isinstance(body, dict):
            content = body.get("text", {}).get("content", "").strip()
        elif hasattr(body, "text"):
            content = getattr(body.text, "content", "").strip()

        print(f"📩 [收到微信消息] '{content}'")
        stream_id = generate_req_id("stream")
        lower_c = content.lower()

        # 1. 查持仓
        if any(k in lower_c for k in ["持仓", "仓位", "资产", "position"]):
            reply = query_current_holdings()
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)

        # 2. 盯盘功能
        elif lower_c.startswith("盯盘"):
            reply = add_watch_target(content)
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)
        elif any(k in lower_c for k in ["查盯盘", "盯盘列表", "监控列表"]):
            reply = get_watchlist_status()
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)
        elif any(k in lower_c for k in ["清空盯盘", "取消盯盘", "删除盯盘"]):
            reply = clear_watchlist()
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)

        # 3. 个股/ETF 诊断
        elif any(lower_c.startswith(k) for k in ["诊断", "分析", "看", "查 "]):
            kw = re.sub(r"^(诊断|分析|看|查)\s*", "", content).strip()
            reply = diagnose_symbol(kw)
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)

        # 4. 财报排雷
        elif lower_c.startswith("排雷"):
            kw = re.sub(r"^排雷\s*", "", content).strip()
            reply = get_financial_audit_report(kw)
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)

        # 5. 多因子选股
        elif "选股" in lower_c or "榜单" in lower_c:
            reply = get_screener_top_stocks(content)
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)

        # 6. 策略执行
        elif any(k in lower_c for k in ["个股增强", "双轨", "alpha", "牧原", "战神"]):
            await ws_client.reply_stream(frame, stream_id, "⏳ 收到【科创-个股龙头增强 Alpha-Master】执行指令，正在全速计算 16 大长矛与双星共振...", finish=False)
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, run_strategy_sync, "star_stock_alpha_master_notifier.py", ["--push"], "科创-个股增强 Alpha-Master 策略")
            await ws_client.reply_stream(frame, stream_id, f"\n\n{res}", finish=True)
        elif any(k in lower_c for k in ["科创", "kechuang", "银行轮动", "14大长矛"]):
            await ws_client.reply_stream(frame, stream_id, "⏳ 收到【科创-银行轮动 V5.9】执行指令，正在计算全域 14 大长矛动量与风控...", finish=False)
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, run_strategy_sync, "chinext_bank_strategy_notifier.py", ["--push"], "科创-银行轮动 V5.9 策略")
            await ws_client.reply_stream(frame, stream_id, f"\n\n{res}", finish=True)
        elif any(k in lower_c for k in ["五福", "wufu", "5.2"]):
            await ws_client.reply_stream(frame, stream_id, "⏳ 收到【五福 5.2 策略】执行指令，正在全速计算最新动量与风控指标...", finish=False)
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, run_strategy_sync, os.path.join("quant_strategies", "wufu_5_2", "wufu_5_2_local_bot.py"), ["--force"], "五福 5.2 日内趋势策略")
            await ws_client.reply_stream(frame, stream_id, f"\n\n{res}", finish=True)
        elif any(k in lower_c for k in ["七星", "qixing", "7.3"]):
            await ws_client.reply_stream(frame, stream_id, "⏳ 收到【七星量化策略】执行指令，正在计算跨板块龙头...", finish=False)
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, run_strategy_sync, os.path.join("quant_strategies", "seven_stars", "local_etf_quant_bot.py"), ["--now"], "七星跨板块 ETF 轮动策略")
            await ws_client.reply_stream(frame, stream_id, f"\n\n{res}", finish=True)
        elif any(k in lower_c for k in ["晚报", "态势", "研报", "日报", "macro"]):
            await ws_client.reply_stream(frame, stream_id, "⏳ 收到【全球宏观大势研报】生成指令，正在拉取多源行情并渲染 4K Bento 大屏...", finish=False)
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, run_strategy_sync, "global_macro_evening_report.py", ["--force"], "全球宏观大势与量化全景战略晚报")
            await ws_client.reply_stream(frame, stream_id, f"\n\n{res}", finish=True)
        elif any(k in lower_c for k in ["全量", "巡检", "执行", "all", "1448"]):
            await ws_client.reply_stream(frame, stream_id, "⏳ 正在执行 14:48 全量量化策略尾盘巡检...", finish=False)
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, run_strategy_sync, "run_all_strategies_daily.py", [], "全天候全量策略尾盘巡检")
            await ws_client.reply_stream(frame, stream_id, f"\n\n{res}", finish=True)

        # 7. 电脑硬件与运维
        elif any(k in lower_c for k in ["电脑状态", "硬件", "状态", "sys", "health"]):
            reply = get_system_hardware_status()
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)
        elif any(k in lower_c for k in ["更新代码", "git pull", "升级"]):
            reply = execute_git_pull()
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)
        elif lower_c == "ping":
            now_t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            reply = f"🟢 Pong! 【MUMUMU23333的机器人 · 在线正常】\n• ⏰ 响应时间：{now_t}\n• ⚡ WebSocket 极速双向连接就绪！"
            await ws_client.reply_stream(frame, stream_id, reply, finish=True)
        else:
            await ws_client.reply_stream(frame, stream_id, get_help_menu(), finish=True)
    except Exception as e:
        print(f"[!] 处理消息异常: {e}")

ws_client.on("message.text", on_message_text)


async def main_loop():
    print("=" * 80)
    print("🤖 【MUMUMU23333的机器人】全功能旗舰版正在连接企业微信官方服务器...")
    print(f"👉 Bot ID: {BOT_ID}")
    print("=" * 80)
    
    while True:
        try:
            await ws_client.connect_async()
            print("🎉 长连接建立成功！全功能量化掌上中枢已就席！")
            while ws_client.is_connected:
                await asyncio.sleep(1)
            print("⚠️ 连接中断，正在自动重新连接...")
        except Exception as e:
            print(f"[!] 连接异常: {e}，5 秒后重连...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main_loop())
