"""Exercise the Lab 2 shell, traps, UART input, and Lab 1 boot output in QEMU."""

import os
from pathlib import Path
import pty
import re
import select
import subprocess
from tempfile import TemporaryDirectory
from time import monotonic, sleep


KERNEL = Path(__file__).resolve().parents[2] / "2024302111239-kernel"
QEMU = [
    "qemu-system-riscv64", "-machine", "virt", "-bios", "none",
    "-kernel", "kernel/kernel", "-nographic", "-smp", "1", "-m", "128M",
]


def main() -> None:
    with TemporaryDirectory(prefix="ospractice-lab2-") as temporary:
        log = Path(temporary) / "interrupts.log"
        master, slave = pty.openpty()
        process = subprocess.Popen(
            QEMU + ["-d", "int", "-D", str(log)], cwd=KERNEL,
            stdin=slave, stdout=slave, stderr=slave, close_fds=True,
        )
        os.close(slave)
        output = bytearray()

        def wait_for(fragment: bytes, count: int = 1, seconds: float = 8) -> None:
            deadline = monotonic() + seconds
            while output.count(fragment) < count and monotonic() < deadline:
                ready, _, _ = select.select([master], [], [], 0.05)
                if ready:
                    output.extend(os.read(master, 65536))
            assert output.count(fragment) >= count, (fragment, bytes(output[-500:]))

        try:
            wait_for(b"sh> ")
            banner = (KERNEL / "expect_banner.txt").read_bytes()
            assert output.splitlines()[0] == banner.strip(), bytes(output[:80])

            os.write(master, b"hix\x7f\n")
            wait_for(b"hix\x08 \x08\r\n")
            wait_for(b"hi: user program running, pid=")
            wait_for(b"sh> ", 2)

            os.write(master, b"badecall\n")
            wait_for(b"TEST-1 PASS: unknown syscalls all return -1")
            wait_for(b"sh> ", 3)

            os.write(master, b"badptr\n")
            wait_for(b"BADPTR PASS")
            wait_for(b"sh> ", 4)

            os.write(master, b"bufstorm\n")
            wait_for(b"sh> bufstorm\r\n")
            for typed, line, copies in (
                (b"onx\x7fe\n", b"one\n", 1),
                (b"two\n", b"two\n", 2),
                (b"three\n", b"three\n", 2),
                (b"four\n", b"four\n", 2),
            ):
                for byte in typed:
                    os.write(master, bytes([byte]))
                    sleep(0.08)
                wait_for(line.replace(b"\n", b"\r\n"), copies)
            assert b"ttwwoo" not in output
            wait_for(b"BUFSTORM lines=4 bytes=19")
            wait_for(b"sh> ", 5)

            header = (KERNEL / "kernel/course_sid.h").read_text(encoding="utf-8")
            capacity = int(re.search(r"#define LAB2_BUF_SIZE (\d+)", header).group(1))
            payload = b"k" * (capacity // 2)
            os.write(master, b"inputcheck\n")
            wait_for(b"sh> inputcheck\r\n")
            os.write(master, payload)
            result = f"INPUTCHECK count={len(payload)} checksum={sum(payload)}".encode()
            wait_for(result)
            wait_for(b"sh> ", 6)

            os.write(master, b"spin\n")
            wait_for(b"spin 1\r\n")
            os.write(master, b"abc\n")
            wait_for(b"abc\r\n")
            wait_for(b"spin 2")

            allowed = {"user_ecall", "s_timer", "s_external"}
            seen = set()
            for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
                if "desc=" in line:
                    description = line.split("desc=", 1)[1]
                    assert description in allowed, line
                    seen.add(description)
            assert seen == allowed, seen
            print("Lab 2 QEMU interaction: PASS")
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            os.close(master)


if __name__ == "__main__":
    main()
