"""Check the Lab 1 serial contract against a real QEMU cold boot."""

from pathlib import Path
import subprocess


KERNEL = Path(__file__).resolve().parents[2] / "2024302111239-kernel"
QEMU = [
    "qemu-system-riscv64", "-machine", "virt", "-bios", "none",
    "-kernel", "kernel/kernel", "-nographic",
]


def main() -> None:
    try:
        subprocess.run(QEMU, cwd=KERNEL, capture_output=True, timeout=3, check=True)
        raise AssertionError("kernel exited before the observation window ended")
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or b"") + (exc.stderr or b"")

    lines = output.decode("ascii").splitlines()
    expected_banner = (KERNEL / "expect_banner.txt").read_text(encoding="utf-8").strip()
    assert lines[0] == expected_banner, lines[0]
    assert lines[1] == (
        "SELFTEST zero=0 min=-2147483648 max=2147483647 "
        "hex=0xffffffff empty=[]"
    ), lines[1]
    assert lines[2] == "SELFTEST long=[" + "0123456789abcdef" * 32 + "]", len(lines[2])
    assert len(lines) >= 3, lines
    print("Lab 1 serial output: PASS")


if __name__ == "__main__":
    main()
