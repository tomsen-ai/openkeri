// kernel-ch2 —— 第 2 章可真编译/真运行:printf + bump 分配器 + panic
// 三处「承重墙」末尾各有一个标记,本地沙箱按标记把学习者写的那一行填进来;
// 直接编译则用参考答案,可独立验证工具链。

typedef unsigned int   uint32_t;
typedef unsigned int   paddr_t;
#define PAGE_SIZE 4096u
#define RAM_START 0x80204000u

extern char __stack_top[];

// —— 黑盒:ecall 陷入 OpenSBI ——
struct sbiret { long error; long value; };
struct sbiret sbi_call(long a0_, long a1_, long a2_, long a3_,
                       long a4_, long a5_, long fid, long eid) {
    register long a0 __asm__("a0") = a0_;
    register long a1 __asm__("a1") = a1_;
    register long a2 __asm__("a2") = a2_;
    register long a3 __asm__("a3") = a3_;
    register long a4 __asm__("a4") = a4_;
    register long a5 __asm__("a5") = a5_;
    register long a6 __asm__("a6") = fid;
    register long a7 __asm__("a7") = eid;
    __asm__ __volatile__("ecall"
                         : "=r"(a0), "=r"(a1)
                         : "r"(a0), "r"(a1), "r"(a2), "r"(a3),
                           "r"(a4), "r"(a5), "r"(a6), "r"(a7)
                         : "memory");
    return (struct sbiret){ .error = a0, .value = a1 };
}
void putchar(char ch) { sbi_call(ch, 0, 0, 0, 0, 0, 0, 1); }

static void print_hex(uint32_t v) {
    const char *d = "0123456789abcdef";
    char buf[8]; int i = 0;
    if (v == 0) { putchar('0'); return; }
    while (v) { buf[i++] = d[v & 0xf]; v >>= 4; }
    while (i--) putchar(buf[i]);
}
static void print_int(int v) {
    char buf[12]; int i = 0;
    if (v < 0) { putchar('-'); v = -v; }
    if (v == 0) { putchar('0'); return; }
    while (v) { buf[i++] = (char)('0' + v % 10); v /= 10; }
    while (i--) putchar(buf[i]);
}

// —— 承重墙 ①:printf 主循环里「普通字符原样输出」——
void printf(const char *fmt, ...) {
    __builtin_va_list ap; __builtin_va_start(ap, fmt);
    while (*fmt) {
        if (*fmt == '%') {
            fmt++;
            if (*fmt == 's') { const char *s = __builtin_va_arg(ap, const char *); while (*s) putchar(*s++); }
            else if (*fmt == 'd') { print_int(__builtin_va_arg(ap, int)); }
            else if (*fmt == 'x') { print_hex(__builtin_va_arg(ap, uint32_t)); }
            else if (*fmt == '%') { putchar('%'); }
            else { putchar('%'); if (*fmt) putchar(*fmt); }
        } else {
            putchar(*fmt); // {{PRINTF}}
        }
        if (*fmt) fmt++;
    }
    __builtin_va_end(ap);
}

// —— 承重墙 ②:bump 分配器,把 next 往前撞 n 页 ——
paddr_t alloc_pages(uint32_t n) {
    static paddr_t next = RAM_START;
    paddr_t cur = next;
    next += n * PAGE_SIZE; // {{ALLOC}}
    return cur;
}

// —— 承重墙 ③:panic 打印后就地停住 ——
void panic_at(const char *file, int line, const char *msg) {
    printf("PANIC: %s:%d: %s\n", file, line, msg);
    for (;;); // {{PANIC}}
}
#define PANIC(msg) panic_at("kernel/main.c", __LINE__, msg)

void kernel_main(void) {
    paddr_t p1 = alloc_pages(1);
    paddr_t p2 = alloc_pages(1);
    printf("p1=0x%x p2=0x%x\n", p1, p2);
    PANIC("out of memory");
}

__attribute__((section(".text.boot")))
__attribute__((naked))
void boot(void) {
    __asm__ __volatile__(
        "la sp, __stack_top\n"
        "j  kernel_main\n"
    );
}
