"""Static (ELF) evidence for interrupt handlers of the official-SDK samples."""
import re
import subprocess
from pathlib import Path

from ch32hil.dut import ROOT

TOOLS = ROOT / ".arduino/official/data/packages/WCH/tools/riscv-wch-gcc/15.2.0/bin/riscv32-wch-elf-"


def _run(tool, *args):
    return subprocess.run([str(TOOLS) + tool, *map(str, args)], capture_output=True, text=True, check=True).stdout


def symbols(elf):
    return {m.group(2): int(m.group(1), 16) for m in re.finditer(r"(?m)^([0-9a-f]{8}) [A-Za-z] (\S+)$", _run("nm", elf))}


def vector_words(elf, count=40):
    """Words of the vector table in .init (word index = IRQn: the SDK numbers interrupts by vector slot)."""
    words = []
    for line in _run("objdump", "-s", "-j", ".init", elf).splitlines():
        m = re.match(r"^ ([0-9a-f]{4}) ((?:[0-9a-f]{1,8} ?)+)", line)
        if m:
            for w in m.group(2).split():
                words.append(int.from_bytes(bytes.fromhex(w.rjust(8, "0")), "little"))
    return words[:count]


def check_irq_handler(elf, name, irqn):
    """Handler `name` is in the vector table slot of IRQ `irqn`, is not the default handler and returns with mret."""
    syms = symbols(elf)
    if name not in syms:
        raise AssertionError(f"{name} not linked")
    words = vector_words(elf)
    slot = irqn  # this SDK numbers IRQs by vector slot (SysTick 12, WWDG 16, TIM1_UP 35)
    if words[slot] != syms[name]:
        raise AssertionError(f"vector slot {slot} = 0x{words[slot]:x}, {name} = 0x{syms[name]:x}")
    default = syms.get("Default_Handler")
    if default is not None and syms[name] == default:
        raise AssertionError(f"{name} is the default handler")
    text = _run("objdump", "-d", f"--disassemble={name}", elf)
    if "mret" not in text:
        raise AssertionError(f"{name} does not return with mret (not an interrupt-attribute function)")
    return {"symbol": name, "address": f"0x{syms[name]:x}", "vector_slot": slot, "returns_with_mret": True}
