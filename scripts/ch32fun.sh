#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
book="$root/externals/ch32v003-book-code"
fun="$book/ch32fun"
sample="$root/samples/ch32v003/blink_and_read"
revision=2679ac059f3ada402731e5a10818cc0814e9ec4c
case "${1:-}" in
  check)
    missing=0
    for tool in git make gcc pkg-config riscv64-unknown-elf-gcc riscv64-unknown-elf-objcopy riscv64-unknown-elf-objdump; do
      if command -v "$tool" >/dev/null; then printf '%s: %s\n' "$tool" "$(command -v "$tool")"; "$tool" --version | head -n 1 || true; else echo "missing: $tool" >&2; missing=1; fi
    done
    for lib in libusb-1.0 libudev; do
      if command -v pkg-config >/dev/null && version="$(pkg-config --modversion "$lib" 2>/dev/null)"; then
        echo "$lib: $version"
      else
        echo "missing: $lib development package (or pkg-config)" >&2
        missing=1
      fi
    done
    actual="$(git -C "$fun" rev-parse HEAD 2>/dev/null || true)"
    echo "ch32fun: ${actual:-missing} (required $revision)"
    [[ "$actual" == "$revision" ]] || missing=1
    exit "$missing";;
  build)
    "$0" check
    make -C "$sample" build PREFIX=riscv64-unknown-elf
    echo "BUILD OK: $sample/main.bin";;
  programmer)
    "$0" check
    make -C "$fun/minichlink" minichlink CFLAGS='-O0 -g3 -Wall -std=gnu17 -DCH32V003 -I. -DMINICHLINK'
    echo "programmer: $fun/minichlink/minichlink";;
  flash)
    [[ -f "$sample/main.bin" ]] || { echo 'FLASH FAILED: build artifact missing; run build first' >&2; exit 1; }
    "$0" programmer
    result=0
    output="$("$fun/minichlink/minichlink" -w "$sample/main.bin" flash -b 2>&1)" || result=$?
    printf '%s\n' "$output"
    if [[ $result -ne 0 ]] || [[ "$output" != *'Detected: CH32V003'* ]] || [[ "$output" != *'Image written.'* ]] || [[ "$output" == *'No detected chip.'* ]] || [[ "$output" == *'Unknown chip'* ]]; then
      echo 'FLASH FAILED: programmer failed or did not confirm CH32V003 and image write' >&2
      exit 1
    fi
    echo 'FLASH OK (runtime unverified)';;
  *) echo "usage: $0 {check|build|programmer|flash}" >&2; exit 2;;
esac
