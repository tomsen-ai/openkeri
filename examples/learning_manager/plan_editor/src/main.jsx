import React, { useCallback, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Background,
  Handle,
  Position,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  applyNodeChanges,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "./styles.css";

const STORAGE_KEY = "openkeri.planEditorDraft.v1";
const ROADMAP_COLUMN_GAP = 520;
const ROADMAP_BRANCH_GAP = 156;
const ROADMAP_BRANCH_START_Y = 198;

const EMPTY_FORM = {
  goal: "我想用 30 天准备算法面试，重点是能自己规划和复盘",
  durationDays: 30,
  dailyMinutes: 25,
  preference: "生成思维导图式计划，允许分支和汇合，节点不要太多",
};

function PlanNode({ data, selected }) {
  const shortDescription =
    data.description && data.description.length > 55
      ? `${data.description.slice(0, 35)}…`
      : data.description || "";
  const shouldShowDescription = selected || data.kind === "goal";

  return (
    <div className={`plan-node ${selected ? "selected" : ""} ${data.kind} ${data.layoutRole || ""}`}>
      <Handle id="left" className="plan-handle left" type="target" position={Position.Left} />
      <Handle id="top" className="plan-handle top" type="target" position={Position.Top} />
      <div className="node-meta">
        <span>{nodeKindLabel(data.kind)}</span>
        <div className="node-badges">
          <i className={`status-dot ${data.status || "not_started"}`} title={nodeStatusLabel(data.status)} />
          {data.orderIndex ? <b>{data.orderIndex}</b> : null}
        </div>
      </div>
      <strong>{data.title}</strong>
      <small>{data.group || "未分组"} · {data.estimated_minutes || 0} min</small>
      {shouldShowDescription && shortDescription ? <p>{shortDescription}</p> : null}
      <Handle id="right" className="plan-handle right" type="source" position={Position.Right} />
      <Handle id="bottom" className="plan-handle bottom" type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = { planNode: PlanNode };

function App() {
  const savedDraft = loadDraft();
  const restoredDraft = savedDraft ? restoreFlowDraftFromStorage(savedDraft) : null;
  const importInputRef = useRef(null);
  const [prompt, setPrompt] = useState(EMPTY_FORM.goal);
  const [title, setTitle] = useState(savedDraft?.title || "计划草稿");
  const [summary, setSummary] = useState(
    savedDraft?.summary || "输入目标后生成一个可编辑的计划图。",
  );
  const [nodes, setNodes] = useState(restoredDraft?.nodes || []);
  const [graphEdges, setGraphEdges] = useState(restoredDraft?.graphEdges || []);
  const [isGenerating, setIsGenerating] = useState(false);
  const [message, setMessage] = useState("");
  const [selectedNodeId, setSelectedNodeId] = useState("");
  const [isConnectMode, setIsConnectMode] = useState(false);
  const [studyNodeId, setStudyNodeId] = useState("");

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId),
    [nodes, selectedNodeId],
  );
  const studyNode = useMemo(
    () => nodes.find((node) => node.id === studyNodeId),
    [nodes, studyNodeId],
  );
  const stats = useMemo(() => getPlanStats(nodes), [nodes]);

  const onNodesChange = useCallback(
    (changes) => {
      setNodes((items) => {
        const nextNodes = applyNodeChanges(changes, items);
        persistDraft(title, summary, nextNodes, graphEdges);
        return nextNodes;
      });
    },
    [graphEdges, summary, title],
  );

  const onEdgesChange = useCallback(
    (changes) => {
      const removedIds = new Set(
        changes.filter((change) => change.type === "remove").map((change) => change.id),
      );
      if (!removedIds.size) return;
      const removedViewEdges = applyFlowLayout(nodes, graphEdges).edges.filter((edge) =>
        removedIds.has(edge.id),
      );
      setGraphEdges((items) => {
        const nextEdges = items.filter(
          (edge) =>
            !removedIds.has(edge.id) &&
            !removedViewEdges.some(
              (removedEdge) => removedEdge.source === edge.source && removedEdge.target === edge.target,
            ),
        );
        persistDraft(title, summary, nodes, nextEdges);
        return nextEdges;
      });
    },
    [graphEdges, nodes, summary, title],
  );

  const onConnect = useCallback(
    (connection) => {
      setGraphEdges((items) => {
        const nextEdges = addEdge(
          {
            ...connection,
            id: `edge-${connection.source}-${connection.target}-${Date.now()}`,
            type: "smoothstep",
          },
          items,
        );
        persistDraft(title, summary, nodes, nextEdges);
        return nextEdges;
      });
    },
    [nodes, summary, title],
  );

  const flowNodes = useMemo(() => nodes, [nodes]);
  const flowEdges = useMemo(() => applyFlowLayout(nodes, graphEdges).edges, [graphEdges, nodes]);

  async function generateDraft() {
    if (!prompt.trim()) {
      setMessage("先输入一个学习目标。");
      return;
    }

    setIsGenerating(true);
    setMessage("");
    try {
      const response = await fetch("/api/generate-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal: prompt,
          durationDays: EMPTY_FORM.durationDays,
          dailyMinutes: EMPTY_FORM.dailyMinutes,
          preference: EMPTY_FORM.preference,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "生成失败");
      const next = toFlowDraft(payload);
      setTitle(payload.title);
      setSummary(payload.summary);
      setNodes(next.nodes);
      setGraphEdges(next.graphEdges);
      setSelectedNodeId(next.nodes[0]?.id || "");
      persistDraft(payload.title, payload.summary, next.nodes, next.graphEdges);
      setMessage("已生成计划草稿。");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setIsGenerating(false);
    }
  }

  function persistDraft(draftTitle, draftSummary, draftNodes, draftEdges) {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(toProjectDraft(draftTitle, draftSummary, draftNodes, draftEdges, prompt)),
    );
  }

  function exportProject() {
    const project = toProjectDraft(title, summary, nodes, graphEdges, prompt);
    const blob = new Blob([JSON.stringify(project, null, 2)], {
      type: "application/json",
    });
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
      setMessage("已导入 project。");
    } catch (error) {
      setMessage(`导入失败：${error.message}`);
    } finally {
      event.target.value = "";
    }
  }

  function updateSelectedNode(field, value) {
    const nextNodes = nodes.map((node) =>
      node.id === selectedNodeId
        ? {
            ...node,
            data: {
              ...node.data,
              [field]: field === "estimated_minutes" ? Number(value) || 0 : value,
            },
          }
        : node,
    );
    setNodes(nextNodes);
    persistDraft(title, summary, nextNodes, graphEdges);
  }

  function addNode() {
    const parentNode = selectedNode || nodes[0];
    const id = `node-${Date.now()}`;
    const nextNode = {
      id,
      type: "planNode",
      position: parentNode
        ? { x: parentNode.position.x, y: parentNode.position.y + 170 }
        : { x: 0, y: 120 },
      data: {
        title: "新节点",
        kind: "task",
        description: "",
        estimated_minutes: 25,
        group: parentNode?.data?.group || "",
        status: "not_started",
        learningNotes: "",
      },
    };
    const nextNodes = [...nodes, nextNode];
    const nextEdges = parentNode
      ? [
          ...graphEdges,
          {
            id: `edge-${parentNode.id}-${id}`,
            source: parentNode.id,
            target: id,
            sourceHandle: "bottom",
            targetHandle: "top",
            type: "smoothstep",
            className: "branch-edge",
          },
        ]
      : graphEdges;
    setNodes(nextNodes);
    setGraphEdges(nextEdges);
    setSelectedNodeId(id);
    persistDraft(title, summary, nextNodes, nextEdges);
  }

  function deleteSelectedNode() {
    if (!selectedNodeId) return;
    const nextNodes = nodes.filter((node) => node.id !== selectedNodeId);
    const nextEdges = graphEdges.filter(
      (edge) => edge.source !== selectedNodeId && edge.target !== selectedNodeId,
    );
    setNodes(nextNodes);
    setGraphEdges(nextEdges);
    setSelectedNodeId("");
    persistDraft(title, summary, nextNodes, nextEdges);
  }

  function relayoutGraph() {
    const next = applyFlowLayout(nodes, graphEdges);
    setNodes(next.nodes);
    persistDraft(title, summary, next.nodes, graphEdges);
  }

  return (
    <main className="workspace">
      <nav className="app-toolbar">
        <div className="brand-lockup">
          <span>OpenKeri</span>
          <strong>Plan Studio</strong>
        </div>
        <div className="toolbar-title">
          <strong>{title}</strong>
          <span>{nodes.length || 0} 节点 · {stats.phaseCount} 阶段 · {stats.totalMinutes} min</span>
        </div>
        <div className="toolbar-actions">
          <button type="button" onClick={addNode}>
            新增
          </button>
          <button type="button" disabled={!selectedNodeId} onClick={deleteSelectedNode}>
            删除
          </button>
          <button
            type="button"
            className={isConnectMode ? "active" : ""}
            onClick={() => setIsConnectMode((value) => !value)}
          >
            连线
          </button>
          <button type="button" onClick={relayoutGraph}>
            布局
          </button>
          <button type="button" onClick={() => importInputRef.current?.click()}>
            导入
          </button>
          <button type="button" onClick={exportProject}>
            导出
          </button>
        </div>
      </nav>
      <input
        ref={importInputRef}
        className="project-import-input"
        type="file"
        accept="application/json,.json"
        onChange={importProject}
      />

      <section className="canvas-panel">
        <ReactFlowProvider>
          <ReactFlow
            nodes={flowNodes}
            edges={flowEdges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
            fitView
            nodesDraggable
            nodesConnectable={isConnectMode}
            elementsSelectable
            defaultEdgeOptions={{
              type: "smoothstep",
              style: {
                strokeWidth: 3.4,
                stroke: "rgba(190, 236, 178, 0.9)",
              },
              labelBgPadding: [8, 6],
              labelBgStyle: { fill: "rgba(18, 22, 18, 0.82)", fillOpacity: 0.92 },
              labelStyle: {
                fill: "#ecffe6",
                fontWeight: 700,
                fontSize: 13,
              },
            }}
            fitViewOptions={{ padding: 0.16, minZoom: 0.18, maxZoom: 1.45 }}
          >
            <Background gap={22} size={1.5} color="#4b4b4f" />
          </ReactFlow>
        </ReactFlowProvider>
        {!nodes.length ? (
          <div className="empty-canvas">
            <strong>创建一个学习计划图</strong>
            <span>在底部输入目标，生成后可以拖动、连线和编辑节点。</span>
          </div>
        ) : null}
        {isGenerating ? <div className="loading-mask">正在生成计划结构...</div> : null}
      </section>

      {selectedNode ? (
        <aside className="node-panel">
          <div className="node-panel-header">
            <div>
              <span>{nodeKindLabel(selectedNode.data.kind)}节点</span>
              <strong>{selectedNode.data.title}</strong>
            </div>
            <button type="button" onClick={() => setSelectedNodeId("")}>
              ×
            </button>
          </div>

          <label>
            标题
            <input
              value={selectedNode.data.title || ""}
              onChange={(event) => updateSelectedNode("title", event.target.value)}
            />
          </label>

          <div className="panel-grid">
            <label>
              类型
              <select
                value={selectedNode.data.kind || "task"}
                onChange={(event) => updateSelectedNode("kind", event.target.value)}
              >
                <option value="goal">目标</option>
                <option value="phase">阶段</option>
                <option value="concept">概念</option>
                <option value="task">任务</option>
                <option value="practice">练习</option>
                <option value="review">复盘</option>
                <option value="project">项目</option>
                <option value="checkpoint">检查</option>
                <option value="resource">资源</option>
              </select>
            </label>
            <label>
              时间
              <input
                type="number"
                min="0"
                value={selectedNode.data.estimated_minutes || 0}
                onChange={(event) => updateSelectedNode("estimated_minutes", event.target.value)}
              />
            </label>
          </div>

          <label>
            状态
            <select
              value={selectedNode.data.status || "not_started"}
              onChange={(event) => updateSelectedNode("status", event.target.value)}
            >
              <option value="not_started">未开始</option>
              <option value="in_progress">进行中</option>
              <option value="done">已完成</option>
            </select>
          </label>

          <label>
            分组
            <input
              value={selectedNode.data.group || ""}
              onChange={(event) => updateSelectedNode("group", event.target.value)}
            />
          </label>

          <label>
            说明
            <textarea
              rows={6}
              value={selectedNode.data.description || ""}
              onChange={(event) => updateSelectedNode("description", event.target.value)}
            />
          </label>

          <button
            className="study-entry-button"
            type="button"
            onClick={() => setStudyNodeId(selectedNode.id)}
          >
            进入学习
          </button>
        </aside>
      ) : null}

      {studyNode ? (
        <section className="study-page">
          <div className="study-shell">
            <header className="study-header">
              <button type="button" onClick={() => setStudyNodeId("")}>
                返回计划图
              </button>
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

      <section className="composer">
        <input
          value={prompt}
          placeholder="What would you like to create?"
          onChange={(event) => setPrompt(event.target.value)}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
              generateDraft();
            }
          }}
        />
        <div className="composer-bottom">
          <span>⌘ Enter 生成</span>
          <button className="send-button" onClick={generateDraft} disabled={isGenerating}>
            ↑
          </button>
        </div>
        {message ? <p className="message">{message}</p> : null}
      </section>
    </main>
  );

  function updateStudyNode(field, value) {
    const nextNodes = nodes.map((node) =>
      node.id === studyNodeId
        ? {
            ...node,
            data: {
              ...node.data,
              [field]: value,
            },
          }
        : node,
    );
    setNodes(nextNodes);
    persistDraft(title, summary, nextNodes, graphEdges);
  }
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
  return value
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "learning-project";
}

function toFlowDraft(draft) {
  const nodes = draft.nodes.map((node) => ({
    id: node.id,
    type: "planNode",
    data: {
      title: node.title,
      kind: node.kind,
      description: node.description,
      estimated_minutes: node.estimated_minutes,
      group: node.group || "",
      status: node.status || "not_started",
      learningNotes: node.learningNotes || "",
    },
  }));

  const graphEdges = draft.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.label || "",
    type: "smoothstep",
  }));
  const layout = applyFlowLayout(nodes, graphEdges);

  return {
    nodes: layout.nodes,
    graphEdges,
  };
}

function restoreFlowDraftFromStorage(draft) {
  const draftNodes = draft.nodes?.map((node) => ({
    id: node.id,
    type: "planNode",
    data: {
      title: node.data?.title || node.title,
      kind: node.data?.kind || node.kind,
      description: node.data?.description || node.description,
      estimated_minutes: node.data?.estimated_minutes || node.estimated_minutes || 0,
      group: node.data?.group || node.group || "",
      status: node.data?.status || node.status || "not_started",
      learningNotes: node.data?.learningNotes || node.learningNotes || "",
    },
  }));

  const sourceEdges = draft.graphEdges || draft.edges || [];
  const draftEdges = sourceEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.label || "",
    type: "smoothstep",
  }));

  if (!draftNodes?.length || !draftEdges?.length) {
    return { nodes: [], graphEdges: [] };
  }
  const layout = applyFlowLayout(draftNodes, draftEdges);

  return {
    nodes: layout.nodes,
    graphEdges: draftEdges,
  };
}

function applyFlowLayout(nodes, edges) {
  const parentsByTarget = new Map();
  const childrenBySource = new Map();
  const indegree = new Map(nodes.map((node) => [node.id, 0]));

  for (const edge of edges) {
    if (!childrenBySource.has(edge.source)) childrenBySource.set(edge.source, []);
    if (!parentsByTarget.has(edge.target)) parentsByTarget.set(edge.target, []);
    childrenBySource.get(edge.source).push(edge.target);
    parentsByTarget.get(edge.target).push(edge.source);
    indegree.set(edge.target, (indegree.get(edge.target) || 0) + 1);
  }

  const depthById = getDepthById(nodes, childrenBySource, indegree);
  const spineNodes = nodes
    .filter((node) => isRoadmapSpineNode(node))
    .sort((a, b) => {
      const depthDiff = (depthById.get(a.id) ?? 0) - (depthById.get(b.id) ?? 0);
      return depthDiff || nodes.indexOf(a) - nodes.indexOf(b);
    });

  const mainNodes = spineNodes.length >= 2 ? spineNodes : nodes.slice(0, Math.min(nodes.length, 5));
  const mainIndexById = new Map(mainNodes.map((node, index) => [node.id, index]));
  const branchBuckets = new Map(mainNodes.map((node) => [node.id, []]));

  for (const node of nodes) {
    if (mainIndexById.has(node.id)) continue;
    const ownerId = findNearestMainParent(node.id, parentsByTarget, mainIndexById);
    const fallbackId = mainNodes[Math.min(mainNodes.length - 1, Math.max(0, depthById.get(node.id) ?? 0))]?.id;
    const bucketId = ownerId || fallbackId || mainNodes[0]?.id;
    if (!branchBuckets.has(bucketId)) branchBuckets.set(bucketId, []);
    branchBuckets.get(bucketId).push(node);
  }

  const positionedMainNodes = mainNodes.map((node, index) => ({
    ...node,
    data: { ...node.data, layoutRole: "spine", orderIndex: index + 1 },
    position: {
      x: index * ROADMAP_COLUMN_GAP,
      y: 120,
    },
  }));

  const positionedBranchNodes = [];
  const displayEdges = [];

  for (let index = 0; index < mainNodes.length - 1; index += 1) {
    const source = mainNodes[index];
    const target = mainNodes[index + 1];
    displayEdges.push({
      id: `roadmap-main-${source.id}-${target.id}`,
      source: source.id,
      target: target.id,
      sourceHandle: "right",
      targetHandle: "left",
      type: "smoothstep",
      className: "main-edge",
    });
  }

  for (const [mainId, branchNodes] of branchBuckets.entries()) {
    const mainIndex = mainIndexById.get(mainId) ?? 0;
    const x = mainIndex * ROADMAP_COLUMN_GAP;
    branchNodes.forEach((node, index) => {
      const sideOffset = branchNodes.length > 3 && index % 2 ? 260 : 0;
      positionedBranchNodes.push({
        ...node,
        data: { ...node.data, layoutRole: "branch" },
        position: {
          x: x + sideOffset,
          y: 120 + ROADMAP_BRANCH_START_Y + Math.floor(index / 2) * ROADMAP_BRANCH_GAP,
        },
      });
      displayEdges.push({
        id: `roadmap-branch-${mainId}-${node.id}`,
        source: mainId,
        target: node.id,
        sourceHandle: "bottom",
        targetHandle: "top",
        type: "smoothstep",
        className: "branch-edge",
      });
    });
  }

  return {
    nodes: centeredFlowLayout([...positionedMainNodes, ...positionedBranchNodes]),
    edges: displayEdges,
  };
}

function getDepthById(nodes, childrenBySource, indegree) {
  const depthById = new Map();
  const queue = nodes
    .filter((node) => (indegree.get(node.id) || 0) === 0)
    .map((node) => node.id);

  if (!queue.length) {
    nodes.forEach((node, index) => depthById.set(node.id, index));
    return depthById;
  }

  queue.forEach((nodeId) => depthById.set(nodeId, 0));
  while (queue.length) {
    const nodeId = queue.shift();
    const nextDepth = (depthById.get(nodeId) ?? 0) + 1;
    for (const childId of childrenBySource.get(nodeId) || []) {
      if (depthById.get(childId) === undefined || nextDepth < depthById.get(childId)) {
        depthById.set(childId, nextDepth);
        queue.push(childId);
      }
    }
  }

  nodes.forEach((node) => {
    if (!depthById.has(node.id)) depthById.set(node.id, 0);
  });
  return depthById;
}

function findNearestMainParent(nodeId, parentsByTarget, mainIndexById) {
  const seen = new Set();
  const queue = [...(parentsByTarget.get(nodeId) || [])];
  while (queue.length) {
    const parentId = queue.shift();
    if (seen.has(parentId)) continue;
    seen.add(parentId);
    if (mainIndexById.has(parentId)) return parentId;
    queue.push(...(parentsByTarget.get(parentId) || []));
  }
  return null;
}

function isRoadmapSpineNode(node) {
  return ["goal", "phase", "project", "checkpoint", "review"].includes(node.data?.kind);
}

function centeredFlowLayout(nodes) {
  if (!nodes.length) return nodes;
  const minX = Math.min(...nodes.map((node) => node.position.x));
  const maxX = Math.max(...nodes.map((node) => node.position.x));
  if (maxX - minX < 420) return nodes;
  const shift = -minX - (maxX - minX) / 2;

  return nodes.map((node) => ({
    ...node,
    position: {
      ...node.position,
      x: node.position.x + shift,
    },
  }));
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
  return (
    {
      goal: "目标",
      phase: "阶段",
      concept: "概念",
      task: "任务",
      practice: "练习",
      review: "复盘",
      project: "项目",
      checkpoint: "检查",
      resource: "资源",
    }[kind] || "节点"
  );
}

function nodeStatusLabel(status) {
  return (
    {
      not_started: "未开始",
      in_progress: "进行中",
      done: "已完成",
    }[status] || "未开始"
  );
}

function getPlanStats(nodes) {
  return nodes.reduce(
    (acc, node) => {
      if (node.data?.kind === "phase") acc.phaseCount += 1;
      acc.totalMinutes += Number(node.data?.estimated_minutes || 0);
      return acc;
    },
    { phaseCount: 0, totalMinutes: 0 },
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
