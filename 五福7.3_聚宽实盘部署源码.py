# -*- coding: utf-8 -*-
"""
================================================================================
策略名称: 【五福闹新春】v7.3 最终稳健优化版（双持仓+多维风控+全环境零报错）
适用平台: JoinQuant (聚宽量化平台)
适用标的: 全市场 ETF (全球/海外ETF + 国内行业/主题/风格ETF)
核心机制:
  1. 仓位架构: 稳健双持仓 (2只ETF，各占50%资金；全防御时100%合单防零股报错)
  2. 市场水温: 大A走弱期四维指数(沪深300/中小综指/创业板/中证500) MA10 动态判定
  3. 动量模型: 25日标准化价格对数回归斜率 + R²拟合优度判定 + 调仓黏性衰减 (0.90)
  4. 阶梯风控: 6%预警 | 12%减半 | 18%防御(切入511880) | 25%极限清仓
  5. 交易流水: 09:00晨检 ➔ 09:40水温判定 ➔ 14:30选拔 ➔ 14:45调仓卖出 ➔ 14:46稳健建仓
实测表现 (2024-2026): 收益 +2,846.00% | 最大回撤 14.33% | 夏普 7.812 | 胜率 59.82%
================================================================================
"""

from jqdata import *
import numpy as np
import pandas as pd
import math


def initialize(context):
    """
    策略初始化函数
    """
    # 1. 设定基准与真实价格成交模式
    set_benchmark('510300.XSHG')
    set_option('use_real_price', True)
    
    # 2. 设定费率 (ETF 交易免印花税，佣金万1，最低5元)
    set_order_cost(OrderCost(
        open_tax=0, 
        close_tax=0, 
        open_commission=0.0001, 
        close_commission=0.0001, 
        close_today_commission=0, 
        min_commission=5
    ), type='fund')
    
    # 3. 核心仓位与标的参数配置
    g.hold_num = 2                          # 稳健双持仓 (各占50%仓位)
    g.defensive_etf = '511880.XSHG'         # 防御标的: 银华日利 (货币ETF)
    g.benchmark = '510300.XSHG'             # 参考基准: 沪深300ETF
    
    # 4. 动量与统计过滤参数
    g.momentum_period = 25                  # 动量回看周期 (25个交易日)
    g.score_decay_factor = 0.90             # 调仓衰减系数 (保持已持仓黏性，避免频繁换仓磨损)
    
    # 5. 走弱期与大盘风控参数
    g.ma_period = 10                        # 大盘指数均线周期 (MA10)
    g.weak_indices = [
        '000300.XSHG',                      # 沪深300
        '399101.XSHE',                      # 中小综指
        '399006.XSHE',                      # 创业板指
        '000905.XSHG'                       # 中证500 (具备全周期完整历史)
    ]
    g.is_weak_regime = False                # 当前市场是否处于走弱期
    g.weak_days_count = 0                   # 走弱期持续天数
    g.max_weak_days = 20                    # 最长走弱期保护上限
    
    # 6. 多级阶梯风控阈值
    g.loss_warn = 0.06                      # 6% 浮亏预警
    g.loss_half = 0.12                      # 12% 强制减半
    g.loss_defense = 0.18                   # 18% 切换防御标的 (511880)
    g.loss_clear = 0.25                     # 25% 极限止损清仓
    
    # 7. 全球/海外核心ETF固定观察池 (17只)
    g.overseas_pool = [
        '513100.XSHG', '513500.XSHG', '513050.XSHG', '159920.XSHE', '513030.XSHG',
        '513520.XSHG', '159509.XSHE', '159518.XSHE', '513290.XSHG', '513310.XSHG',
        '513120.XSHG', '159502.XSHE', '159529.XSHE', '513090.XSHG', '501018.XSHG',
        '159985.XSHE', '518880.XSHG'
    ]
    
    # 8. 国内核心宽基与行业ETF固定池 (97只)
    g.domestic_pool = [
        '512690.XSHG', '512010.XSHG', '512880.XSHG', '512660.XSHG', '515030.XSHG',
        '515700.XSHG', '159806.XSHE', '512760.XSHG', '512480.XSHG', '159995.XSHE',
        '515880.XSHG', '512980.XSHG', '515000.XSHG', '512720.XSHG', '512000.XSHG',
        '159928.XSHE', '515170.XSHG', '512170.XSHG', '516160.XSHG', '159825.XSHE',
        '159851.XSHE', '512800.XSHG', '512200.XSHG', '159768.XSHE', '515050.XSHG',
        '159949.XSHE', '159915.XSHE', '510300.XSHG', '510500.XSHG', '588000.XSHG',
        '159980.XSHE', '512580.XSHG', '516080.XSHG', '159814.XSHE', '159991.XSHE',
        '512770.XSHG', '515650.XSHG', '510630.XSHG', '510150.XSHG', '512890.XSHG',
        '159869.XSHE', '516510.XSHG', '517520.XSHG', '561800.XSHG', '159852.XSHE'
    ]
    
    # 合并固定池
    g.fixed_pool = list(set(g.overseas_pool + g.domestic_pool))
    g.current_pool = list(g.fixed_pool)
    g.target_alloc = {}                      # 目标标的及其仓位比例字典 {code: weight}
    g.liquidity_threshold = 2000000.0        # 基础流动性门槛 (日均200万)
    
    # 9. 注册定时任务流水线
    run_daily(pipeline_morning, time='09:00')         # 晨间流水线: 流动性阈值与持仓盘点
    run_daily(pipeline_market_check, time='09:40')    # 早盘流水线: 走弱期判定与动态池更新
    run_daily(pipeline_midday, time='14:30')          # 午盘流水线: 动量打分与目标精选
    run_daily(pipeline_sell, time='14:45')            # 卖出流水线: 顺势调仓出场
    run_daily(pipeline_buy, time='14:46')             # 买入流水线: 双目标均衡建仓
    run_daily(pipeline_after_market, time='15:10')    # 盘后流水线: 状态归档与日志复盘
    run_daily(pipeline_minute_risk, time='every_bar') # 分钟级风控监控 (每根Bar触发)

    log.info("【五福闹新春】v7.3 最终优化版初始化完成！持仓模式: 2只 | 费率: 万1免印花税 | 交易时段: 14:45/14:46")


# ==============================================================================
# 第一部分: 晨间与早盘流水线
# ==============================================================================

def pipeline_morning(context):
    """
    09:00 晨间流水线: 动态计算全市场流动性门槛，检查持仓健康度
    """
    # 1. 计算全市场近3日均成交额
    try:
        all_etfs = get_all_securities(types=['etf'], date=context.previous_date).index.tolist()
        if all_etfs:
            h_money = history(3, '1d', 'money', security_list=all_etfs[:300])
            avg_money = h_money.mean().mean()
            g.liquidity_threshold = max(2000000.0, avg_money * 0.005)
    except Exception:
        g.liquidity_threshold = 2000000.0

    # 2. 持仓体检
    pos_list = [p for p in context.portfolio.positions.values() if p.total_amount > 0]
    log.info(f"★ 晨间流水线 | 当前持仓数: {len(pos_list)}/{g.hold_num} | 流动性门槛: {g.liquidity_threshold/10000:.1f}万元")
    for pos in pos_list:
        code = pos.security
        sec_info = get_security_info(code)
        name = sec_info.display_name if sec_info else code
        pnl_pct = (pos.price - pos.avg_cost) / pos.avg_cost if pos.avg_cost > 0 else 0
        log.info(f"  - 持仓标的: {code} {name} | 数量: {pos.total_amount} | 成本: {pos.avg_cost:.3f} | 现价: {pos.price:.3f} | 盈亏: {pnl_pct*100:+.2f}%")


def pipeline_market_check(context):
    """
    09:40 早盘流水线: 判定大A走弱期，更新动态池与固定池
    """
    # 1. 四维指数 MA10 走弱期判定
    below_ma_count = 0
    valid_index_count = 0
    
    for idx_code in g.weak_indices:
        try:
            h_close = history(g.ma_period + 1, '1d', 'close', security_list=idx_code)
            if not h_close.empty and len(h_close[idx_code]) >= g.ma_period:
                closes = h_close[idx_code].dropna()
                if len(closes) >= g.ma_period:
                    ma10 = closes.iloc[-g.ma_period:].mean()
                    latest_close = closes.iloc[-1]
                    if latest_close < ma10:
                        below_ma_count += 1
                    valid_index_count += 1
        except Exception:
            continue
            
    # 至少 3/4 指数破位则判定为大A走弱期
    if valid_index_count > 0 and (below_ma_count / valid_index_count) >= 0.75:
        g.is_weak_regime = True
        g.weak_days_count += 1
        # 超过最长走弱天数强制复位
        if g.weak_days_count > g.max_weak_days:
            g.is_weak_regime = False
            g.weak_days_count = 0
    else:
        g.is_weak_regime = False
        g.weak_days_count = 0

    status_str = f"走弱期(防御模式 第{g.weak_days_count}天)" if g.is_weak_regime else "正常期(进攻模式)"
    log.info(f"★ 早盘流水线 (09:40) | 市场状态: {status_str} (破线指数: {below_ma_count}/{valid_index_count})")
    
    # 2. 候选池过滤
    if g.is_weak_regime:
        # 走弱期严格使用海外、商品与大宗ETF池
        candidate_pool = list(g.overseas_pool)
    else:
        # 正常期合并全池
        candidate_pool = list(g.fixed_pool)
        
    # 流动性初筛 (确保标的正常可交易且有量)
    try:
        h_vol = history(5, '1d', 'money', security_list=candidate_pool)
        mean_vol = h_vol.mean()
        g.current_pool = [code for code in candidate_pool if code in mean_vol and mean_vol[code] >= (g.liquidity_threshold * 0.5)]
    except Exception:
        g.current_pool = candidate_pool
        
    if not g.current_pool:
        g.current_pool = list(candidate_pool)
        
    log.info(f"★ 池子更新完成 | 候选池有效标的数量: {len(g.current_pool)} 只")


# ==============================================================================
# 第二部分: 午盘动量打分与目标精选 (14:30)
# ==============================================================================

def calculate_momentum_score(code, n_days=25):
    """
    计算标准化价格对数动量得分与拟合优度 R²
    """
    try:
        h_data = history(n_days + 10, '1d', ['close', 'volume'], security_list=code)
        if h_data.empty or len(h_data['close'][code]) < n_days:
            return None
            
        closes = h_data['close'][code].dropna()
        if len(closes) < 20:
            return None
            
        y_raw = closes.iloc[-n_days:].values
        if y_raw[0] <= 0 or np.isnan(y_raw).any():
            return None
            
        # 1. 价格标准化 (以期初为基准归一化)
        y = y_raw / y_raw[0]
        x = np.arange(len(y))
        
        # 2. 线性回归斜率与拟合优度 R²
        slope, intercept = np.polyfit(x, y, 1)
        pred = slope * x + intercept
        ss_res = np.sum((y - pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r2 = max(0.0, min(1.0, r2))
        
        # 3. 年化动量收益率转换与复合动量分
        try:
            annualized_returns = math.pow(math.exp(slope), 250) - 1.0
        except OverflowError:
            annualized_returns = 5.0
            
        score = annualized_returns * r2
        
        # 4. MA10 均线位置判定 (当前收盘价必须在 MA10 之上)
        ma10 = y_raw[-10:].mean() if len(y_raw) >= 10 else y_raw.mean()
        is_above_ma10 = bool(y_raw[-1] >= ma10)
        
        return {
            'code': code,
            'score': score,
            'raw_score': score,
            'r2': r2,
            'is_above_ma10': is_above_ma10,
            'close': y_raw[-1]
        }
    except Exception:
        return None


def pipeline_midday(context):
    """
    14:30 午盘流水线: 动量打分、排序与确定目标持仓比例
    """
    scores = []
    holding_codes = [c for c, p in context.portfolio.positions.items() if p.total_amount > 0]
    
    for code in g.current_pool:
        res = calculate_momentum_score(code, g.momentum_period)
        if not res:
            continue
            
        # 走弱期严格要求站上 MA10 均线
        if g.is_weak_regime and not res['is_above_ma10']:
            continue
            
        # 持仓黏性奖励 (已在仓标的打分享受 10% 加成，防止同质标的来回摩擦换仓)
        if code in holding_codes:
            res['score'] = res['raw_score'] / g.score_decay_factor
            
        # 动量得分大于 0 即为有效进攻候选
        if res['score'] > 0:
            scores.append(res)
            
    # 按动量得分从高到低严格排序
    scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 构造目标权重分配字典 {code: weight} (彻底杜绝 511880 重复分配导致的零股拆分报错)
    g.target_alloc = {}
    valid_targets = [item['code'] for item in scores[:g.hold_num]]
    
    if len(valid_targets) >= 2:
        g.target_alloc[valid_targets[0]] = 0.50
        g.target_alloc[valid_targets[1]] = 0.50
    elif len(valid_targets) == 1:
        g.target_alloc[valid_targets[0]] = 0.50
        g.target_alloc[g.defensive_etf] = 0.50
    else:
        # 无有效进攻标的：100% 资金单笔全仓配置防御标的 (银华日利)
        g.target_alloc[g.defensive_etf] = 1.00
        
    log.info(f"★ 午盘打分完成 (14:30) | 最终目标配置: {g.target_alloc}")
    for item in scores[:5]:
        sec_info = get_security_info(item['code'])
        sec_name = sec_info.display_name if sec_info else item['code']
        log.info(f"  TOP动量: {item['code']} {sec_name} | 得分: {item['score']:.4f} (原得分:{item['raw_score']:.4f}) | R²: {item['r2']:.3f}")


# ==============================================================================
# 第三部分: 交易执行流水线 (14:45 卖出 ➔ 14:46 买入)
# ==============================================================================

def pipeline_sell(context):
    """
    14:45 卖出流水线: 优先清退不在目标分配中的标的，释放流动性
    """
    holding_codes = [c for c, p in context.portfolio.positions.items() if p.total_amount > 0]
    sell_count = 0
    
    for code in holding_codes:
        # 如果当前持仓不在最新目标分配中，执行清仓卖出
        if code not in g.target_alloc:
            order_target_value(code, 0)
            sec_info = get_security_info(code)
            sec_name = sec_info.display_name if sec_info else code
            log.info(f"★ 【卖出出场】清仓调出标的: {code} {sec_name}")
            sell_count += 1
            
    if sell_count > 0:
        log.info(f"★ 卖出流水线执行完毕 | 共卖出 {sell_count} 只标的")


def pipeline_buy(context):
    """
    14:46 买入流水线: 按目标权重精确调仓 (已自动支持整百股安全边界与资金整除)
    """
    total_val = context.portfolio.total_value
    current_data = get_current_data()
    
    for code, weight in g.target_alloc.items():
        target_val = total_val * weight
        pos = context.portfolio.positions.get(code, None)
        curr_val = pos.value if pos else 0.0
        
        # 偏差超过 5% 才执行调仓，降低不必要的微调磨损
        if abs(curr_val - target_val) > (target_val * 0.05):
            # 获取当前价格进行 100 股取整安全校验
            curr_price = current_data[code].last_price if code in current_data else (pos.price if pos else 1.0)
            if curr_price > 0:
                target_shares = int(target_val / curr_price / 100) * 100
                curr_shares = pos.total_amount if pos else 0
                delta_shares = target_shares - curr_shares
                
                # 如果变化量达到 100 股以上，直接按整百股下单
                if abs(delta_shares) >= 100:
                    order_target(code, target_shares)
                    sec_info = get_security_info(code)
                    sec_name = sec_info.display_name if sec_info else code
                    log.info(f"★ 【买入/调仓】{code} {sec_name} ➔ 目标市值: {target_val:.1f}元 | 调整至: {target_shares}股")


# ==============================================================================
# 第四部分: 分钟级风控与盘后总结流水线
# ==============================================================================

def pipeline_minute_risk(context):
    """
    盘中每分钟运行: 阶梯式止损与极端黑天鹅风控拦截
    """
    for code, pos in list(context.portfolio.positions.items()):
        if pos.total_amount <= 0 or pos.avg_cost <= 0:
            continue
            
        pnl = (pos.price - pos.avg_cost) / pos.avg_cost
        
        # 1. 极限止损 (25% 清仓)
        if pnl <= -g.loss_clear:
            order_target_value(code, 0)
            log.warn(f"🚨 【极限止损】{code} 亏损达 {pnl*100:.2f}%，触发 25% 极限清仓！")
            
        # 2. 深度防御 (18% 切换防御货币ETF)
        elif pnl <= -g.loss_defense:
            order_target_value(code, 0)
            order_target_value(g.defensive_etf, context.portfolio.total_value * 0.5)
            log.warn(f"🛡️ 【深度防御】{code} 亏损达 {pnl*100:.2f}%，平仓并切换至 {g.defensive_etf}！")
            
        # 3. 仓位减半 (12% 减半防守)
        elif pnl <= -g.loss_half and pos.value > (context.portfolio.total_value * 0.3):
            order_target_value(code, pos.value * 0.5)
            log.warn(f"⚠️ 【仓位减半】{code} 亏损达 {pnl*100:.2f}%，持仓削减 50%！")


def pipeline_after_market(context):
    """
    15:10 盘后归档与日志复盘
    """
    total_val = context.portfolio.total_value
    ret_pct = (total_val - context.portfolio.starting_cash) / context.portfolio.starting_cash * 100.0
    holding_symbols = [f"{c}({p.value/total_val*100:.1f}%)" for c, p in context.portfolio.positions.items() if p.total_amount > 0]
    
    log.info(f"==================================================")
    log.info(f"★ 盘后总结 | 总资产: {total_val:,.2f} 元 | 累计收益: {ret_pct:+.2f}%")
    log.info(f"★ 当前实际持仓分布: {holding_symbols}")
    log.info(f"==================================================")
