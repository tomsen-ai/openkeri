// kernel-ch1 —— 第 1 章可真编译/真运行的最小内核(RISC-V 32, QEMU virt + OpenSBI)
// 两处「承重墙」(boot 里支栈那行、kernel_main 里打印那行)末尾各有一个标记,
// 本地沙箱按标记把学习者写的那一行填进来;直接编译则用参考答案,可独立验证工具链。

typedef unsigned int   uint32_t;
typedef int            int32_t;

extern char __stack_top[];

// —— 黑盒:通过 ecall 陷入 OpenSBI(M 模式)——
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

void putchar(char ch) {
    sbi_call(ch, 0, 0, 0, 0, 0, 0, 1 /* EID 1 = console putchar */);
}

// —— 承重墙 ②:打印循环 ——
void kernel_main(void) {
    const char *s = "Hello from my kernel!\n";
    for (int i = 0; s[i]; i++)
        putchar(s[i]); // {{PRINT}}
    for (;;);
}

// —— 承重墙 ①:开机第一段,先支栈再进 C ——
__attribute__((section(".text.boot")))
__attribute__((naked))
void boot(void) {
    __asm__ __volatile__(
        "la sp, __stack_top\n" // {{BOOT_SP}}
        "j  kernel_main\n"
    );
}
