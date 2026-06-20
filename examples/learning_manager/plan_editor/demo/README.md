# 造核 · OS 课程 Demo

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
