import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import MindElixir from "mind-elixir";
import "mind-elixir/style";
import "./styles.css";

const STORAGE_KEY = "openkeri.planEditorDraft.v1";

const STAGE_COLORS = [
  { line: "#3b82f6", soft: "#dbeafe", ink: "#1e40af" },
  { line: "#10b981", soft: "#d1fae5", ink: "#065f46" },
  { line: "#f59e0b", soft: "#fef3c7", ink: "#92400e" },
  { line: "#8b5cf6", soft: "#ede9fe", ink: "#5b21b6" },
  { line: "#ec4899", soft: "#fce7f3", ink: "#9d174d" },
];

const EMPTY_FORM = {
  goal: "",
  durationDays: 30,
  dailyMinutes: 25,
  preference: "",
};

const BRIEF_FIELDS = [
  { key: "objective.one_sentence", label: "本轮目标" },
  { key: "objective.outcome", label: "预期结果" },
  { key: "scope.include", label: "学习重点" },
  { key: "scope.exclude", label: "暂不深入" },
  { key: "strategy.rationale", label: "路线策略" },
];

const CHIP_ICONS = {
  code: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 7 4 12 9 17" />
      <polyline points="15 7 20 12 15 17" />
    </svg>
  ),
  python: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 6h6a3 3 0 0 1 3 3v3H10a3 3 0 0 0-3 3v3a3 3 0 0 0 3 3" />
      <path d="M16 18h-6a3 3 0 0 1-3-3V12h7a3 3 0 0 0 3-3V6a3 3 0 0 0-3-3" />
    </svg>
  ),
  atom: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="1.6" fill="currentColor" />
      <ellipse cx="12" cy="12" rx="10" ry="4" />
      <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(60 12 12)" />
      <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(-60 12 12)" />
    </svg>
  ),
};

const START_EXAMPLES = [
  { label: "30 天算法面试", icon: "code" },
  { label: "两周入门 Python", icon: "python" },
  { label: "系统学习 React 状态管理", icon: "atom" },
];
const START_MAX_CHARS = 300;

const PREVIEW_BRIEF = {
  title: "30天算法面试冲刺计划",
  objective: {
    one_sentence: "在30天内系统复习算法核心知识，提升面试常见题型的解题能力。",
    outcome: "能够独立完成常见数据结构、动态规划、图论与搜索题，并清楚复盘解题思路。",
    success_criteria: [
      "能稳定识别数组、链表、树、图、动态规划等常见题型",
      "能在限时环境下完成中等难度高频题",
      "能复盘复杂题的思路和边界条件",
    ],
  },
  scope: {
    include: [
      "数组与字符串",
      "链表",
      "树",
      "图等基础数据结构",
      "排序与搜索算法",
      "动态规划",
      "贪心等核心算法",
    ],
    exclude: ["竞赛级算法证明", "底层系统设计"],
    light_touch: ["复杂数学证明", "低频冷门算法"],
  },
  constraints: {
    time_window: "30天",
    pace: "每天集中练习并复盘",
    learner_background: "已有基础编程经验",
    use_context: "算法面试准备",
  },
  strategy: {
    route_type: "practice_first",
    rationale: "以高频题型为主线，先建立解题模板，再通过练习和复盘提升速度与稳定性。",
  },
  assumptions: ["用户已经掌握一门编程语言的基础语法。"],
  risks: ["只刷题不复盘会导致模板迁移能力不足。"],
  preview: {
    phases: [
      { phase_name: "题型框架建立", focus: "整理常见数据结构和解题模板", estimated_child_count: 3 },
      { phase_name: "高频题专项练习", focus: "按题型进行限时训练", estimated_child_count: 4 },
      { phase_name: "综合模拟与复盘", focus: "模拟面试节奏并总结薄弱点", estimated_child_count: 3 },
    ],
  },
  sections: [
    {
      id: "practice-plan",
      title: "练习方式",
      kind: "practice",
      summary: "每天用固定题型训练加错题复盘形成稳定节奏。",
      bullets: ["先做模板题", "再做变式题", "最后复盘错题"],
      editable: true,
    },
    {
      id: "risk-control",
      title: "风险控制",
      kind: "warning",
      summary: "避免只追求刷题数量，优先保证复盘质量。",
      bullets: ["记录卡点", "整理边界条件", "复述解法"],
      editable: true,
    },
  ],
  schedule: {
    duration_days: 30,
    daily_minutes: 90,
    total_minutes: 2700,
  },
  slots: {
    learning_subject: "算法面试",
    target_outcome: "30天内提升算法面试解题能力",
    time_window: "30天",
    available_rhythm: "每天练习",
    learner_background: "有基础编程经验",
    preferred_style: "刷题与复盘结合",
    use_context: "技术面试",
  },
  user_choices: [],
};

const PREVIEW_INTAKE = {
  status: "needs_choice",
  state: {
    raw_goal: "两周入门 Python",
    slots: {
      learning_subject: "Python",
      target_outcome: "两周内完成 Python 入门并能做一个小项目",
    },
    constraints: { duration_days: 14, daily_minutes: 30, total_minutes: 420 },
    decisions: [],
    round_index: 0,
  },
  question: {
    id: "preview-route",
    target_slot: "use_context",
    title: "选择一条学习路线",
    description: "根据你的目标，先确定这次学习更偏向哪种产出。",
    choices: [
      {
        id: "foundation",
        label: "掌握基础语法",
        description: "能读懂简单 Python 代码，编写基本脚本。",
        fills: { use_context: "基础语法入门" },
      },
      {
        id: "project",
        label: "完成一个小项目",
        description: "例如数据分析、网页爬虫或自动化脚本。",
        fills: { use_context: "项目驱动学习" },
      },
      {
        id: "interview",
        label: "准备面试",
        description: "重点学习常见面试题和算法基础。",
        fills: { use_context: "技术面试准备" },
      },
      {
        id: "automation",
        label: "工作自动化",
        description: "用于处理 Excel、邮件、文件等办公任务。",
        fills: { use_context: "办公自动化" },
      },
    ],
  },
};

const PREVIEW_LEARNING_POINT_PROJECT = {
  id: "learning-point-preview",
  schemaVersion: 1,
  goal: "30 天准备算法面试，先手工体验数组和链表节点",
  title: "30天算法面试冲刺计划",
  summary: "预览 n6 / Arrays and Linked Lists 的第一个 learning point：Two pointers。",
  nodes: [
    {
      id: "n1",
      type: "goal",
      data: {
        title: "掌握算法面试核心题型",
        kind: "goal",
        description: "在30天内建立常见算法题型的识别、编码和复盘能力。",
        estimated_minutes: 5,
        group: "",
        status: "in_progress",
        learningNotes: "",
      },
      position: { x: 0, y: 0 },
    },
    {
      id: "n2",
      type: "stage",
      data: {
        title: "Foundation",
        kind: "stage",
        description: "先训练线性结构、哈希、栈队列等基础题型。",
        estimated_minutes: 5,
        group: "",
        status: "in_progress",
        learningNotes: "",
      },
      position: { x: 0, y: 0 },
    },
    {
      id: "n6",
      type: "learn",
      data: {
        title: "Arrays and Linked Lists",
        kind: "learn",
        description: "用 learning point 的方式训练数组、字符串和链表题：每个点只包含 lesson、practice、qa。",
        estimated_minutes: 60,
        group: "Foundation",
        status: "in_progress",
        learningNotes: "",
      },
      position: { x: 0, y: 0 },
    },
  ],
  graphEdges: [
    { id: "e1", source: "n1", target: "n2", relation: "next", label: "" },
    { id: "e2", source: "n2", target: "n6", relation: "contains", label: "" },
  ],
  updatedAt: "2026-06-07T00:00:00.000Z",
};

const NODE_LEARNING_PLAN = {
  nodeId: "n6",
  title: "Arrays & Linked Lists",
  subtitle: "Linear Structure Pattern Training",
  stage: "Foundation",
  goal: "30-day algorithm interview prep",
  completionCriteria: [
    "完成 Two Pointers 的 lesson slides",
    "完成 2 道双指针 practice，并写出移动理由",
    "记录至少 2 条 mistake notes 或边界条件",
  ],
  learningPoints: [
    {
      id: "two-pointers",
      title: "Two Pointers",
      subtitle: "左右指针 / 两端收缩",
      status: "current",
      purpose:
        "看到有序数组、回文、两端收缩类题目时，能判断是否适合双指针，并解释一次 left/right 移动为什么能排除候选。",
      lesson: {
        slides: [
          {
            id: "intro",
            title: "Lesson 1 · 认识双指针",
            subtitle: "为什么需要两个指针",
            layout: "concept",
            heading: "核心思想",
            body: "通过两个指针从不同位置出发，根据条件移动指针，逐步缩小搜索空间或完成一次线性扫描。",
            bullets: [
              "left/right 可以从两端出发，也可以从同一端以不同速度前进",
              "每一轮先判断当前状态，再移动一个或两个指针",
              "关键不是记模板，而是说清楚移动后排除了什么候选",
            ],
          },
          {
            id: "when",
            title: "Lesson 2 · 什么时候使用双指针?",
            subtitle: "识别信号 + 核心想法",
            layout: "concept_with_example",
            heading: "识别信号",
            body: "当题目可以通过移动边界来排除一批候选时，双指针通常比枚举所有组合更直接。",
            bullets: [
              "输入有序，题目要找一对数或比较两端",
              "回文、对称检查、两端逐步靠近",
              "每次移动一个边界都能排除一批不可能候选",
            ],
            example: {
              title: "示例：判断回文字符串",
              caption: "从两端向中间移动，比较对应字符，直到相遇。",
              diagram: {
                cells: ["h", "e", "l", "l", "o", "l", "e", "h"],
                arrows: ["up", "right", "", "", "", "", "left", "up"],
                labels: ["left", "", "", "", "", "", "", "right"],
              },
              code: {
                language: "JavaScript",
                body: `function isPalindrome(s) {
  let left = 0, right = s.length - 1;
  while (left < right) {
    if (s[left] !== s[right]) return false;
    left++;
    right--;
  }
  return true;
}`,
              },
            },
          },
          {
            id: "rule",
            title: "Lesson 3 · 移动 left / right 的规则",
            subtitle: "排除候选的判断",
            layout: "rule_summary",
            heading: "移动规则要绑定 invariant",
            body: "不要只说“太小移动 left”。要补上：为什么固定 right 时，left 左边的候选已经不可能成为答案。",
            rules: [
              {
                title: "Two Sum II",
                detail: "sum < target 时移动 left，因为数组有序，left 左边的数只会让 sum 更小。",
              },
              {
                title: "Palindrome",
                detail: "两端相等时同时移动；不相等时可以立刻判 false，因为这对字符必须匹配。",
              },
              {
                title: "Loop condition",
                detail: "需要两个不同元素时通常用 left < right，避免同一个位置被使用两次。",
              },
            ],
          },
          {
            id: "palindrome",
            title: "Lesson 4 · 回文判断",
            subtitle: "对称比较",
            layout: "concept_with_example",
            heading: "先过滤，再比较",
            body: "Valid Palindrome 的难点不在移动本身，而在每次比较前跳过无关字符并保持指针合法。",
            bullets: [
              "先跳过非字母数字字符",
              "比较时统一大小写",
              "每一轮结束后让 left/right 继续向中间靠近",
            ],
            example: {
              title: "示例：跳过符号后比较",
              caption: "只把有效字符纳入比较，标点和空格不改变 invariant。",
              diagram: {
                cells: ["a", ",", " ", "m", "a", "n", "a", "!"],
                arrows: ["up", "right", "right", "", "", "", "left", "up"],
                labels: ["left", "", "", "", "", "", "right", ""],
              },
              code: {
                language: "JavaScript",
                body: `function isAlphaNum(ch) {
  return /[a-z0-9]/i.test(ch);
}`,
              },
            },
          },
          {
            id: "two-sum",
            title: "Lesson 5 · Two Sum II",
            subtitle: "利用有序性",
            layout: "rule_summary",
            heading: "用有序性解释每次移动",
            body: "Two Sum II 的核心是把 O(n²) 的 pair search 压成一次两端收缩。",
            rules: [
              {
                title: "sum === target",
                detail: "当前 pair 命中，按题目要求返回 1-based index。",
              },
              {
                title: "sum < target",
                detail: "固定 right 时，left 左边的数更小，所以移动 left。",
              },
              {
                title: "sum > target",
                detail: "固定 left 时，right 右边的数更大，所以移动 right。",
              },
            ],
          },
          {
            id: "review",
            title: "Lesson 6 · 复盘 invariant",
            subtitle: "归纳判断模板",
            layout: "checkpoint",
            heading: "检查你是否真的掌握",
            body: "做题前先口头回答三个问题，再开始写代码。",
            checklist: [
              "题目里的序列、有序性或对称性是什么？",
              "当前 left/right 代表的搜索范围是什么？",
              "移动一个指针后，哪些候选被排除，为什么？",
            ],
            takeaway: "如果说不出排除理由，先不要急着套双指针模板。",
          },
        ],
      },
      practice: {
        problems: [
          {
            id: "valid-palindrome",
            title: "Valid Palindrome",
            difficulty: "easy",
            focus: "跳过无关字符后做两端比较",
            statement:
              "给定一个字符串，忽略大小写和非字母数字字符后，判断它是否是回文。",
            examples: [
              {
                input: '"A man, a plan, a canal: Panama"',
                output: "true",
                explanation: '过滤后为 "amanaplanacanalpanama"。',
              },
              {
                input: '"race a car"',
                output: "false",
                explanation: "过滤后两端比较会出现不匹配。",
              },
            ],
            thinkingFields: [
              {
                id: "patternChoice",
                label: "pattern choice",
                placeholder: "例如：双指针，因为要从两端比较有效字符",
              },
              {
                id: "movementReason",
                label: "pointer movement reason",
                multiline: true,
                placeholder: "说明跳过字符、比较字符后 left/right 为什么这样移动",
              },
              {
                id: "boundaryCase",
                label: "boundary cases",
                placeholder: "例如：空字符串、只有标点、大小写混合",
              },
            ],
            starterCode: `function isPalindrome(s) {
  let left = 0;
  let right = s.length - 1;

  // write your solution
}`,
            reviewRubric: [
              {
                id: "pattern",
                pattern: "双指针|two\\s*pointers?|left|right",
                ok: "已经把解法和 left/right 指针联系起来。",
                missing: "先在 pattern choice 写为什么是双指针。",
              },
              {
                id: "movement",
                pattern: "回文|palindrome|跳过|skip|比较|compare",
                ok: "移动理由和回文判断信号有连接。",
                missing: "说明跳过字符和比较后，left/right 为什么继续移动。",
              },
              {
                id: "boundary",
                pattern: "left\\s*<\\s*right|空|empty|single|单|标点|大小写",
                ok: "边界意识有体现。",
                missing: "补一个边界 case：空输入、只有标点或大小写混合。",
              },
            ],
          },
          {
            id: "two-sum-ii",
            title: "Two Sum II - Input Array Is Sorted",
            difficulty: "medium",
            focus: "利用有序性解释 left/right 移动",
            statement:
              "给定升序数组 numbers 和 target，返回两个数的 1-based 下标，使它们的和等于 target。",
            examples: [
              {
                input: "numbers = [2,7,11,15], target = 9",
                output: "[1,2]",
                explanation: "2 + 7 = 9，返回 1-based 下标。",
              },
            ],
            thinkingFields: [
              {
                id: "patternChoice",
                label: "pattern choice",
                placeholder: "例如：双指针，因为数组有序且要找一对数",
              },
              {
                id: "movementReason",
                label: "pointer movement reason",
                multiline: true,
                placeholder: "分别解释 sum < target 和 sum > target 时移动哪边",
              },
              {
                id: "boundaryCase",
                label: "boundary cases",
                placeholder: "例如：left < right、1-based index、一定有答案",
              },
            ],
            starterCode: `function twoSum(numbers, target) {
  let left = 0;
  let right = numbers.length - 1;

  // write your solution
}`,
            reviewRubric: [
              {
                id: "pattern",
                pattern: "双指针|two\\s*pointers?|left|right",
                ok: "已经把解法和 left/right 指针联系起来。",
                missing: "先在 pattern choice 写为什么是双指针。",
              },
              {
                id: "movement",
                pattern: "有序|sorted|sum|太小|太大|target",
                ok: "移动理由和有序数组信号有连接。",
                missing: "说明 sum 太小/太大时移动哪边，以及排除了哪些候选。",
              },
              {
                id: "indexing",
                pattern: "1-based|1\\s*based|下标|index|left\\s*<\\s*right",
                ok: "下标和循环边界有体现。",
                missing: "补上 1-based index 和 left < right 的边界说明。",
              },
            ],
          },
        ],
      },
      qa: {
        suggestedQuestions: [
          "为什么 sum < target 时移动 left？",
          "什么时候用 left < right，什么时候用 left <= right？",
          "这题为什么不用哈希表？",
          "双指针和滑动窗口怎么区分？",
        ],
      },
    },
    {
      id: "sliding-window",
      title: "Sliding Window",
      subtitle: "连续区间 / 状态维护",
      status: "not_started",
      lesson: { slides: [] },
      practice: { problems: [] },
      qa: { suggestedQuestions: [] },
    },
    {
      id: "slow-write",
      title: "Slow Write Pointer",
      subtitle: "原地写入 / 去重压缩",
      status: "not_started",
      lesson: { slides: [] },
      practice: { problems: [] },
      qa: { suggestedQuestions: [] },
    },
    {
      id: "dummy-head",
      title: "Dummy Head and Merge Tail",
      subtitle: "链表合并 / 哨兵节点",
      status: "not_started",
      lesson: { slides: [] },
      practice: { problems: [] },
      qa: { suggestedQuestions: [] },
    },
    {
      id: "fast-slow",
      title: "Fast / Slow Pointer",
      subtitle: "快慢指针 / 环与中点",
      status: "not_started",
      lesson: { slides: [] },
      practice: { problems: [] },
      qa: { suggestedQuestions: [] },
    },
    {
      id: "pointer-reversal",
      title: "Pointer Reversal",
      subtitle: "链表反转 / 局部重连",
      status: "not_started",
      lesson: { slides: [] },
      practice: { problems: [] },
      qa: { suggestedQuestions: [] },
    },
  ],
};

function SparkleIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M12 3l1.6 4.6L18 9.2l-4.4 1.6L12 15.4l-1.6-4.6L6 9.2l4.4-1.6L12 3z"
        fill="currentColor"
      />
      <path d="M18.5 14l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7.7-2z" fill="currentColor" opacity="0.6" />
    </svg>
  );
}

function installMindElixirTopicDragForwarding(host, me) {
  let forwarding = false;
  const interactiveSelector = [
    "#input-box",
    "a",
    "button",
    "input",
    "select",
    "textarea",
    "[contenteditable='true']",
    "[contenteditable='plaintext-only']",
    "me-epd",
    ".hyper-link",
  ].join(",");

  const handlePointerDown = (event) => {
    if (
      forwarding ||
      event.pointerType !== "mouse" ||
      event.button !== 0 ||
      me.spacePressed
    ) {
      return;
    }
    const target = event.target;
    if (!(target instanceof HTMLElement) || target.closest(interactiveSelector)) return;

    const topic = target.closest("me-tpc");
    if (!topic || target === topic) return;

    forwarding = true;
    try {
      topic.dispatchEvent(
        new PointerEvent("pointerdown", {
          bubbles: true,
          cancelable: true,
          composed: true,
          button: event.button,
          buttons: event.buttons,
          clientX: event.clientX,
          clientY: event.clientY,
          ctrlKey: event.ctrlKey,
          metaKey: event.metaKey,
          shiftKey: event.shiftKey,
          altKey: event.altKey,
          pointerId: event.pointerId,
          pointerType: event.pointerType,
        }),
      );
    } finally {
      forwarding = false;
    }

    event.preventDefault();
    event.stopPropagation();
  };

  host.addEventListener("pointerdown", handlePointerDown, true);
  return () => host.removeEventListener("pointerdown", handlePointerDown, true);
}

function installMindElixirSelectionSync(host, me, onSelectNode) {
  const interactiveSelector = [
    "#input-box",
    "a",
    "button",
    "input",
    "select",
    "textarea",
    "[contenteditable='true']",
    "[contenteditable='plaintext-only']",
    "me-epd",
    ".hyper-link",
  ].join(",");

  const syncSelection = (event) => {
    if (event.pointerType !== "mouse" || event.button !== 0 || me.spacePressed) return;
    const target = event.target;
    if (!(target instanceof HTMLElement) || target.closest(interactiveSelector)) return;

    const topic = target.closest("me-tpc");
    if (!topic?.nodeObj?.id) return;

    me.selectNode(topic, true);
    onSelectNode?.(topic.nodeObj.id);
  };

  host.addEventListener("pointerdown", syncSelection, true);
  return () => host.removeEventListener("pointerdown", syncSelection, true);
}

function MindMapCanvas({
  nodes,
  graphEdges,
  title,
  selectedNodeId,
  onSelectNode,
  onZoomChange,
  onTreeChange,
  instanceRef: externalInstanceRef,
}) {
  const containerRef = useRef(null);
  const instanceRef = useRef(null);
  const lastSerializedRef = useRef("");

  // Initialize once
  useEffect(() => {
    if (!containerRef.current) return;
    const data = buildMindElixirData(nodes, graphEdges, title);
    const me = new MindElixir({
      el: containerRef.current,
      direction: MindElixir.RIGHT,
      editable: true,
      contextMenu: false,
      toolBar: false,
      keypress: true,
      allowUndo: false,
      scaleSensitivity: 0.18,
      scaleMin: 0.2,
      scaleMax: 3,
      theme: {
        name: "openkeri-light",
        type: "light",
        palette: STAGE_COLORS.map((c) => c.line),
        cssVar: {
          "--main-color": "#0f172a",
          "--main-bgcolor": "#ffffff",
          "--color": "#0f172a",
          "--bgcolor": "#ffffff",
          "--root-color": "#f8fafc",
          "--root-bgcolor": "#0f172a",
          "--root-border-color": "#0f172a",
          "--selected": "#0f172a",
          "--panel-color": "#0f172a",
          "--panel-bgcolor": "#ffffff",
          "--panel-border-color": "rgba(15, 23, 42, 0.08)",
        },
      },
    });
    me.init(data);
    instanceRef.current = me;
    if (externalInstanceRef) externalInstanceRef.current = me;
    lastSerializedRef.current = JSON.stringify(data);
    const cleanupTopicDragForwarding = installMindElixirTopicDragForwarding(containerRef.current, me);
    const cleanupSelectionSync = installMindElixirSelectionSync(
      containerRef.current,
      me,
      onSelectNode,
    );

    const handleOperation = () => {
      const tree = me.getData();
      const serialized = JSON.stringify(tree);
      if (serialized === lastSerializedRef.current) return;
      lastSerializedRef.current = serialized;
      onTreeChange?.(tree);
    };
    const handleSelect = (node) => onSelectNode?.(node?.id || "");
    const handleScale = (scale) => onZoomChange?.(scale);

    me.bus.addListener("operation", handleOperation);
    me.bus.addListener("selectNewNode", handleSelect);
    me.bus.addListener("scale", handleScale);

    return () => {
      me.bus.removeListener("operation", handleOperation);
      me.bus.removeListener("selectNewNode", handleSelect);
      me.bus.removeListener("scale", handleScale);
      cleanupTopicDragForwarding();
      cleanupSelectionSync();
      me.destroy?.();
      instanceRef.current = null;
      if (externalInstanceRef) externalInstanceRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Push external data changes (generate / import / undo / inspector edit) in
  useEffect(() => {
    const me = instanceRef.current;
    if (!me) return;
    const data = buildMindElixirData(nodes, graphEdges, title);
    const serialized = JSON.stringify(data);
    if (serialized === lastSerializedRef.current) return;
    lastSerializedRef.current = serialized;
    me.refresh(data);
    me.clearHistory?.();
  }, [nodes, graphEdges, title]);

  // Reflect external selection
  useEffect(() => {
    const me = instanceRef.current;
    if (!me || !selectedNodeId) return;
    try {
      const el = me.findEle(selectedNodeId);
      if (el) me.selectNode(el);
    } catch {
      /* selection target may not exist yet */
    }
  }, [selectedNodeId]);

  return <div ref={containerRef} className="mm-canvas-host" />;
}

function buildMindElixirData(nodes, graphEdges, title) {
  const goal = nodes.find((n) => n.data?.kind === "goal");
  if (!goal) {
    return { nodeData: { id: "empty", topic: title || "新计划", children: [] } };
  }

  const nodeById = new Map(nodes.map((n) => [n.id, n]));
  const childrenBySource = new Map();
  for (const edge of graphEdges) {
    if (!childrenBySource.has(edge.source)) childrenBySource.set(edge.source, []);
    childrenBySource.get(edge.source).push(edge.target);
  }

  const stageIds = orderedStageIds(goal.id, nodes, graphEdges);

  function buildChildNode(nodeId, stageIndex = 0) {
    const node = nodeById.get(nodeId);
    const kind = node?.data?.kind;
    const isProject = kind === "project";
    const childIds = (childrenBySource.get(nodeId) || []).filter((id) => {
      const childKind = nodeById.get(id)?.data?.kind;
      return childKind === "learn" || childKind === "project";
    });

    return {
      id: nodeId,
      topic: node?.data?.title || (isProject ? "未命名项目" : "未命名学习单元"),
      style: isProject
        ? { background: "#fff8ec", color: "#92400e", border: "1px solid rgba(241, 193, 121, 0.6)" }
        : { background: "#ffffff", color: "#0f172a", border: "1px solid rgba(15, 23, 42, 0.08)" },
      children: childIds.map((childId) => buildChildNode(childId, stageIndex)),
    };
  }

  const stageChildren = stageIds.map((stageId, index) => {
    const stage = nodeById.get(stageId);
    const color = STAGE_COLORS[index % STAGE_COLORS.length];
    const childIds = (childrenBySource.get(stageId) || []).filter((id) => {
      const k = nodeById.get(id)?.data?.kind;
      return k === "learn" || k === "project";
    });
    return {
      id: stageId,
      topic: stage?.data?.title || "未命名阶段",
      branchColor: color.line,
      style: { background: color.soft, color: color.ink, border: `1px solid ${color.line}` },
      expanded: false,
      children: childIds.map((childId) => buildChildNode(childId, index)),
    };
  });

  return {
    nodeData: {
      id: goal.id,
      topic: goal.data?.title || title || "目标",
      root: true,
      children: stageChildren,
    },
    direction: MindElixir.RIGHT,
  };
}

function orderedStageIds(goalId, nodes, edges) {
  const directGoalChildIds = new Set(
    edges.filter((edge) => edge.source === goalId).map((edge) => edge.target),
  );
  const stages = nodes.filter(
    (n) => n.data?.kind === "stage" || directGoalChildIds.has(n.id),
  );
  if (!stages.length) return [];
  const stageIds = new Set(stages.map((s) => s.id));
  const nextBySource = new Map();
  for (const edge of edges) {
    if (edge.relation !== "next") continue;
    if (!nextBySource.has(edge.source)) nextBySource.set(edge.source, []);
    nextBySource.get(edge.source).push(edge.target);
  }
  const ordered = [];
  const visited = new Set();
  function walk(fromId) {
    for (const tid of nextBySource.get(fromId) || []) {
      if (stageIds.has(tid) && !visited.has(tid)) {
        visited.add(tid);
        ordered.push(tid);
        walk(tid);
      }
    }
  }
  walk(goalId);
  for (const sid of [...ordered]) walk(sid);
  for (const s of stages) {
    if (!visited.has(s.id)) {
      visited.add(s.id);
      ordered.push(s.id);
    }
  }
  return ordered;
}

function OpenKeriLogo({ size = 22 }) {
  return (
    <svg
      className="ok-logo"
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M50.7 18.5A23.8 23.8 0 1 0 51 45.8"
        stroke="currentColor"
        strokeWidth="4.4"
        strokeLinecap="round"
      />
      <path
        d="M23 44V24M23 32.5l17.5-13M23 32.5l17.5 13"
        stroke="currentColor"
        strokeWidth="4.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="23" cy="24" r="5.2" fill="currentColor" />
      <circle cx="23" cy="44" r="5.2" fill="currentColor" />
      <circle cx="42.5" cy="18.5" r="5.2" fill="currentColor" />
      <circle cx="42.5" cy="45.5" r="5.2" fill="currentColor" />
    </svg>
  );
}

function OpenKeriBrand({ className = "", compact = false, onClick }) {
  const Component = onClick ? "button" : "div";
  return (
    <Component
      className={`ok-brand ${compact ? "compact" : ""} ${onClick ? "clickable" : ""} ${className}`}
      type={onClick ? "button" : undefined}
      onClick={onClick}
    >
      <OpenKeriLogo size={compact ? 20 : 24} />
      <strong>OpenKeri</strong>
      <span>Plan Studio</span>
    </Component>
  );
}

function LoadingLine({ active, label, elapsedSeconds }) {
  if (!active) return null;
  return (
    <div className="loading-line">
      <i />
      <span>{label || "处理中"} · {elapsedSeconds}s</span>
    </div>
  );
}

function App() {
  const previewMode = new URLSearchParams(window.location.search).get("preview");
  const shouldPreviewBrief = previewMode === "brief";
  const shouldPreviewIntake = previewMode === "intake";
  const shouldPreviewLearningPoint = previewMode === "learning-point";
  const savedDraft = loadDraft();
  const restoredDraft = shouldPreviewLearningPoint
    ? restoreFlowDraftFromStorage(PREVIEW_LEARNING_POINT_PROJECT)
    : savedDraft
      ? restoreFlowDraftFromStorage(savedDraft)
      : null;
  const hasRestoredDraft = Boolean(restoredDraft?.nodes?.length);
  const importInputRef = useRef(null);
  const [screen, setScreen] = useState(
    shouldPreviewBrief
      ? "brief"
      : shouldPreviewIntake || shouldPreviewLearningPoint
        ? shouldPreviewIntake
          ? "intake"
          : "editor"
        : hasRestoredDraft
          ? "editor"
          : "start",
  );
  const [prompt, setPrompt] = useState(
    shouldPreviewBrief
      ? "30天算法面试冲刺"
      : shouldPreviewIntake
        ? "两周入门 Python"
        : shouldPreviewLearningPoint
          ? PREVIEW_LEARNING_POINT_PROJECT.goal
          : savedDraft?.goal || EMPTY_FORM.goal,
  );
  const [title, setTitle] = useState(
    shouldPreviewLearningPoint
      ? PREVIEW_LEARNING_POINT_PROJECT.title
      : savedDraft?.title || "计划草稿",
  );
  const [summary, setSummary] = useState(
    shouldPreviewLearningPoint
      ? PREVIEW_LEARNING_POINT_PROJECT.summary
      : savedDraft?.summary || "输入目标后生成一个可编辑的计划图。",
  );
  const [nodes, setNodes] = useState(restoredDraft?.nodes || []);
  const [graphEdges, setGraphEdges] = useState(restoredDraft?.graphEdges || []);
  const [isGenerating, setIsGenerating] = useState(false);
  const [message, setMessage] = useState("");
  const [intakeResult, setIntakeResult] = useState(shouldPreviewIntake ? PREVIEW_INTAKE : null);
  const [selectedIntakeChoiceId, setSelectedIntakeChoiceId] = useState(
    shouldPreviewIntake ? "project" : "",
  );
  const [intakeNotes, setIntakeNotes] = useState("");
  const [pendingBrief, setPendingBrief] = useState(shouldPreviewBrief ? PREVIEW_BRIEF : null);
  const [activeBriefField, setActiveBriefField] = useState("");
  const [loadingLabel, setLoadingLabel] = useState("");
  const [loadingStartedAt, setLoadingStartedAt] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [selectedNodeId, setSelectedNodeId] = useState(
    shouldPreviewLearningPoint ? "n6" : "",
  );
  const [studyNodeId, setStudyNodeId] = useState(
    shouldPreviewLearningPoint ? "n6" : "",
  );
  const [zoomLevel, setZoomLevel] = useState(1);
  const mindElixirRef = useRef(null);
  const promptRef = useRef(null);

  const historyRef = useRef({ past: [], future: [] });
  const skipHistoryRef = useRef(false);
  const [historyTick, setHistoryTick] = useState(0);
  const canUndo = historyRef.current.past.length > 0;
  const canRedo = historyRef.current.future.length > 0;

  const snapshot = useCallback(
    () => ({
      title,
      summary,
      nodes,
      graphEdges,
    }),
    [title, summary, nodes, graphEdges],
  );

  const pushHistory = useCallback(() => {
    if (skipHistoryRef.current) return;
    historyRef.current.past.push(snapshot());
    if (historyRef.current.past.length > 100) {
      historyRef.current.past.shift();
    }
    historyRef.current.future = [];
    setHistoryTick((t) => t + 1);
  }, [snapshot]);

  const applySnapshot = useCallback((snap) => {
    skipHistoryRef.current = true;
    setTitle(snap.title);
    setSummary(snap.summary);
    setNodes(snap.nodes);
    setGraphEdges(snap.graphEdges);
    setSelectedNodeId("");
    persistDraft(snap.title, snap.summary, snap.nodes, snap.graphEdges);
    // Release the guard on next tick so the state writes above don't push history
    queueMicrotask(() => {
      skipHistoryRef.current = false;
    });
  }, []);

  const undo = useCallback(() => {
    const past = historyRef.current.past;
    if (!past.length) return;
    const prev = past.pop();
    historyRef.current.future.push(snapshot());
    applySnapshot(prev);
    setHistoryTick((t) => t + 1);
  }, [snapshot, applySnapshot]);

  const redo = useCallback(() => {
    const future = historyRef.current.future;
    if (!future.length) return;
    const next = future.pop();
    historyRef.current.past.push(snapshot());
    applySnapshot(next);
    setHistoryTick((t) => t + 1);
  }, [snapshot, applySnapshot]);

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId),
    [nodes, selectedNodeId],
  );
  const studyNode = useMemo(
    () => nodes.find((node) => node.id === studyNodeId),
    [nodes, studyNodeId],
  );
  const stats = useMemo(() => getPlanStats(nodes), [nodes]);

  useEffect(() => {
    if (!loadingStartedAt) {
      setElapsedSeconds(0);
      return undefined;
    }
    const intervalId = window.setInterval(() => {
      setElapsedSeconds(Math.max(1, Math.floor((Date.now() - loadingStartedAt) / 1000)));
    }, 300);
    return () => window.clearInterval(intervalId);
  }, [loadingStartedAt]);

  // Auto-expand prompt textarea to fit content
  useEffect(() => {
    const el = promptRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.max(el.scrollHeight, 128)}px`;
  }, [prompt]);

  // Sync edits from the mind-elixir canvas back into our nodes/graphEdges
  const onTreeChange = useCallback(
    (tree) => {
      pushHistory();
      const { nodes: nextNodes, edges: nextEdges } = treeToNodesAndEdges(
        tree,
        nodes,
      );
      setNodes(nextNodes);
      setGraphEdges(nextEdges);
      persistDraft(title, summary, nextNodes, nextEdges);
    },
    [nodes, title, summary, pushHistory],
  );

  async function generateDraft() {
    if (!prompt.trim()) {
      setMessage("先输入一个学习目标。");
      return;
    }
    setIsGenerating(true);
    setLoadingLabel("分析目标");
    setLoadingStartedAt(Date.now());
    setIntakeResult(null);
    setSelectedIntakeChoiceId("");
    setPendingBrief(null);
    setMessage("");
    try {
      const intake = await postJson("/api/intake/start", { goal: prompt, preference: "" });
      if (intake.status === "needs_choice") {
        setIntakeResult(intake);
        setSelectedIntakeChoiceId("");
        setScreen("intake");
        return;
      }
      setPendingBrief(intake.brief);
      setActiveBriefField("");
      setScreen("brief");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setIsGenerating(false);
      setLoadingLabel("");
      setLoadingStartedAt(0);
    }
  }

  function chooseIntakeOption(choiceId) {
    setSelectedIntakeChoiceId(choiceId);
  }

  async function continueIntake() {
    if (!intakeResult?.state || !selectedIntakeChoiceId) return;
    setIsGenerating(true);
    setLoadingLabel("整理方案");
    setLoadingStartedAt(Date.now());
    setMessage("");
    try {
      const nextIntake = await postJson("/api/intake/answer", {
        state: intakeResult.state,
        choiceId: selectedIntakeChoiceId,
        notes: intakeNotes,
      });
      if (nextIntake.status === "needs_choice") {
        setIntakeResult(nextIntake);
        setSelectedIntakeChoiceId("");
        setScreen("intake");
        return;
      }
      setIntakeResult(nextIntake);
      setPendingBrief(nextIntake.brief);
      setActiveBriefField("");
      setScreen("brief");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setIsGenerating(false);
      setLoadingLabel("");
      setLoadingStartedAt(0);
    }
  }

  async function confirmGeneratePlan() {
    if (!pendingBrief) return;
    setIsGenerating(true);
    setLoadingLabel("生成计划图");
    setLoadingStartedAt(Date.now());
    setMessage("");
    try {
      await generatePlanFromBrief(pendingBrief);
    } catch (error) {
      const text = error.message || "生成失败";
      setMessage(text.length > 120 ? `${text.slice(0, 120)}…` : text);
    } finally {
      setIsGenerating(false);
      setLoadingLabel("");
      setLoadingStartedAt(0);
    }
  }

  async function generatePlanFromBrief(brief) {
    const payload = await postJson("/api/generate-plan", {
      goal: brief?.objective?.one_sentence || prompt,
      durationDays: brief?.schedule?.duration_days || EMPTY_FORM.durationDays,
      dailyMinutes: brief?.schedule?.daily_minutes || EMPTY_FORM.dailyMinutes,
      preference: EMPTY_FORM.preference,
      brief,
    });
    const next = toFlowDraft(payload);
    setTitle(payload.title);
    setSummary(payload.summary);
    setNodes(next.nodes);
    setGraphEdges(next.graphEdges);
    setSelectedNodeId("");
    persistDraft(payload.title, payload.summary, next.nodes, next.graphEdges);
    setScreen("editor");
    setIntakeResult(null);
    setSelectedIntakeChoiceId("");
    setPendingBrief(null);
    setMessage("");
  }

  function updatePendingBrief(field, value) {
    setPendingBrief((brief) => (brief ? setBriefFieldValue(brief, field, value) : brief));
  }

  function persistDraft(draftTitle, draftSummary, draftNodes, draftEdges) {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(toProjectDraft(draftTitle, draftSummary, draftNodes, draftEdges, prompt)),
    );
  }

  function exportProject() {
    const project = toProjectDraft(title, summary, nodes, graphEdges, prompt);
    const blob = new Blob([JSON.stringify(project, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${slugify(title || "learning-project")}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function importProject(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const raw = await file.text();
      const project = JSON.parse(raw);
      const restored = restoreFlowDraftFromStorage(project);
      setPrompt(project.goal || EMPTY_FORM.goal);
      setTitle(project.title || "计划草稿");
      setSummary(project.summary || "");
      setNodes(restored.nodes);
      setGraphEdges(restored.graphEdges);
      setSelectedNodeId("");
      setScreen("editor");
      setIntakeResult(null);
      setSelectedIntakeChoiceId("");
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(
          toProjectDraft(
            project.title || "计划草稿",
            project.summary || "",
            restored.nodes,
            restored.graphEdges,
            project.goal || EMPTY_FORM.goal,
          ),
        ),
      );
      setMessage("");
    } catch (error) {
      setMessage(`导入失败：${error.message}`);
    } finally {
      event.target.value = "";
    }
  }

  function updateSelectedNode(field, value) {
    pushHistory();
    const nextNodes = nodes.map((node) =>
      node.id === selectedNodeId
        ? {
            ...node,
            type: field === "kind" ? normalizeNodeKind(value) : node.type,
            data: {
              ...node.data,
              [field]:
                field === "kind"
                  ? normalizeNodeKind(value)
                  : field === "estimated_minutes"
                    ? Number(value) || 0
                    : value,
            },
          }
        : node,
    );
    setNodes(nextNodes);
    persistDraft(title, summary, nextNodes, graphEdges);
  }

  function updateStudyNodeLearningNotes(nodeId, learningNotes) {
    const nextNodes = nodes.map((node) =>
      node.id === nodeId
        ? {
            ...node,
            data: {
              ...node.data,
              learningNotes,
            },
          }
        : node,
    );
    setNodes(nextNodes);
    persistDraft(title, summary, nextNodes, graphEdges);
  }

  function addChildNode() {
    const me = mindElixirRef.current;
    if (!me) return;
    const parentEl = me.currentNode;
    if (!parentEl) {
      setMessage("请先选中一个节点，再添加子节点。");
      return;
    }
    const id = `node-${Date.now()}`;
    const topic = parentEl.nodeObj?.root ? "新阶段" : "新学习节点";
    me.addChild(parentEl, { id, topic });
  }

  function deleteSelectedNode() {
    const me = mindElixirRef.current;
    if (!me) return;
    const currentEl = me.currentNode;
    if (!currentEl) {
      setMessage("请先选中一个节点再删除。");
      return;
    }
    // Don't allow deleting the root (goal) node
    if (currentEl.nodeObj?.root) {
      setMessage("不能删除目标节点。");
      return;
    }
    me.removeNodes([currentEl]);
  }

  if (screen === "start") {
    const trimmedPrompt = prompt.trim();
    const canSubmit = !!trimmedPrompt && !isGenerating;
    const charCount = prompt.length;
    return (
      <main className="start-workspace">
        <div className="start-bg" aria-hidden="true">
          <span className="start-bg-blur start-bg-blur--tl" />
          <span className="start-bg-blur start-bg-blur--br" />
          <span className="start-bg-blur start-bg-blur--bl" />
          <span className="start-bg-dots" />
        </div>
        <div className="app-brand-anchor">
          <OpenKeriBrand onClick={() => setScreen("start")} />
        </div>
        <section className="start-main">
          <div className="start-panel">
            <div className="start-head">
              <div className="start-head-icon" aria-hidden="true">
                <SparkleIcon size={16} />
              </div>
              <div className="start-head-text">
                <h1>创建学习计划</h1>
                <p>输入目标，生成可编辑的学习导图</p>
              </div>
            </div>
            <div className="start-form">
              <div className="start-textarea-wrap">
                <textarea
                  ref={promptRef}
                  className="start-textarea"
                  value={prompt}
                  rows={1}
                  maxLength={START_MAX_CHARS}
                  disabled={isGenerating}
                  placeholder="例如：30 天准备算法面试，重点补动态规划和图论，每天晚上 1 小时"
                  onChange={(event) => {
                    setPrompt(event.target.value);
                    setMessage("");
                    const el = event.target;
                    el.style.height = "auto";
                    el.style.height = `${Math.max(el.scrollHeight, 128)}px`;
                  }}
                  onKeyDown={(event) => {
                    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                      if (canSubmit) generateDraft();
                    }
                  }}
                />
                <span className="start-counter">{charCount} / {START_MAX_CHARS}</span>
              </div>
              <div className="start-examples">
                <span className="start-examples-label">试试这些：</span>
                <div className="start-chip-row">
                  {START_EXAMPLES.map((example) => (
                    <button
                      type="button"
                      key={example.label}
                      className="start-chip"
                      disabled={isGenerating}
                      onClick={() => {
                        setPrompt(example.label);
                        setMessage("");
                        queueMicrotask(() => {
                          const el = promptRef.current;
                          if (el) {
                            el.style.height = "auto";
                            el.style.height = `${Math.max(el.scrollHeight, 128)}px`;
                          }
                        });
                      }}
                    >
                      <span className="start-chip-icon">{CHIP_ICONS[example.icon]}</span>
                      <span>{example.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="start-divider" />
            <div className="start-footer">
              <div className="start-footer-left">
                <button
                  type="button"
                  className="start-import"
                  onClick={() => importInputRef.current?.click()}
                  disabled={isGenerating}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 7h5l2-2h11v12a2 2 0 0 1-2 2H3z" />
                  </svg>
                  <span>导入已有计划</span>
                </button>
                {hasRestoredDraft ? (
                  <button
                    type="button"
                    className="start-import"
                    onClick={() => setScreen("editor")}
                  >
                    返回编辑器
                  </button>
                ) : null}
              </div>
              <div className="start-footer-right">
                {!isGenerating ? <span className="start-hint">Cmd / Ctrl + Enter</span> : null}
                <button
                  type="button"
                  className={`start-primary ${isGenerating ? "is-loading" : ""}`}
                  onClick={generateDraft}
                  disabled={!canSubmit}
                >
                  {isGenerating ? (
                    <>
                      <span className="start-spinner" />
                      <span>{loadingLabel || "生成中"}</span>
                      <span className="start-primary-time">{elapsedSeconds}s</span>
                    </>
                  ) : (
                    <>
                      <SparkleIcon size={14} />
                      <span>生成学习导图</span>
                    </>
                  )}
                </button>
              </div>
            </div>
            {message ? <p className="form-message start-message">{message}</p> : null}
          </div>
        </section>
        <input
          ref={importInputRef}
          className="project-import-input"
          type="file"
          accept="application/json,.json"
          onChange={importProject}
        />
      </main>
    );
  }

  if (screen === "intake" && intakeResult?.status === "needs_choice") {
    return (
      <main className="intake-workspace">
        <div className="app-brand-anchor">
          <OpenKeriBrand onClick={() => setScreen("start")} />
        </div>
        <section className="intake-shell">
          <header className="intake-header">
            <span className="intake-step">计划协商</span>
            <h1>选择一条学习路线</h1>
            <p className="intake-prompt">{prompt}</p>
          </header>
          <div className={`route-list route-count-${Math.min(intakeResult.question?.choices.length || 0, 4)}`}>
            {intakeResult.question?.choices.map((choice) => {
              const selected = selectedIntakeChoiceId === choice.id;
              return (
                <button
                  type="button"
                  key={choice.id}
                  className={selected ? "selected" : ""}
                  onClick={() => chooseIntakeOption(choice.id)}
                >
                  <span className="route-radio" />
                  <div className="route-body">
                    <strong>{choice.label}</strong>
                    <span>{choice.description}</span>
                  </div>
                </button>
              );
            })}
          </div>
          <label className="intake-notes">
            <span>补充说明（可选）</span>
            <textarea
              rows={2}
              placeholder="例如：我有编程基础 / 每天只有 30 分钟"
              value={intakeNotes}
              onChange={(event) => setIntakeNotes(event.target.value)}
            />
          </label>
          <footer className="intake-actions">
            <button
              type="button"
              className="secondary"
              disabled={isGenerating}
              onClick={() => {
                setScreen("start");
                setIntakeResult(null);
                setSelectedIntakeChoiceId("");
                setIntakeNotes("");
              }}
            >
              返回
            </button>
            <button
              type="button"
              className={`primary ${isGenerating ? "is-loading" : ""}`}
              disabled={!selectedIntakeChoiceId || isGenerating}
              onClick={continueIntake}
            >
              {isGenerating ? (
                <>
                  <span className="start-spinner" />
                  <span>{loadingLabel || "处理中"}</span>
                  <span className="start-primary-time">{elapsedSeconds}s</span>
                </>
              ) : (
                "继续"
              )}
            </button>
          </footer>
          {message ? <p className="form-message">{message}</p> : null}
        </section>
      </main>
    );
  }

  if (screen === "brief" && pendingBrief) {
    const BRIEF_CARDS = [
      { key: "objective.one_sentence", label: "本轮目标", icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <circle cx="12" cy="12" r="4" />
        </svg>
      )},
      { key: "scope.include", label: "学习重点", icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
      )},
      { key: "strategy.rationale", label: "路线策略", icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      )},
    ];

    function getTagsForScope(value) {
      if (!value) return [];
      if (typeof value === "string") {
        return value.split(/[,，、;；\n]/).map((s) => s.trim()).filter(Boolean);
      }
      if (Array.isArray(value)) return value.map(String).filter(Boolean);
      return [String(value)];
    }

    return (
      <main className="intake-workspace">
        <div className="app-brand-anchor">
          <OpenKeriBrand onClick={() => setScreen("start")} />
        </div>
        <section className="brief-shell">
          <header className="brief-header">
            <span className="brief-step">计划草案</span>
            <h1>确认计划要点</h1>
            <p className="brief-subtitle">我们已根据你的目标生成以下学习方案，确认后将生成可编辑思维导图</p>
            <div className="brief-target-pill">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <circle cx="12" cy="12" r="4" />
              </svg>
              <span>{pendingBrief.title || "学习计划"}</span>
            </div>
          </header>

          <div className="brief-body">
            {BRIEF_CARDS.map((card, index) => {
              const expanded = activeBriefField === card.key;
              const fullText = getBriefFieldValue(pendingBrief, card.key);
              const isScope = card.key === "scope.include";
              const tags = isScope ? getTagsForScope(fullText) : [];
              return (
                <div
                  key={card.key}
                  className={`brief-card ${expanded ? "expanded" : ""}`}
                >
                  <div className="brief-card-main">
                    <span className="brief-card-num">{String(index + 1).padStart(2, "0")}</span>
                    <div className="brief-card-icon" aria-hidden="true">{card.icon}</div>
                    <div className="brief-card-content">
                      <strong className="brief-card-title">{card.label}</strong>
                      {isScope && tags.length > 0 ? (
                        <div className="brief-card-tags">
                          {tags.slice(0, 8).map((tag, i) => (
                            <span key={i} className="brief-tag-chip">{tag}</span>
                          ))}
                        </div>
                      ) : (
                        <p className="brief-card-desc">{fullText}</p>
                      )}
                    </div>
                    <button
                      type="button"
                      className="brief-card-expand"
                      onClick={() => setActiveBriefField(expanded ? "" : card.key)}
                    >
                      {expanded ? "收起" : "查看详情"}
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points={expanded ? "18 15 12 9 6 15" : "6 9 12 15 18 9"} />
                      </svg>
                    </button>
                  </div>
                  {expanded ? (
                    <div className="brief-card-editor">
                      <div className="brief-editor-head">
                        <span>编辑详情</span>
                        <small>{card.label}</small>
                      </div>
                      <textarea
                        value={fullText}
                        onChange={(event) =>
                          updatePendingBrief(card.key, event.target.value)
                        }
                        rows={4}
                      />
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>

          <footer className="brief-actions">
            <button
              type="button"
              className="brief-back"
              disabled={isGenerating}
              onClick={() => setScreen(intakeResult?.status === "needs_choice" ? "intake" : "start")}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6" />
              </svg>
              <span>返回修改</span>
            </button>
            <button
              type="button"
              className={`brief-cta ${isGenerating ? "is-loading" : ""}`}
              disabled={isGenerating}
              onClick={confirmGeneratePlan}
            >
              {isGenerating ? (
                <>
                  <span className="start-spinner" />
                  <span>{loadingLabel || "生成中"}</span>
                  <span className="start-primary-time">{elapsedSeconds}s</span>
                </>
              ) : (
                <>
                  <SparkleIcon size={14} />
                  <span>生成思维导图</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </>
              )}
            </button>
          </footer>
          {message ? (
            <div className="form-message-box">
              <p className="form-message">{message}</p>
              <button type="button" className="secondary" onClick={confirmGeneratePlan} disabled={isGenerating}>
                重新生成
              </button>
            </div>
          ) : null}
        </section>
      </main>
    );
  }

  return (
    <main className="mm-workspace">
      <header className="mm-topbar">
        <div className="mm-topbar-left">
          <OpenKeriBrand className="mm-brand" onClick={() => setScreen("start")} />
          <div className="mm-title-stack">
            <strong>{title || "计划草稿"}</strong>
            <span>Learning Plan</span>
          </div>
        </div>
        <div className="mm-topbar-center">
          <button
            type="button"
            className="mm-tool"
            disabled={!canUndo}
            onClick={undo}
            title="撤销 (Cmd/Ctrl+Z)"
          >
            ↺
          </button>
          <button
            type="button"
            className="mm-tool"
            disabled={!canRedo}
            onClick={redo}
            title="重做 (Cmd/Ctrl+Shift+Z)"
          >
            ↻
          </button>
          <span className="mm-tool-divider" />
          <button
            type="button"
            className="mm-tool"
            onClick={addChildNode}
            title="在当前选中节点下新增子节点"
          >
            + 子节点
          </button>
          <button
            type="button"
            className="mm-tool"
            onClick={deleteSelectedNode}
            title="删除选中节点"
          >
            − 删除
          </button>
        </div>
        <div className="mm-topbar-right">
          <div className="mm-stats">
            <span>{nodes.length} 节点</span>
            <em>·</em>
            <span>{stats.phaseCount} 阶段</span>
            <em>·</em>
            <span>{formatMinutes(stats.totalMinutes)}</span>
          </div>
          <button type="button" className="mm-ghost" onClick={() => importInputRef.current?.click()}>
            导入
          </button>
          <button type="button" className="mm-cta" onClick={exportProject}>
            导出
          </button>
        </div>
      </header>

      <input
        ref={importInputRef}
        className="project-import-input"
        type="file"
        accept="application/json,.json"
        onChange={importProject}
      />

      <section className="mm-canvas-area">
        <MindMapCanvas
          nodes={nodes}
          graphEdges={graphEdges}
          title={title}
          selectedNodeId={selectedNodeId}
          onSelectNode={setSelectedNodeId}
          onZoomChange={setZoomLevel}
          onTreeChange={onTreeChange}
          instanceRef={mindElixirRef}
        />
        {!nodes.length ? (
          <div className="empty-canvas">
            <strong>还没有计划图</strong>
            <span>回到起始页输入目标，或导入已有计划。</span>
            <button type="button" className="mm-cta" onClick={() => setScreen("start")}>
              新建计划
            </button>
          </div>
        ) : null}
        {isGenerating ? <div className="loading-mask">正在生成计划结构…</div> : null}
      </section>

      {selectedNode ? (
        <aside className={`mm-inspector node-kind-${selectedNode.data.kind || "learn"}`}>
          <div className="mm-inspector-sheen" aria-hidden="true" />
          <div className="mm-inspector-head">
            <div className="node-kind-mark" aria-hidden="true">
              <span>{nodeKindLabel(selectedNode.data.kind).slice(0, 1)}</span>
            </div>
            <div className="node-title-block">
              <span>{nodeKindLabel(selectedNode.data.kind)}</span>
              <input
                className="node-title-input"
                value={selectedNode.data.title || ""}
                onChange={(event) => updateSelectedNode("title", event.target.value)}
              />
              <div className="node-title-meta">
                <span>{formatMinutes(Number(selectedNode.data.estimated_minutes || 0))}</span>
                <i />
                <span className={`node-status-text status-${selectedNode.data.status || "not_started"}`}>
                  {nodeStatusLabel(selectedNode.data.status)}
                </span>
              </div>
            </div>
            <button type="button" onClick={() => setSelectedNodeId("")} aria-label="关闭">×</button>
          </div>

          <label className="mm-field mm-description-field">
            <span>说明</span>
            <textarea
              rows={4}
              value={selectedNode.data.description || ""}
              onChange={(event) => updateSelectedNode("description", event.target.value)}
              placeholder="补充这个节点在计划中的作用..."
            />
          </label>

          <div className="node-property-row">
            <label className="node-property">
              <span>类型</span>
              <select
                value={selectedNode.data.kind || "learn"}
                onChange={(event) => updateSelectedNode("kind", event.target.value)}
              >
                <option value="goal">目标</option>
                <option value="stage">阶段</option>
                <option value="learn">学习</option>
                <option value="project">项目</option>
              </select>
            </label>
            <label className="node-property">
              <span>时间</span>
              <input
                type="number"
                min="0"
                value={selectedNode.data.estimated_minutes || 0}
                onChange={(event) => updateSelectedNode("estimated_minutes", event.target.value)}
              />
            </label>
            <label className="node-property">
              <span>状态</span>
              <div className="node-status-toggle">
                {["not_started", "in_progress", "done"].map((status) => (
                  <button
                    type="button"
                    key={status}
                    className={(selectedNode.data.status || "not_started") === status ? "active" : ""}
                    onClick={() => updateSelectedNode("status", status)}
                    title={nodeStatusLabel(status)}
                    aria-label={`设置状态为${nodeStatusLabel(status)}`}
                    aria-pressed={(selectedNode.data.status || "not_started") === status}
                  >
                    <span className={`node-status-dot status-${status}`} />
                  </button>
                ))}
              </div>
            </label>
          </div>

          <div className="node-action-row">
            <div>
              <span>节点内容</span>
              <small>后续将在这里生成解释、练习和项目验收标准</small>
            </div>
            <button
              type="button"
              className="node-open-study"
              onClick={() => setStudyNodeId(selectedNode.id)}
            >
              打开
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>
        </aside>
      ) : null}

      {studyNode ? (
        <NodeLearningWorkspace
          studyNode={studyNode}
          onClose={() => setStudyNodeId("")}
          onLearningNotesChange={(learningNotes) => updateStudyNodeLearningNotes(studyNode.id, learningNotes)}
        />
      ) : null}

      <footer className="mm-bottombar">
        <div className="mm-map-status">
          <span>{Math.round(zoomLevel * 100)}%</span>
        </div>
      </footer>
    </main>
  );
}

function NodeLearningWorkspace({ studyNode, onClose, onLearningNotesChange }) {
  const planData = useMemo(() => getNodeLearningPlan(studyNode), [studyNode]);
  const initialLearningPoint = getInitialLearningPoint(planData);
  const [currentLearningPointId, setCurrentLearningPointId] = useState(initialLearningPoint?.id || "");
  const [mode, setMode] = useState("lesson");
  const [currentSlideId, setCurrentSlideId] = useState(getInitialSlideId(initialLearningPoint));
  const [currentProblemId, setCurrentProblemId] = useState(getInitialProblemId(initialLearningPoint));
  const [planOpen, setPlanOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState("plan");
  const [qaInput, setQaInput] = useState("");
  const [qaAnswer, setQaAnswer] = useState("");
  const [notesByLearningPoint, setNotesByLearningPoint] = useState(() =>
    parseLearningPointNotes(studyNode?.data?.learningNotes, initialLearningPoint?.id),
  );
  const [practiceDraftsByProblem, setPracticeDraftsByProblem] = useState({});
  const [feedbackByProblem, setFeedbackByProblem] = useState({});

  const currentLearningPoint = getLearningPointById(planData, currentLearningPointId) || initialLearningPoint;
  const slides = currentLearningPoint?.lesson?.slides || [];
  const problems = currentLearningPoint?.practice?.problems || [];
  const currentSlideIndex = Math.max(0, slides.findIndex((slide) => slide.id === currentSlideId));
  const currentSlide = slides[currentSlideIndex] || null;
  const selectedProblem = problems.find((problem) => problem.id === currentProblemId) || problems[0] || null;
  const currentPlanItemId = getCurrentPlanItemId(mode, currentLearningPoint, currentSlide, selectedProblem);
  const planRows = useMemo(
    () =>
      buildNodePlanRows(planData, {
        currentLearningPointId: currentLearningPoint?.id,
        mode,
        currentSlideId: currentSlide?.id,
        currentProblemId: selectedProblem?.id,
      }),
    [planData, currentLearningPoint?.id, mode, currentSlide?.id, selectedProblem?.id],
  );
  const currentPracticeDraft = getPracticeDraft(selectedProblem, practiceDraftsByProblem);
  const currentFeedback = selectedProblem ? feedbackByProblem[selectedProblem.id] : null;
  const currentNotes = currentLearningPoint ? notesByLearningPoint[currentLearningPoint.id] || "" : "";

  useEffect(() => {
    const nextInitial = getInitialLearningPoint(planData);
    if (!planData.learningPoints.some((point) => point.id === currentLearningPointId)) {
      setCurrentLearningPointId(nextInitial?.id || "");
      setCurrentSlideId(getInitialSlideId(nextInitial));
      setCurrentProblemId(getInitialProblemId(nextInitial));
    }
  }, [planData, currentLearningPointId]);

  useEffect(() => {
    const point = getLearningPointById(planData, currentLearningPointId);
    if (!point) return;
    const nextSlideId = getInitialSlideId(point);
    const nextProblemId = getInitialProblemId(point);
    if (nextSlideId && !point.lesson.slides.some((slide) => slide.id === currentSlideId)) {
      setCurrentSlideId(nextSlideId);
    }
    if (!nextSlideId && currentSlideId) setCurrentSlideId("");
    if (nextProblemId && !point.practice.problems.some((problem) => problem.id === currentProblemId)) {
      setCurrentProblemId(nextProblemId);
    }
    if (!nextProblemId && currentProblemId) setCurrentProblemId("");
  }, [planData, currentLearningPointId, currentSlideId, currentProblemId]);

  useEffect(() => {
    setNotesByLearningPoint(parseLearningPointNotes(studyNode?.data?.learningNotes, initialLearningPoint?.id));
  }, [studyNode?.id, initialLearningPoint?.id, studyNode?.data?.learningNotes]);

  function goPrev() {
    if (!slides.length) return;
    const nextIndex = Math.max(0, currentSlideIndex - 1);
    setCurrentSlideId(slides[nextIndex].id);
  }

  function goNext() {
    if (!slides.length) return;
    const nextIndex = Math.min(slides.length - 1, currentSlideIndex + 1);
    setCurrentSlideId(slides[nextIndex].id);
  }

  function startPractice(problemId = selectedProblem?.id) {
    const targetProblem = problems.find((problem) => problem.id === problemId) || problems[0];
    if (!targetProblem) return;
    setCurrentProblemId(targetProblem.id);
    setMode("practice");
  }

  function backToLesson() {
    setMode("lesson");
  }

  function selectPlanItem(item) {
    setPlanOpen(false);
    const point = getLearningPointById(planData, item.learningPointId);
    if (!point) return;
    setCurrentLearningPointId(point.id);
    if (item.kind === "practice") {
      setCurrentProblemId(item.problemId || getInitialProblemId(point));
      setMode("practice");
      return;
    }
    if (item.kind === "lesson") {
      setCurrentSlideId(item.slideId || getInitialSlideId(point));
      setMode("lesson");
      return;
    }
    const firstSlideId = getInitialSlideId(point);
    const firstProblemId = getInitialProblemId(point);
    setCurrentSlideId(firstSlideId);
    setCurrentProblemId(firstProblemId);
    setMode(firstSlideId ? "lesson" : firstProblemId ? "practice" : "lesson");
  }

  function updatePracticeDraft(field, value) {
    if (!selectedProblem) return;
    setPracticeDraftsByProblem((drafts) => ({
      ...drafts,
      [selectedProblem.id]: {
        ...getPracticeDraft(selectedProblem, drafts),
        [field]: value,
      },
    }));
    setFeedbackByProblem((feedbacks) => ({ ...feedbacks, [selectedProblem.id]: null }));
  }

  function submitPractice() {
    if (!selectedProblem) return;
    const draft = getPracticeDraft(selectedProblem, practiceDraftsByProblem);
    const combined = [
      ...selectedProblem.thinkingFields.map((field) => draft[field.id] || ""),
      draft.code || "",
    ]
      .join("\n")
      .toLowerCase();
    const missing = [];
    const ok = [];

    selectedProblem.reviewRubric.forEach((rule) => {
      const re = new RegExp(rule.pattern, "i");
      if (re.test(combined)) ok.push(rule.ok);
      else missing.push(rule.missing);
    });

    if ((draft.code || "").trim().length >= 40 && (draft.code || "").trim() !== (selectedProblem.starterCode || "").trim()) {
      ok.push("代码长度足够 review。");
    } else {
      missing.push("代码还太短，先写完整解法。");
    }

    setFeedbackByProblem((feedbacks) => ({
      ...feedbacks,
      [selectedProblem.id]: {
        status: missing.length ? "needs-work" : "ready",
        title: missing.length ? "还缺几个 practice 证据" : "练习可以提交 review",
        items: [...ok, ...missing],
      },
    }));
  }

  function updateCurrentNotes(value) {
    if (!currentLearningPoint) return;
    setNotesByLearningPoint((notes) => {
      const next = { ...notes, [currentLearningPoint.id]: value };
      onLearningNotesChange?.(serializeLearningPointNotes(next));
      return next;
    });
  }

  function askQa(question) {
    const q = (question ?? qaInput).trim();
    if (!q || !currentLearningPoint) return;
    setQaInput(q);
    setQaAnswer(answerLearningPointQa(currentLearningPoint, q));
  }

  return (
    <section className="nl-workspace" role="dialog" aria-label="Node learning workspace">
      <div className="start-bg" aria-hidden="true">
        <span className="start-bg-blur start-bg-blur--tl" />
        <span className="start-bg-blur start-bg-blur--br" />
        <span className="start-bg-blur start-bg-blur--bl" />
        <span className="start-bg-dots" />
      </div>
      <header className="nl-page-head">
        <OpenKeriBrand onClick={onClose} />
        <LessonHeader
          title={
            mode === "practice"
              ? `Practice · ${selectedProblem?.title || currentLearningPoint?.title || "Learning point"}`
              : currentSlide?.title || "Lesson"
          }
          planOpen={planOpen}
          onTogglePlan={() => setPlanOpen((v) => !v)}
        />
      </header>
      <div className="nl-stage">
        <div className="nl-stage-inner">
          {planOpen ? (
            <NodePlanDropdown
              planData={planData}
              rows={planRows}
              onClose={() => setPlanOpen(false)}
              onSelectItem={selectPlanItem}
              currentItemId={currentPlanItemId}
            />
          ) : null}

          <div className="nl-slide-frame">
            {mode === "lesson" ? (
              <LessonRenderer
                learningPoint={currentLearningPoint}
                slide={currentSlide}
                slideIndex={currentSlideIndex}
                totalSlides={slides.length}
                onPrev={goPrev}
                onNext={goNext}
                onStartPractice={() => startPractice()}
                canPrev={slides.length > 0 && currentSlideIndex > 0}
                canNext={slides.length > 0 && currentSlideIndex < slides.length - 1}
                canStartPractice={problems.length > 0}
              />
            ) : (
              <PracticeRenderer
                learningPoint={currentLearningPoint}
                problems={problems}
                problemId={selectedProblem?.id || ""}
                selectedProblem={selectedProblem}
                onSelectProblem={setCurrentProblemId}
                draft={currentPracticeDraft}
                onUpdate={updatePracticeDraft}
                onSubmit={submitPractice}
                feedback={currentFeedback}
                onBack={backToLesson}
              />
            )}
          </div>
        </div>
      </div>

      <KeriFloating
        open={drawerOpen}
        onOpenTab={(tab) => {
          setDrawerTab(tab);
          setDrawerOpen(true);
        }}
      />

      {drawerOpen ? (
        <KeriDrawer
          planData={planData}
          planRows={planRows}
          currentLearningPoint={currentLearningPoint}
          currentItemId={currentPlanItemId}
          tab={drawerTab}
          onChangeTab={setDrawerTab}
          onClose={() => setDrawerOpen(false)}
          notes={currentNotes}
          onNotesChange={updateCurrentNotes}
          qaInput={qaInput}
          onQaInput={setQaInput}
          qaAnswer={qaAnswer}
          onAskQa={askQa}
          onSelectPlanItem={(item) => {
            setDrawerOpen(false);
            selectPlanItem(item);
          }}
        />
      ) : null}
    </section>
  );
}

function getNodeLearningPlan(studyNode) {
  if (!studyNode || shouldUseLinearStructurePlan(studyNode)) return NODE_LEARNING_PLAN;
  const title = studyNode.data?.title || "Learning node";
  return {
    nodeId: studyNode.id,
    title,
    subtitle: studyNode.data?.group || "Managed learning workspace",
    stage: studyNode.data?.group || "Plan node",
    goal: "Learning plan node",
    completionCriteria: [
      "明确这个节点的 learning point",
      "补齐 lesson slides 和 practice problems",
      "保留当前节点的 notes 和 Q&A 上下文",
    ],
    learningPoints: [
      {
        id: "workspace-setup",
        title,
        subtitle: "Node workspace fallback",
        status: "current",
        lesson: {
          slides: [
            {
              id: "overview",
              title: "Lesson 1 · Node overview",
              subtitle: "Fallback lesson data",
              layout: "concept",
              heading: title,
              body: studyNode.data?.description || "这个节点还没有专属的本地 learning plan 数据。",
              bullets: [
                "外层 plan graph 只保留路线",
                "节点内部后续按 learning point 组织",
                "当前 fallback 不会复用 Two Pointers 内容",
              ],
            },
          ],
        },
        practice: { problems: [] },
        qa: {
          suggestedQuestions: [
            "这个节点应该拆成哪些 learning point？",
            "这个节点完成后应该能做什么？",
          ],
        },
      },
    ],
  };
}

function shouldUseLinearStructurePlan(studyNode) {
  if (studyNode.id === NODE_LEARNING_PLAN.nodeId) return true;
  const title = `${studyNode.data?.title || ""} ${studyNode.data?.description || ""}`.toLowerCase();
  return (
    /arrays?\s*(and|&)\s*linked\s*lists?/.test(title) ||
    (/数组/.test(title) && /链表/.test(title)) ||
    (/双指针/.test(title) && /链表/.test(title))
  );
}

function getInitialLearningPoint(planData) {
  return planData.learningPoints.find((point) => point.status === "current") || planData.learningPoints[0] || null;
}

function getLearningPointById(planData, learningPointId) {
  return planData.learningPoints.find((point) => point.id === learningPointId) || null;
}

function getInitialSlideId(learningPoint) {
  return learningPoint?.lesson?.slides?.[0]?.id || "";
}

function getInitialProblemId(learningPoint) {
  return learningPoint?.practice?.problems?.[0]?.id || "";
}

function getCurrentPlanItemId(mode, learningPoint, slide, problem) {
  if (!learningPoint) return "";
  if (mode === "practice" && problem) return `practice:${learningPoint.id}:${problem.id}`;
  if (slide) return `lesson:${learningPoint.id}:${slide.id}`;
  return `lp:${learningPoint.id}`;
}

function buildNodePlanRows(planData, state) {
  return planData.learningPoints.flatMap((point) => {
    const pointStatus = point.id === state.currentLearningPointId ? "current" : point.status || "not_started";
    const slides = point.lesson?.slides || [];
    const problems = point.practice?.problems || [];
    const currentSlideIndex = slides.findIndex((slide) => slide.id === state.currentSlideId);
    const rows = [
      {
        type: "group",
        id: `lp:${point.id}`,
        learningPointId: point.id,
        title: point.title,
        subtitle: point.subtitle,
        status: pointStatus,
      },
    ];

    slides.forEach((slide, index) => {
      const isCurrent = point.id === state.currentLearningPointId && state.mode === "lesson" && slide.id === state.currentSlideId;
      const status =
        isCurrent
          ? "current"
          : point.id === state.currentLearningPointId && (state.mode === "practice" || index < currentSlideIndex)
            ? "done"
            : point.status === "done"
              ? "done"
              : "not_started";
      rows.push({
        type: "item",
        id: `lesson:${point.id}:${slide.id}`,
        kind: "lesson",
        learningPointId: point.id,
        slideId: slide.id,
        title: slide.title,
        status,
      });
    });

    problems.forEach((problem) => {
      const isCurrent = point.id === state.currentLearningPointId && state.mode === "practice" && problem.id === state.currentProblemId;
      rows.push({
        type: "item",
        id: `practice:${point.id}:${problem.id}`,
        kind: "practice",
        learningPointId: point.id,
        problemId: problem.id,
        title: `Practice · ${problem.title}`,
        status: isCurrent ? "current" : point.status === "done" ? "done" : "not_started",
      });
    });

    return rows;
  });
}

function getPracticeDraft(problem, draftsByProblem) {
  if (!problem) return {};
  const fields = Object.fromEntries(problem.thinkingFields.map((field) => [field.id, ""]));
  return {
    ...fields,
    code: problem.starterCode || "",
    ...(draftsByProblem[problem.id] || {}),
  };
}

function parseLearningPointNotes(rawNotes, defaultLearningPointId) {
  if (!rawNotes) return {};
  try {
    const parsed = JSON.parse(rawNotes);
    if (parsed?.schema === "nodeLearningNotes.v1" && parsed.byLearningPoint && typeof parsed.byLearningPoint === "object") {
      return parsed.byLearningPoint;
    }
  } catch {
    // Legacy notes were stored as a plain string.
  }
  return defaultLearningPointId ? { [defaultLearningPointId]: rawNotes } : {};
}

function serializeLearningPointNotes(notesByLearningPoint) {
  return JSON.stringify({
    schema: "nodeLearningNotes.v1",
    byLearningPoint: notesByLearningPoint,
  });
}

function LessonHeader({ title, planOpen, onTogglePlan }) {
  return (
    <div className="nl-lesson-header">
      <button
        type="button"
        className={`nl-lesson-title ${planOpen ? "open" : ""}`}
        onClick={onTogglePlan}
        aria-expanded={planOpen}
      >
        <span className="nl-lesson-tag" aria-hidden="true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="14" rx="2" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
        </span>
        <strong>{title || "Lesson"}</strong>
        <svg className="nl-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
    </div>
  );
}

function NodePlanDropdown({ planData, rows, onClose, onSelectItem, currentItemId }) {
  const statusLabel = { current: "在做", done: "已学", not_started: "未学" };
  return (
    <>
      <div className="nl-plan-scrim" onClick={onClose} />
      <div className="nl-plan-dropdown" role="menu">
        <header className="nl-plan-head">
          <div className="nl-plan-head-text">
            <strong>{planData.title}</strong>
            <span>{planData.subtitle}</span>
          </div>
          <button type="button" className="nl-plan-close" onClick={onClose} aria-label="关闭">×</button>
        </header>

        <ol className="nl-plan-timeline">
          {rows.map((row) => {
            const isCurrent = row.id === currentItemId;
            const status = isCurrent ? "current" : row.status;
            if (row.type === "group") {
              return (
                <li key={row.id} className={`nl-tl-row group status-${status} ${isCurrent ? "is-current" : ""}`}>
                  <span className="nl-tl-dot group" aria-hidden="true" />
                  <div className="nl-tl-text">
                    <span className="nl-tl-title">{row.title}</span>
                    <span className="nl-tl-status">{statusLabel[status]}</span>
                  </div>
                </li>
              );
            }
            return (
              <li key={row.id} className={`nl-tl-row item status-${status} ${isCurrent ? "is-current" : ""}`}>
                <span className="nl-tl-dot" aria-hidden="true" />
                <button type="button" className="nl-tl-btn" onClick={() => onSelectItem(row)}>
                  <span className={`nl-tl-kind kind-${row.kind}`}>{row.kind === "lesson" ? "L" : "P"}</span>
                  <span className="nl-tl-title">{row.title.replace(/^(Lesson|Practice)\s*[·:]\s*/, "")}</span>
                  <span className="nl-tl-status">{statusLabel[status]}</span>
                </button>
              </li>
            );
          })}
        </ol>
      </div>
    </>
  );
}

function StatusPill({ status, compact }) {
  const label = { current: "正在学", done: "已完成", not_started: "未开始" }[status] || status;
  return <span className={`nl-status-pill status-${status} ${compact ? "compact" : ""}`}>{label}</span>;
}

function LessonRenderer({
  learningPoint,
  slide,
  slideIndex,
  totalSlides,
  onPrev,
  onNext,
  onStartPractice,
  canPrev,
  canNext,
  canStartPractice,
}) {
  return (
    <article className="nl-slide">
      {slide ? (
        <div className="nl-slide-body">{renderLessonSlideContent(slide)}</div>
      ) : (
        <div className="nl-empty-state">
          <strong>{learningPoint?.title || "Learning point"}</strong>
          <span>这个 learning point 还没有 lesson slides。</span>
        </div>
      )}

      <footer className="nl-slide-dock">
        <div className="nl-dock-bar">
          <span className="nl-dock-progress">{totalSlides ? `${slideIndex + 1} / ${totalSlides}` : "0 / 0"}</span>
          <span className="nl-dock-sep" />
          <button type="button" className="nl-dock-btn" onClick={onPrev} disabled={!canPrev} aria-label="上一页">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <button type="button" className="nl-dock-btn play" onClick={onStartPractice} disabled={!canStartPractice} aria-label="开始练习">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="6 4 20 12 6 20 6 4" />
            </svg>
          </button>
          <button type="button" className="nl-dock-btn" onClick={onNext} disabled={!canNext} aria-label="下一页">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>
      </footer>
    </article>
  );
}

function renderLessonSlideContent(slide) {
  if (slide.layout === "concept_with_example") {
    return (
      <>
        <ConceptSection slide={slide} />
        <section className="nl-slide-section nl-slide-example">
          <ExampleBlock example={slide.example} />
          <CodeBlock code={slide.example?.code} />
        </section>
      </>
    );
  }
  if (slide.layout === "rule_summary") {
    return (
      <>
        <ConceptSection slide={slide} compact />
        <section className="nl-rule-list">
          {(slide.rules || []).map((rule) => (
            <div className="nl-rule-card" key={rule.title}>
              <strong>{rule.title}</strong>
              <p>{rule.detail}</p>
            </div>
          ))}
        </section>
      </>
    );
  }
  if (slide.layout === "checkpoint") {
    return (
      <>
        <ConceptSection slide={slide} />
        <section className="nl-checkpoint-list">
          {(slide.checklist || []).map((item, index) => (
            <div className="nl-checkpoint-item" key={item}>
              <span>{index + 1}</span>
              <p>{item}</p>
            </div>
          ))}
        </section>
        {slide.takeaway ? <p className="nl-takeaway">{slide.takeaway}</p> : null}
      </>
    );
  }
  return <ConceptSection slide={slide} />;
}

function ConceptSection({ slide, compact = false }) {
  return (
    <section className="nl-slide-section">
      <header className={`nl-section-head ${compact ? "compact" : ""}`}>
        <span className="nl-section-icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 18h6" />
            <path d="M10 22h4" />
            <path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2v.3h6V17c0-.7.4-1.5 1-2A7 7 0 0 0 12 2z" />
          </svg>
        </span>
        <div>
          {compact ? <h3>{slide.heading}</h3> : <h2>{slide.heading}</h2>}
          <p>{slide.body}</p>
        </div>
      </header>
      {slide.bullets?.length ? (
        <ul className="nl-bullets">
          {slide.bullets.map((item) => <li key={item}>{item}</li>)}
        </ul>
      ) : null}
    </section>
  );
}

function ExampleBlock({ example }) {
  if (!example) return <div className="nl-example-block" />;
  return (
    <div className="nl-example-block">
      <div className="nl-example-head">
        <i className="nl-example-bar" />
        <strong>{example.title}</strong>
      </div>
      {example.diagram ? <StringDiagram diagram={example.diagram} /> : null}
      {example.caption ? <p className="nl-example-caption">{example.caption}</p> : null}
    </div>
  );
}

function CodeBlock({ code }) {
  if (!code?.body) return <div className="nl-code-panel empty" />;
  return (
    <div className="nl-code-panel">
      <header>
        <span>{code.language || "Code"}</span>
        <button type="button" className="nl-copy-btn" onClick={() => navigator.clipboard?.writeText(code.body)}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          复制
        </button>
      </header>
      <pre><code dangerouslySetInnerHTML={{ __html: highlightJs(code.body) }} /></pre>
    </div>
  );
}

function StringDiagram({ diagram }) {
  const cells = diagram?.cells || [];
  const arrows = diagram?.arrows || [];
  const labels = diagram?.labels || [];
  const gridStyle = { gridTemplateColumns: `repeat(${Math.max(cells.length, 1)}, minmax(0, 1fr))` };
  return (
    <div className="nl-diagram">
      <div className="nl-diagram-row" style={gridStyle}>
        {cells.map((ch, i) => (
          <span key={`${ch}-${i}`} className="nl-cell">{ch}</span>
        ))}
      </div>
      <div className="nl-diagram-row arrows" style={gridStyle}>
        {cells.map((_, i) => {
          const dir = arrows[i] || "";
          return (
            <span key={i} className={`nl-arrow ${dir}`} aria-hidden="true">
              {dir === "up" ? "↑" : dir === "right" ? "→" : dir === "left" ? "←" : ""}
            </span>
          );
        })}
      </div>
      <div className="nl-diagram-row labels" style={gridStyle}>
        {cells.map((_, i) => (
          <span key={i} className="nl-pointer-label">{labels[i] || ""}</span>
        ))}
      </div>
    </div>
  );
}

function highlightJs(code) {
  const escape = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const tokens = [
    { re: /\b(function|let|const|var|while|if|else|return|true|false|null)\b/g, cls: "tok-kw" },
    { re: /\b(\d+)\b/g, cls: "tok-num" },
    { re: /"[^"]*"|'[^']*'/g, cls: "tok-str" },
  ];
  let html = escape(code);
  tokens.forEach((t) => {
    html = html.replace(t.re, (m) => `__${t.cls}__${m}__END__`);
  });
  html = html
    .replace(/__tok-kw__(.+?)__END__/g, '<span class="tok-kw">$1</span>')
    .replace(/__tok-num__(.+?)__END__/g, '<span class="tok-num">$1</span>')
    .replace(/__tok-str__(.+?)__END__/g, '<span class="tok-str">$1</span>')
    .replace(/\b(isPalindrome|isAlphaNum|twoSum)\b/g, '<span class="tok-fn">$1</span>')
    .replace(/\b(left|right|target|sum)\b/g, '<span class="tok-var">$1</span>');
  return html;
}

function PracticeRenderer({
  learningPoint,
  problems,
  problemId,
  selectedProblem,
  onSelectProblem,
  draft,
  onUpdate,
  onSubmit,
  feedback,
  onBack,
}) {
  return (
    <article className="nl-practice">
      <header className="nl-practice-head">
        <button type="button" className="nl-secondary-btn ghost" onClick={onBack}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back to lesson
        </button>
        <strong>Practice · {learningPoint?.title || "Learning point"}</strong>
      </header>

      {selectedProblem ? (
        <div className="nl-practice-grid">
          <aside className="nl-problem-list">
            <span className="nl-side-label">Problems</span>
            {problems.map((problem) => {
              const active = problem.id === problemId;
              return (
                <button
                  type="button"
                  key={problem.id}
                  className={`nl-problem-item ${active ? "active" : ""}`}
                  onClick={() => onSelectProblem(problem.id)}
                >
                  <strong>{problem.title}</strong>
                  <span className={`nl-diff diff-${problem.difficulty}`}>{problem.difficulty}</span>
                </button>
              );
            })}
          </aside>

          <section className="nl-problem-statement">
            <span className="nl-side-label">Problem</span>
            <h3>{selectedProblem.title}</h3>
            <p>{selectedProblem.statement || selectedProblem.focus}</p>
            {selectedProblem.examples?.length ? (
              <div className="nl-example-list">
                {selectedProblem.examples.map((example, index) => (
                  <div className="nl-practice-example" key={`${selectedProblem.id}-ex-${index}`}>
                    <strong>Example {index + 1}</strong>
                    <span>Input: {example.input}</span>
                    <span>Output: {example.output}</span>
                    {example.explanation ? <p>{example.explanation}</p> : null}
                  </div>
                ))}
              </div>
            ) : null}
            <div className="nl-pre-fields">
              {selectedProblem.thinkingFields.map((field) => (
                <label key={field.id}>
                  <span>{field.label}</span>
                  {field.multiline ? (
                    <textarea
                      rows={3}
                      value={draft[field.id] || ""}
                      onChange={(e) => onUpdate(field.id, e.target.value)}
                      placeholder={field.placeholder}
                    />
                  ) : (
                    <input
                      value={draft[field.id] || ""}
                      onChange={(e) => onUpdate(field.id, e.target.value)}
                      placeholder={field.placeholder}
                    />
                  )}
                </label>
              ))}
            </div>
          </section>

          <section className="nl-editor-column">
            <span className="nl-side-label">Editor</span>
            <textarea
              className="nl-editor"
              value={draft.code || ""}
              onChange={(e) => onUpdate("code", e.target.value)}
              placeholder="// 写你的解法\n"
              spellCheck="false"
            />
            <button type="button" className="nl-primary-btn nl-submit" onClick={onSubmit}>
              Submit
            </button>
            {feedback ? (
              <div className={`nl-feedback ${feedback.status}`}>
                <strong>{feedback.title}</strong>
                <ul>
                  {feedback.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
        </div>
      ) : (
        <div className="nl-empty-state">
          <strong>{learningPoint?.title || "Learning point"}</strong>
          <span>这个 learning point 还没有 practice problems。</span>
        </div>
      )}
    </article>
  );
}

const KERI_TIPS = [
  "卡住了？问问我 ✨",
  "需要小提示吗？",
  "试试点 Plan 看进度",
  "想做笔记？我帮你存",
  "对哪一步还没把握？",
  "想要个例子？",
];

function KeriFloating({ open, onOpenTab }) {
  const getViewportSize = () => {
    const positiveMin = (...values) => Math.min(...values.filter((value) => value > 0));
    return {
      width: positiveMin(window.visualViewport?.width || 0, window.innerWidth, window.outerWidth),
      height: positiveMin(window.visualViewport?.height || 0, window.innerHeight, window.outerHeight),
    };
  };
  const [tipIndex, setTipIndex] = useState(0);
  const [typed, setTyped] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [viewportSize, setViewportSize] = useState(getViewportSize);

  useEffect(() => {
    if (open) return;
    const tip = KERI_TIPS[tipIndex];
    setTyped("");
    let i = 0;
    const typer = setInterval(() => {
      i += 1;
      setTyped(tip.slice(0, i));
      if (i >= tip.length) clearInterval(typer);
    }, 60);
    const next = setTimeout(() => {
      setTipIndex((idx) => (idx + 1) % KERI_TIPS.length);
    }, 4200);
    return () => {
      clearInterval(typer);
      clearTimeout(next);
    };
  }, [tipIndex, open]);

  useEffect(() => {
    if (!menuOpen) return;
    function onDocClick() { setMenuOpen(false); }
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, [menuOpen]);

  useEffect(() => {
    const viewport = window.visualViewport;
    const updateViewportSize = () => {
      setViewportSize(getViewportSize());
    };
    updateViewportSize();
    viewport?.addEventListener("resize", updateViewportSize);
    window.addEventListener("resize", updateViewportSize);
    return () => {
      viewport?.removeEventListener("resize", updateViewportSize);
      window.removeEventListener("resize", updateViewportSize);
    };
  }, []);

  if (open) return null;

  const shortcuts = [
    { key: "ask", label: "Ask", glyph: "?" },
    { key: "plan", label: "Plan", glyph: "≡" },
    { key: "notes", label: "Notes", glyph: "✎" },
  ];

  return (
    <div
      className={`nl-keri-anchor ${menuOpen ? "menu-open" : ""}`}
      style={{
        "--nl-vw": `${Math.round(viewportSize.width)}px`,
        "--nl-vh": `${Math.round(viewportSize.height)}px`,
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {!menuOpen ? (
        <div className="nl-keri-bubble" aria-live="polite">
          {typed}
          <span className="nl-keri-caret" aria-hidden="true" />
        </div>
      ) : null}

      <div className="nl-keri-fan" role="menu">
        {shortcuts.map((s, i) => (
          <button
            type="button"
            key={s.key}
            className="nl-keri-chip"
            style={{ "--i": i }}
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpen(false);
              onOpenTab(s.key);
            }}
            aria-label={s.label}
          >
            <span className="nl-keri-chip-glyph" aria-hidden="true">{s.glyph}</span>
            <span className="nl-keri-chip-label">{s.label}</span>
          </button>
        ))}
      </div>

      <button
        type="button"
        className="nl-keri-btn"
        onClick={() => setMenuOpen((v) => !v)}
        aria-label="打开 Keri"
        aria-expanded={menuOpen}
      >
        <OpenKeriLogo size={34} />
      </button>
    </div>
  );
}

function KeriDrawer({
  planData,
  planRows,
  currentLearningPoint,
  currentItemId,
  tab,
  onChangeTab,
  onClose,
  notes,
  onNotesChange,
  qaInput,
  onQaInput,
  qaAnswer,
  onAskQa,
  onSelectPlanItem,
}) {
  return (
    <>
      <div className="nl-drawer-scrim" onClick={onClose} />
      <aside className="nl-drawer" role="complementary">
        <header className="nl-drawer-head">
          <div className="nl-drawer-title">
            <span className="nl-keri-btn-mini" aria-hidden="true">K</span>
            <strong>Keri</strong>
          </div>
          <button type="button" onClick={onClose} aria-label="关闭" className="nl-icon-btn">×</button>
        </header>

        <div className="nl-drawer-tabs" role="tablist">
          {[
            ["plan", "Plan"],
            ["ask", "Ask"],
            ["notes", "Notes"],
          ].map(([key, label]) => (
            <button
              type="button"
              key={key}
              className={tab === key ? "active" : ""}
              onClick={() => onChangeTab(key)}
              role="tab"
              aria-selected={tab === key}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="nl-drawer-body">
          {tab === "plan" ? (
            <DrawerPlanTab
              planData={planData}
              planRows={planRows}
              currentItemId={currentItemId}
              onSelectPlanItem={onSelectPlanItem}
            />
          ) : null}

          {tab === "ask" ? (
            <DrawerAskTab
              learningPoint={currentLearningPoint}
              qaInput={qaInput}
              onQaInput={onQaInput}
              qaAnswer={qaAnswer}
              onAskQa={onAskQa}
            />
          ) : null}

          {tab === "notes" ? (
            <DrawerNotesTab learningPoint={currentLearningPoint} notes={notes} onNotesChange={onNotesChange} />
          ) : null}
        </div>
      </aside>
    </>
  );
}

function DrawerPlanTab({ planData, planRows, currentItemId, onSelectPlanItem }) {
  const firstItemByLearningPoint = planRows.reduce((acc, row) => {
    if (row.type === "item" && !acc[row.learningPointId]) acc[row.learningPointId] = row;
    return acc;
  }, {});
  return (
    <div className="nl-drawer-plan">
      <div className="nl-drawer-section">
        <strong>{planData.title}</strong>
        <span>{planData.subtitle}</span>
      </div>
      <div className="nl-drawer-section">
        <span className="nl-side-label">完成判定</span>
        <ul className="nl-criteria">
          {planData.completionCriteria.map((criterion) => (
            <li key={criterion}><i className="nl-dot" /> {criterion}</li>
          ))}
        </ul>
      </div>
      <div className="nl-drawer-section">
        <span className="nl-side-label">Learning points</span>
        <ul className="nl-drawer-group-list">
          {planData.learningPoints.map((point) => {
            const firstItem = firstItemByLearningPoint[point.id] || {
              type: "group",
              id: `lp:${point.id}`,
              learningPointId: point.id,
            };
            const status = point.id === currentItemId?.split(":")[1] || firstItem.id === currentItemId
              ? "current"
              : point.status || "not_started";
            return (
              <li key={point.id} className={`status-${status}`}>
              <button
                type="button"
                onClick={() => onSelectPlanItem(firstItem)}
              >
                <strong>{point.title}</strong>
                <StatusPill status={status} compact />
              </button>
            </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

function DrawerAskTab({ learningPoint, qaInput, onQaInput, qaAnswer, onAskQa }) {
  const suggestedQuestions = learningPoint?.qa?.suggestedQuestions || [];
  return (
    <div className="nl-drawer-ask">
      <div className="nl-drawer-section">
        <strong>Ask about {learningPoint?.title || "Learning point"}</strong>
        <span>提问会保留在当前 learning point。</span>
      </div>
      {suggestedQuestions.length ? (
        <div className="nl-drawer-section">
          <span className="nl-side-label">Suggested</span>
          <div className="nl-suggested-q">
            {suggestedQuestions.map((q) => (
              <button type="button" key={q} onClick={() => onAskQa(q)}>{q}</button>
            ))}
          </div>
        </div>
      ) : null}
      {qaAnswer ? (
        <div className="nl-drawer-answer">
          <span>answer</span>
          <p>{qaAnswer}</p>
        </div>
      ) : null}
      <div className="nl-drawer-ask-input">
        <textarea
          rows={2}
          value={qaInput}
          onChange={(e) => onQaInput(e.target.value)}
          placeholder="问 Keri 一个关于当前 learning point 的问题…"
        />
        <button type="button" className="nl-primary-btn" onClick={() => onAskQa()}>
          发送
        </button>
      </div>
    </div>
  );
}

function DrawerNotesTab({ learningPoint, notes, onNotesChange }) {
  return (
    <div className="nl-drawer-notes">
      <div className="nl-drawer-section">
        <strong>{learningPoint?.title || "Learning point"} notes</strong>
        <span>记录这个 learning point 里要避免的具体错误。</span>
      </div>
      <textarea
        value={notes}
        onChange={(e) => onNotesChange(e.target.value)}
        placeholder="记录一个你要避免的错误，例如：没有解释 left/right 移动理由。"
      />
    </div>
  );
}

function answerLearningPointQa(learningPoint, question) {
  if (learningPoint?.id === "two-pointers") return answerTwoPointerQa(question);
  return `先围绕 ${learningPoint?.title || "当前 learning point"} 做判断：它要解决的题目信号是什么，核心 invariant 是什么，完成后要能独立解释哪一步。`;
}

function answerTwoPointerQa(question) {
  const normalized = question.toLowerCase();
  if (/sum|target|太小|left|right|移动/.test(normalized)) {
    return "Two Sum II 里数组有序。当前 sum < target 时，固定 right 不变，left 左边的数只会更小，所以这些候选都不可能达到 target，可以移动 left。sum > target 时同理移动 right。";
  }
  if (/left\s*<\s*right|<=|while|条件|相遇/.test(normalized)) {
    return "如果题目需要两个不同位置的元素，通常用 left < right，避免同一个元素被使用两次。left <= right 更常见于二分查找或允许单点被处理的扫描。";
  }
  if (/hash|哈希|不用/.test(normalized)) {
    return "哈希表也能做普通 Two Sum，但 Two Sum II 的输入已经有序。双指针能用 O(1) 额外空间，并且移动指针的理由来自有序性，所以更贴合这个 learning point。";
  }
  if (/window|滑动|窗口/.test(normalized)) {
    return "双指针这里是两端收缩，目标是排除候选 pair。滑动窗口通常维护一个连续区间的状态，比如窗口内不能重复、窗口和满足条件。关键区别是有没有一个持续维护的窗口 invariant。";
  }
  return "先回到这个 learning point 的判断：题目是否有有序、两端比较、pair search 或回文信号？如果有，再问 left/right 每次移动能排除哪些候选。";
}

async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "请求失败");
  return payload;
}

function getBriefFieldValue(brief, fieldKey) {
  if (!brief) return "";
  const value = fieldKey.split(".").reduce((current, key) => current?.[key], brief);
  if (Array.isArray(value)) return value.join("\n");
  return value || "";
}

function getBriefFieldKeyword(brief, fieldKey, maxLen = 24) {
  const full = getBriefFieldValue(brief, fieldKey);
  if (!full) return "";
  const firstLine = full.split(/[\n;；]/)[0].trim();
  const firstClause = firstLine.split(/[。！？.!?]/)[0].trim() || firstLine;
  if (firstClause.length <= maxLen) return firstClause;
  return `${firstClause.slice(0, maxLen)}…`;
}

function setBriefFieldValue(brief, fieldKey, value) {
  const next = structuredClone(brief);
  const keys = fieldKey.split(".");
  let target = next;
  for (const key of keys.slice(0, -1)) {
    target[key] = target[key] || {};
    target = target[key];
  }
  const finalKey = keys[keys.length - 1];
  const previousValue = target[finalKey];
  target[finalKey] = Array.isArray(previousValue)
    ? value.split("\n").map((item) => item.trim()).filter(Boolean)
    : value;
  return next;
}

function toProjectDraft(draftTitle, draftSummary, draftNodes, draftGraphEdges, draftGoal) {
  return {
    id: "single-project",
    schemaVersion: 1,
    goal: draftGoal,
    title: draftTitle,
    summary: draftSummary,
    nodes: draftNodes,
    graphEdges: draftGraphEdges,
    updatedAt: new Date().toISOString(),
  };
}

function slugify(value) {
  return (
    value
      .trim()
      .toLowerCase()
      .replace(/[^\p{L}\p{N}]+/gu, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 80) || "learning-project"
  );
}

function toFlowDraft(draft) {
  const nodes = draft.nodes.map((node) => ({
    id: node.id,
    type: normalizeNodeKind(node.kind),
    data: {
      title: node.title,
      kind: normalizeNodeKind(node.kind),
      description: node.description,
      estimated_minutes: node.estimated_minutes,
      group: node.group || "",
      status: node.status || "not_started",
      learningNotes: node.learningNotes || "",
    },
    position: { x: 0, y: 0 },
  }));

  const graphEdges = draft.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    relation: edge.relation || inferEdgeRelation(edge),
    label: "",
  }));

  return { nodes, graphEdges };
}

function restoreFlowDraftFromStorage(draft) {
  const draftNodes = draft.nodes?.map((node) => ({
    id: node.id,
    type: normalizeNodeKind(node.data?.kind || node.kind),
    data: {
      title: node.data?.title || node.title,
      kind: normalizeNodeKind(node.data?.kind || node.kind),
      description: node.data?.description || node.description,
      estimated_minutes: node.data?.estimated_minutes || node.estimated_minutes || 0,
      group: node.data?.group || node.group || "",
      status: node.data?.status || node.status || "not_started",
      learningNotes: node.data?.learningNotes || node.learningNotes || "",
    },
    position: node.position || { x: 0, y: 0 },
  }));

  const sourceEdges = draft.graphEdges || draft.edges || [];
  const draftEdges = sourceEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    relation: edge.relation || inferEdgeRelation(edge),
    label: "",
    type: "bezier",
  }));

  if (!draftNodes?.length || !draftEdges?.length) {
    return { nodes: [], graphEdges: [] };
  }
  return { nodes: draftNodes, graphEdges: draftEdges };
}

function inferEdgeRelation(edge) {
  const label = edge.label || "";
  if (/开始|下一阶段|next/i.test(label)) return "next";
  return "contains";
}

function treeToNodesAndEdges(tree, existingNodes) {
  const nodeById = new Map(existingNodes.map((n) => [n.id, n]));
  const nextNodes = [];
  const nextEdges = [];
  const root = tree.nodeData;

  function visit(obj, parentId, kindHint = "learn") {
    const existing = nodeById.get(obj.id);
    const isRoot = !parentId;
    const kind = isRoot
      ? "goal"
      : parentId === root.id
        ? "stage"
        : !existing
        ? kindHint
        : existing.data?.kind;
    nextNodes.push({
      id: obj.id,
      type: kind,
      position: { x: 0, y: 0 },
      data: {
        ...existing?.data,
        title: obj.topic,
        kind,
      },
    });
    if (parentId) {
      nextEdges.push({
        id: `edge-${parentId}-${obj.id}`,
        source: parentId,
        target: obj.id,
        relation: parentId === root.id ? "next" : "contains",
        label: "",
      });
    }
    for (const child of obj.children || []) {
      visit(child, obj.id, obj.id === root.id ? "stage" : "learn");
    }
  }

  visit(root, null, "goal");
  return { nodes: nextNodes, edges: nextEdges };
}


function normalizeNodeKind(kind) {
  const normalized =
    {
      phase: "stage",
      concept: "learn",
      task: "learn",
      practice: "learn",
      review: "learn",
      checkpoint: "project",
      resource: "learn",
    }[kind] || kind;
  return ["goal", "stage", "learn", "project"].includes(normalized) ? normalized : "learn";
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function nodeKindLabel(kind) {
  return { goal: "目标", stage: "阶段", learn: "学习", project: "项目" }[kind] || "节点";
}

function nodeStatusLabel(status) {
  return { not_started: "未开始", in_progress: "进行中", done: "已完成" }[status] || "未开始";
}

function getPlanStats(nodes) {
  return nodes.reduce(
    (acc, node) => {
      if (node.data?.kind === "stage") acc.phaseCount += 1;
      acc.totalMinutes += Number(node.data?.estimated_minutes || 0);
      return acc;
    },
    { phaseCount: 0, totalMinutes: 0 },
  );
}

function formatMinutes(total) {
  if (!total) return "0 min";
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  if (hours && minutes) return `${hours} h ${minutes} min`;
  if (hours) return `${hours} h`;
  return `${minutes} min`;
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
