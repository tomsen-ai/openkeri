(function () {
  const PLAN_TEMPLATES = {
    algorithm: {
      title: "算法学习计划",
      colors: ["#58cc02", "#14c9a2", "#ff9f1c"],
      stages: [
        {
          title: "基础热身",
          description: "先建立常见数据结构和基本题感。",
          nodes: [
            ["数组", "learn", "理解数组、索引、边界和遍历。"],
            ["哈希", "practice", "用映射关系解决查找和计数问题。"],
            ["双指针", "practice", "练习左右指针和快慢指针。"],
            ["阶段复盘", "review", "整理基础题型的共同模式。"],
          ],
        },
        {
          title: "核心套路",
          description: "把高频解题模式串成稳定路线。",
          nodes: [
            ["滑动窗口", "learn", "识别窗口扩张、收缩和答案更新。"],
            ["栈与队列", "practice", "处理单调性、括号和顺序结构。"],
            ["二分", "practice", "练习边界判断和搜索答案。"],
            ["阶段复盘", "review", "比较不同套路适合的题目形态。"],
          ],
        },
        {
          title: "综合训练",
          description: "把路线变成可迁移的面试准备。",
          nodes: [
            ["树", "learn", "掌握递归、层序和路径问题。"],
            ["图", "practice", "练习 BFS、DFS 和连通性。"],
            ["综合复盘", "review", "回看错题和卡住的模式。"],
            ["模拟面试", "checkpoint", "完成一次限时综合练习。"],
          ],
        },
      ],
    },
    reading: {
      title: "英文阅读计划",
      colors: ["#1cb0f6", "#ce82ff", "#ffb020"],
      stages: [
        {
          title: "建立节奏",
          description: "先把阅读变成每天可以开始的小动作。",
          nodes: [
            ["短文速读", "learn", "读一篇短文，只抓主旨和结构。"],
            ["关键词", "practice", "圈出影响理解的关键词。"],
            ["一句复述", "reflection", "用一句中文或英文复述内容。"],
          ],
        },
        {
          title: "理解细节",
          description: "开始处理句子、段落和术语。",
          nodes: [
            ["长句拆解", "learn", "拆主干、修饰语和逻辑连接。"],
            ["术语卡片", "practice", "把高频术语整理成小卡片。"],
            ["段落总结", "reflection", "为每段写一个短标题。"],
          ],
        },
        {
          title: "输出复盘",
          description: "把读过的内容转化成自己的材料。",
          nodes: [
            ["文章复盘", "review", "回顾一篇文章的结构和观点。"],
            ["主题阅读", "practice", "围绕一个主题连续读两篇。"],
            ["阅读小结", "checkpoint", "输出一段自己的理解。"],
          ],
        },
      ],
    },
    custom: {
      title: "学习计划",
      colors: ["#58cc02", "#1cb0f6", "#ff9f1c"],
      stages: [
        {
          title: "入门",
          description: "建立基础概念和学习节奏。",
          nodes: [
            ["目标拆解", "plan", "把目标拆成几个可执行的小方向。"],
            ["基础概念", "learn", "先理解最基础的词和关系。"],
            ["小练习", "practice", "做一个低压力练习。"],
          ],
        },
        {
          title: "推进",
          description: "围绕核心技能持续练习。",
          nodes: [
            ["核心概念", "learn", "理解最常用的核心概念。"],
            ["应用练习", "practice", "完成一个小应用或例子。"],
            ["阶段复盘", "review", "记录哪里顺、哪里卡。"],
          ],
        },
        {
          title: "整合",
          description: "把学习内容变成一个可回看的成果。",
          nodes: [
            ["综合练习", "practice", "把前面的内容组合起来。"],
            ["输出总结", "reflection", "写一段自己的总结。"],
            ["小项目", "project", "做一个能代表学习成果的小项目。"],
          ],
        },
      ],
    },
  };

  window.OpenKeriTemplates = { PLAN_TEMPLATES };
})();
