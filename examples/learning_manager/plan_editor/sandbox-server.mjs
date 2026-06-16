// 极简本地沙箱后端:目录 / 读文件 / 存文件 / 真跑 run.sh 并流式吐真实输出。
// 用法:node sandbox-server.mjs [项目目录]   默认 = ../../../../openkeri-xv6/myos-lab
// 只用 Node 内置模块,无依赖。换项目 = 换目录参数,通用。
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(process.argv[2] || path.join(os.homedir(), "Desktop/openkeri-xv6/myos-ch1"));
const PORT = 5175;
const TEXT_EXT = new Set([".c", ".h", ".ld", ".sh", ".txt", ".md", ".s", ".S", ".cfg"]);
const RUN_TIMEOUT = 6000;

if (!fs.existsSync(ROOT)) { console.error("项目目录不存在:", ROOT); process.exit(1); }
const inside = (p) => { const r = path.resolve(ROOT, p); return r.startsWith(ROOT) ? r : null; };
const send = (res, code, type, body) => { res.writeHead(code, { "Content-Type": type, "Access-Control-Allow-Origin": "*" }); res.end(body); };

const server = http.createServer((req, res) => {
  const u = new URL(req.url, `http://localhost:${PORT}`);

  // 目录(递归,带层级;文本文件可点,二进制只显示)
  if (u.pathname === "/api/tree") {
    const SKIP = new Set(["kernel.elf", "kernel.map", ".DS_Store"]);
    const walk = (dir, rel) => fs.readdirSync(dir, { withFileTypes: true })
      .filter((d) => !d.name.startsWith(".") && !SKIP.has(d.name))
      .sort((a, b) => a.isDirectory() === b.isDirectory() ? a.name.localeCompare(b.name) : a.isDirectory() ? -1 : 1)
      .map((d) => {
        const rp = rel ? rel + "/" + d.name : d.name;
        return d.isDirectory()
          ? { name: d.name, path: rp, type: "dir", children: walk(path.join(dir, d.name), rp) }
          : { name: d.name, path: rp, type: "file", text: TEXT_EXT.has(path.extname(d.name)) };
      });
    return send(res, 200, "application/json", JSON.stringify({ root: path.basename(ROOT), tree: walk(ROOT, "") }));
  }

  // 读文件
  if (u.pathname === "/api/file") {
    const f = inside(u.searchParams.get("path") || "");
    if (!f || !fs.existsSync(f)) return send(res, 404, "text/plain", "not found");
    return send(res, 200, "text/plain; charset=utf-8", fs.readFileSync(f, "utf8"));
  }

  // 存文件
  if (u.pathname === "/api/save" && req.method === "POST") {
    let body = ""; req.on("data", (c) => (body += c));
    req.on("end", () => {
      try { const { path: p, content } = JSON.parse(body); const f = inside(p); if (!f) throw 0;
        fs.writeFileSync(f, content, "utf8"); send(res, 200, "application/json", '{"ok":true}');
      } catch { send(res, 400, "application/json", '{"ok":false}'); }
    });
    return;
  }

  // 真跑:spawn run.sh,流式回传 stdout+stderr,超时杀掉整个进程组(qemu 不会自己退)
  if (u.pathname === "/api/run" && req.method === "POST") {
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8", "Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache" });
    const child = spawn("bash", ["run.sh"], { cwd: ROOT, detached: true });
    let done = false;
    const finish = (tail) => { if (done) return; done = true; clearTimeout(timer); try { process.kill(-child.pid, "SIGTERM"); } catch {} if (tail) res.write(tail); res.end(); };
    const timer = setTimeout(() => finish("\n—— (运行已停止:qemu 持续运行,沙箱在 " + RUN_TIMEOUT / 1000 + "s 后收尾) ——\n"), RUN_TIMEOUT);
    child.stdout.on("data", (d) => res.write(d));
    child.stderr.on("data", (d) => res.write(d));
    child.on("close", () => finish());
    child.on("error", (e) => finish("\n[沙箱错误] " + e.message + "\n"));
    req.on("close", () => { if (!done) { done = true; clearTimeout(timer); try { process.kill(-child.pid, "SIGTERM"); } catch {} } });
    return;
  }

  // 静态:前端页面("/" = 路线图首页)
  const file = u.pathname === "/" ? "plan_roadmap_preview.html" : u.pathname.slice(1);
  const fp = path.join(__dirname, file);
  if (fs.existsSync(fp) && fs.statSync(fp).isFile()) {
    const ext = path.extname(fp);
    const type = ext === ".html" ? "text/html; charset=utf-8" : ext === ".mjs" || ext === ".js" ? "text/javascript" : "text/plain";
    return send(res, 200, type, fs.readFileSync(fp));
  }
  send(res, 404, "text/plain", "not found");
});

server.listen(PORT, () => {
  console.log(`\n  沙箱后端已启动`);
  console.log(`  项目目录: ${ROOT}`);
  console.log(`  打开:     http://localhost:${PORT}\n`);
});
