# OS 课程 Demo

「从零做一个操作系统」交互课的原型集合。互动 slide + 真沙箱形态。
由 plan_editor 的 vite dev server 一起服务。

## 入口

```bash
cd examples/learning_manager/plan_editor
npm run dev
```

- 完整页(路线图 + 内嵌章节播放器):
  http://127.0.0.1:5173/demo/plan_roadmap_preview.html
- 把整张 OS 路线图灌进 Plan Studio 编辑器:
  http://127.0.0.1:5173/demo/seed-plan.html

## 目录

```text
demo/
  plan_roadmap_preview.html   完整页:8 阶段路线图,点章节在同页展开学习区(iframe 嵌 ch1)
  seed-plan.html              把 seed-plan-data.json 写入 localStorage 后跳转编辑器
  seed-plan-data.json         整张课程数据(goal/stage/learn/project 共 40 节点)
  chapters/                   各章节学习页
    ch1.html                  第一章「内核引导」标杆课(互动 slide + 沙箱动手),已成形
    ch1_*_preview.html        第一章的其它形态原型(slide/chat/doc/build/workspace),选型用
  figures/                    单独的动图/插图原型(fig_*)
  sandbox/                    真沙箱
    sandbox.html              前端:目录树 / 编辑 / 运行
    sandbox-server.mjs        后端(:5175),连本地 xv6 实验项目,真编译真跑 run.sh
```

## 沙箱后端(动手环节需要)

```bash
node demo/sandbox/sandbox-server.mjs [xv6项目目录]
# 默认目录 = ~/Desktop/openkeri-xv6/myos-ch1(需自备该实验仓库)
```

## 章节路线

内核引导 → 内存分配与 printf → 陷阱与异常 → 进程与上下文切换
→ 虚拟内存与页表 → 用户态与系统调用 → 文件系统 → 命令行 Shell

目前只有第一章接入学习区,其余章节为「制作中」。
