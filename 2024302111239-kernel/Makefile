# 个人累积内核构建入口；Lab 2 用户程序规则由 Makefile.upgrade 提供。
CC   = riscv64-unknown-elf-gcc
LD   = riscv64-unknown-elf-ld
CFLAGS = -Wall -Werror -O -std=gnu99 -mcmodel=medany -ffreestanding \
         -nostdlib -fno-common -ggdb -march=rv64gc -fno-stack-protector -fno-pie
QEMU = qemu-system-riscv64

OBJS = kernel/entry.o kernel/start.o kernel/console.o kernel/printf.o kernel/main.o \
       kernel/kalloc.o kernel/vm.o kernel/proc.o kernel/swtch.o \
       kernel/trap.o kernel/kernelvec.o kernel/syscall.o \
       kernel/trampoline_wrap.o kernel/userimg.o

kernel/kernel: $(OBJS) kernel/kernel.ld
	$(LD) -T kernel/kernel.ld -o $@ $(OBJS)

%.o: %.c kernel/riscv.h kernel/course_sid.h kernel/defs.h kernel/vmcore.h
	$(CC) $(CFLAGS) -Ikernel -c -o $@ $<

%.o: %.S kernel/course_sid.h
	$(CC) $(CFLAGS) -Ikernel -c -o $@ $<

kernel/trampoline_wrap.o: kernel/trampoline.S

# 验收环境固定(排雷环节禁止改动本行以下内容)
qemu: kernel/kernel
	$(QEMU) -machine virt -bios none -kernel kernel/kernel -nographic

clean:
	rm -f kernel/*.o kernel/kernel

include Makefile.upgrade

UPROGS += badecall bufstorm inputcheck badptr
kernel/userimg.S: user-flat/badecall.bin user-flat/bufstorm.bin \
                  user-flat/inputcheck.bin user-flat/badptr.bin

clean: clean-extra
