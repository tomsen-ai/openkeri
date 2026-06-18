/* ch1 可交互文章 · 共享内容与渲染工具
   图(FIG)/代码(CODE)/文案(DOC)直接沿用「视频版」ch1.html 的素材。
   两个文章原型(滚动版 / 行内版)都吃这一份。 */
window.CH1 = (function () {
  const AR = `<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="5" refY="4.5" orient="auto"><path d="M1,1 L8,4.5 L1,8" fill="none" stroke="#94a3b8" stroke-width="1.5"/></marker><marker id="ip" markerWidth="9" markerHeight="9" refX="5" refY="4.5" orient="auto"><path d="M1,1 L8,4.5 L1,8" fill="none" stroke="#6366f1" stroke-width="1.5"/></marker></defs>`;

  const FIG = {
    compare: () => `<svg viewBox="0 0 760 220">${AR}
      <g class="p f-l"><text x="180" y="22" text-anchor="middle" font-size="12" font-weight="700" fill="#475569">平时:你写个普通程序</text>
        <rect x="70" y="36" width="220" height="32" rx="8" fill="#fff" stroke="#e6e9f0"/><text x="180" y="57" text-anchor="middle" font-size="13">你的程序</text></g>
      <g class="p f-lhelp"><line x1="180" y1="68" x2="180" y2="90" stroke="#cbd5e1" marker-end="url(#ar)"/><rect x="56" y="92" width="248" height="34" rx="8" fill="#eef2ff" stroke="#c7d2fe"/><text x="180" y="114" text-anchor="middle" font-size="12" fill="#4f46e5">操作系统:加载 · 内存 · printf</text></g>
      <g class="p f-l"><line x1="180" y1="126" x2="180" y2="148" stroke="#cbd5e1" marker-end="url(#ar)"/><rect x="86" y="150" width="188" height="34" rx="8" fill="#dcfce7" stroke="#86efac"/><text x="180" y="172" text-anchor="middle" font-size="13" fill="#15803d">屏幕:Hello ✓</text></g>
      <line x1="380" y1="24" x2="380" y2="196" stroke="#e6e9f0" stroke-dasharray="4 4"/>
      <g class="p f-r"><text x="580" y="22" text-anchor="middle" font-size="12" font-weight="700" fill="#dc2626">现在:你写的就是操作系统</text>
        <rect x="470" y="36" width="220" height="32" rx="8" fill="#fff" stroke="#e6e9f0"/><text x="580" y="57" text-anchor="middle" font-size="13">你的程序(内核)</text></g>
      <g class="p f-rgone"><line x1="580" y1="68" x2="580" y2="90" stroke="#cbd5e1" marker-end="url(#ar)"/><rect x="456" y="92" width="248" height="34" rx="8" fill="#fee2e2" stroke="#fca5a5"/><text x="580" y="114" text-anchor="middle" font-size="12" fill="#dc2626">脚下什么都没有 —— 全靠你自己</text></g>
      <g class="p f-rq"><line x1="580" y1="126" x2="580" y2="148" stroke="#cbd5e1" marker-end="url(#ar)"/><rect x="500" y="150" width="160" height="34" rx="8" fill="#f1f5f9" stroke="#cbd5e1"/><text x="580" y="172" text-anchor="middle" font-size="13" fill="#94a3b8">屏幕:?</text></g></svg>`,
    boot: () => `<svg viewBox="0 0 760 130">${AR}
      <g class="p f-1"><rect x="20" y="44" width="120" height="44" rx="10" fill="#fff" stroke="#e6e9f0"/><text x="80" y="71" text-anchor="middle" font-size="13">上电</text></g>
      <g class="p f-2"><rect x="190" y="44" width="170" height="44" rx="10" fill="#eef2ff" stroke="#c7d2fe"/><text x="275" y="66" text-anchor="middle" font-size="13" fill="#4f46e5">固件 OpenSBI</text><text x="275" y="82" text-anchor="middle" font-size="10.5" fill="#818cf8">比你先醒</text></g>
      <g class="p f-3"><rect x="410" y="44" width="160" height="44" rx="10" fill="#fff" stroke="#e6e9f0"/><text x="490" y="66" text-anchor="middle" font-size="13">跳到约定地址</text><text x="490" y="82" text-anchor="middle" font-size="11" class="mono" fill="#475569">0x80200000</text></g>
      <g class="p f-4"><rect x="620" y="44" width="120" height="44" rx="10" fill="#dcfce7" stroke="#86efac"/><text x="680" y="71" text-anchor="middle" font-size="13" fill="#15803d">你的 boot</text></g>
      <g stroke="#cbd5e1" marker-end="url(#ar)"><line x1="140" y1="66" x2="186" y2="66"/><line x1="360" y1="66" x2="406" y2="66"/><line x1="570" y1="66" x2="616" y2="66"/></g></svg>`,
    mem: () => `<svg viewBox="0 0 600 300">${AR}
      <text x="44" y="20" class="addr" text-anchor="middle">高地址</text><line x1="44" y1="30" x2="44" y2="270" stroke="#cbd5e1"/><text x="44" y="288" class="addr" text-anchor="middle">低</text>
      <g class="p f-stack"><rect x="120" y="70" width="360" height="110" rx="6" fill="#fef9ec" stroke="#fcd34d"/><text x="300" y="96" text-anchor="middle" font-size="13" fill="#b45309">栈区(预留 128KB)</text><text x="110" y="78" text-anchor="end" class="addr">__stack_top</text><line x1="300" y1="110" x2="300" y2="168" stroke="#d97706" stroke-width="1.6" marker-end="url(#ar)"/><text x="316" y="144" font-size="11.5" fill="#b45309">栈从顶往下增长</text></g>
      <g class="p f-data"><rect x="120" y="185" width="360" height="40" rx="6" fill="#fff" stroke="#e6e9f0"/><text x="300" y="210" text-anchor="middle" font-size="12.5">.rodata / .data / .bss</text></g>
      <g class="p f-text"><rect x="120" y="230" width="360" height="40" rx="6" fill="#eef2ff" stroke="#c7d2fe"/><text x="300" y="255" text-anchor="middle" font-size="13" fill="#4f46e5">.text — 内核代码(boot 在最前)</text><text x="110" y="255" text-anchor="end" class="addr">0x80200000</text></g></svg>`,
    stack: () => `<svg viewBox="0 0 600 250">${AR}
      <text x="300" y="20" text-anchor="middle" font-size="12.5" font-weight="700" fill="#475569">调用栈:每调一层函数,压一个栈帧</text>
      <g class="p f-frames"><rect x="180" y="40" width="240" height="36" rx="6" fill="#fff" stroke="#e6e9f0"/><text x="300" y="63" text-anchor="middle" font-size="12.5">kernel_main 的栈帧</text>
        <rect x="180" y="84" width="240" height="36" rx="6" fill="#fff" stroke="#e6e9f0"/><text x="300" y="107" text-anchor="middle" font-size="12.5">putchar 的栈帧</text></g>
      <g class="p f-sp"><rect x="180" y="128" width="240" height="44" rx="6" fill="#eef2ff" stroke="#c7d2fe"/><text x="300" y="146" text-anchor="middle" font-size="12.5" fill="#4f46e5">当前函数的栈帧</text><text x="300" y="163" text-anchor="middle" font-size="10.5" fill="#818cf8">局部变量 + 返回地址</text><text x="450" y="153" font-size="13" class="mono" fill="#dc2626">← sp</text></g>
      <g class="p f-bad"><text x="300" y="210" text-anchor="middle" font-size="12.5" fill="#475569">平时操作系统替你把 sp 铺好;现在没人铺 →</text><text x="300" y="230" text-anchor="middle" font-size="12.5" fill="#dc2626">sp 指着乱地址 → 函数一写就崩</text></g></svg>`,
    ecall: () => `<svg viewBox="0 0 600 240">${AR}
      <g class="p f-lane"><rect x="60" y="26" width="190" height="34" rx="8" fill="#eef2ff" stroke="#c7d2fe"/><text x="155" y="48" text-anchor="middle" font-size="12.5" fill="#4f46e5">你的内核 · putchar('H')</text><text x="155" y="74" text-anchor="middle" class="addr">S 模式(权限低)</text><line x1="155" y1="82" x2="155" y2="210" stroke="#cbd5e1" stroke-dasharray="4 4"/>
        <rect x="360" y="26" width="190" height="34" rx="8" fill="#fef9ec" stroke="#fcd34d"/><text x="455" y="48" text-anchor="middle" font-size="12.5" fill="#b45309">OpenSBI 固件</text><text x="455" y="74" text-anchor="middle" class="addr">M 模式(权限高)</text><line x1="455" y1="82" x2="455" y2="210" stroke="#cbd5e1" stroke-dasharray="4 4"/></g>
      <g class="p f-call"><line x1="155" y1="110" x2="451" y2="110" stroke="#6366f1" stroke-width="1.6" marker-end="url(#ip)"/><text x="305" y="103" text-anchor="middle" font-size="12" fill="#4f46e5">ecall:这是字符 'H'</text><rect x="372" y="126" width="166" height="32" rx="7" fill="#fff" stroke="#e6e9f0"/><text x="455" y="147" text-anchor="middle" font-size="12">把 'H' 写到屏幕</text></g>
      <g class="p f-ret"><line x1="455" y1="182" x2="159" y2="182" stroke="#94a3b8" stroke-width="1.4" stroke-dasharray="5 4" marker-end="url(#ar)"/><text x="305" y="175" text-anchor="middle" font-size="12" fill="#64748b">返回(切回 S 模式)</text></g></svg>`,
    life: () => { const xs = [["固件", "#fef9ec", "#b45309"], ["0x80200000", "#fff", "#475569"], ["boot", "#fff", "#334155"], ["支栈", "#eef2ff", "#4f46e5"], ["kernel_main", "#fff", "#334155"], ["putchar", "#fff", "#334155"], ["ecall", "#fef9ec", "#b45309"], ["屏幕 Hello", "#dcfce7", "#15803d"]]; let w = 0; const g = xs.map((c, k) => { const wd = c[0].length > 6 ? 96 : 70; const x = 14 + w; w += wd + 14; return `<g class="p f-${k}"><rect x="${x}" y="44" width="${wd}" height="36" rx="9" fill="${c[1]}" stroke="#e6e9f0"/><text x="${x + wd / 2}" y="66" text-anchor="middle" font-size="11" class="${c[0].match(/[a-z_]/) ? "mono" : ""}" fill="${c[2]}">${c[0]}</text></g>${k < xs.length - 1 ? `<line x1="${x + wd}" y1="62" x2="${x + wd + 14}" y2="62" stroke="#cbd5e1" marker-end="url(#ar)"/>` : ""}`; }).join(""); return `<svg viewBox="0 0 ${w + 10} 110">${AR}${g}</svg>`; },
  };

  const CODE = {
    out: { file: "kernel.c", lines: [
      { h: `<span class="ty">void</span> <span class="fn">putchar</span>(<span class="ty">char</span> ch) {` },
      { h: `  <span class="fn">sbi_call</span>(ch, <span class="nu">0</span>,<span class="nu">0</span>,<span class="nu">0</span>,<span class="nu">0</span>,<span class="nu">0</span>,<span class="nu">0</span>, <span class="nu">1</span>);`, cls: "box" },
      { h: `}` }, { h: `` },
      { h: `<span class="ty">void</span> <span class="fn">kernel_main</span>(<span class="ty">void</span>) {` },
      { h: `  <span class="ty">const char</span> *s = <span class="st">"Hello from my kernel!\\n"</span>;` },
      { h: `  <span class="kw">for</span> (<span class="ty">int</span> i = <span class="nu">0</span>; s[i]; i++)` },
      { h: `    <span class="fn">putchar</span>(s[i]);`, cls: "wall" },
      { h: `}` },
    ] },
  };

  /* DOC = 文章的块序列。每个 figure/code/brief 块的 steps[] = 一段讲解 + 它点亮哪块。
     (steps 由「视频版」B[].segs 转来:prose=say,lit/code=该句 cues 点亮的目标。) */
  const DOC = [
    { kind: "section", num: "01", kicker: "第 1 章", title: "内核引导", sub: "你的第一句话",
      lede: "从一块什么都没有的裸机,到屏幕上冒出 Hello —— 这一章,你亲手补齐操作系统平时白送你的三样。" },

    { kind: "figure", fig: "compare", capn: 1, cap: "你在写的,是操作系统本身",
      read: "先分清你这次到底在写什么。平时你写一句 <span class=\"term\">printf</span>,屏幕就冒出字 —— 那是因为脚下垫着一整层操作系统,替你把程序加载进内存、分好运行空间、递上 printf 这样的现成工具。而这一章,你写的就是<b>这层操作系统本身</b>。脚下那层一旦抽走,想让屏幕吐出一个 Hello,<b>启动、内存、输出</b>这三样,全得你自己补回来。",
      steps: [
      { say: "先搞清楚你在写什么。平时你写一句 printf,屏幕就出字 —— 背后是操作系统替你加载、给内存、提供 printf。", lit: [".f-l", ".f-lhelp"] },
      { say: "而这一章你写的,就是这个操作系统本身;脚下那层一旦没了,Hello 就得你自己补回三样:<b>启动 · 内存 · 输出</b>。", lit: [".f-r", ".f-rgone", ".f-rq"] },
    ] },

    { kind: "brief", title: "这一章你要做出什么", goal: "屏幕跑出 Hello from my kernel!", capn: 2, cap: "三块代码,两处要你亲手写",
      rows: [
        ["启动", "arch/boot.c", "机器一开机,最先跑的就是它。它先给内核铺好一块「栈」(函数运行时存东西的临时草稿区),再跳进主程序 —— 没有它,你写的任何 C 代码都跑不起来。", "w", "boot"],
        ["输出", "kernel/main.c", "内核的主程序。这一章它只干一件事:把 “Hello from my kernel!” 这串字,一个字符一个字符地送出去。", "w", "main"],
        ["底层输出", "arch/sbi.c · drivers/console.c", "字符到底怎么「冒到屏幕上」?裸机自己点不亮屏,得请固件代劳 —— 这套底层细节已给你写好,你知道它负责「把一个字符吐到屏幕」就够了。", "b", "sbi"],
      ],
      read: "这一章的终点很具体:让一台刚通电、什么都没有的机器,在屏幕上打出第一句话 —— <b>Hello from my kernel!</b>。为此你会碰到三块代码。<b>启动</b>(boot.c)是开机后最先跑的那段,它得先铺出一块叫「栈」的临时草稿区,C 代码才跑得起来,关键几行要你亲手写。<b>输出</b>(main.c)是内核主程序,这章只干一件事:把那串字一个字符一个字符送出去,也要你写。至于字符究竟怎么「冒到屏幕上」,裸机点不亮屏,得喊更底层的固件代劳;这部分(sbi.c / console.c)<b>已经给你写好</b>,知道它「负责把一个字符吐到屏幕」就够了。所以真正要你吃透、动手的,就两处:<b>支栈</b>和<b>打印</b>。",
      steps: [
        { say: "先说清这一章你要做出什么:让一台刚开机、什么都没有的机器,在屏幕上打出第一句话,Hello。为此你要碰三块代码。", lit: [] },
        { say: "<b>第一块,启动</b>,在 boot 这个文件。机器一上电,最先跑的就是它;它得先铺出一块叫「栈」的草稿区,栈没铺好,后面任何 C 代码一跑就崩。这块的关键几行,要你亲手写、得吃透。", lit: ["[data-k='boot']"] },
        { say: "<b>第二块,输出</b>,在 main 这个文件,它是内核的主程序。这一章它只干一件事:把 Hello 一个字符一个字符送出去。这几行,也要你亲手写。", lit: ["[data-k='main']"] },
        { say: "可字符到底怎么冒到屏幕上?裸机自己点不亮屏,得喊更底层的固件帮忙。这套细节放在 sbi 和 console 两个文件里,<b>已经给你写好了</b> —— 你只要知道它负责把一个字符吐到屏幕。", lit: ["[data-k='sbi']"] },
        { say: "所以这一章,真正要你吃透、亲手写的就两处:<b>支栈</b>和<b>打印</b>。带着这个目标,我们一步步来,先搞懂为什么,再动手。", lit: ["[data-k='boot']", "[data-k='main']"] },
      ] },

    { kind: "section", num: "1", kicker: "第一关", title: "启动", sub: "代码凭啥能被跑到",
      lede: "开机那一刻,先跑的根本不是你的代码。这一关,把控制权一路接到你手里。" },

    { kind: "figure", fig: "boot", capn: 3, cap: "开机接力:固件先醒,再把棒交给你",
      read: "开机那一刻,先跑的根本不是你的代码。CPU 一通电什么都不懂,只会跳到一个写死的固定地址去执行。在你之前,有一段叫固件的小程序 —— <b>OpenSBI</b> —— 比你先醒;它做完最底层的准备,跳到约定好的地址 <span class=\"term\">0x80200000</span>,把接力棒交到你手里。那个地址上等着接棒的,就是你的 <b>boot</b>。",
      steps: [
      { say: "开机时 CPU 什么都不懂,只会跳到一个固定地址执行。", lit: [".f-1"] },
      { say: "有段叫固件的小程序 —— <b>OpenSBI</b>,比你先醒;它做完准备,跳到约定地址 <span class=\"term\">0x80200000</span>,把接力棒交给你的 boot。", lit: [".f-2", ".f-3", ".f-4"] },
    ] },

    { kind: "note", variant: "比喻", icon: "lightbulb",
      title: "打个比方", body: "OpenSBI 就像大楼的<b>物业前台</b>:它比你先到岗,把水电(最底层硬件)张罗好,再把钥匙(控制权)交给刚搬进来的你。往后你想用点公共服务,还得回头喊它 —— 这就是待会儿要用的 <span class=\"term\">ecall</span>。" },

    { kind: "figure", fig: "mem", capn: 4, cap: "链接脚本把代码和栈钉在内存里",
      aside: { file: "kernel.ld", lines: [
        { h: `. = <span class="nu">0x80200000</span>;        <span class="cm">// 代码从这开始摆</span>` },
        { h: `__stack_top = .;       <span class="cm">// 最上面预留一段当栈</span>` } ] },
      read: "代码摆在内存的哪个位置,不是碰运气,而是由<b>链接脚本</b>一行行钉死的。脚本里 <span class=\"term\">. = 0x80200000</span> 这一句,就是把内核代码摆到这个地址,固件才正好跳得过来。再往最上面,预留出一段空间专门当<b>栈</b>,并记下栈顶的位置 <span class=\"term\">__stack_top</span> —— 这个名字,下一关马上要用到。",
      steps: [
        { say: "代码摆在内存哪里,由链接脚本一行行钉死。点号等于 <span class=\"term\">0x80200000</span>,就是把内核代码摆到这,固件正好跳来。", lit: [".f-text"] },
        { say: "最上面再预留一段当栈,记下栈顶 <span class=\"term\">__stack_top</span> —— 下一关就要用它。", lit: [".f-stack"] },
      ] },

    { kind: "scene", ic: "bolt", big: "你写个 C 函数 —— 直接崩了", sub: "语法明明没错,为什么?",
      say: "代码能跑到了,你写个再普通不过的 C 函数,结果直接崩。语法没错,为什么?" },

    { kind: "figure", fig: "stack", capn: 5, cap: "没人替你铺栈,sp 指着乱地址",
      read: "问题出在<b>栈</b>上。每个 C 函数一运行,都需要一小块草稿区,用来放局部变量、记住「我执行完该回到哪」;每往下调一层函数,就压进一个新的栈帧。这块草稿区现在在哪,由寄存器 <span class=\"term\">sp</span> 指着。平时操作系统早替你把 sp 铺在一块好内存上;可现在没人替你做 —— sp 指向一个乱七八糟的地址,于是你的函数刚一动笔,就崩了。",
      steps: [
      { say: "原因在<b>栈</b>。每个 C 函数运行,都要一块草稿区放局部变量、记返回地址,每调一层就压一个栈帧。", lit: [".f-frames"] },
      { say: "寄存器 <span class=\"term\">sp</span> 指着当前栈顶。平时操作系统替你铺好;现在没人铺,sp 指着乱地址,函数一写就崩。", lit: [".f-sp", ".f-bad"] },
    ] },

    { kind: "scene", ic: "monitor", big: "想打印 Hello —— 没有 printf", sub: "printf 本来就是操作系统给你的",
      say: "代码稳稳跑起来了,你想打印 Hello,伸手找 printf …… 没有。那屏幕上,怎么才能冒出一个字?" },

    { kind: "figure", fig: "ecall", capn: 6, cap: "求固件代劳:一条 ecall 过去再切回",
      read: "你自己确实点不亮屏幕 —— 那是更底层的硬件的事。但你能做一件事:<b>求那个比你先醒、权限更高的固件帮忙</b>。用一条特殊指令 <span class=\"term\">ecall</span>,把要打印的字符连同「请写到屏幕」的请求一起托付给固件;它办完,再把控制权切回给你。把这一整套动作包成一个函数,就是你的 <b>putchar</b>。",
      steps: [
      { say: "你自己点不亮屏幕,那是更底层的事;但你能<b>求那个先醒的固件</b>。", lit: [".f-lane"] },
      { say: "用一条特殊指令 <span class=\"term\">ecall</span>,把字符托给固件,它替你写到屏幕,办完再切回来。包成函数,就是你的 putchar。", lit: [".f-call", ".f-ret"] },
    ] },

    { kind: "code", code: "out", capn: 7, cap: "putchar 与主循环",
      read: "把这两步落到代码上。<b>putchar</b> 这一层靠 ecall 求固件,属于<b>黑盒</b> —— 照抄就行,不必纠结寄存器怎么排。主函数里先备好要打印的字符串。真正要你写的,是那行循环体:把字符串里的字符一个一个交给 putchar 送出去 —— 这就是这一章的<b>承重墙</b>。",
      steps: [
      { say: "看代码。输出这步靠 ecall 求固件,是<b>黑盒</b>,照抄就行,别纠结。", code: [1] },
      { say: "主函数里备好字符串 Hello。", code: [5] },
      { say: "然后循环里,一个字符一个字符 putchar 出去 —— 这行是<b>承重墙</b>,你来写。", code: [6, 7] },
    ] },

    { kind: "hands", wall: "该你了", title: "完成内核:支栈 + 打印", file: "arch/boot.c",
      sub: "进真沙箱,填好 arch/boot.c 和 kernel/main.c 两处承重墙 —— 在 boot.c 把 sp 指到栈顶,在 main.c 把每个字符 putchar 出去,然后点运行,见证它说出第一句话。" },

    { kind: "figure", fig: "life", capn: 8, cap: "一个字符走过的全程",
      read: "回头看这一个字符走过的全程,你就会发现它一点都不神秘:固件先醒,跳到约定地址,你的 boot 接手、支起栈,进入主函数,调用 putchar,一条 ecall 把字符喊给固件,固件最后把它送上屏幕。这一串环节里的每一个,都是你刚刚亲手补齐的。",
      steps: [
      { say: "回头看这一个字符走了多远 ——", lit: [".f-0"] },
      { say: "固件先醒,跳到地址,boot,支起栈,进主函数,调 putchar,一条 ecall 喊到固件,固件把字送上屏幕。", lit: [".f-0", ".f-1", ".f-2", ".f-3", ".f-4", ".f-5", ".f-6", ".f-7"] },
    ] },

    { kind: "take", line: `它一点都不是魔法 ——<br>你补齐了 <b>启动</b> · <b>内存</b> · <b>输出</b> 三样。`,
      foot: "这就是从零造一个操作系统,真正的意思。" },
  ];

  /* —— 渲染:把一个块的「视觉」部分转成 HTML（图 / 代码 / 项目地图）—— */
  function buildVisual(block) {
    if (block.kind === "figure") {
      let h = `<div class="fig lit-scope">${FIG[block.fig]()}</div>`;
      if (block.aside) h += `<div class="codew aside"><div class="cf">${block.aside.file}</div><div class="body">${block.aside.lines.map((l) => `<div class="p"><span class="gut"></span><span class="src">${l.h}</span></div>`).join("")}</div></div>`;
      return h;
    }
    if (block.kind === "code") {
      const c = CODE[block.code];
      return `<div class="codew lit-scope"><div class="cf">${c.file}<span class="legend"><b class="k">承重墙</b> 你写 · <b class="x">黑盒</b> 照抄</span></div><div class="body">${c.lines.map((l, i) => `<div class="p ${l.cls || ""}" data-i="${i}"><span class="gut"></span><span class="src">${l.h || " "}</span></div>`).join("")}</div></div>`;
    }
    if (block.kind === "brief") {
      const tag = { w: "承重墙", b: "黑盒", r: "读懂" };
      return `<div class="brief-goal">产出 · <b>${block.goal}</b></div>
        <div class="pmlegend"><span class="ptag t-w">承重墙</span> 你写&吃透 · <span class="ptag t-b">黑盒</span> 给你&照抄</div>
        <div class="projmap lit-scope">${block.rows.map((r) => `<div class="pmrow p" data-k="${r[4]}"><div class="prow1"><span class="pmod">${r[0]}</span><span class="pfile">${r[1]}</span><span class="ptag t-${r[3]}">${tag[r[3]]}</span></div><div class="pdesc">${r[2]}</div></div>`).join("")}</div>`;
    }
    return "";
  }

  /* —— 高亮:把某一步的状态打到视觉容器上 —— */
  function applyState(vizEl, step) {
    if (!vizEl || !step) return;
    const scope = vizEl.querySelector(".lit-scope") || vizEl;
    const hasLit = step.lit && step.lit.length;
    const hasCode = step.code && step.code.length;
    scope.classList.toggle("has-lit", !!(hasLit || hasCode));
    scope.querySelectorAll(".p.lit").forEach((x) => x.classList.remove("lit"));
    if (hasLit) step.lit.forEach((sel) => scope.querySelectorAll(sel).forEach((x) => x.classList.add("lit")));
    if (hasCode) step.code.forEach((i) => { const r = scope.querySelector(`[data-i="${i}"]`); if (r) r.classList.add("lit"); });
  }

  /* —— 一屏一幕:把视觉块包成带落款的卡片(落款只留「图 N」,标题归文字栏)—— */
  function vizCard(b) {
    const cap = `<div class="figcap"><b>图 ${b.capn}</b></div>`;
    if (b.kind === "figure") return `<div class="figcard">${buildVisual(b)}</div>${cap}`;
    return `${buildVisual(b)}${cap}`;   // brief / code 自带边框,不再外包卡片
  }

  /* —— 把 DOC 摊平成「帧」序列:多步的图/代码/地图,每一步 = 一帧 —— */
  function flatten() {
    const frames = [];
    DOC.forEach((b) => {
      if (b.kind === "figure" || b.kind === "code" || b.kind === "brief")
        b.steps.forEach((s, i) => frames.push({ type: "viz", block: b, step: s, i, n: b.steps.length }));
      else frames.push({ type: b.kind, block: b });
    });
    return frames;
  }

  /* —— 单帧 HTML（幻灯片 / 卷轴共用,外层各自包居中容器）—— */
  function renderFrameInner(f) {
    const b = f.block;
    if (f.type === "section") return `<div class="section"><div class="kick"><span class="num">${/^\d+$/.test(b.num) ? b.num : '<span class="mi">flag</span>'}</span>${b.kicker}</div><h1>${b.title}</h1><div class="sub">${b.sub}</div><div class="rule"></div><p class="lede">${b.lede}</p></div>`;
    if (f.type === "scene") return `<div class="scene"><div class="glow"></div><div class="ic"><span class="mi">${b.ic}</span></div><div class="big">${b.big}</div><div class="sub">${b.sub}</div></div>`;
    if (f.type === "take") return `<div class="take"><div class="glow"></div><div class="ck"><span class="mi">check</span></div><div class="line">${b.line}</div><div class="foot">${b.foot}</div></div>`;
    if (f.type === "hands") return `<div class="handsframe"><div class="hicon"><span class="mi">construction</span></div><span class="wall">${b.wall}</span><div class="bigt">${b.title}</div><div class="subt">${b.sub}</div><button class="callmascot"><span class="mi">sports_esports</span> 唤起 Keri,开始动手</button></div>`;
    return `<div class="framebody">${vizCard(b)}<div class="frame-text prose">${f.step.say}</div>${f.n > 1 ? `<div class="frame-meta">第 ${f.i + 1} / ${f.n} 步</div>` : ""}</div>`;
  }

  /* —— 应用某帧的高亮状态到它自己的 DOM —— */
  function applyFrame(frameEl, f) { if (f && f.type === "viz") applyState(frameEl, f.step); }

  /* —— 图文页:左图(可点 ◀▶ 聚焦讲解)+ 右成段讲解文字 —— */
  function renderPageInner(b) {
    const stepper = b.steps && b.steps.length > 1
      ? `<div class="pgstep"><button class="wbtn prev"><span class="mi">arrow_back</span></button><div class="wdots">${b.steps.map(() => "<i></i>").join("")}</div><button class="wbtn next">聚焦讲解 <span class="mi">arrow_forward</span></button></div>`
      : "";
    const head = b.kind === "brief" ? b.title : b.cap;
    return `<div class="page">
      <div class="page-viz">${vizCard(b)}${stepper}</div>
      <div class="page-text"><h2 class="pg-head">${head}</h2><div class="prose">${b.read || (b.steps && b.steps[0] ? b.steps[0].say : "")}</div></div>
    </div>`;
  }

  /* —— 给一张图文页接上图的聚焦 ◀▶ —— */
  function wirePage(root, b) {
    const viz = root.querySelector(".page-viz");
    if (!b.steps || b.steps.length < 2) { applyState(viz, (b.steps && b.steps[0]) || { lit: [] }); return; }
    const dots = [...root.querySelectorAll(".wdots i")];
    const prev = root.querySelector(".prev"), next = root.querySelector(".next");
    const last = b.steps.length - 1; let i = 0;
    const show = (n) => {
      i = n; applyState(viz, b.steps[i]);
      dots.forEach((d, k) => { d.className = k === i ? "on" : k < i ? "seen" : ""; });
      prev.disabled = i === 0;
      next.innerHTML = i < last ? `聚焦讲解 <span class="mi">arrow_forward</span>` : `<span class="mi">replay</span> 从头`;
    };
    prev.onclick = () => { if (i > 0) show(i - 1); };
    next.onclick = () => show(i < last ? i + 1 : 0);
    show(0);
  }

  const KERI = `<svg width="30" height="30" viewBox="0 0 64 64" fill="none"><path d="M50.7 18.5A23.8 23.8 0 1 0 51 45.8" stroke="#fff" stroke-width="4.6" stroke-linecap="round"/><path d="M23 44V24M23 32.5l17.5-13M23 32.5l17.5 13" stroke="#fff" stroke-width="4.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="23" cy="24" r="5" fill="#fff"/><circle cx="23" cy="44" r="5" fill="#fff"/><circle cx="42.5" cy="18.5" r="5" fill="#fff"/><circle cx="42.5" cy="45.5" r="5" fill="#fff"/></svg>`;

  /* —— 浮动吉祥物 Keri:点它滑出沙箱面板（沙箱不再内嵌画面）—— */
  function mountMascot(hands) {
    if (window.__mascot) return window.__mascot;
    const back = document.createElement("div"); back.className = "sbback";
    const panel = document.createElement("div"); panel.className = "sbpanel";
    panel.innerHTML = `<div class="ph"><span class="wall">${hands.wall}</span><div class="pt"><b>${hands.title}</b><div class="s">${hands.sub}</div></div><button class="x" title="收起"><span class="mi">close</span></button></div><iframe title="真沙箱"></iframe>`;
    const m = document.createElement("div"); m.className = "mascot";
    m.innerHTML = `<div class="tip">卡住了?点我进沙箱动手 →</div><button class="orb" title="Keri · 动手台">${KERI}</button>`;
    document.body.append(back, panel, m);
    const iframe = panel.querySelector("iframe");
    const open = () => { if (!iframe.getAttribute("src")) iframe.setAttribute("src", "../sandbox/sandbox.html" + (hands.file ? "?file=" + encodeURIComponent(hands.file) : "")); panel.classList.add("open"); back.classList.add("open"); m.classList.remove("calling"); };
    const close = () => { panel.classList.remove("open"); back.classList.remove("open"); };
    const call = () => m.classList.add("calling");
    m.querySelector(".orb").onclick = open; panel.querySelector(".x").onclick = close; back.onclick = close;
    return (window.__mascot = { open, close, call, el: m });
  }

  return { AR, FIG, CODE, DOC, buildVisual, applyState, vizCard, flatten, renderFrameInner, applyFrame, renderPageInner, wirePage, mountMascot };
})();
