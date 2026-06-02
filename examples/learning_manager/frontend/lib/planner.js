(function () {
  const { PLAN_TEMPLATES } = window.OpenKeriTemplates;

  function createProject({
    goal = "新的学习目标",
    type = "custom",
    durationDays = 30,
    dailyMinutes = 25,
    id,
  } = {}) {
    const planType = PLAN_TEMPLATES[type] ? type : inferType(goal);
    const template = PLAN_TEMPLATES[planType] || PLAN_TEMPLATES.custom;
    const projectId = id || `project_${Date.now()}`;
    let order = 1;

    const stages = template.stages.map((stage, stageIndex) => {
      const stageId = `${projectId}_stage_${String(stageIndex + 1).padStart(3, "0")}`;
      return {
        id: stageId,
        title: stage.title,
        description: stage.description,
        color: template.colors[stageIndex % template.colors.length],
        nodes: stage.nodes.map(([title, nodeType, description]) => {
          const node = {
            id: `${projectId}_node_${String(order).padStart(3, "0")}`,
            title,
            type: nodeType,
            status: order === 1 ? "ready" : "locked",
            estimatedMinutes: Math.min(dailyMinutes, nodeType === "review" ? 15 : 30),
            description,
            content: buildNodeContent(title, nodeType, description),
            stageId,
            stageTitle: stage.title,
            order,
            prerequisites: order === 1 ? [] : [`${projectId}_node_${String(order - 1).padStart(3, "0")}`],
            reviewAfterDays: nodeType === "review" ? 0 : 2,
            spent: 0,
            completedAt: null,
            result: "",
          };
          order += 1;
          return node;
        }),
      };
    });

    return {
      id: projectId,
      title: template.title,
      goal,
      type: planType,
      durationDays,
      dailyMinutes,
      streak: 3,
      createdAt: new Date().toISOString(),
      stages,
      history: [
        {
          id: `${projectId}_event_001`,
          type: "project_created",
          title: "创建计划",
          detail: goal,
          createdAt: new Date().toISOString(),
        },
      ],
    };
  }

  function inferType(goal) {
    if (/算法|leetcode|面试|数据结构/i.test(goal)) return "algorithm";
    if (/英文|阅读|文章|读/i.test(goal)) return "reading";
    return "custom";
  }

  function createDefaultState() {
    return {
      version: 4,
      activeProjectId: "project_seed",
      session: { projectId: "project_seed", nodeId: "project_seed_node_001" },
      projects: [
        createProject({
          id: "project_seed",
          goal: "我想用 30 天准备算法面试",
          type: "algorithm",
          durationDays: 30,
          dailyMinutes: 25,
        }),
        createProject({
          id: "project_reading",
          goal: "我想每天读一点英文技术文章",
          type: "reading",
          durationDays: 30,
          dailyMinutes: 20,
        }),
      ],
    };
  }

  function buildNodeContent(title, type, description) {
    const action = {
      learn: "先理解概念，再看一个最小例子。",
      practice: "做一个小练习，重点观察自己卡在哪里。",
      review: "回看本阶段完成过的节点，写出一个共同模式。",
      reflection: "用自己的话复述，不追求完整。",
      checkpoint: "用限时方式完成一次小检查。",
      project: "做一个可以保存下来的小成果。",
      plan: "把范围收窄成今天能开始的一步。",
    }[type] || "完成一个小学习动作。";

    return `${description} ${action} 这一版先只放占位内容，后面再把资料、练习和 AI 辅导逐步加进来。`;
  }

  function getProjectNodes(project) {
    return project.stages.flatMap((stage) => stage.nodes);
  }

  function findProject(state, projectId) {
    return state.projects.find((project) => project.id === projectId) || state.projects[0];
  }

  function findNode(project, nodeId) {
    return getProjectNodes(project).find((node) => node.id === nodeId) || null;
  }

  function findStage(project, stageId) {
    return project.stages.find((stage) => stage.id === stageId) || project.stages[0];
  }

  function currentNode(project) {
    return (
      getProjectNodes(project).find((node) => node.status === "active") ||
      getProjectNodes(project).find((node) => node.status === "ready") ||
      null
    );
  }

  function projectProgress(project) {
    const nodes = getProjectNodes(project);
    const done = nodes.filter((node) => node.status === "done").length;
    return nodes.length ? Math.round((done / nodes.length) * 100) : 0;
  }

  function completeNode(project, nodeId, note = "") {
    const nodes = getProjectNodes(project);
    const node = nodes.find((item) => item.id === nodeId);
    if (!node || node.status === "locked") return null;

    node.status = "done";
    node.spent = node.estimatedMinutes;
    node.result = note.trim();
    node.completedAt = new Date().toISOString();

    const next = nodes.find((item) => item.order === node.order + 1);
    if (next && next.status === "locked") next.status = "ready";

    project.history.unshift({
      id: `${project.id}_event_${Date.now()}`,
      type: "node_completed",
      title: node.title,
      detail: note.trim() || "完成节点",
      nodeId: node.id,
      createdAt: new Date().toISOString(),
    });

    return { node, next };
  }

  window.OpenKeriPlanner = {
    createProject,
    createDefaultState,
    getProjectNodes,
    findProject,
    findNode,
    findStage,
    currentNode,
    projectProgress,
    completeNode,
  };
})();
