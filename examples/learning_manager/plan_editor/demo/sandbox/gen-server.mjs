// gen-server.mjs —— 决策词元的「带栏杆的动态生成」后端(零依赖,Node 18+)
//
//   学习者在一个真实设计决策上做了选择 → 这里按他的选择,现场生成接下来的剧情。
//   栏杆三道:① 受约束的 system prompt(教法铁律)② structured outputs(LLM 只产出
//   数据,填进固定 JSON 结构,渲染器写死长相,画不崩)③ 没 API key 时回退到预制岔路。
//
//   启动:ANTHROPIC_API_KEY=sk-ant-... node demo/sandbox/gen-server.mjs   → :5176
//   没 key 也能启动,只是返回预制岔路(前端照样能演示形态)。

import http from "node:http";

const PORT = 5176;
const KEY = process.env.ANTHROPIC_API_KEY || "";
const MODEL = "claude-opus-4-8";

// 结构化输出的 schema —— 这就是「栏杆」:LLM 只能往这些格子里填文字,变不出别的花样。
const SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["headline", "beats"],
  properties: {
    headline: { type: "string" },
    beats: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["kind", "title", "text"],
        properties: {
          kind: { type: "string", enum: ["narrative", "wall", "reveal", "aside"] },
          title: { type: "string" },
          text: { type: "string" },
        },
      },
    },
  },
};

const SYSTEM = `你是「造核」OS 学习课的剧情生成器。这是一篇「故事性编程」的可交互文章(不是 chatbot),
第 4 章「让 CPU 轮流干活」(进程与调度)。学习者刚在一个真实设计决策上做了选择,你要顺着他的选择,
动态生成接下来一小段剧情。

铁律(必须守住):
1. 先撞墙再揭晓 —— 学习者选了哪个方案,就让他亲历那个方案的代价、亲手撞到它的墙;不要干列对比表、
   不要一上来就说教。取舍要从他走的这条路里长出来。
2. 承重墙 vs 黑盒 —— 核心机制讲透(进程=被保存的现场、切换、调度);寄存器汇编这类水管件当黑盒带过。
3. 中文、口语化,像在跟一个初学者讲故事;每一拍简短(1-3 句)。
4. 你只产出数据,填进给定的 JSON 结构;不写 HTML、不碰样式。

每一拍的 kind:
- narrative:推进剧情的叙述。
- wall:撞墙时刻(亲历这个选择的代价/失败)。title 是一句戏剧性的大字。
- reveal:揭晓 —— 撞墙之后点破机制 / 引出下一个方案。
- aside:旁注(比喻 / 坑 / 提示)。

生成 4~6 拍,至少包含一个 wall 和一个 reveal。`;

const BRANCH = {
  coop: "合作式调度(谁跑完一段、自觉调用 yield 让出 CPU)",
  preempt: "抢占式调度(定时器中断到点,强行把 CPU 从当前进程手里夺走)",
};

// 没 key 时的预制岔路(让 demo 在没接 LLM 时也能演形态)
const CANNED = {
  coop: { headline: "你选了合作式 —— 先尝甜头,再撞墙", beats: [
    { kind: "narrative", title: "先跑起来", text: "你让每个进程跑完自己一段,就自觉调用 yield 让位。代码简单得不可思议 —— 两个程序乖乖交替,屏幕吐出 ABABAB,你笑了。" },
    { kind: "wall", title: "程序 A 不让位了 —— B 再也没醒过来", text: "你写的程序 A 进了个死循环,从不调用 yield。合作式全靠自觉,A 不让,调度器毫无办法。B 被永远饿死,屏幕停在 AAAA…" },
    { kind: "reveal", title: "自觉靠不住", text: "问题不在 A 写错了 —— 而在「让不让位」这件事,绝不能交给进程自己决定。你需要一个不讲情面的力量,到点就强行收回 CPU。这就是抢占。" },
    { kind: "aside", title: "提示", text: "几乎所有真实操作系统都不用纯合作式 —— 一个流氓程序就能冻死整机。但先撞这堵墙,你才真懂抢占为什么值得那份复杂。" },
  ] },
  preempt: { headline: "你选了抢占式 —— 想得超前,但先还债", beats: [
    { kind: "narrative", title: "请定时器当裁判", text: "你不信任进程自觉,直接上定时器中断:每隔一小段,硬把 CPU 从当前进程手里夺走,交给下一个。公平,谁也别想霸占。" },
    { kind: "wall", title: "切回来时,A 现场全乱了", text: "定时器随时打断 A —— 可能正算到一半。你没把 A 的寄存器、栈完整存下来就切走;轮回 A 时,它从一个错乱的现场继续,当场崩。" },
    { kind: "reveal", title: "抢占的代价:现场必须存得干净", text: "抢占强大,但它要求你在任意一刻都能把一个进程的完整现场存下、再原样复原 —— 这正是上一章 trap 那块肌肉。抢占=随时存现场→换人→复现场。" },
    { kind: "aside", title: "比喻", text: "合作式像同事自觉轮班,抢占式像有个领班拿着秒表强制换岗 —— 公平,但换岗那一下,必须把每个人手头的活原封不动接管过来。" },
  ] },
};

async function generate(choice) {
  const desc = BRANCH[choice] || BRANCH.coop;
  if (!KEY) return { ...CANNED[choice] || CANNED.coop, _mode: "canned" };
  const body = {
    model: MODEL,
    max_tokens: 2000,
    system: SYSTEM,
    messages: [{ role: "user", content:
      `决策点:两个程序在一颗 CPU 上轮流跑,谁来决定何时把 CPU 切走?\n学习者选了:【${desc}】。\n请按铁律,生成他选这个之后亲历的剧情(先让他撞到这个选择的墙,再揭晓)。` }],
    output_config: { format: { type: "json_schema", schema: SCHEMA } },
  };
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error("anthropic " + r.status + " " + (await r.text()).slice(0, 300));
  const data = await r.json();
  if (data.stop_reason === "refusal") throw new Error("refused");
  const txt = (data.content || []).find((b) => b.type === "text")?.text || "{}";
  return { ...JSON.parse(txt), _mode: "live" };
}

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "content-type", "Access-Control-Allow-Methods": "POST,OPTIONS" };

http.createServer((req, res) => {
  if (req.method === "OPTIONS") { res.writeHead(204, CORS); return res.end(); }
  if (req.method === "POST" && req.url === "/api/decide") {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", async () => {
      try {
        const { choice } = JSON.parse(body || "{}");
        const out = await generate(choice === "preempt" ? "preempt" : "coop");
        res.writeHead(200, { ...CORS, "content-type": "application/json" });
        res.end(JSON.stringify(out));
      } catch (e) {
        res.writeHead(500, { ...CORS, "content-type": "application/json" });
        res.end(JSON.stringify({ error: String(e.message || e) }));
      }
    });
    return;
  }
  res.writeHead(404, CORS); res.end("not found");
}).listen(PORT, () => {
  console.log(`gen-server :${PORT}  ·  模式: ${KEY ? "LIVE(真接 Claude " + MODEL + ")" : "CANNED(没 ANTHROPIC_API_KEY,返回预制岔路)"}`);
});
