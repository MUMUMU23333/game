# -*- coding: utf-8 -*-
"""
====================================================================================================
🏆【Google Pro 智能双账号持久化自动故障转移引擎 (Auto-Failover Key Pool v2.0)】
====================================================================================================
核心能力：
1. 【跨进程状态持久化】：通过 .key_pool_state.json 在多进程、多脚本间共享冷却状态与当前活跃账号。
2. 【无感自动重试切号】：提供 @auto_retry_failover 装饰器与 call_llm_with_failover 通用函数，
   遇到 429、ResourceExhausted、Quota Exceeded 时自动切到备用账号并重试，上层代码 0 报错。
# 账号资产通过环境变量或本地 .env 加载
====================================================================================================
"""
import os
import sys
import json
import time
import functools
import logging
from typing import List, Dict, Any, Callable

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".key_pool_state.json")

def _load_env_keys():
    k1 = os.environ.get("GEMINI_API_KEY_1", os.environ.get("GEMINI_API_KEY", ""))
    k2 = os.environ.get("GEMINI_API_KEY_2", "")
    
    # 尝试从本地 .env 读取 (如果环境变量不存在)
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY_1="):
                        k1 = line.split("=", 1)[1].strip()
                    elif line.startswith("GEMINI_API_KEY_2="):
                        k2 = line.split("=", 1)[1].strip()
        except Exception:
            pass
    return k1, k2

_KEY1, _KEY2 = _load_env_keys()

ACCOUNTS_CONFIG = [
    {
        "id": 1,
        "name": "PRO 账号 1 (Primary)",
        "key": _KEY1,
        "email": "Primary Pro"
    },
    {
        "id": 2,
        "name": "PRO 账号 2 (Backup)",
        "key": _KEY2,
        "email": "Backup Pro"
    }
]

class PersistentKeyPool:
    def __init__(self):
        self.accounts = ACCOUNTS_CONFIG
        self.state_file = STATE_FILE
        self._ensure_state()

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"active_key_index": 0, "cooldowns": {}}

    def _save_state(self, state: Dict[str, Any]):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存 Key 状态失败: {e}")

    def _ensure_state(self):
        state = self._load_state()
        if "active_key_index" not in state:
            state["active_key_index"] = 0
        if "cooldowns" not in state:
            state["cooldowns"] = {}
        self._save_state(state)

    def get_current_key_info(self) -> Dict[str, Any]:
        """获取当前最优先且未冷却的 Key 信息"""
        state = self._load_state()
        now = time.time()
        cooldowns = state.get("cooldowns", {})
        
        # 优先使用当前指向的账号
        curr_idx = state.get("active_key_index", 0)
        curr_acc = self.accounts[curr_idx % len(self.accounts)]
        
        if cooldowns.get(curr_acc["key"], 0) < now:
            # 环境变量同步更新
            os.environ["GEMINI_API_KEY"] = curr_acc["key"]
            os.environ["LLM_API_KEY"] = curr_acc["key"]
            return curr_acc

        # 如果当前账号在冷却，寻找另一个未冷却的账号
        for idx, acc in enumerate(self.accounts):
            if cooldowns.get(acc["key"], 0) < now:
                state["active_key_index"] = idx
                self._save_state(state)
                os.environ["GEMINI_API_KEY"] = acc["key"]
                os.environ["LLM_API_KEY"] = acc["key"]
                logging.info(f"🔄 检测到备用账号可用，自动激活: [{acc['name']}]")
                return acc

        # 如果都在冷却期，取最早恢复的
        earliest_acc = min(self.accounts, key=lambda a: cooldowns.get(a["key"], 0))
        os.environ["GEMINI_API_KEY"] = earliest_acc["key"]
        os.environ["LLM_API_KEY"] = earliest_acc["key"]
        return earliest_acc

    def get_active_key(self) -> str:
        return self.get_current_key_info()["key"]

    def mark_exhausted_and_switch(self, failed_key: str, cooldown_seconds: int = 300) -> Dict[str, Any]:
        """标记耗尽并立即切换到下一个账号"""
        state = self._load_state()
        now = time.time()
        if "cooldowns" not in state:
            state["cooldowns"] = {}
        
        state["cooldowns"][failed_key] = now + cooldown_seconds
        
        # 寻找失败账号的名称
        failed_name = next((a["name"] for a in self.accounts if a["key"] == failed_key), "未知账号")
        logging.warning(f"🚨 【配额超限警报】[{failed_name}] 触发速率限制/配额耗尽，进入 {cooldown_seconds}秒 冷却保护！")

        # 切换到另一个账号
        curr_idx = state.get("active_key_index", 0)
        next_idx = (curr_idx + 1) % len(self.accounts)
        state["active_key_index"] = next_idx
        self._save_state(state)

        next_acc = self.accounts[next_idx]
        os.environ["GEMINI_API_KEY"] = next_acc["key"]
        os.environ["LLM_API_KEY"] = next_acc["key"]
        logging.info(f"✨ 【无缝接力成功】已自动切换至备用账号: [{next_acc['name']}] (Key: {next_acc['key'][:12]}...)")
        return next_acc


# 全局单例
pool = PersistentKeyPool()

def get_api_key() -> str:
    """获取当前可用 API Key"""
    return pool.get_active_key()

def get_current_account() -> str:
    """获取当前使用的账号名称"""
    return pool.get_current_key_info()["name"]

def switch_key(failed_key: str = None, cooldown_seconds: int = 300) -> str:
    """手动或捕获异常时触发切换"""
    if not failed_key:
        failed_key = pool.get_active_key()
    new_acc = pool.mark_exhausted_and_switch(failed_key, cooldown_seconds=cooldown_seconds)
    return new_acc["key"]


# ===================================================================
# 核心装饰器与执行器：上层调用自动切号
# ===================================================================
def is_quota_error(e: Exception) -> bool:
    """智能识别是否为配额/限流错误"""
    err_msg = str(e).lower()
    quota_signals = [
        "429", "resource_exhausted", "quota", "rate limit",
        "too many requests", "exceeded", "limit reached", "exhausted"
    ]
    return any(sig in err_msg for sig in quota_signals)


def auto_retry_failover(max_retries: int = 3, cooldown_seconds: int = 300):
    """
    通用函数装饰器：自动捕获配额异常，自动切号重试
    使用方法：
    @auto_retry_failover()
    def my_ai_analysis_function(...):
        ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_retries):
                current_key = pool.get_active_key()
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if is_quota_error(e):
                        logging.warning(f"⚠️ 调用失败 [尝试 {attempt+1}/{max_retries}]: 捕获到配额限制 ({e})")
                        # 切换到下一个 Key
                        pool.mark_exhausted_and_switch(current_key, cooldown_seconds=cooldown_seconds)
                        time.sleep(0.5) # 微延迟后重试
                    else:
                        # 非配额错误直接抛出
                        raise e
            raise last_err
        return wrapper
    return decorator
