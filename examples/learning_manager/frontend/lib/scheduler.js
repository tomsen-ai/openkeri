(function () {
  const { currentNode, findStage } = window.OpenKeriPlanner;

  function buildTodayQueue(state, limit = 4) {
    const projects = orderProjects(state);
    const reviewItems = [];
    const mainItems = [];

    projects.forEach((project) => {
      project.stages.forEach((stage) => {
        stage.nodes.forEach((node) => {
          if (node.status === "review_due") {
            reviewItems.push(toQueueItem(project, stage, node, "复习"));
          }
        });
      });

      const node = currentNode(project);
      if (node) {
        mainItems.push(toQueueItem(project, findStage(project, node.stageId), node, "推进"));
      }
    });

    return [...reviewItems, ...mainItems].slice(0, limit);
  }

  function orderProjects(state) {
    const active = state.projects.find((project) => project.id === state.activeProjectId);
    const rest = state.projects.filter((project) => project.id !== state.activeProjectId);
    return active ? [active, ...rest] : state.projects;
  }

  function toQueueItem(project, stage, node, reason) {
    return {
      project,
      stage,
      node,
      reason,
      progress: window.OpenKeriPlanner.projectProgress(project),
    };
  }

  window.OpenKeriScheduler = { buildTodayQueue };
})();
