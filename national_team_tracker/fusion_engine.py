"""
信号双阶段融合引擎 (Signal Fusion Engine)
将 T+0 盘中异动雷达信号 与 T+1 交易所官方份额审计结果深度交叉比对，输出 4 级置信度研判。
"""

from typing import Dict, List, Any
from .intraday_scanner import IntradayScanner
from .share_auditor import ShareAuditor


class FusionEngine:
    """国家队资金与交易异动融合判定引擎"""

    def __init__(self, scanner: IntradayScanner = None, auditor: ShareAuditor = None):
        self.scanner = scanner or IntradayScanner()
        self.auditor = auditor or ShareAuditor()

    def run_composite_analysis(self) -> Dict[str, Any]:
        """
        执行双重确认综合分析
        """
        intraday_data = self.scanner.scan_once()
        audit_data = self.auditor.audit_today_inflow()

        # 建立代码映射字典
        intraday_map = {item["code"]: item for item in intraday_data["metrics"]}
        audit_map = {item["code"]: item for item in audit_data["details"]}

        fused_results = []
        overall_stats = {"AAA": 0, "AA": 0, "C": 0, "D": 0, "NORMAL": 0}

        for code, intra in intraday_map.items():
            audit = audit_map.get(code, {})
            name = intra["name"]
            category = intra["category"]
            price = intra["price"]
            chg_pct = intra["chg_pct"]
            intra_score = intra["score"]
            inflow_money = audit.get("inflow_money_yi", 0.0)
            amount_yi = intra.get("amount_yi", 0.0)

            # ==========================================
            # 融合研判逻辑 (交叉矩阵)
            # ==========================================
            # 1. 强力真护盘 (AAA 级)
            if (intra_score >= 50 and inflow_money >= 5.0) or (inflow_money >= 10.0 and amount_yi >= 20.0):
                grade = "AAA"
                verdict_title = "🟢 AAA级: 真金白银强力护盘"
                confidence = 95
                action_advice = "【核心多头】国家队主力真金白银进场托底，封死下跌空间，建议积极跟随或提升多头仓位。"
                overall_stats["AAA"] += 1

            # 2. 水下隐蔽增持 (AA 级)
            elif inflow_money >= 5.0 and intra_score < 50:
                grade = "AA"
                verdict_title = "🔵 AA级: 水下隐蔽潜伏增持"
                confidence = 85
                action_advice = "【左侧布局】盘面平稳但份额持续大额净增，汇金在水下分批吸筹，指数底部极其坚实。"
                overall_stats["AA"] += 1

            # 3. 虚假脉冲 / 情绪倒手 (C 级)
            elif intra_score >= 50 and inflow_money <= 0.5:
                grade = "C"
                verdict_title = "🟡 C级: 盘中脉冲/游资倒手"
                confidence = 80
                action_advice = "【严禁追高】盘中放量急拉但官方份额并未实质净申购，多为游资或量化倒手，警惕冲高回落。"
                overall_stats["C"] += 1

            # 4. 借机减仓 / 高抛兑现 (D 级)
            elif inflow_money <= -5.0:
                grade = "D"
                verdict_title = "🔴 D级: 机构阶段性净赎回"
                confidence = 85
                action_advice = "【风控减仓】宽基出现巨额净赎回，机构资金正在抽离，注意防御性控仓。"
                overall_stats["D"] += 1

            # 5. 常规波动
            else:
                grade = "NORMAL"
                verdict_title = "⚪ 常态波动"
                confidence = 60
                action_advice = "【维持现状】未触发显著的国家队异动或天量申赎，按原量化策略执行。"
                overall_stats["NORMAL"] += 1

            fused_results.append({
                "code": code,
                "name": name,
                "category": category,
                "price": price,
                "chg_pct": chg_pct,
                "amount_yi": amount_yi,
                "intra_score": intra_score,
                "inflow_money_yi": inflow_money,
                "grade": grade,
                "verdict_title": verdict_title,
                "confidence": confidence,
                "action_advice": action_advice,
                "reasons": intra.get("reasons", [])
            })

        # 6大板块资金归集与动向分析
        sector_flows = {
            "沪深300": 0.0,
            "中证500": 0.0,
            "中证1000": 0.0,
            "创业板": 0.0,
            "科创50": 0.0,
            "大金融(证券银行)": 0.0
        }
        sector_scores = {k: 0.0 for k in sector_flows}
        sector_counts = {k: 0 for k in sector_flows}

        for item in fused_results:
            cat = item["category"]
            inflow = item["inflow_money_yi"]
            score = item["intra_score"]
            
            key = "沪深300"
            if "300" in cat: key = "沪深300"
            elif "500" in cat: key = "中证500"
            elif "1000" in cat: key = "中证1000"
            elif "创业" in cat: key = "创业板"
            elif "科创" in cat: key = "科创50"
            elif "金融" in cat or "证券" in cat or "银行" in cat: key = "大金融(证券银行)"

            sector_flows[key] += inflow
            sector_scores[key] += score
            sector_counts[key] += 1

        # 计算各板块平均异动评分
        for k in sector_scores:
            if sector_counts[k] > 0:
                sector_scores[k] = round(sector_scores[k] / sector_counts[k], 1)

        # 排序寻找国家队首选进攻方向
        sorted_sectors = sorted(sector_flows.items(), key=lambda x: (x[1], sector_scores[x[0]]), reverse=True)
        top_sector = sorted_sectors[0][0]

        # ==========================================
        # 券商金工与大V深度战法：国家队三阶段生命周期研判
        # ==========================================
        # 统计各核心集群的资金热度
        f_300 = sector_flows.get("沪深300", 0.0)
        f_small = sector_flows.get("中证500", 0.0) + sector_flows.get("中证1000", 0.0)
        f_fin = sector_flows.get("大金融(证券银行)", 0.0)
        s_300 = sector_scores.get("沪深300", 0.0)
        s_small = max(sector_scores.get("中证500", 0.0), sector_scores.get("中证1000", 0.0))
        s_fin = sector_scores.get("大金融(证券银行)", 0.0)

        if s_fin >= 45 or f_fin >= 5.0:
            lifecycle_stage = "🚀 【阶段三·情绪主升共振期】大金融/证券爆发，市场风险偏好全面激活"
            kol_tactic = "【大V战法·右侧重仓主升】买入【证券ETF(512880) + 中证1000(512100)】，吃情绪主升最大弹性，仓位 80%~90%。"
        elif s_small >= 45 or f_small >= 5.0:
            lifecycle_stage = "⚡ 【阶段二·流动性扩散反弹期】资金由大盘扩散至中小创，全市场弹性最高"
            kol_tactic = "【大V战法·波段进攻黄金点】买入【中证500(510500) + 创业板(159915)】，5日胜率超76%，仓位 60%~80%。"
        elif s_300 >= 30 or f_300 >= 5.0 or audit_data["total_inflow_yi"] >= 10.0:
            lifecycle_stage = "🛡️ 【阶段一·大盘权重托底期】汇金集中扫货沪深300/银行，封死大盘暴跌下限"
            kol_tactic = "【大V战法·左侧稳健抄底】买入【沪深300(510300) + 银行ETF(512800)】做安全底仓，仓位 40%~60%。"
        else:
            lifecycle_stage = "⚪ 【常态平衡期】国家队处于日常静默监控状态"
            kol_tactic = "【大V战法·耐心中性观望】维持 30%~50% 基础仓位，等待国家队下一轮放量托底信号。"

        # ==========================================
        # 投资者入场时机全局决策 (无需懂量化，直出结论)
        # ==========================================
        if overall_stats["AAA"] >= 1 or audit_data["total_inflow_yi"] >= 20.0:
            timing_signal = "🟢 强烈建议入场跟随 (国家队真金白银重度护盘)"
            timing_stage = f"【主升共振期】多宽基放量净申购 · {lifecycle_stage}"
            position_advice = "70% ~ 90% (积极进取)"
            recommended_targets = f"首选进攻品种: 【{top_sector}】+ 沪深300主力"
            tactical_guide = "【大V次日确认战法】不急于盘中追高，次日早盘 09:35~09:50 回踩分时均线时分批入场，持股 5~10 日锁定胜率。"
        elif overall_stats["AA"] >= 1 or audit_data["total_inflow_yi"] >= 5.0:
            timing_signal = "🔵 建议分批低吸潜伏 (国家队水下隐蔽建仓)"
            timing_stage = f"【左侧筑底期】盘面波澜不惊但份额持续单边净增 · {lifecycle_stage}"
            position_advice = "40% ~ 60% (逢低分批布局)"
            recommended_targets = f"重点配置: 【中证500(510500)】+ 银行ETF(512800)"
            tactical_guide = "【大V分批挂单战法】在指数收阴或回踩 20 日均线下方时分批挂单，买入高胜率底仓品种。"
        elif overall_stats["C"] >= 2 and audit_data["total_inflow_yi"] <= 0:
            timing_signal = "🟡 保持观望 / 严禁追高 (游资量化短线倒手/假护盘)"
            timing_stage = "【情绪假动作】盘中脉冲放量但官方份额零净增，极易冲高回落"
            position_advice = "20% ~ 30% (轻仓防守)"
            recommended_targets = "暂时观望，不盲目开仓"
            tactical_guide = "【大V防被套戒律】当前异动为游资倒手，夜间无真金白银申购，日内拉高坚决不追。"
        elif overall_stats["D"] >= 1 or audit_data["total_inflow_yi"] <= -10.0:
            timing_signal = "🔴 警惕风险 / 逢高减仓 (机构阶段性抽离资金)"
            timing_stage = "【高抛离场期】宽基出现明显净赎回，大资金借反弹套现"
            position_advice = "0% ~ 20% (严控风险)"
            recommended_targets = "建议降低权益仓位，配置货币/国债ETF"
            tactical_guide = "逢反弹坚决减仓防守，等待下一轮官方份额恢复大额净申购。"
        else:
            timing_signal = "⚪ 常态持仓观望 (市场资金处于平衡期)"
            timing_stage = f"【无明显外力干预】国家队处于日常静默状态 · {lifecycle_stage}"
            position_advice = "30% ~ 50% (中性平衡)"
            recommended_targets = "精选个股或按既定指数定投策略执行"
            tactical_guide = "维持常规平衡仓位，持续监控盘中突发异动。"

        # ==========================================
        # 中证1000 + 银行ETF 动态自适应智能杠铃配比引擎
        # ==========================================
        if overall_stats["AAA"] >= 1 or audit_data["total_inflow_yi"] >= 15.0 or s_small >= 40:
            barbell_ratio = "🚀 【极速进攻态】中证1000 (75%) : 银行ETF (25%)"
            barbell_desc = "国家队流动性外溢/共振反弹确立，重仓小盘成长博取最大单波弹性（目标冲高 +8%~+13%）"
        elif s_300 >= 25 or f_300 >= 5.0 or overall_stats["AA"] >= 1:
            barbell_ratio = "⚖️ 【攻守均衡态】中证1000 (50%) : 银行ETF (50%)"
            barbell_desc = "大盘处于企稳通道，等权配置兼顾成长弹性与银行高股息防守"
        else:
            barbell_ratio = "🛡️ 【深度防御态】中证1000 (20%) : 银行ETF (80%)"
            barbell_desc = "市场处于常态震荡或阴跌防守期，重仓银行高股息避险压舱，最大程度压缩回撤"

        timing_decision = {
            "timing_signal": timing_signal,
            "timing_stage": timing_stage,
            "lifecycle_stage": lifecycle_stage,
            "kol_tactic": kol_tactic,
            "barbell_ratio": barbell_ratio,
            "barbell_desc": barbell_desc,
            "position_advice": position_advice,
            "recommended_targets": recommended_targets,
            "tactical_guide": tactical_guide,
            "top_sector": top_sector,
            "sector_flows": sector_flows,
            "sector_scores": sector_scores
        }

        return {
            "timestamp": intraday_data["timestamp"],
            "total_inflow_yi": audit_data["total_inflow_yi"],
            "macro_verdict": audit_data["macro_verdict"],
            "overall_stats": overall_stats,
            "timing_decision": timing_decision,
            "results": fused_results,
            "alerts": intraday_data["alerts"]
        }
