"""
========================================================================================
👑 DTB-Apex V1.0 溢价熔断旗舰版 · 盘中实时监控与全渠道自动提醒引擎
DTB-Apex V1.0: Real-Time Premium Circuit-Breaker & Barbell Alert Engine
========================================================================================
核心机制：
1. 黄金三元底座：50% 科技资产 + 30% 农业银行 (601288) + 20% 华安黄金 (518880)
2. ATR-Keltner 动量智能接力 (捕捉纳指主升浪加速)
3. 8.0% 相对溢价硬顶熔断 (DPSA: 当 159509 溢价偏离 > 8.0% 时，100% 切换至 513100 避险)
4. 美涨A跌杀溢价错位低吸 (Dislocation Sniper: 偏离 < -1.5% 时逆势满额低吸捡便宜)
5. 极端情绪反向加速收割 (科技市值超配 >= 56% + 溢价 > 8% 时多止盈 4% 锁入农行与黄金)
6. 黄金避险虹吸自愈 (RSI < 28 且黄金暴涨时，抽调黄金高位利润抄底纳指)
========================================================================================
已配置默认推送通道：企业微信机器人 Webhook
========================================================================================
"""

import sys
import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 默认企业微信 Webhook 地址
DEFAULT_WECOM_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=64166d95-479a-4426-a405-e3f9af55656d"


class DTBApexRealtimeMonitor:
    """
    DTB-Apex V1.0 每日盘中/晚间实时信号监控与推送引擎
    """
    def __init__(self,
                 tech_core: str = '513100',      # 纳斯达克100 (低溢价/防守底仓)
                 tech_alpha: str = '159509',     # 纳斯达克科技 (高弹性/主升浪冲刺)
                 bank_code: str = '601288',      # 农业银行 (6.5% 免税高股息现金流)
                 gold_code: str = '518880',      # 华安黄金ETF (全球避险抗通胀)
                 prem_limit: float = 8.0):       # 相对溢价硬顶熔断阈值 (8.0%)
        self.tech_core = tech_core
        self.tech_alpha = tech_alpha
        self.bank_code = bank_code
        self.gold_code = gold_code
        self.prem_limit = prem_limit
        self.session = requests.Session()
        self.session.trust_env = False

    def fetch_realtime_quote(self, code: str) -> dict:
        """
        获取实时行情 (腾讯秒级接口)
        """
        market = 'sh' if code.startswith('51') or code.startswith('58') or code.startswith('60') else 'sz'
        url = f"http://qt.gtimg.cn/q={market}{code}"
        try:
            resp = self.session.get(url, timeout=5)
            text = resp.text
            if "~" in text:
                parts = text.split("~")
                name = parts[1]
                current_price = float(parts[3])
                prev_close = float(parts[4])
                change_pct = float(parts[32])
                high = float(parts[33])
                low = float(parts[34])
                amount = float(parts[37])
                
                return {
                    'code': code,
                    'name': name,
                    'price': current_price,
                    'prev_close': prev_close,
                    'change_pct': change_pct,
                    'high': high,
                    'low': low,
                    'amount_wan': amount
                }
        except Exception as e:
            print(f"[-] 获取 {code} 实时行情失败: {e}")
        return {'code': code, 'name': code, 'price': 0.0, 'prev_close': 0.0, 'change_pct': 0.0, 'high': 0.0, 'low': 0.0, 'amount_wan': 0.0}

    def fetch_history_data(self, code: str, lookback: int = 120) -> pd.DataFrame:
        """
        获取历史前复权 K 线
        """
        market = 'sh' if code.startswith('51') or code.startswith('58') or code.startswith('60') else 'sz'
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,{lookback},qfq"
        try:
            res = self.session.get(url, timeout=5).json()
            raw = res.get('data', {}).get(f'{market}{code}', {})
            k_data = raw.get('qfqday') or raw.get('day', [])
            records = []
            for item in k_data:
                records.append({
                    'date': str(item[0]),
                    'close': float(item[2]),
                    'high': float(item[3]),
                    'low': float(item[4])
                })
            df = pd.DataFrame(records)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                return df.sort_values('date').reset_index(drop=True)
        except Exception as e:
            print(f"[-] 获取 {code} 历史 K 线失败: {e}")
        return pd.DataFrame()

    def calculate_technical_and_premium_radar(self) -> dict:
        """
        计算最新技术动量指标与 159509/513100 相对溢价偏离度
        """
        df_ndx = self.fetch_history_data(self.tech_core, lookback=120)
        df_tech = self.fetch_history_data(self.tech_alpha, lookback=120)
        
        if df_ndx.empty:
            return {'close': 0, 'ema20': 0, 'ma50': 0, 'atr20': 0, 'rsi14': 50, 'prem_spread': 0.0}

        df_ndx['ema20'] = df_ndx['close'].ewm(span=20, adjust=False).mean()
        df_ndx['ma50'] = df_ndx['close'].rolling(50).mean()
        high_low = df_ndx['high'] - df_ndx['low']
        high_close = np.abs(df_ndx['high'] - df_ndx['close'].shift())
        low_close = np.abs(df_ndx['low'] - df_ndx['close'].shift())
        df_ndx['atr20'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(20).mean()
        
        delta = df_ndx['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        df_ndx['rsi14'] = 100 - (100 / (1 + rs))

        # 计算 159509 相对 513100 溢价偏离度
        prem_spread = 0.0
        if not df_tech.empty:
            df_merged = pd.merge(df_ndx[['date', 'close']].rename(columns={'close':'c_ndx'}),
                                 df_tech[['date', 'close']].rename(columns={'close':'c_tech'}), on='date', how='inner')
            if len(df_merged) >= 20:
                df_merged['price_ratio'] = df_merged['c_tech'] / df_merged['c_ndx']
                df_merged['ratio_ma20'] = df_merged['price_ratio'].rolling(20).mean()
                df_merged['prem_spread'] = (df_merged['price_ratio'] / df_merged['ratio_ma20'] - 1) * 100
                prem_spread = df_merged['prem_spread'].iloc[-1]

        last_row = df_ndx.iloc[-1]
        return {
            'close': last_row['close'],
            'ema20': last_row['ema20'],
            'ma50': last_row['ma50'],
            'atr20': last_row['atr20'],
            'rsi14': last_row['rsi14'],
            'prem_spread': prem_spread
        }

    def generate_daily_signal_report(self) -> dict:
        """
        生成 DTB-Apex V1.0 今日全景实盘信号研报
        """
        q_ndx = self.fetch_realtime_quote(self.tech_core)
        q_tech = self.fetch_realtime_quote(self.tech_alpha)
        q_bank = self.fetch_realtime_quote(self.bank_code)
        q_gold = self.fetch_realtime_quote(self.gold_code)
        
        radar = self.calculate_technical_and_premium_radar()
        
        c_cur = q_ndx['price'] if q_ndx['price'] > 0 else radar['close']
        e20 = radar['ema20']
        m50 = radar['ma50']
        atr = radar['atr20']
        rsi = radar['rsi14']
        prem = radar['prem_spread']

        # -------------------------------------------------------------
        # DTB-Apex V1.0 核心决策逻辑
        # -------------------------------------------------------------
        is_dislocation_sniper = (c_cur > e20) and (prem < -1.5)
        is_momentum = (c_cur > e20 + 0.3 * atr) and (rsi > 50)
        is_premium_breaker = (prem > self.prem_limit)

        if is_dislocation_sniper:
            recommended_tech = f"🚀 纳指科技 ({self.tech_alpha}) · 触发【美涨A跌杀溢价折价脉冲低吸】"
            action_badge = "🎯 【折价满额低吸】"
            state_desc = f"隔夜美股趋势健康，A 股日内情绪杀溢价导致相对偏离度达 {prem:+.2f}% (< -1.5%)，触发黄金坑满额捡便宜指令！"
        elif is_momentum:
            if is_premium_breaker:
                recommended_tech = f"🛡️ 纳指100 ({self.tech_core}) · 触发【8.0% 相对溢价硬顶熔断避险】"
                action_badge = "⚠️ 【溢价熔断避险】"
                state_desc = f"纳指动量强劲，但 159509 相对溢价偏离度高达 {prem:+.2f}% (> {self.prem_limit}%)，果断 100% 切换至 513100 避险拒当接盘侠！"
            else:
                recommended_tech = f"🚀 纳指科技 ({self.tech_alpha}) · 主升浪加速态 (溢价安全)"
                action_badge = "🚀 【主升浪冲刺】"
                state_desc = f"纳指强势突破 (现价 > EMA20+0.3ATR)，且 159509 溢价偏离度 {prem:+.2f}% (<= {self.prem_limit}%) 处于安全加速通道，享受科技爆发！"
        else:
            recommended_tech = f"🛡️ 纳指100 ({self.tech_core}) · 低回撤防守/筑底态"
            action_badge = "🛡️ 【稳健防御筑底】"
            state_desc = "纳指处于震荡筑底蓄势期，100% 坚守低回撤的纳指 100 (513100) 压舱石。"

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown_body = f"""### 👑 DTB-Apex V1.0 溢价熔断旗舰版 · 实盘监控信号

> ⏰ **监控时间**：{now_str} (北京时间)

**📊 【实时行情速览】**:
• **纳斯达克100 ({self.tech_core})**: <font color="info">{q_ndx['price']:.3f} 元 ({q_ndx['change_pct']:+.2f}%)</font>
• **纳斯达克科技 ({self.tech_alpha})**: <font color="info">{q_tech['price']:.3f} 元 ({q_tech['change_pct']:+.2f}%)</font>
• **农业银行     ({self.bank_code})**: <font color="info">{q_bank['price']:.3f} 元 ({q_bank['change_pct']:+.2f}%)</font>
• **华安黄金ETF ({self.gold_code})**: <font color="warning">{q_gold['price']:.3f} 元 ({q_gold['change_pct']:+.2f}%)</font>

**🎯 【核心决策指令】**:
• **科技端推荐持有**: <font color="comment">**{recommended_tech}**</font>
• **银行底座建议**: **30%** (农业银行 601288 · 6.5% 免税高股息现金流)
• **黄金底座建议**: **20%** (华安黄金 518880 · 全球避险硬通货)

**⚡ 【DTB-Apex 核心量化雷达】**:
• **相对溢价偏离度**: `{prem:+.2f}%` (8.0% 溢价熔断线 | -1.5% 错位低吸线)
• 纳指100 现价: `{c_cur:.3f}` | EMA20: `{e20:.3f}` | MA50牛熊线: `{m50:.3f}`
• ATR(20) 突破阈值: `{e20 + 0.3 * atr:.3f}` | RSI(14) 动量值: `{rsi:.1f}`

**💡 【当前状态诊断】**:
> {action_badge} {state_desc}

**📌 【全天候再平衡操作指南】**:
• 若科技市值偏离 $\\ge 56\\%$ 且溢价 $> 8\\%$：【触发极端情绪反向加速收割，多卖 4% 狂热筹码锁定至农行与黄金】
• 若科技市值偏离 $\\le 44\\%$：【用农行分红现金流与黄金浮盈低吸纳指】
• 44% ~ 56% 之间：<font color="info">**【🟢 维持持仓，享受免税复利，无需操作】**</font>
"""
        return {
            'time': now_str,
            'title': f"DTB-Apex V1.0 策略提醒: 科技端持有【{recommended_tech.split('·')[0].strip()}】",
            'markdown': markdown_body.strip(),
            'recommended_tech': recommended_tech,
            'prem_spread': prem,
            'q_ndx': q_ndx,
            'q_tech': q_tech,
            'q_bank': q_bank,
            'q_gold': q_gold
        }

    # -------------------------------------------------------------
    # 消息推送渠道
    # -------------------------------------------------------------
    def send_wecom_webhook(self, markdown_content: str, webhook_url: str):
        if not webhook_url: return
        payload = {"msgtype": "markdown", "markdown": {"content": markdown_content}}
        try:
            r = self.session.post(webhook_url, json=payload, timeout=5)
            print(f"[+] [企业微信] 推送响应: {r.text}")
        except Exception as e:
            print(f"[-] [企业微信] 推送失败: {e}")

    def send_pushplus(self, title: str, content: str, token: str):
        if not token: return
        url = "http://www.pushplus.plus/send"
        payload = {"token": token, "title": title, "content": content.replace("\n", "<br/>"), "template": "html"}
        try:
            r = self.session.post(url, json=payload, timeout=5)
            print(f"[+] [PushPlus] 微信推送响应: {r.json().get('msg')}")
        except Exception as e:
            print(f"[-] [PushPlus] 推送失败: {e}")

    def run_and_notify_all(self):
        """
        主执行入口：生成研报并分发到所有已配置渠道
        """
        rep = self.generate_daily_signal_report()
        print("\n" + rep['markdown'] + "\n")
        
        wecom = os.environ.get("WECOM_WEBHOOK", DEFAULT_WECOM_WEBHOOK).strip()
        pp_token = os.environ.get("PUSHPLUS_TOKEN", "").strip()
        
        if wecom:
            self.send_wecom_webhook(rep['markdown'], wecom)
        if pp_token:
            self.send_pushplus(rep['title'], rep['markdown'], pp_token)
            
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_file:
            try:
                with open(summary_file, "a", encoding="utf-8") as f:
                    f.write(rep['markdown'] + "\n")
            except Exception:
                pass


if __name__ == '__main__':
    monitor = DTBApexRealtimeMonitor()
    monitor.run_and_notify_all()
