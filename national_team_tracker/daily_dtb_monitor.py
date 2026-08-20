"""
========================================================================================
DTB 4.0 巅峰旗舰版 · 盘中实时监控与全渠道自动提醒引擎
Real-Time Daily Monitor & Multi-Channel Alert Engine (GitHub Actions Ready)
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


class DTBRealtimeMonitor:
    """
    DTB 4.0 每日盘中/收盘实时信号监控与提醒器
    """
    def __init__(self,
                 tech_core: str = '513100',      # 纳指100
                 tech_alpha: str = '159509',     # 纳指科技
                 bank_code: str = '601288',      # 农业银行 (可配置 512800)
                 gold_code: str = '518880'):     # 华安黄金
        self.tech_core = tech_core
        self.tech_alpha = tech_alpha
        self.bank_code = bank_code
        self.gold_code = gold_code
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
                volume = float(parts[36])
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
        return {'code': code, 'name': code, 'price': 0.0, 'change_pct': 0.0}

    def fetch_history_factors(self, code: str = '513100', lookback: int = 120) -> dict:
        """
        获取 T-1 历史指标群 (EMA20, MA50, ATR20, RSI14)
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
                df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
                df['ma50'] = df['close'].rolling(50).mean()
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                df['atr20'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(20).mean()
                
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.nan)
                df['rsi14'] = 100 - (100 / (1 + rs))
                
                last_row = df.iloc[-1]
                return {
                    'close': last_row['close'],
                    'ema20': last_row['ema20'],
                    'ma50': last_row['ma50'],
                    'atr20': last_row['atr20'],
                    'rsi14': last_row['rsi14']
                }
        except Exception as e:
            print(f"[-] 计算历史技术指标失败: {e}")
        return {'close': 0, 'ema20': 0, 'ma50': 0, 'atr20': 0, 'rsi14': 50}

    def generate_daily_signal_report(self) -> dict:
        """
        生成今日全景信号研报
        """
        q_ndx = self.fetch_realtime_quote(self.tech_core)
        q_tech = self.fetch_realtime_quote(self.tech_alpha)
        q_bank = self.fetch_realtime_quote(self.bank_code)
        q_gold = self.fetch_realtime_quote(self.gold_code)
        
        factors = self.fetch_history_factors(self.tech_core)
        
        c_cur = q_ndx['price'] if q_ndx['price'] > 0 else factors['close']
        e20 = factors['ema20']
        m50 = factors['ma50']
        atr = factors['atr20']
        rsi = factors['rsi14']
        
        # 1. 判定当前科技端主选标的
        is_breakout = (c_cur > e20 + 0.3 * atr) and (rsi > 50)
        
        if is_breakout:
            recommended_tech = f"🚀 纳指科技 ({self.tech_alpha}) · 主升浪加速态"
        else:
            recommended_tech = f"🛡️ 纳指100 ({self.tech_core}) · 低回撤防守/筑底态"

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown_body = f"""### 👑 DTB 4.0 巅峰旗舰版 · 今日量化实盘监控信号

> ⏰ **监控时间**：{now_str} (北京时间)

**📊 【实时行情速览】**:
• **纳斯达克100 (513100)**: <font color="info">{q_ndx['price']:.3f} 元 ({q_ndx['change_pct']:+.2f}%)</font>
• **纳斯达克科技 (159509)**: <font color="info">{q_tech['price']:.3f} 元 ({q_tech['change_pct']:+.2f}%)</font>
• **农业银行     (601288)**: <font color="info">{q_bank['price']:.3f} 元 ({q_bank['change_pct']:+.2f}%)</font>
• **华安黄金ETF (518880)**: <font color="warning">{q_gold['price']:.3f} 元 ({q_gold['change_pct']:+.2f}%)</font>

**🎯 【核心决策指令】**:
• **科技端推荐持有**: <font color="comment">**{recommended_tech}**</font>
• **银行底座建议**: **30%** (农业银行 601288 · 6.5%分红压舱石)
• **黄金底座建议**: **20%** (华安黄金 518880 · 避险抗通胀)

**⚡ 【量化技术雷达】**:
• 纳指100 现价: `{c_cur:.3f}` | EMA20: `{e20:.3f}` | MA50牛熊线: `{m50:.3f}`
• ATR(20) 突破阈值: `{e20 + 0.3 * atr:.3f}` | RSI(14) 动量值: `{rsi:.1f}`

**📌 【再平衡操作提示】**:
• 若科技市值偏离 $\\ge 56\\%$：【止盈部分科技，买入农行与黄金】
• 若科技市值偏离 $\\le 44\\%$：【用农行股息与黄金浮盈低吸纳指】
• 44% ~ 56% 之间：<font color="info">**【🟢 维持持仓，静待复利，无需操作】**</font>
"""
        return {
            'time': now_str,
            'title': f"DTB 4.0 策略提醒: 科技端持有【{recommended_tech.split('·')[0].strip()}】",
            'markdown': markdown_body.strip(),
            'recommended_tech': recommended_tech,
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
        主执行入口：生成报告并分发到所有已配置渠道
        """
        rep = self.generate_daily_signal_report()
        print("\n" + rep['markdown'] + "\n")
        
        # 读取环境变量配置 (优先环境变量，默认企业微信)
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
    monitor = DTBRealtimeMonitor()
    monitor.run_and_notify_all()
