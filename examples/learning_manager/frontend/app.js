(function () {
  const {
    createProject,
    getProjectNodes,
    findProject,
    findNode,
    findStage,
    currentNode,
    projectProgress,
    completeNode,
  } = window.OpenKeriPlanner;
  const { buildTodayQueue } = window.OpenKeriScheduler;
  const { loadState, saveState } = window.OpenKeriStorage;

  let state = loadState();
  let selectedDuration = 30;
  let selectedMinutes = 25;

  function activeProject() {
    return findProject(state, state.activeProjectId);
  }

  function sessionProject() {
    return findProject(state, state.session.projectId);
  }

  function sessionNode() {
    const project = sessionProject();
    return findNode(project, state.session.nodeId) || currentNode(project);
  }

  function save() {
    saveState(state);
  }

  function showPage(pageId) {
    document.querySelectorAll(".page").forEach((page) => {
      page.classList.toggle("active", page.id === pageId);
    });
    document.querySelectorAll("[data-nav]").forEach((button) => {
      button.classList.toggle("active", button.dataset.page === pageId);
    });
    if (pageId === "projects") requestAnimationFrame(syncCourseBar);
  }

  function startSession(projectId, nodeId) {
    state.activeProjectId = projectId;
    state.session = { projectId, nodeId };
    save();
    render();
    showPage("session");
  }

  function render() {
    const project = activeProject();
    renderTodayList();
    renderSession();
    renderMap(project);
    syncCourseBar();
    renderMetrics();
  }

  function renderTodayList() {
    const list = document.getElementById("today-list");
    const items = buildTodayQueue(state);
    list.innerHTML = "";

    if (!items.length) {
      list.innerHTML = `
        <section class="card today-card primary-card">
          <span class="lesson-badge">✓</span>
          <div class="lesson">
            <p class="label">Today</p>
            <h2 class="lesson-title">都完成了</h2>
            <div class="chips"><span class="chip">休息一下</span></div>
          </div>
        </section>
      `;
      return;
    }

    items.forEach((item, index) => {
      const card = document.createElement("button");
      card.className = `card today-card ${index === 0 ? "primary-card" : ""}`;
      card.innerHTML = `
        <span class="lesson-badge">${index + 1}</span>
        <div class="lesson">
          <p class="label">${item.project.title}</p>
          <h2 class="lesson-title">${item.node.title}</h2>
          <div class="chips">
            <span class="chip">${item.node.estimatedMinutes} min</span>
            <span class="chip">${item.stage.title}</span>
            <span class="chip">${item.reason}</span>
          </div>
        </div>
        <span class="start-pill">${index === 0 ? "开始" : `${item.progress}%`}</span>
      `;
      card.addEventListener("click", () => {
        startSession(item.project.id, item.node.id);
      });
      list.appendChild(card);
    });
  }

  function renderSession() {
    const project = sessionProject();
    const node = sessionNode();

    document.getElementById("session-project").textContent = project.title;
    document.getElementById("session-title").textContent = node ? node.title : "全部完成";
    document.getElementById("session-description").textContent = node
      ? node.description
      : "这个计划已经完成。";
    document.getElementById("session-chip").textContent = node
      ? `${node.estimatedMinutes} min`
      : "done";
    document.getElementById("complete-session").disabled = !node;
    document.getElementById("session-note").value = "";

    const content = document.getElementById("session-content");
    content.innerHTML = node
      ? `<strong>占位学习内容</strong><span>${node.content}</span>`
      : `<strong>没有待完成节点</strong><span>可以创建新计划，或者回顾历史记录。</span>`;

    const steps = sessionSteps(node);
    document.getElementById("session-steps").innerHTML = steps
      .map(
        (step, index) => `
          <div class="step">
            <span class="step-dot">${index + 1}</span>${step}
          </div>
        `,
      )
      .join("");
  }

  function sessionSteps(node) {
    if (!node) return ["回顾完成记录", "选择下一个计划"];
    if (node.type === "review") return ["回看本阶段", "写一句总结", "标记完成"];
    if (node.type === "checkpoint") return ["限时完成", "记录卡点", "决定是否复习"];
    if (node.type === "reflection") return ["复述内容", "写一句理解", "标记完成"];
    return ["看简短说明", "做一个小练习", "写一句总结"];
  }

  function renderMap(project) {
    const map = document.getElementById("project-map");
    map.innerHTML = "";

    project.stages.forEach((stage, index) => {
      const section = document.createElement("section");
      section.className = "stage";
      section.dataset.stageIndex = String(index);
      section.style.setProperty("--unit-color", stage.color);
      section.innerHTML = `
        <div class="path">
          ${stage.nodes.map(renderNode).join("")}
        </div>
      `;
      map.appendChild(section);
    });

    map.querySelectorAll("[data-node-id]").forEach((button) => {
      button.addEventListener("click", () => {
        startSession(project.id, button.dataset.nodeId);
      });
    });
  }

  function renderNode(node) {
    const disabled = node.status === "locked" ? "disabled" : "";
    return `
      <button class="node-row ${node.status}" data-node-id="${node.id}" ${disabled}>
        <span class="node-icon">${nodeIcon(node.status)}</span>
        <span class="node-card">
          <strong>${node.title}</strong>
          <small>${nodeTypeLabel(node.type)} · ${node.estimatedMinutes} min</small>
        </span>
      </button>
    `;
  }

  function currentStageIndex() {
    const map = document.getElementById("project-map");
    const stages = [...map.querySelectorAll(".stage")];
    if (!stages.length) return 0;
    const marker = map.scrollTop + map.clientHeight * 0.34;
    return stages.reduce((active, stage) => {
      if (stage.offsetTop <= marker) return Number(stage.dataset.stageIndex);
      return active;
    }, 0);
  }

  function syncCourseBar() {
    const project = activeProject();
    if (!project) return;
    const stageIndex = currentStageIndex();
    const stage = project.stages[stageIndex] || project.stages[0];
    const done = stage.nodes.filter((node) => node.status === "done").length;
    const bar = document.getElementById("course-bar");
    bar.style.setProperty("--unit-color", stage.color);
    document.getElementById("course-project").textContent = project.title;
    document.getElementById("course-stage").textContent = stage.title;
    document.getElementById("course-count").textContent = `${done}/${stage.nodes.length}`;
  }

  function openProjectPicker() {
    renderProjectPicker();
    const picker = document.getElementById("project-picker");
    picker.classList.add("open");
    picker.setAttribute("aria-hidden", "false");
  }

  function closeProjectPicker() {
    const picker = document.getElementById("project-picker");
    picker.classList.remove("open");
    picker.setAttribute("aria-hidden", "true");
  }

  function renderProjectPicker() {
    const list = document.getElementById("project-choice-list");
    list.innerHTML = "";
    state.projects.forEach((project) => {
      const progress = projectProgress(project);
      const button = document.createElement("button");
      button.className = `project-choice ${
        project.id === state.activeProjectId ? "active" : ""
      }`;
      button.innerHTML = `
        <span>
          <strong>${project.title}</strong>
          <span>${project.goal}</span>
        </span>
        <span class="choice-progress" style="--p: ${progress}%">${progress}%</span>
      `;
      button.addEventListener("click", () => {
        selectProject(project.id);
      });
      list.appendChild(button);
    });
  }

  function selectProject(projectId) {
    const project = findProject(state, projectId);
    state.activeProjectId = project.id;
    state.session.projectId = project.id;
    state.session.nodeId = currentNode(project)?.id || "";
    save();
    render();
    document.getElementById("project-map").scrollTop = 0;
    closeProjectPicker();
    showPage("projects");
  }

  function renderMetrics() {
    const nodes = state.projects.flatMap(getProjectNodes);
    const done = nodes.filter((node) => node.status === "done");
    const minutes = done.reduce((sum, node) => sum + (node.spent || 0), 0);
    const streak = Math.max(...state.projects.map((project) => project.streak), 0);
    document.getElementById("metric-done").textContent = done.length;
    document.getElementById("metric-minutes").textContent = minutes;
    document.getElementById("metric-streak").textContent = streak;
    renderHistory();
  }

  function renderHistory() {
    const list = document.getElementById("recent-history");
    const events = state.projects
      .flatMap((project) => project.history.map((event) => ({ ...event, project })))
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
      .slice(0, 5);

    list.innerHTML = events
      .map(
        (event) => `
          <div class="history-item">
            <span>
              <strong>${event.title}</strong>
              ${event.project.title}
            </span>
            <span>${formatDate(event.createdAt)}</span>
          </div>
        `,
      )
      .join("");
  }

  function nodeIcon(status) {
    if (status === "done") return "✓";
    if (status === "locked") return "●";
    if (status === "review_due") return "↻";
    return "▶";
  }

  function nodeTypeLabel(type) {
    return (
      {
        learn: "概念",
        practice: "练习",
        review: "复盘",
        reflection: "输出",
        checkpoint: "检查",
        project: "项目",
        plan: "计划",
      }[type] || "节点"
    );
  }

  function completeCurrentSession() {
    const project = sessionProject();
    const node = sessionNode();
    if (!node) return;
    const note = document.getElementById("session-note").value;
    const result = completeNode(project, node.id, note);
    if (result?.next) {
      state.session.nodeId = result.next.id;
    }
    state.activeProjectId = project.id;
    save();
    render();
    showPage("today");
  }

  function createRoute() {
    const goal = document.getElementById("goal-input").value.trim();
    const type = document.getElementById("type-input").value;
    const project = createProject({
      goal: goal || "新的学习目标",
      type,
      durationDays: selectedDuration,
      dailyMinutes: selectedMinutes,
    });
    state.projects.unshift(project);
    state.activeProjectId = project.id;
    state.session = { projectId: project.id, nodeId: currentNode(project)?.id || "" };
    save();
    render();
    showPage("projects");
  }

  function formatDate(value) {
    return new Intl.DateTimeFormat("zh-CN", { month: "numeric", day: "numeric" }).format(
      new Date(value),
    );
  }

  document.querySelectorAll("[data-page]").forEach((button) => {
    button.addEventListener("click", () => showPage(button.dataset.page));
  });

  document.querySelectorAll("[data-go-create]").forEach((button) => {
    button.addEventListener("click", () => showPage("create"));
  });

  document.querySelectorAll("[data-duration]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedDuration = Number(button.dataset.duration);
      document.querySelectorAll("[data-duration]").forEach((item) => {
        item.classList.toggle("selected", item === button);
      });
    });
  });

  document.querySelectorAll("[data-minutes]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedMinutes = Number(button.dataset.minutes);
      document.querySelectorAll("[data-minutes]").forEach((item) => {
        item.classList.toggle("selected", item === button);
      });
    });
  });

  document.getElementById("complete-session").addEventListener("click", () => {
    completeCurrentSession();
  });

  document.getElementById("project-map").addEventListener("scroll", () => {
    syncCourseBar();
  });

  document.getElementById("course-bar").addEventListener("click", () => {
    openProjectPicker();
  });

  document.getElementById("close-picker").addEventListener("click", () => {
    closeProjectPicker();
  });

  document.getElementById("picker-backdrop").addEventListener("click", () => {
    closeProjectPicker();
  });

  document.getElementById("create-route").addEventListener("click", () => {
    createRoute();
  });

  render();
})();
