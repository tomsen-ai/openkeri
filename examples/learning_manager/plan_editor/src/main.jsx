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
  const savedDraft = loadDraft();
  const restoredDraft = savedDraft ? restoreFlowDraftFromStorage(savedDraft) : null;
  const hasRestoredDraft = Boolean(restoredDraft?.nodes?.length);
  const importInputRef = useRef(null);
  const [screen, setScreen] = useState(
    shouldPreviewBrief ? "brief" : shouldPreviewIntake ? "intake" : hasRestoredDraft ? "editor" : "start",
  );
  const [prompt, setPrompt] = useState(
    shouldPreviewBrief
      ? "30天算法面试冲刺"
      : shouldPreviewIntake
        ? "两周入门 Python"
        : savedDraft?.goal || EMPTY_FORM.goal,
  );
  const [title, setTitle] = useState(savedDraft?.title || "计划草稿");
  const [summary, setSummary] = useState(
    savedDraft?.summary || "输入目标后生成一个可编辑的计划图。",
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
  const [selectedNodeId, setSelectedNodeId] = useState("");
  const [studyNodeId, setStudyNodeId] = useState("");
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
              <small>
                {formatMinutes(Number(selectedNode.data.estimated_minutes || 0))} · {nodeStatusLabel(selectedNode.data.status)}
              </small>
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
              <select
                value={selectedNode.data.status || "not_started"}
                onChange={(event) => updateSelectedNode("status", event.target.value)}
              >
                <option value="not_started">未开始</option>
                <option value="in_progress">进行中</option>
                <option value="done">已完成</option>
              </select>
            </label>
          </div>
        </aside>
      ) : null}

      {studyNode ? (
        <section className="study-page">
          <div className="study-shell">
            <header className="study-header">
              <button type="button" onClick={() => setStudyNodeId("")}>返回思维导图</button>
              <div>
                <span>{nodeKindLabel(studyNode.data.kind)} · {nodeStatusLabel(studyNode.data.status)}</span>
                <h1>{studyNode.data.title}</h1>
              </div>
            </header>
            <div className="study-grid">
              <article>
                <span>学习目标</span>
                <p>{studyNode.data.description || `理解 ${studyNode.data.title} 的核心概念和典型应用。`}</p>
              </article>
              <article>
                <span>核心概念</span>
                <ul>
                  <li>先说清这个知识点解决什么问题。</li>
                  <li>整理关键定义、常见操作和边界条件。</li>
                  <li>用一个小例子确认自己真的理解。</li>
                </ul>
              </article>
              <article>
                <span>学习步骤</span>
                <ol>
                  <li>阅读并复述概念。</li>
                  <li>手写一个最小例子。</li>
                  <li>完成 1-2 道相关练习。</li>
                  <li>记录卡住点和复盘结论。</li>
                </ol>
              </article>
              <article>
                <span>练习 / 自测</span>
                <ul>
                  <li>不用资料解释这个知识点。</li>
                  <li>说出一个适合使用它的场景。</li>
                  <li>找出一个容易错的细节。</li>
                </ul>
              </article>
            </div>
            <label className="study-notes">
              学习笔记
              <textarea
                rows={7}
                value={studyNode.data.learningNotes || ""}
                onChange={(event) => updateStudyNode("learningNotes", event.target.value)}
                placeholder="记录今天学到了什么、哪里还不清楚、下一步要练什么。"
              />
            </label>
          </div>
        </section>
      ) : null}

      <footer className="mm-bottombar">
        <div className="mm-map-status">
          <span>{Math.round(zoomLevel * 100)}%</span>
        </div>
      </footer>
    </main>
  );

  function updateStudyNode(field, value) {
    const nextNodes = nodes.map((node) =>
      node.id === studyNodeId
        ? { ...node, data: { ...node.data, [field]: value } }
        : node,
    );
    setNodes(nextNodes);
    persistDraft(title, summary, nextNodes, graphEdges);
  }
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
