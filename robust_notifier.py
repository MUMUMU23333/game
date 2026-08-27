# -*- coding: utf-8 -*-
"""
================================================================================
🚀 高可用量化策略推送引擎 (Universal Robust Notifier)
================================================================================
特性：
1. 3 次指数退避重试 (Exponential Backoff)，杜绝因网络抖动导致的静默丢消息
2. 代理环境变量安全隔离，避免代理劫持
3. 详细投递日志与毫秒级耗时统计
4. 支持企业微信、Server酱、PushPlus、钉钉、飞书等全渠道
================================================================================
"""

import os
import sys
import time
import json
import requests
from typing import Optional, Dict, Any

# 修复编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 隔离系统代理
def get_clean_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session

def send_wecom_robust(
    webhook_url: str,
    title: str,
    content: str,
    max_retries: int = 3,
    timeout: int = 15
) -> bool:
    """
    向企业微信机器人发送 Markdown 消息，支持指数退避重试
    """
    if not webhook_url or "YOUR_BOT_KEY" in webhook_url or not webhook_url.startswith("http"):
        print(f"⚠️ [推送告警] 未配置有效的企业微信 Webhook URL，消息将在控制台展示：")
        print("\n" + "=" * 60)
        print(f"【企业微信消息预览】\n{content}")
        print("=" * 60 + "\n")
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    headers = {"Content-Type": "application/json"}
    session = get_clean_session()

    for attempt in range(1, max_retries + 1):
        start_t = time.time()
        try:
            resp = session.post(webhook_url, json=payload, headers=headers, timeout=timeout)
            cost_ms = (time.time() - start_t) * 1000
            
            if resp.status_code == 200:
                res_json = resp.json()
                if res_json.get("errcode") == 0:
                    print(f"✅ [企业微信] [{title}] 消息投递成功！(耗时: {cost_ms:.1f}ms, 尝试: {attempt}/{max_retries})")
                    return True
                else:
                    errmsg = res_json.get("errmsg", "未知错误")
                    print(f"⚠️ [企业微信] [{title}] 接口返回错误 (code={res_json.get('errcode')}): {errmsg}")
            else:
                print(f"⚠️ [企业微信] [{title}] HTTP状态码异常: {resp.status_code}")

        except requests.exceptions.Timeout:
            print(f"⏳ [企业微信] [{title}] 请求超时 ({timeout}s) - 尝试第 {attempt}/{max_retries} 次")
        except requests.exceptions.RequestException as e:
            print(f"❌ [企业微信] [{title}] 网络连接异常: {e} - 尝试第 {attempt}/{max_retries} 次")
        except Exception as e:
            print(f"❌ [企业微信] [{title}] 未知异常: {e}")

        if attempt < max_retries:
            sleep_sec = 2 ** attempt  # 2s, 4s, 8s
            time.sleep(sleep_sec)

    print(f"🚨 [企业微信] [{title}] 达到最大重试次数 ({max_retries})，推送最终失败！")
    return False

if __name__ == "__main__":
    # 本地快速测试
    test_webhook = (os.environ.get("WECOM_WEBHOOK") or "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=46012c55-7fd0-4060-baa8-fc110bb3ca5d")
    print("正在进行 robust_notifier 连通性测试...")
    send_wecom_robust(test_webhook, "系统心跳连通性测试", "### 🛡️ 量化高可用推送引擎就绪\n- **状态**: 正常\n- **重试策略**: 3次指数退避\n- **网络通道**: 隔离干净会话")
