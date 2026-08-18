# 🐂 《牛牛勇敢向前冲 4.5 · 马里奥大金币与多血条抛物线弹道版》 (Bull Run 4.5: Mario Big Coins, Monster HP & Parabolic Homing Trajectory)

> **华尔街金融大逃杀 · 掌机级横屏跑酷 · 原生 HTML5 Canvas + Web Audio API 工业级独立单文件神作**  
> 制作人：**蒋尊森** | 核心架构：**独立小游戏工坊 & 全栈架构专家团**

[![Game Version](https://img.shields.io/badge/version-4.5.0--MarioCoin-gold.svg)](https://github.com/MUMUMU23333/game)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-brightgreen.svg)](https://mumumu23333.github.io/game/)
[![FPS](https://img.shields.io/badge/Target%20FPS-60%20Lock-blue.svg)](https://github.com/MUMUMU23333/game)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎮 全球在线试玩直达链接 (Instant Play)

* 📱 **手机 / 电脑浏览器直接打开**：  
  👉 **[https://mumumu23333.github.io/game/](https://mumumu23333.github.io/game/)**  
  *(手机竖屏点开自动旋转为大视野全屏横屏，左右大拇指触控即玩！)*

---

## ✨ 4.5 马里奥大金币与多血条抛物线弹道版重磅升级

1. 🪙 **马里奥风格立体大金币与冷银灰币 (Mario-style Eye-catching 3D Coins)**：
   - 金币尺寸由 16px 放大至 **`22px`**（醒目度大幅跃升），宝箱由 26px 放大至 **`28px`**，判定磁吸距离扩大至 38px，拾取更过瘾；
   - **3D 动态旋转透视**：采用余弦周期动态透视（`0.32 ~ 1.0` 自旋），模拟经典街机金币翻转；
   - **亮金渐变与经典马里奥竖条暗槽**：亮金多层渐变（`#fff9c4 -> #ffd700 -> #f59e0b`）+ 纯白斜切高光 + 凹槽竖纹；
   - **冷银灰暗做空币**：冷铁深灰银质感 + 猩红警示芯 + 鲜明金属白描边，牛熊金币状态一目了然！
2. 🦏 **不同障碍物/动物差异化生命值与受击反馈 (Differentiated Monster HP & Hits)**：
   - **绿K线柱 (PIPE)**：生命值 20 HP（普通金币 1 击即碎，奖励 ¥350）；
   - **暴跌黑天鹅 (SWAN)**：生命值 40 HP（普通金币需 2 击，狂暴强化金币 1 击，奖励 ¥800）；
   - **做空巨熊 (BEAR)**：生命值 60 HP（普通金币需 3 击，狂暴强化金币 2 击，奖励 ¥1,200）；
   - **重型灰犀牛 (RHINO)**：生命值 90 HP（普通金币需 4~5 击，狂暴强化金币 2~3 击，奖励 ¥1,800）；
   - **受击后退与动态 Mini 血条**：怪物受击产生 **`10px` 物理后挫（Hit Recoil）**、4 帧受击白闪、实时跳出 `💥 -XX` 扣血跳字（暴击 `🔥 暴击 -XX`），受伤后头顶呈现迷你动态三色血条。
3. 🏹 **金币攻击抛物线弹道与微导引吸附 (Parabolic Arc & Homing Coin Trajectory)**：
   - 金币射击带有向上起跳初速（`vy = -1.8`）与真实微重力抛物线（`vy += 0.045`）；
   - **扇区微导引**：金币对前方 280px 范围内的怪物或 Boss 进行柔和平滑追踪微调，弹道打击感爆棚；
   - 伴随金色火花光尾（Spark Trail）与高速旋转。

1. 🦢 **全新黑炭灰高辨识度黑天鹅与高光描边 (Crisp Outline Black Swan)**：
   - 保留冷峻优雅的黑炭与黑曜石羽翼基底（`#18181b` / `#27272a` / `#3f3f46`）；
   - **高反差纯白亮线双重描边（Crisp White Highlight Outline + Neon Glow）**：全身羽翼、S型颈项与头部均勾勒出锐利的高反差亮白轮廓与赛博冰蓝微光光晕，**在任何黑夜、阴雨或烈日背景下均 100% 鲜明刺目，绝对不与背景融为一体**！
   - 搭配鲜亮金琥珀喙嘴（`#f59e0b`）、黑色鼻瘤、猩红发光眼（`#ff1744`）与高亮警示横幅。
2. 🌧️ **熊市灰暗压抑沮丧氛围重构 (Gloomy & Depressed Bear Market)**：
   - 遭遇暴跌、阴跌或熊市 Boss 现身时，天空平滑渐变为压抑深沉的暗夜暴雨穹顶（`#06070d` -> `#140f1a` -> `#1a1120`）；
   - 伴随 **低垂沉重的雷暴乌云**、**冷冽倾斜的阴跌雨丝（Rain Streaks）**、**漫天飘落的割肉爆仓灰烬** 与 **远方偶发的暗红低频电闪**；
   - 跑道地面平滑渐变为冰冷破裂的灰黑冷石与暗红警戒线，将熊市寒冬的萧瑟绝望感拉满！
3. ☀️ **牛市欢快明朗与鸟语花香氛围 (Joyful & Sunny Bull Market)**：
   - 进入牛市多头主升浪与狂欢时，背景平滑绽放为蔚蓝晴空与金色阳光（`#1976d2` -> `#64b5f6` -> `#fff9c4`）；
   - 伴随暖阳日晕、悠然白云、远空飞鸟、随风翻滚的粉樱与金叶，以及地面盛开的五彩小野花！
4. 🎵 **五声音阶拾取音效与连击泛音 (Dynamic Pentatonic Coin SFX)**：
   - 连续拾取金币音调沿五声音阶动态爬升（`C5 -> D5 -> E5 -> G5 -> A5 -> C6 -> D6`）；5 连板触发璀璨高八度泛音与彩虹星芒！
5. 💥 **拳拳到肉击中反馈与破甲打击感**：
   - 超低频肉体重音（`130Hz -> 38Hz`）+ 金属破甲声 + 3~5 帧受击白闪 + 8~14px 物理受击后挫！
6. 👑 **击败 Boss 史诗级三段式爆鸣与 24 连发火山金币雨**：
   - 14 帧定格慢放 + 20px 镜头震颤 + 全屏金闪 + 3 重震波 + ¥60,000~¥100,000 终极分红！
7. 🐊 **熊市三大 Boss 独立 AI 与主角前后走位微操**：
   - 鳄鱼庄家、空头巨熊、控盘巨鲸左右突进撕咬；支持 A/D/←/→ 自由拉扯走位与 J/X 金币弹幕反击！

---

## 🚀 目录结构与历史版本归档 (Project Structure & Archive)

```
bull_run_game/
├── index.html                  # 默认入口（100% 独立单文件，最新发布版）
├── bull_run_standalone.html    # 独立单文件分发版
├── game.html                   # 镜像单文件
├── README.md                   # 项目说明与快速开始
├── CHANGELOG.md                # 📜 全版本迭代更新日志与修改记录
├── 旧版本/                     # 📁 历史版本归档文件夹 (单文件即开即玩)
│   ├── bull_run_v4.0.0_黄金觉醒版.html
│   ├── bull_run_v4.1.0_牛市渐变大屏版.html
│   ├── bull_run_v4.2.0_熊市Boss与金币走位版.html
│   └── bull_run_v4.3.0_爽快音效与史诗打击特效版.html
└── assets/
    ├── poster.jpg              # 制作人-蒋尊森 开场海报原图
    └── skins_data.js           # 5款战牛像素立绘 base64 数据
```

---

## 📜 详细更新日志 (Changelog)

每次版本迭代的详细修改内容、设计考量与功能特性，请查阅 👉 **[CHANGELOG.md](CHANGELOG.md)**。

---

## 🛠️ 本地运行

无需安装任何繁琐依赖，直接双击 `index.html` 或 `旧版本/` 下的任意历史版本，即可在 Chrome / Edge / Safari / 手机微信 中直接运行！
