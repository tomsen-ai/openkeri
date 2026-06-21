// run-server.mjs —— 本地真沙箱:真编译 + 真跑 qemu,把内核输出抓回来(按章节)
//
//   纯本地、零依赖(只用 Node 内置模块 + 你本机的 clang/lld/qemu)。开源友好。
//   启动:node demo/sandbox/run-server.mjs   → :5177
//   POST /api/run  body: { chapter: 1|2, answers?: { <slot>: "<学习者写的那行>" } }
//   返回: { ok, console, raw, expect, stage?, stderr? }

import http from "node:http";
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, cpSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = 5177;
const TIMEOUT_MS = 2500;

// 每章一个真实工程:目录、预期输出(用来判对错)、承重墙槽位(标记 + 类型)
const PROJECTS = {
  1: { dir: "kernel-ch1", expect: "Hello from my kernel!",
       slots: { boot: { marker: "BOOT_SP", kind: "asm" }, print: { marker: "PRINT", kind: "stmt" } } },
  2: { dir: "kernel-ch2", expect: "p2=0x80205000",
       slots: { printf: { marker: "PRINTF", kind: "stmt" }, alloc: { marker: "ALLOC", kind: "stmt" }, panic: { marker: "PANIC", kind: "stmt" } } },
};

function findClang() {
  for (const c of ["/opt/homebrew/opt/llvm/bin/clang", "clang", "/usr/bin/clang"]) {
    try {
      const r = spawnSync(c, ["--print-targets"], { encoding: "utf8" });
      if (r.stdout && /riscv/i.test(r.stdout)) return c;
    } catch (_) {}
  }
  return null;
}
const CLANG = findClang();

// —— agent 驱动:真派给 kimi 去编辑工作区文件 ——
const KIMI = (process.env.HOME || "") + "/.kimi-code/bin/kimi";
const WS = {
  1: { dir: join(__dirname, "workspace-ch1"), file: "kernel.c", slots: {
    boot:  { marker: "BOOT_SP", placeholder: `        " "  /* {{BOOT_SP}}  TODO: 把 sp 指到栈顶 __stack_top */`,
             desc: "set the stack pointer to the top of the stack via an inline-asm string literal",
             fmt: (v) => `"${v.replace(/^"|"$/g, "").replace(/\\n$/, "")}\\n"` },
    print: { marker: "PRINT", placeholder: `        ;  /* {{PRINT}}  TODO: 把第 i 个字符 s[i] 送出去 */`,
             desc: "send the i-th character s[i] to putchar inside the loop",
             fmt: (v) => v.trim().replace(/;$/, "") + ";" },
  } },
};

function runKimi(cwd, prompt) {
  return new Promise((resolve) => {
    const p = spawn(KIMI, ["-p", prompt], { cwd, stdio: ["ignore", "pipe", "pipe"] });
    let out = "", err = "";
    p.stdout.on("data", (d) => (out += d));
    p.stderr.on("data", (d) => (err += d));
    const t = setTimeout(() => { p.kill("SIGKILL"); resolve({ code: -1, out, err: err + "\n[timeout 90s]" }); }, 90000);
    p.on("close", (code) => { clearTimeout(t); resolve({ code, out, err }); });
    p.on("error", (e) => { clearTimeout(t); resolve({ code: -1, out, err: String(e.message) }); });
  });
}

async function agentHandle(body) {
  const ws = WS[body.chapter || 1];
  if (!ws) return { ok: false, error: "本章没有 workspace" };
  const slot = ws.slots[body.slot];
  if (!slot) return { ok: false, error: "未知承重墙 " + body.slot };
  const path = join(ws.dir, ws.file);
  const value = String(body.value || "").trim();
  const code = slot.fmt(value);
  // 先把这行还原成 TODO,好让 agent 真去"填"
  let src = readFileSync(path, "utf8");
  src = src.replace(new RegExp(".*\\{\\{" + slot.marker + "\\}\\}.*"), slot.placeholder);
  writeFileSync(path, src);
  const prompt = `In kernel.c, the line containing the marker {{${slot.marker}}} is a TODO placeholder. Replace ONLY that single line so it will ${slot.desc}. The exact code to place there is: ${code}   (keep the // {{${slot.marker}}} marker comment on that line). Change nothing else in the file, then reply DONE.`;
  const t0 = Date.now();
  const r = await runKimi(ws.dir, prompt);
  const ms = ((Date.now() - t0) / 1000).toFixed(1);
  const after = readFileSync(path, "utf8");
  const line = (after.split(/\r?\n/).find((l) => l.includes("{{" + slot.marker + "}}")) || "").trim();
  const norm = (s) => s.replace(/[";]/g, "").replace(/\\n/g, "").replace(/\s/g, "");
  const ok = r.code === 0 && norm(line).includes(norm(value));
  return { ok, ms, file: ws.file, marker: slot.marker, line, content: after };
}

function applyAnswers(dir, chap, answers = {}) {
  const p = join(dir, "kernel.c");
  let src = readFileSync(p, "utf8");
  for (const [key, ans] of Object.entries(answers)) {
    const slot = chap.slots[key];
    if (!slot || !ans || !String(ans).trim()) continue;
    const re = new RegExp(".*\\{\\{" + slot.marker + "\\}\\}.*");
    let v = String(ans).trim();
    if (slot.kind === "asm") { if (!v.includes('"')) v = `"${v}\\n"`; }
    else { if (!v.endsWith(";")) v = v + ";"; }
    src = src.replace(re, `        ${v} // {{${slot.marker}}}`);
  }
  writeFileSync(p, src);
}

function build(dir) {
  const r = spawnSync(CLANG, [
    "--target=riscv32-unknown-elf", "-march=rv32imac", "-mabi=ilp32",
    "-ffreestanding", "-nostdlib", "-fno-stack-protector", "-fno-builtin",
    "-fuse-ld=lld", "-Wl,-T," + join(dir, "kernel.ld"),
    "-o", join(dir, "kernel.elf"), join(dir, "kernel.c"),
  ], { encoding: "utf8" });
  return { ok: r.status === 0, stderr: r.stderr || "" };
}

function run(dir) {
  return new Promise((resolve) => {
    const q = spawn("qemu-system-riscv32", [
      "-machine", "virt", "-bios", "default", "-nographic", "--no-reboot",
      "-kernel", join(dir, "kernel.elf"),
    ]);
    let out = "";
    q.stdout.on("data", (d) => (out += d));
    q.stderr.on("data", (d) => (out += d));
    const t = setTimeout(() => q.kill("SIGKILL"), TIMEOUT_MS);
    q.on("close", () => { clearTimeout(t); resolve(out); });
    q.on("error", (e) => { clearTimeout(t); resolve("qemu error: " + e.message); });
  });
}

// 去掉 OpenSBI 横幅,只留我们内核打的
function cleanConsole(raw) {
  return raw.split(/\r?\n/)
    .map((l) => l.replace(/\s+$/, ""))
    .filter((l) => l.trim())
    .filter((l) => !/\s:\s/.test(l))                 // OpenSBI 的 "key : value" 行
    .filter((l) => /[A-Za-z0-9]{3,}/.test(l))         // 有实义内容(滤掉 OpenSBI 的 ASCII logo)
    .filter((l) => !/^(OpenSBI|Platform|Firmware|Runtime|Domain|Boot HART|Standard|MIDELEG|MEDELEG|PMP|Region|Hart|Next Address)/i.test(l))
    .join("\n").trim();
}

async function handle(body) {
  if (!CLANG) return { ok: false, error: "本机找不到带 riscv 后端的 clang(试试 brew install llvm)" };
  const chap = PROJECTS[body.chapter || 1];
  if (!chap) return { ok: false, error: "未知章节 " + body.chapter };
  const dir = mkdtempSync(join(tmpdir(), "kfs-"));
  cpSync(join(__dirname, chap.dir), dir, { recursive: true });
  applyAnswers(dir, chap, body.answers || {});
  const b = build(dir);
  if (!b.ok) return { ok: false, stage: "build", stderr: b.stderr, expect: chap.expect };
  const raw = await run(dir);
  return { ok: true, console: cleanConsole(raw), raw, expect: chap.expect };
}

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "content-type", "Access-Control-Allow-Methods": "POST,OPTIONS" };
http.createServer((req, res) => {
  if (req.method === "OPTIONS") { res.writeHead(204, CORS); return res.end(); }
  if (req.method === "POST" && req.url === "/api/run") {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", async () => {
      try {
        const out = await handle(JSON.parse(body || "{}"));
        res.writeHead(200, { ...CORS, "content-type": "application/json" });
        res.end(JSON.stringify(out));
      } catch (e) {
        res.writeHead(500, { ...CORS, "content-type": "application/json" });
        res.end(JSON.stringify({ ok: false, error: String(e.message || e) }));
      }
    });
    return;
  }
  if (req.method === "POST" && req.url === "/api/agent") {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", async () => {
      try {
        const out = await agentHandle(JSON.parse(body || "{}"));
        res.writeHead(200, { ...CORS, "content-type": "application/json" });
        res.end(JSON.stringify(out));
      } catch (e) {
        res.writeHead(500, { ...CORS, "content-type": "application/json" });
        res.end(JSON.stringify({ ok: false, error: String(e.message || e) }));
      }
    });
    return;
  }
  res.writeHead(404, CORS); res.end("not found");
}).listen(PORT, () => {
  console.log(`run-server :${PORT}  ·  clang: ${CLANG || "(未找到 riscv clang)"}  ·  chapters: ${Object.keys(PROJECTS).join(",")}`);
});
