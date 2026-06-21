# 造核 · 交互学习 Demo

> ⚠️ 下面大段是**旧 OS 方向**的文档,保留作参考。当前主线已转向 **codex demo**,见下面这段交接。

---

## 🔀 当前进展 & 交接(更新于 2026-06-22,分支 `demo/ch1`)

### 一句话定位
openkeri = **学=造**:说想学什么,AI 生成学习路线 + 陪你从零把它**真造出来**(真编译真跑,你写承重墙那几行)。**不是**泛泛的"AI 学习 agent"。

### 战略决策(已定,别再推翻)
1. **demo 主题从「操作系统」换成「做一个你自己的 mini-codex(AI 编程 agent)」** —— codex 流量比 OS 好、更贴 AI 时代。形态(深文 + 承重墙 + 真沙箱 + 看项目 + 路线图)是话题无关的,直接复用。
2. **模式 = B骨架 + A嫁接**:带你从 0→1 造一个自己的 mini-codex(承重墙、ownership),同时对照真 Codex/Claude-Code 怎么做、它们的设计决策。
3. **demo 策略**:把**一章/一个体验**打磨到最好 = demo,开源它(比视频更适合动手型产品)。
4. 真 agent 集成(`kimi -p` 真改文件)已验证可行,但**前端用 mock**(真 agent 太慢、不可控,demo 要顺)。

### 刚做完的(本次会话重点)
**`demo/codex_studio.html`** —— 落地页 + **学习地图**(已成形,提交 `3718036`):
- 输入目标 → mock 生成动画 → 出地图。
- 地图 = **建造顺序(P0→P4 彩色序列)= 学习路线** 叠在 **架构图**上;每个架构框挂 `Pn` 角标(这块归哪一步造)。
- **点阶段胶囊** → 右侧面板出「目标 / 做到才算过(验收) / 这一步要造哪些块」,图上对应块高亮、其余变暗。
- **点架构节点** → 出组件卡(是什么 / 角色 / 归哪步造),可跳到对应阶段。
- `agent loop` 居中发光(= agent 的本质);底部 `↻ 工具结果回灌 history`。
- 设计:深色玻璃质感、单一 violet 主色 + 阶段配色、入场动画。

学习路线 P0→P4(架构组件映射见 `codex_studio.html` 里的 `STAGES` / `ABOX`):
- **P0 能对话**(立骨架:CLI/REPL · agent loop · model client · history · LLM API)
- **P1 闭环第一个工具(shell)** ★重心(tool dispatcher · shell)—— tool_call 闭环 = agent 本质
- **P2 真能改代码**(apply_patch · read_file)
- **P3 加安全闸**(approval gate · MVP 用确认替代真沙箱)
- **P4 好用起来**(search · 上下文管理)
- P5 长大(可选,MVP 之后:真沙箱 · MCP · 多前端)

### 两图关系(用户原话,务必记住)
**同一批组件的两种投影**:架构图=空间(谁连谁、最终长啥样),路线图=时间(按什么顺序造、每步怎么验)。桥:路线图每一格放大,就是架构图里某几个框的具体实现。**学习跟着 P0→P4 走,架构图是地图。**

### 下一步(未做)
1. 把 **P1 真接进第一章**:深文 + 承重墙 + 真 agent 跑 + 对照真 codex 的设计决策(diff 格式那段讨论:V4A/apply_patch vs search-replace,关键是匹配三级容错 + 错误回灌)。
2. 同法铺其余 P 阶段。
3. 把 P1/loop 这一章打包成可跑的开源 demo。

### ⚠️ 与用户协作的硬约束(踩过雷)
- **借鉴 ≠ 照抄**:给参考图时,学它的"做法/样式",别把内容整个搬过来。
- **一次一个问题**,别甩研究报告/表格。**有参考就别自己编**。
- 文字要**连贯成段**(别碎片跳跃);别堆字、标题尤其要短。
- **别动不动整页推倒重画** —— 用户认可的版本就在它基础上改;要改先指到具体一处。
- 设计交给你自主**做好看**,别老问。
- 用户要**快**,少绕。

### 跑起来
```bash
cd examples/learning_manager/plan_editor && npm run dev
# 落地页 + 学习地图:http://127.0.0.1:5173/demo/codex_studio.html
```
codex demo 的真沙箱/章节当前仍是 OS 版(`chapters/ch1_deep.html` 等 + `sandbox/run-server.mjs`,真 clang+qemu),作为形态参考;codex 版章节尚未做。

---

## (旧)造核 · OS 课程 Demo

「从零做一个操作系统」的交互学习课。形态是**故事性的编程** —— 不是和 chatbot 聊天写代码,而是顺一条故事线、边读边亲手把内核搭出来。由 plan_editor 的 vite dev server 一起服务。

## 入口

```bash
cd examples/learning_manager/plan_editor
npm run dev
```

- 第一章标杆课:http://127.0.0.1:5173/demo/chapters/ch1.html
- 完整页(8 阶段路线图 + 内嵌学习区):http://127.0.0.1:5173/demo/plan_roadmap_preview.html
- 把整张 OS 路线图灌进 Plan Studio 编辑器:http://127.0.0.1:5173/demo/seed-plan.html

## 目录

```text
demo/
  plan_roadmap_preview.html   完整页:8 阶段路线图,点章节在同页展开学习区
  seed-plan.html              把 seed-plan-data.json 写入 localStorage 后跳转编辑器
  seed-plan-data.json         整张课程数据(goal/stage/learn/project 共 40 节点)
  chapters/
    ch1.html                  ★ 第一章「内核引导」标杆课(故事性编程,已成形)
    os-design.css             设计系统 / 词元规范(方向 A · 工程蓝图),各章 <link> 复用
  sandbox/
    sandbox.html              真沙箱前端:目录树 / 编辑 / 运行
    sandbox-server.mjs        真沙箱后端(:5175),连本地 xv6 实验项目,真编译真跑 run.sh
```

## 一章 = 哪些「词元」(规范见 os-design.css 的组件类)

叙述文字 · 讲解图 · 可玩图(拖一个值看效果) · 练(选择题) · **动手**(承重墙就地写 → 暗线项目) · 术语点出 · 旁注(比喻/坑/提示) · 撞墙情境 · 运行成就 · 浮动 Keri 问答。

组织:一章拆模块,**学(文字+图+练)→ 做(承重墙就地写)** 咬着走;项目是暗线(脚手架已给,只填承重墙、写对自动并入),章末一键运行出成果。

## 沙箱后端(动手「运行」需要)

```bash
node demo/sandbox/sandbox-server.mjs [xv6项目目录]
# 默认目录 = ~/Desktop/openkeri-xv6/myos-ch1(需自备该实验仓库)
```

## 章节路线

内核引导 → 内存分配与 printf → 陷阱与异常 → 进程与上下文切换
→ 虚拟内存与页表 → 用户态与系统调用 → 文件系统 → 命令行 Shell

目前只有第一章成形(ch1.html),其余章节套 os-design.css 后续铺。
