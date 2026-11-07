#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
fun="$root/externals/ch32fun"
target="${2:-ch32v003}"
case "$target" in
  ch32v003|ch32v002) ;;
  *) echo "error: unknown target $target (use ch32v003 or ch32v002)" >&2; exit 2;;
esac
sample="$root/samples_${target}_ch32fun/blink_and_read"
revision=b28d285460ce052a179dba8f4a22c6f73ff8e328
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
    if [[ "$target" == ch32v002 ]]; then
      id_result=0
      id_output="$("$fun/minichlink/minichlink" -r + 0x1ffff704 4 -b 2>&1)" || id_result=$?
      printf '%s\n' "$id_output"
      id_line="$(printf '%s\n' "$id_output" | sed -n 's/^1ffff704: \([0-9a-fA-F][0-9a-fA-F]\) \([0-9a-fA-F][0-9a-fA-F]\) \([0-9a-fA-F][0-9a-fA-F]\) \([0-9a-fA-F][0-9a-fA-F]\).*$/\4\3\2\1/p')"
      if [[ $id_result -ne 0 || ! "$id_line" =~ ^[0-9a-fA-F]{8}$ ]] || (( (16#$id_line >> 20) != 0x002 )); then
        echo 'FLASH FAILED: could not verify CH32V002 chip identifier' >&2
        exit 1
      fi
      if [[ "$id_output" == *'No detected chip.'* || "$id_output" == *'Unknown chip'* ]]; then
        echo 'FLASH FAILED: chip detection error' >&2
        exit 1
      fi
      echo "CH32V002 identifier: 0x$id_line"
    fi
    result=0
    output="$("$fun/minichlink/minichlink" -w "$sample/main.bin" flash -b 2>&1)" || result=$?
    printf '%s\n' "$output"
    expected='Detected CH32V003'
    [[ "$target" == ch32v002 ]] && expected='Detected CH32V002'
    if [[ $result -ne 0 ]] || [[ "$output" != *"$expected"* ]] || [[ "$output" != *'Image written.'* ]] || [[ "$output" == *'No detected chip.'* ]] || [[ "$output" == *'Unknown chip'* ]]; then
      echo "FLASH FAILED: programmer failed or did not confirm $target and image write" >&2
      exit 1
    fi
    echo 'FLASH OK (runtime unverified)';;
  *) echo "usage: $0 {check|build|programmer|flash} [ch32v003|ch32v002]" >&2; exit 2;;
esac
