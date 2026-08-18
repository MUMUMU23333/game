# 🐂 《牛牛勇敢向前冲 4.2 · 熊市Boss与金币弹幕走位版》 (Bull Run 4.2: Bear Boss AI & Coin Cannon)

> **华尔街金融大逃杀 · 掌机级横屏跑酷 · 原生 HTML5 Canvas + Web Audio API 工业级独立单文件神作**  
> 制作人：**蒋尊森** | 核心架构：**独立小游戏工坊 & 全栈架构专家团**

[![Game Version](https://img.shields.io/badge/version-4.2.0--BearBoss-gold.svg)](https://github.com/MUMUMU23333/game)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-brightgreen.svg)](https://mumumu23333.github.io/game/)
[![FPS](https://img.shields.io/badge/Target%20FPS-60%20Lock-blue.svg)](https://github.com/MUMUMU23333/game)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎮 全球在线试玩直达链接 (Instant Play)

* 📱 **手机 / 电脑浏览器直接打开**：  
  👉 **[https://mumumu23333.github.io/game/](https://mumumu23333.github.io/game/)**  
  *(手机竖屏点开自动旋转为大视野全屏横屏，左右大拇指触控即玩！)*

---

## ✨ 4.2 熊市Boss与金币弹幕走位版重磅全新升级

1. 🐊 **熊市三大 Boss 左右突进攻击 AI (Bear Boss Intelligent AI)**：
   - 包含 **🐊 鳄鱼庄家 (Crocodile Market Maker)**、**🐻 空头巨熊 (Wall Street Giant Bear)**、**🐋 控盘巨鲸 (Wall Street Whale)** 3 大独立 Boss！
   - 具备 **悬停巡逻（HOVER）**、**狂暴突进（LUNGE，前冲至玩家身前张嘴撕咬攻击）** 与 **后撤重整（RETREAT）** 左右智能走位 AI，顶部实时呈现独立 Boss 动态血条！
2. 🕹️ **主角前进与后退灵活走位 (Forward / Backward Navigation)**：
   - 触控操作条与键盘全面支持 **◀️ 后退 (A / ←)** 与 **▶️ 前进 (D / →)**，支持在屏幕 35px ~ 650px 宽广区间内自由微操躲避 Boss 突刺与障碍！
3. 🪙 **金币射击系统与量化金币炮道具 (Coin Bullet Attack & Ammo Cannon)**：
   - 全新 **🪙 金币射击 (J / X 键 或 屏幕金色圆钮)**：高速向右射出旋转金色硬币子弹，带有发光残影与 ¥ 字样！
   - 子弹击中 Boss 造成 20~35 点伤害与爆裂金花；击中做空黑天鹅/阴跌怪直接粉碎并赚取资金！
   - 场景新增 **量化金币炮 (COIN_CANNON)** 拾取道具，直接补满 +30 发金币弹药！
4. 🔒 **单熊市严格单 Boss 锁定机制 (Strict Single Boss per Bear Market)**：
   - 每个大熊市阶段严格仅唤醒 1 个 Boss，离开熊市时 Boss 自动撤退逃窜，彻底杜绝重复刷怪与同屏冲突 BUG！
5. 🎁 **Boss 击溃巨额分红奖励 (Massive Defeat Payout)**：
   - 击败 Boss 喷发 12 连发飞行金币飞入右上角 HUD，狂揽 **¥60,000 ~ ¥100,000** 巨额分红并赠送 1 次免费 Roguelike 秘籍抽卡！
6. 🌸 **牛市自然平滑渐变·蓝天白云鸟语花香**：进入牛市多头主升浪，背景 0.8s 平滑渐变为蔚蓝晴空、悠然浮云、多头吉祥飞鸟、漫天飞舞的樱花金瓣与地平线绽放的野花草地！
7. 📱 **手机端 HUD 黄金比例自适应与防截断**：彻底重构顶部 HUD 弹性栅格与 44px 掌机触控布局，手机横屏下任何金额均 100% 完整清晰呈现！

---

## 🚀 目录结构

```
bull_run_game/
├── index.html                  # 默认入口（100% 独立单文件，含海报与音效）
├── bull_run_standalone.html    # 独立单文件分发版
├── game.html                   # 镜像单文件
├── README.md                   # 项目说明与部署指南
└── assets/
    ├── poster.jpg              # 制作人-蒋尊森 开场海报原图
    └── skins_data.js           # 5款战牛像素立绘 base64 数据
```

---

## 🛠️ 本地运行

无需安装任何繁琐依赖，直接双击 `index.html` 即可在 Chrome / Edge / Safari / 手机微信 中直接运行！
