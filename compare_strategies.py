# -*- coding: utf-8 -*-
"""
双量化策略 (五福 5.2 vs 七星量化) —— 专为企业微信优化的全景对比大屏
【包含：各自5万元初始本金、单策略盈亏、双策略合计总资产与总盈亏透视，并自动生成 HTML 大屏与直达链接】
"""

import os
import sys
import json
import datetime
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CONFIG = {
    "wecom_webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=46012c55-7fd0-4060-baa8-fc110bb3ca5d",
    "initial_capital_per_strategy": 50000.0,  # 两个策略基础本金各 5 万元
    "total_initial_capital": 100000.0,        # 组合总初始本金 10 万元
    "html_dashboard_url": "https://mumumu23333.github.io/game/quant_dashboard.html",
    "etf_names": {
        '518880.XSHG': '华安黄金ETF', '501018.XSHG': '南方原油LOF', '161226.XSHE': '国投白银LOF',
        '159985.XSHE': '华夏豆粕ETF', '159980.XSHE': '大成有色ETF', '513310.XSHG': '中韩芯片ETF',
        '159518.XSHE': '标普油气ETF', '159509.XSHE': '纳指科技ETF', '513100.XSHG': '华夏纳指ETF',
        '513520.XSHG': '华夏日经ETF', '513500.XSHG': '博时标普500', '159502.XSHE': '标普生物科技',
        '513400.XSHG': '道琼斯ETF',  '513030.XSHG': '华安德国ETF', '513290.XSHG': '华夏纳指生物',
        '520830.XSHG': '华泰沙特ETF', '159529.XSHE': '标普消费ETF', '588330.XSHG': '双创龙头ETF',
        '159967.XSHE': '创成长ETF',   '588940.XSHG': '科创50ETF富国','511880.XSHG': '银华日利货币'
    }
}

def get_name(code: str) -> str:
    if not code:
        return "现金避险"
    clean_code = code.replace(".XSHG", "").replace(".XSHE", "")
    for k, v in CONFIG["etf_names"].items():
        if clean_code in k:
            return v
    return clean_code

def get_realtime_price(symbol_code: str):
    if not symbol_code:
        return None
    try:
        prefix = "sh" if symbol_code.endswith(".XSHG") or symbol_code.startswith("sh") else "sz"
        code_num = symbol_code.replace(".XSHG", "").replace(".XSHE", "").replace("sh", "").replace("sz", "")
        symbol = prefix + code_num
        url = f"http://hq.sinajs.cn/list={symbol}"
        headers = {"Referer": "https://finance.sina.com.cn"}
        resp = requests.get(url, headers=headers, timeout=5)
        text = resp.text
        if "=" in text:
            parts = text.split("=")[1].replace('"', '').replace(';\n', '').split(',')
            if len(parts) > 3:
                p = float(parts[3]) if float(parts[3]) > 0 else float(parts[2])
                return p
    except Exception:
        pass
    return None

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def generate_comparison():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    seven_path = os.path.join(base_dir, "七星策略", "portfolio_state.json")
    if not os.path.exists(seven_path):
        seven_path = os.path.join(base_dir, "quant_strategies", "seven_stars", "portfolio_state.json")
        
    wufu_path = os.path.join(base_dir, "五福策略5.2", "portfolio_state.json")
    if not os.path.exists(wufu_path):
        wufu_path = os.path.join(base_dir, "quant_strategies", "wufu_5_2", "portfolio_state.json")

    seven_state = load_json(seven_path)
    wufu_state = load_json(wufu_path)
    base_cap = CONFIG["initial_capital_per_strategy"]

    # 1. 解析七星策略
    s_hold = seven_state.get("current_holding", "518880.XSHG")
    s_name = get_name(s_hold)
    s_cost = float(seven_state.get("entry_price", 8.95))
    s_shares = int(seven_state.get("holding_shares", 5500))
    s_cash = float(seven_state.get("cash", 775.0))
    s_latest = get_realtime_price(s_hold) or s_cost
    s_val = s_shares * s_latest
    s_total = s_val + s_cash
    s_pnl = s_total - base_cap
    s_pnl_pct = (s_pnl / base_cap) * 100
    s_stop_dist = ((s_latest - s_cost * 0.95) / s_latest) * 100 if s_latest > 0 else 5.0
    s_pnl_str = f"+¥{s_pnl:,.2f} (+{s_pnl_pct:.2f}%)" if s_pnl >= 0 else f"-¥{abs(s_pnl):,.2f} ({s_pnl_pct:.2f}%)"
    s_pnl_color = "warning" if s_pnl >= 0 else "info"

    # 2. 解析五福策略 5.2
    w_hold = wufu_state.get("current_holding", "518880.XSHG")
    w_name = get_name(w_hold)
    w_cost = float(wufu_state.get("entry_price", 8.95))
    w_shares = int(wufu_state.get("holding_shares", 5500))
    w_cash = float(wufu_state.get("cash", 775.0))
    w_is_weak = wufu_state.get("is_a_share_weak", True)
    w_latest = get_realtime_price(w_hold) or w_cost
    w_val = w_shares * w_latest
    w_total = w_val + w_cash
    w_pnl = w_total - base_cap
    w_pnl_pct = (w_pnl / base_cap) * 100
    w_stop_dist = ((w_latest - w_cost * 0.95) / w_latest) * 100 if w_latest > 0 else 5.0
    w_status_tag = "🔴 大A走弱期 (锁定全球商品)" if w_is_weak else "🟢 大A正常期 (全市场行业池)"
    w_pnl_str = f"+¥{w_pnl:,.2f} (+{w_pnl_pct:.2f}%)" if w_pnl >= 0 else f"-¥{abs(w_pnl):,.2f} ({w_pnl_pct:.2f}%)"
    w_pnl_color = "warning" if w_pnl >= 0 else "info"

    # 3. 组合合计统计 (总本金 10 万元)
    total_assets_combined = s_total + w_total
    total_pnl_combined = total_assets_combined - CONFIG["total_initial_capital"]
    total_pnl_pct_combined = (total_pnl_combined / CONFIG["total_initial_capital"]) * 100
    comb_pnl_str = f"+¥{total_pnl_combined:,.2f} (+{total_pnl_pct_combined:.2f}%)" if total_pnl_combined >= 0 else f"-¥{abs(total_pnl_combined):,.2f} ({total_pnl_pct_combined:.2f}%)"
    comb_pnl_color = "warning" if total_pnl_combined >= 0 else "info"
    comb_emoji = "🔴" if total_pnl_combined >= 0 else "🟢"

    # 4. 生成 HTML 大屏文件
    try:
        from generate_html_dashboard import render_html_dashboard
        render_html_dashboard()
        # 复制到 quant_dashboard.html
        dash_file = os.path.join(base_dir, "quant_dashboard.html")
        idx_file = os.path.join(base_dir, "index.html")
        if os.path.exists(idx_file):
            with open(idx_file, "r", encoding="utf-8") as rf:
                with open(dash_file, "w", encoding="utf-8") as wf:
                    wf.write(rf.read())
    except Exception as e:
        print(f"Warning: HTML dashboard render failed: {e}")

    # 共振判断
    same_asset = (s_hold[:6] == w_hold[:6])
    consensus_text = f"🔥 <font color=\"warning\">**双策略动量龙头 100% 聚焦于【{s_name}】，主升浪共振强劲！**</font>" if same_asset else "💡 <font color=\"comment\">双策略分别配置不同赛道龙头，呈现多流派防御分散格局。</font>"

    markdown_card = f"""### ⚖️ 双量化策略·每日收盘横向对比大屏
> 📅 **汇总时间**：`{now_str}`
> 🌐 **运行状态**：GitHub Actions 云端全自动执行完毕

---
### 💰 【双策略总资产与合计盈亏透视】
• 🏦 **组合总资产**：`¥{total_assets_combined:,.2f}` 元 (初始总本金 `¥100,000.00` 元)
• 📊 **双策略总浮盈**：{comb_emoji} <font color="{comb_pnl_color}">**{comb_pnl_str}**</font>
• 💼 **资金分配结构**：⭐ 七星策略 `¥{s_total:,.2f}` + 🧧 五福 5.2 `¥{w_total:,.2f}`

---
### 🎯 【两核心决策速览】
• ⭐ **七星策略**：`{s_hold[:6]}` **{s_name}** ➔ <font color="info">🛡️ 继续持有</font>
• 🧧 **五福 5.2** ：`{w_hold[:6]}` **{w_name}** ➔ <font color="info">🛡️ 继续持有</font>
> 💡 {consensus_text}

---
### ⭐ 策略一：七星量化策略 (原版)
> 🏷️ *基础本金：¥50,000.00 元 | 14:47 尾盘执行*
• **当前持仓**：**`{s_hold[:6]}` {s_name}** (仓位 `98.5%`)
• **持仓股数**：`{s_shares:,}` 股 (持仓市值 `¥{s_val:,.2f}`)
• **成本/现价**：`¥{s_cost:.3f}` 元 ➔ `¥{s_latest:.3f}` 元
• **单策略盈亏**：<font color="{s_pnl_color}">**{s_pnl_str}**</font>
• **策略总资产**：`¥{s_total:,.2f}` 元 (现金 `¥{s_cash:,.2f}`)
• **风控安全**：距 5% 止损尚有 <font color="info">**+{s_stop_dist:.2f}%**</font> 缓冲

---
### 🧧 策略二：五福策略 5.2 (日内趋势)
> 🏷️ *基础本金：¥50,000.00 元 | 13:10 趋势买卖*
• **宏观研判**：{w_status_tag}
• **当前持仓**：**`{w_hold[:6]}` {w_name}** (仓位 `98.5%`)
• **持仓股数**：`{w_shares:,}` 股 (持仓市值 `¥{w_val:,.2f}`)
• **成本/现价**：`¥{w_cost:.3f}` 元 ➔ `¥{w_latest:.3f}` 元
• **单策略盈亏**：<font color="{w_pnl_color}">**{w_pnl_str}**</font>
• **策略总资产**：`¥{w_total:,.2f}` 元 (现金 `¥{w_cash:,.2f}`)
• **风控安全**：距 5% 止损尚有 <font color="info">**+{w_stop_dist:.2f}%**</font> 缓冲

---
### 📊 【多维核心指标横向对齐】
• 📌 **【持仓标的】** ⭐ `{s_hold[:6]} {s_name[:4]}` 🆚 🧧 `{w_hold[:6]} {w_name[:4]}`
• 📈 **【单项收益】** ⭐ <font color="{s_pnl_color}">{s_pnl_pct:+.2f}%</font> 🆚 🧧 <font color="{w_pnl_color}">{w_pnl_pct:+.2f}%</font>
• 💰 **【策略资产】** ⭐ `¥{s_total:,.0f}` 🆚 🧧 `¥{w_total:,.0f}`
• 🚦 **【今日操作】** ⭐ <font color="info">🛡️ 维持持仓</font> 🆚 🧧 <font color="info">🛡️ 维持持仓</font>
• 🛡️ **【止损垫度】** ⭐ `+{s_stop_dist:.1f}%` 🆚 🧧 `+{w_stop_dist:.1f}%`

---
📱 **[👉 点击查看【双策略收盘全景 HTML 交互大屏】]({CONFIG["html_dashboard_url"]})**
"""

    print(markdown_card)
    
    # 推送企业微信
    try:
        payload = {"msgtype": "markdown", "markdown": {"content": markdown_card}}
        r = requests.post(CONFIG["wecom_webhook_url"], json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        if r.json().get("errcode") == 0:
            print("✅ 包含 HTML 直达链接的全景对比大屏已成功推送到企业微信！")
        else:
            print(f"❌ 企微返回错误: {r.text}")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

if __name__ == "__main__":
    generate_comparison()
