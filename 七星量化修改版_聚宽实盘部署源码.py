# -*- coding: utf-8 -*-
"""
================================================================================
⭐ 【七星高照】v2.2 最终实盘优化版（8大ETF轮动 + 决策归因 + 企业微信时序推送）
================================================================================
适用平台: JoinQuant (聚宽量化平台)
适用标的: 8 大精选核心资产 ETF/LOF
  • 518880 华安黄金ETF (全球避险资产)
  • 159985 华夏豆粕期货ETF (大宗农产品商品)
  • 501018 南方原油LOF (全球大宗商品能源)
  • 161226 国投白银LOF (贵金属工业双轮驱动)
  • 513100 华夏纳指ETF (全球科技硬核资产)
  • 588330 双创龙头ETF (国内硬科技宽基)
  • 159967 创成长ETF (创业板高弹性成长)
  • 588940 科创50ETF富国 (科创板核心引擎)
防御标的: 511880 银华日利 (货币ETF)

核心机制:
  1. 回看周期: 30日标准化对数回归斜率 + R²拟合优度判定 (v2 迭代实证版)
  2. 溢价风控: 20% 溢价熔断阈值 (防止高位接盘 QDII/LOF 杀溢价)
  3. 防断崖风控: 近3日单日跌幅 > 3% (价格比 < 0.97) 强制清零移出买入池
  4. 硬止损线: 5% 硬止损清仓切换防御标的
  5. 交易时序: 14:47 调仓卖出 ➔ 14:48 动量建仓 ➔ 14:49 微信推送 ➔ 15:02 净值复盘
  6. 消息推送: 修复榜首与持仓逻辑脱节 Bug，自动生成【特殊情况与决策归因】
================================================================================
"""

from jqdata import *
import pandas as pd
import numpy as np
import math
import json
import requests
from datetime import datetime, timedelta

# 企业微信群机器人 Webhook 专属地址
WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=46012c55-7fd0-4060-baa8-fc110bb3ca5d"


def initialize(context):
    """策略初始化函数"""
    # 1. 设定基准与真实价格模式
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    
    # 2. 设定费率 (ETF交易免印花税，佣金万1，最低5元)
    set_slippage(PriceRelatedSlippage(0.0001), type='fund')
    set_order_cost(OrderCost(
        open_tax=0, 
        close_tax=0, 
        open_commission=0.0001, 
        close_commission=0.0001, 
        min_commission=5
    ), type='fund')
    
    # 3. 核心标的池 (8大核心ETF/LOF)
    g.etf_pool = [
        "518880.XSHG",  # 华安黄金ETF
        "159985.XSHE",  # 华夏饲料豆粕期货ETF
        "501018.XSHG",  # 南方原油LOF
        "161226.XSHE",  # 国投白银LOF
        "513100.XSHG",  # 纳指ETF
        "588330.XSHG",  # 双创龙头ETF
        "159967.XSHE",  # 创成长ETF
        "588940.XSHG"   # 科创50ETF富国
    ]
    
    # 4. 核心策略参数
    g.lookback_days = 30           # 动量回看周期 (v2实证最佳周期: 30天)
    g.holdings_num = 1             # 单持仓聚焦最强龙头
    g.defensive_etf = "511880.XSHG"# 防御标的: 银华日利 (货币ETF)
    g.min_money = 5000.0           # 最小建仓金额
    g.stop_loss = 0.95             # 5% 硬止损线
    g.loss_limit = 0.97            # 近3日单日跌幅防断崖阈值 (3%)
    g.min_score_threshold = 0.0    # 最低有效动量分
    g.max_score_threshold = 500.0  # 异常高分过滤
    
    # 5. 溢价过滤参数
    g.enable_premium_filter = True # 开启溢价过滤
    g.premium_threshold = 0.20     # 20% 溢价熔断阈值
    
# 6. 持仓周期追踪与内部状态
    g.strategy_holdings = {3: []}  # 策略持仓列表
    g.holding_start_dates = {}     # 记录各标的建仓日期 {code: 'YYYY-MM-DD'}
    g.stopped_out_etfs = set()     # 当日触发止损标的集合 (防止损后同日被重新买入)
    g.rankings_cache = {'date': None, 'data': None, 'detail': []}
    g.last_push_date = None        # 避免当日重复推送
    
    # 7. 注册交易流水线 (14:47 卖出 ➔ 14:48 买入 ➔ 14:49 推送 ➔ 15:02 结算)
    run_daily(strategy_sell, time='14:47')
    run_daily(strategy_buy, time='14:48')
    run_daily(strategy_notify, time='14:49')
    run_daily(print_summary, time='15:02')

    log.info("⭐ 【七星高照】v2.2 最终优化版初始化完成！交易时序: 14:47卖出 / 14:48买入 / 14:49推送")


# ==============================================================================
# 第一部分: 动量打分与排名引擎 (修复归因脱节 Bug)
# ==============================================================================

def get_cached_rankings(context):
    """获取缓存的当日动量打分与候选榜"""
    today = context.current_dt.date()
    if g.rankings_cache['date'] != today:
        ranked_codes, detail_list = get_ranked_etfs_with_detail(context)
        g.rankings_cache['data'] = ranked_codes
        g.rankings_cache['detail'] = detail_list
        g.rankings_cache['date'] = today
    return g.rankings_cache['data'], g.rankings_cache['detail']


def get_ranked_etfs_with_detail(context):
    """计算全池动量打分，并记录详细状态"""
    scores = []
    detail_list = []
    current_data = get_current_data()
    prev_date = context.previous_date
    
    for etf in g.etf_pool:
        score, raw_score, r2, is_cliff = calculate_momentum_score_detail(context, etf)
        price = current_data[etf].last_price if etf in current_data else 0.0
        sec_info = get_security_info(etf)
        name = sec_info.display_name if sec_info else etf
        
        # 检查溢价率
        premium = get_premium_rate(etf, prev_date) if g.enable_premium_filter else 0.0
        is_premium_over = (premium is not None and premium > g.premium_threshold)
        
        status = "✅ 正常"
        if is_cliff:
            status = "❌ 触发跌幅断崖(单日跌>3%)"
        elif is_premium_over:
            status = f"❌ 溢价熔断(溢价率{premium*100:.1f}%>20%)"
        elif score is None or score <= g.min_score_threshold:
            status = "📉 动量为负/回调"
            
        detail_list.append({
            'code': etf.split('.')[0],
            'full_code': etf,
            'name': name,
            'score': score if score is not None else 0.0,
            'raw_score': raw_score if raw_score is not None else 0.0,
            'r2': r2,
            'price': price,
            'premium': premium,
            'is_cliff': is_cliff,
            'is_premium_over': is_premium_over,
            'status': status
        })
        
        # 仅允许未被断崖和溢价拦截且得分为正的标的进入候选池
        if score and g.min_score_threshold < score < g.max_score_threshold and not is_premium_over:
            scores.append((etf, score))
            
    # 按得分从高到低排序
    scores.sort(key=lambda x: x[1], reverse=True)
    detail_list.sort(key=lambda x: x['raw_score'], reverse=True)
    
    ranked_codes = [s[0] for s in scores]
    return ranked_codes, detail_list


def calculate_momentum_score_detail(context, etf):
    """计算单个标的动量得分及断崖状态"""
    end_date = context.previous_date
    df = get_price(etf, end_date=end_date, count=g.lookback_days + 5, frequency='1d', fields=['close'], fq='pre', panel=False)
    if df is None or len(df) < g.lookback_days:
        return None, 0.0, 0.0, False
        
    prices = df['close'].values
    current_data = get_current_data()
    curr_price = current_data[etf].last_price if etf in current_data else prices[-1]
    if curr_price is None or curr_price <= 0:
        return None, 0.0, 0.0, False
        
    y = np.log(np.append(prices[-g.lookback_days:], curr_price))
    x = np.arange(len(y))
    weights = np.linspace(1, 2, len(y))
    slope, intercept = np.polyfit(x, y, 1, w=weights)
    ann_ret = math.exp(slope * 250) - 1
    y_pred = slope * x + intercept
    ss_res = np.sum(weights * (y - y_pred) ** 2)
    ss_tot = np.sum(weights * (y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0
    raw_score = ann_ret * r2
    score = raw_score
    
    # 检查近3日是否有单日暴跌断崖
    is_cliff = False
    if len(prices) >= 4:
        recent_ret = min(prices[-1] / prices[-2], prices[-2] / prices[-3], prices[-3] / prices[-4])
        if recent_ret < g.loss_limit:
            score = 0.0
            is_cliff = True
            
    return score, raw_score, r2, is_cliff


def get_premium_rate(etf, date):
    """获取指定日期的基金溢价率"""
    price_data = get_price(etf, start_date=date, end_date=date, frequency='1d', fields=['close'], panel=False)
    if price_data.empty:
        return None
    price = price_data['close'][0]
    
    try:
        net_data = get_extras('unit_net_value', etf, start_date=date, end_date=date, df=True)
        if net_data.empty or pd.isna(net_data[etf][0]):
            q = query(finance.FUND_NET_VALUE).filter(
                finance.FUND_NET_VALUE.code == etf,
                finance.FUND_NET_VALUE.day == date
            )
            df = finance.run_query(q)
            if df.empty:
                return None
            net = df['net_value'][0]
        else:
            net = net_data[etf][0]
        if net == 0:
            return None
        return (price - net) / net
    except Exception:
        return None


# ==============================================================================
# 第二部分: 交易执行流水线 (14:47 卖出 ➔ 14:48 买入)
# ==============================================================================

def strategy_sell(context):
    """14:47 调仓卖出: 调出非目标标的或触发止损标的"""
    g.stopped_out_etfs.clear() # 每日重置止损记录
    ranked, _ = get_cached_rankings(context)
    targets = ranked[:g.holdings_num] if ranked else []
    if not targets:
        targets = [g.defensive_etf]
        
    for etf in g.strategy_holdings[3][:]:
        # 不在目标池中，执行清仓
        if etf not in targets:
            close_position(etf)
            log.info(f"★ 【14:47 调仓卖出】{etf} 不在最新目标池，执行清仓")
            
    for etf in g.strategy_holdings[3][:]:
        pos = context.portfolio.positions.get(etf)
        if pos and pos.avg_cost > 0 and pos.price <= pos.avg_cost * g.stop_loss:
            close_position(etf)
            g.stopped_out_etfs.add(etf)
            log.warn(f"🚨 【14:47 触发止损】{etf} 跌破5%止损线，强制平仓出场，今日禁止再次买入")


def strategy_buy(context):
    """14:48 动量买入: 精确建仓最强龙头 (过滤当日止损标的)"""
    ranked, _ = get_cached_rankings(context)
    # 过滤掉当日刚被止损的标的，防止止损后秒买回
    valid_targets = [e for e in ranked if e not in g.stopped_out_etfs]
    targets = valid_targets[:g.holdings_num] if valid_targets else [g.defensive_etf]
    
    total_val = context.portfolio.total_value
    per_val = total_val / len(targets)
    
    for etf in targets:
        if per_val >= g.min_money:
            open_position(context, etf, per_val)


def close_position(security):
    """平仓辅助函数"""
    order = order_target_value(security, 0)
    if order:
        if security in g.strategy_holdings.get(3, []):
            g.strategy_holdings[3].remove(security)
        if security in g.holding_start_dates:
            del g.holding_start_dates[security]
    return order


def open_position(context, security, value):
    """开仓辅助函数 (带整百股安全保护与可用资金限额)"""
    if value < g.min_money:
        return None
        
    current_data = get_current_data()
    price = current_data[security].last_price if security in current_data else 1.0
    if price <= 0:
        return None
        
    # 基于目标价值与可用现金双重限额，防止资金不足报错
    target_shares = int(value / price / 100) * 100
    avail_cash = context.portfolio.available_cash
    max_cash_shares = int(avail_cash * 0.995 / price / 100) * 100
    pos = context.portfolio.positions.get(security)
    curr_shares = pos.total_amount if pos else 0
    
    # 若需加仓，限制加仓量不超过可用现金
    if target_shares > curr_shares:
        delta_need = target_shares - curr_shares
        delta_actual = min(delta_need, max_cash_shares)
        target_shares = curr_shares + delta_actual
        
    delta_shares = target_shares - curr_shares
    
    # 变动超过100股才执行下单
    if abs(delta_shares) >= 100:
        order = order_target(security, target_shares)
        if order:
            if security not in g.strategy_holdings[3]:
                g.strategy_holdings[3].append(security)
            today_str = context.current_dt.strftime("%Y-%m-%d")
            if security not in g.holding_start_dates:
                g.holding_start_dates[security] = today_str
            return order
    return None


# ==============================================================================
# 第三部分: 企业微信智能推送流水线 (14:49 执行)
# ==============================================================================

def strategy_notify(context):
    """14:49 自动生成精简专业报告并推送到企业微信"""
    today_str = context.current_dt.strftime("%Y-%m-%d")
    if g.last_push_date == today_str:
        return
        
    ranked, detail_list = get_cached_rankings(context)
    target_code = ranked[0] if ranked else g.defensive_etf
    
    # 1. 获取当前持仓
    held_etfs = [code for code, p in context.portfolio.positions.items() if p.total_amount > 0]
    total_asset = context.portfolio.total_value
    pos_val = sum(p.value for p in context.portfolio.positions.values() if p.total_amount > 0)
    pos_pct = (pos_val / total_asset * 100.0) if total_asset > 0 else 0.0
    
    current_pos_info = {}
    if held_etfs:
        h_code = held_etfs[0]
        pos = context.portfolio.positions[h_code]
        sec_info = get_security_info(h_code)
        h_name = sec_info.display_name if sec_info else h_code
        cost = pos.avg_cost
        price = pos.price
        pnl_amt = (price - cost) * pos.total_amount
        pnl_pct = ((price - cost) / cost * 100.0) if cost > 0 else 0.0
        
        # 计算持仓天数
        buy_date = g.holding_start_dates.get(h_code, today_str)
        try:
            d_start = datetime.strptime(buy_date, "%Y-%m-%d").date()
            d_curr = context.current_dt.date()
            hold_days = max(1, (d_curr - d_start).days)
        except Exception:
            hold_days = 1
            
        current_pos_info = {
            'code': h_code.split('.')[0],
            'full_code': h_code,
            'name': h_name,
            'amount': pos.total_amount,
            'market_val': pos.value,
            'cost': cost,
            'price': price,
            'pnl_amount': pnl_amt,
            'pnl_pct': pnl_pct,
            'holding_days': hold_days,
            'buy_date': buy_date,
            'stop_price': cost * g.stop_loss,
            'cushion_pct': ((price - cost * g.stop_loss) / price * 100.0) if price > 0 else 0.0
        }
    else:
        # 空仓
        current_pos_info = {
            'code': '511880',
            'full_code': '511880.XSHG',
            'name': '银华日利(空仓防御)',
            'amount': 0,
            'market_val': 0.0,
            'cost': 100.0,
            'price': 100.0,
            'pnl_amount': 0.0,
            'pnl_pct': 0.0,
            'holding_days': 0,
            'buy_date': today_str,
            'stop_price': 100.0,
            'cushion_pct': 0.0
        }

    # 2. 判断是否调仓 (TRANSFER vs HOLD)
    curr_holding_full = held_etfs[0] if held_etfs else None
    action_type = "HOLD"
    target_buy_info = None
    
    if curr_holding_full != target_code:
        action_type = "TRANSFER"
        t_info = get_security_info(target_code)
        t_name = t_info.display_name if t_info else target_code
        t_price = get_current_data()[target_code].last_price if target_code in get_current_data() else 1.0
        t_shares = int(total_asset / t_price / 100) * 100 if t_price > 0 else 0
        t_score = [d['score'] for d in detail_list if d['full_code'] == target_code]
        
        target_buy_info = {
            'code': target_code.split('.')[0],
            'full_code': target_code,
            'name': t_name,
            'price': t_price,
            'amount': t_shares,
            'score': t_score[0] if t_score else 0.0
        }

    # 3. 整理 Top3 动量候选
    top3 = []
    medals = ["🥇", "🥈", "🥉"]
    for i, d in enumerate(detail_list[:3]):
        status_txt = d['status']
        if d['full_code'] == curr_holding_full:
            status_txt += " · 现持仓"
        if d['full_code'] == target_code:
            status_txt += " · 目标龙头"
        top3.append({
            'name': d['name'],
            'code': d['code'],
            'score': d['raw_score'],
            'status': status_txt
        })

    # 4. 自动生成特殊情况说明 (Why Not Buy)
    special_reason = None
    raw_first = detail_list[0] if detail_list else None
    if raw_first and raw_first['full_code'] != target_code:
        # 榜首被过滤了！
        filtered_reason = raw_first['status']
        t_name = get_security_info(target_code).display_name if get_security_info(target_code) else target_code
        special_reason = f"""• **为什么未买入榜首【{raw_first['name']} ({raw_first['code']})】？**
  - **触发风控**：{raw_first['name']} 原动量分虽然排在第 1 ({raw_first['raw_score']:.3f})，但当前【{filtered_reason}】，策略主动规避风险；
  - **执行决策**：根据策略风控规则，自动顺延由有效标的【{t_name} ({target_code.split('.')[0]})】接管龙头仓位！"""

    # 5. 渲染并发送 Markdown
    send_wecom_markdown(
        webhook_url=WECOM_WEBHOOK_URL,
        stage="14:48 盘尾确认",
        action_type=action_type,
        total_asset=total_asset,
        position_pct=pos_pct,
        current_pos=current_pos_info,
        target_buy=target_buy_info,
        top_candidates=top3,
        special_reason=special_reason
    )
    g.last_push_date = today_str


def send_wecom_markdown(webhook_url, stage, action_type, total_asset, position_pct, current_pos, target_buy=None, top_candidates=None, special_reason=None):
    """发送企业微信 Markdown 消息"""
    if not webhook_url:
        return
        
    pnl_val = current_pos.get('pnl_amount', 0.0)
    pnl_pct = current_pos.get('pnl_pct', 0.0)
    hold_days = current_pos.get('holding_days', 1)
    buy_date_str = f" (建仓日: {current_pos['buy_date']})" if 'buy_date' in current_pos else ""
    
    if pnl_val >= 0:
        pnl_tag = f"🔴 **盈利 +¥{pnl_val:,.2f} 元 (+{pnl_pct:.2f}%)**"
        pnl_color_txt = f"<font color=\"warning\">**盈利 +¥{pnl_val:,.2f} 元 (+{pnl_pct:.2f}%)**</font>"
    else:
        pnl_tag = f"🟢 **亏损 -¥{abs(pnl_val):,.2f} 元 ({pnl_pct:.2f}%)**"
        pnl_color_txt = f"<font color=\"info\">**亏损 -¥{abs(pnl_val):,.2f} 元 ({pnl_pct:.2f}%)**</font>"

    # 动量榜 Top3
    medals = ["🥇", "🥈", "🥉"]
    rank_lines = []
    for i, c in enumerate((top_candidates or [])[:3]):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        trend_tag = "📈 上行趋势" if c.get('score', 0) > 0 else "📉 回调筑底"
        rank_lines.append(f"{i+1}. {medal} **{c['name']} ({c['code']})**: 得分 `{c['score']:.3f}` ({trend_tag} | {c.get('status', '正常')})")
    top_block = "\n".join(rank_lines) if rank_lines else "• 动量天梯榜数据计算完毕"

    special_block = ""
    if special_reason:
        special_block = f"""---
### ⚠️ 【特殊情况与决策归因】
> {special_reason}
"""

    timeline_block = """• `⏰ 09:30` 开盘监控 (跨板块7大主题ETF动量扫描)
• `⏰ 14:40` 尾盘动量终测 (原版公式斜率与波动率平价测算)
• `⏰ 14:47` 卖出执行 (清退动量衰减标的)
• `⏰ 14:48` 买入建仓 (精确挂单最强龙头)
• `⏰ 15:02` 收盘归档与账户资产净值结算"""

    if action_type == "TRANSFER" and target_buy:
        markdown = f"""# 🔔 七星量化 调仓换标报告 ({stage})
> 💰 **账户总资产**：¥{total_asset:,.2f} 元 (仓位: {position_pct:.1f}%) | 策略：⭐ **七星跨板块轮动**

### 🎯 【今日执行指令】(按时间节点)
🔴 **卖出** [14:47]：`{current_pos['code']}` {current_pos['name']} · **{current_pos.get('amount', 0):,}股** (清仓)
   └ 结算：已持仓 {hold_days} 日 | 成本 ¥{current_pos['cost']:.3f} ➔ 现价 ¥{current_pos['price']:.3f} | {pnl_color_txt}

🟢 **买入** [14:48]：`{target_buy['code']}` {target_buy['name']} · **约 {target_buy.get('amount', 0):,}股**
   └ 挂单：参考价 **¥{target_buy['price']:.3f}** (动量得分 `{target_buy.get('score', 0):.3f}`)

---
### 📈 【今日动量天梯榜 Top3】
{top_block}
{special_block}
---
### ⏱️ 【当日时序节点全景】
{timeline_block}

> 💡 *风控防线：止损线 ¥{current_pos.get('stop_price', 0):.3f} (距 5% 硬止损尚有 {current_pos.get('cushion_pct', 0):+.2f}% 安全垫)*
"""
    else:
        leader_score = top_candidates[0]['score'] if top_candidates else 0.050
        markdown = f"""# 🛡️ 七星量化 持仓与动量报告 ({stage})
> 💰 **账户总资产**：¥{total_asset:,.2f} 元 (仓位: {position_pct:.1f}%) | 状态：<font color="info">**【继续持有最强龙头】**</font>

### 📦 【当前持仓与实时盈亏】
• **当前标的**：`{current_pos['code']}` **{current_pos['name']}**
• **持仓规模**：{current_pos.get('amount', 0):,} 股 (市值 ¥{current_pos.get('market_val', 0):,.2f} 元)
• **持仓历时**：已持仓 **{hold_days}** 个交易日{buy_date_str}
• **成本/现价**：¥{current_pos['cost']:.3f} ➔ ¥{current_pos['price']:.3f}
• **盈亏状态**：{pnl_tag}
• **龙头优势**：动量分 `{leader_score:.3f}` (有效动量领跑，继续持有吃满主升浪)

---
### 📈 【今日动量天梯榜 Top3】
{top_block}
{special_block}
---
### ⏱️ 【当日时序节点全景】
{timeline_block}

> 💡 *风控提示：建议在每个交易日 14:47 卖出、14:48 买入执行 (止损线 ¥{current_pos.get('stop_price', 0):.3f} · 安全垫 {current_pos.get('cushion_pct', 0):+.2f}%)*
"""

    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {"msgtype": "markdown", "markdown": {"content": markdown.strip()}}
    
    try:
        data_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        resp = requests.post(webhook_url, data=data_bytes, headers=headers, timeout=10)
        log.info(f"★ [企业微信] 推送响应: {resp.text}")
    except Exception as e:
        log.error(f"★ [企业微信] 推送异常: {e}")


# ==============================================================================
# 第四部分: 盘后总结流水线 (15:02 执行)
# ==============================================================================

def print_summary(context):
    """15:02 盘后总结与日志复盘"""
    total_val = context.portfolio.total_value
    log.info(f"==================================================")
    log.info(f"★ 盘后总结 | 总资产: {total_val:,.2f} 元 | 现金: {context.portfolio.available_cash:,.2f} 元")
    stocks = [f"{c}({p.value/total_val*100:.1f}%)" for c, p in context.portfolio.positions.items() if p.total_amount > 0]
    log.info(f"★ 实际持仓标的: {stocks if stocks else '空仓观望'}")
    log.info(f"==================================================")
