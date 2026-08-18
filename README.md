# 🐂 《牛牛勇敢向前冲 4.3 · 爽快音效与史诗打击特效版》 (Bull Run 4.3: Juicy Sound & Epic Impact VFX)

> **华尔街金融大逃杀 · 掌机级横屏跑酷 · 原生 HTML5 Canvas + Web Audio API 工业级独立单文件神作**  
> 制作人：**蒋尊森** | 核心架构：**独立小游戏工坊 & 全栈架构专家团**

[![Game Version](https://img.shields.io/badge/version-4.3.0--JuicyVFX-gold.svg)](https://github.com/MUMUMU23333/game)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-brightgreen.svg)](https://mumumu23333.github.io/game/)
[![FPS](https://img.shields.io/badge/Target%20FPS-60%20Lock-blue.svg)](https://github.com/MUMUMU23333/game)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎮 全球在线试玩直达链接 (Instant Play)

* 📱 **手机 / 电脑浏览器直接打开**：  
  👉 **[https://mumumu23333.github.io/game/](https://mumumu23333.github.io/game/)**  
  *(手机竖屏点开自动旋转为大视野全屏横屏，左右大拇指触控即玩！)*

---

## ✨ 4.3 爽快音效与史诗打击特效版重磅升级

1. 🎵 **动态五声音阶拾取音效与连板泛音 (Dynamic Pentatonic Coin SFX)**：
   - 采用纯净温润三角波 + 晶莹正弦波双振荡器合成马里奥级金币音效；
   - 连续拾取金币触发 **动态五声音阶爬升（Pentatonic Major Scale Climb）**；连击达到 5 连板以上时额外注入璀璨的高八度泛音共鸣与彩虹星芒爆散！
2. 💥 **拳拳到肉击中反馈与破甲打击感 (Juicy Boss Hit Impact & White Flash)**：
   - **双频复合打击音效**：`130Hz -> 38Hz` 超低频肉体击中重音（Sub-bass punch）+ `880Hz -> 320Hz` 清脆金属破甲撞击音；暴击触发 `1200Hz` 强力爆破音！
   - **受击白闪（Damage Flash）**：Boss 被击中瞬间全身高亮白闪 3~5 帧；
   - **物理受击后挫（Recoil Twitch）**：Boss 受击时产生 8~14px 的物理后仰与弹性恢复；
   - **浮动暴击跳字与火花**：爆出 `🔥 暴击 -XX HP` / `💥 -XX HP` 弹跳动态伤害数字与散射粒子。
3. 👑 **击败 Boss 史诗级终极爆鸣与凯旋交响 (Epic Boss Defeat Climax)**：
   - **三段式终极音效**：`130Hz -> 25Hz` 震颤全屏的超重低频爆鸣下潜 + 3 段锯齿波连续连锁爆炸 + 6 音大和弦凯旋交响号角 Fanfare！
   - **史诗 14 帧长定格（Hitstop）** + **镜头剧烈震颤（Shake 20px）** + **全屏耀眼金光闪烁**；
   - **3 重全屏震波**（`BURST_RAYS` 射线 + `RING` 金环 + `STAR_CROSS` 星芒）与 30+ 簇全彩爆炸火花；
   - **24 连发黄金火山大金币雨** 弧形抛物线磁吸飞入右上角 HUD，狂揽 **¥60,000 ~ ¥100,000 终极分红**！
4. 🐊 **熊市三大独立 Boss 左右突进攻击 AI (Bear Boss Intelligent AI)**：
   - 包含 **🐊 鳄鱼庄家**、**🐻 空头巨熊**、**🐋 控盘巨鲸**，具备 **悬停巡逻（HOVER）**、**狂暴突进（LUNGE）** 与 **后撤重整（RETREAT）**，顶部实时专属动态血条！
5. 🕹️ **主角前进与后退自由走位 (Forward / Backward Navigation)**：
   - 触控与键盘（`A`/`D`/`←`/`→`）全支持，在 35px ~ 650px 宽广空间内自由微操拉扯！
6. 🪙 **金币弹幕射击与量化金币炮道具 (Coin Bullet Attack & Ammo Cannon)**：
   - 按下 `J`/`X` 或屏幕金色按钮快速射出高能旋转金币子弹，拾取量化金币炮直接补充 +30 发弹药！
7. 🔒 **单熊市严格单 Boss 锁定防重机制**：离开熊市 Boss 自动撤退逃窜，彻底杜绝重复刷怪与同屏冲突 BUG！

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
