#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
fun="$root/externals/ch32fun"
target="${2:-ch32v003}"
# CH32V002/CH32V006 share the application sources of samples_ch32v00x_ch32fun/ (common layout; only these two devices are verified) and build
# per target into build/<target>/; CH32V003 keeps its own samples_ch32v003_ch32fun/ with main.bin in the sample directory.
case "$target" in
  ch32v003) sample="$root/samples_ch32v003_ch32fun/blink_and_read"; bin="$sample/main.bin"; chip=CH32V003; id_type=; target_args=();;
  ch32v002) sample="$root/samples_ch32v00x_ch32fun/blink_and_read"; bin="$sample/build/ch32v002/main.bin"; chip=CH32V002; id_type=0x002; target_args=(TARGET_MCU=CH32V002);;
  ch32v006) sample="$root/samples_ch32v00x_ch32fun/blink_and_read"; bin="$sample/build/ch32v006/main.bin"; chip=CH32V006; id_type=0x006; target_args=(TARGET_MCU=CH32V006);;
  *) echo "error: unknown target $target (use ch32v003, ch32v002 or ch32v006)" >&2; exit 2;;
esac
# TEST ONLY: CH32FUN_TEST_MINICHLINK replaces the pinned minichlink so host tests can simulate programmer output.
# Real use must leave it unset (the pinned externals/ch32fun/minichlink is built and used).
minichlink_bin="${CH32FUN_TEST_MINICHLINK:-$fun/minichlink/minichlink}"
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
    make -C "$sample" build PREFIX=riscv64-unknown-elf "${target_args[@]}"
    [[ -f "$bin" ]] || { echo "BUILD FAILED: artifact $bin missing" >&2; exit 1; }
    echo "BUILD OK: $bin";;
  programmer)
    "$0" check
    make -C "$fun/minichlink" minichlink CFLAGS='-O0 -g3 -Wall -std=gnu17 -DCH32V003 -I. -DMINICHLINK'
    echo "programmer: $fun/minichlink/minichlink";;
  flash)
    [[ -f "$bin" ]] || { echo "FLASH FAILED: build artifact $bin missing; run build $target first" >&2; exit 1; }
    [[ -n "${CH32FUN_TEST_MINICHLINK:-}" ]] || "$0" programmer
    if [[ -n "$id_type" ]]; then
      # Identify the chip type from the identification area BEFORE writing; stop on mismatch/unreadable/mix-up.
      id_result=0
      id_output="$("$minichlink_bin" -r + 0x1ffff704 4 -b 2>&1)" || id_result=$?
      printf '%s\n' "$id_output"
      id_line="$(printf '%s\n' "$id_output" | sed -n 's/^1ffff704: \([0-9a-fA-F][0-9a-fA-F]\) \([0-9a-fA-F][0-9a-fA-F]\) \([0-9a-fA-F][0-9a-fA-F]\) \([0-9a-fA-F][0-9a-fA-F]\).*$/\4\3\2\1/p')"
      if [[ $id_result -ne 0 || ! "$id_line" =~ ^[0-9a-fA-F]{8}$ ]] || (( (16#$id_line >> 20) != id_type )); then
        echo "FLASH FAILED: could not verify $chip chip identifier (expected type $id_type)" >&2
        exit 1
      fi
      if [[ "$id_output" == *'No detected chip.'* || "$id_output" == *'Unknown chip'* ]]; then
        echo 'FLASH FAILED: chip detection error' >&2
        exit 1
      fi
      echo "$chip identifier: 0x$id_line"
    fi
    result=0
    output="$("$minichlink_bin" -w "$bin" flash -b 2>&1)" || result=$?
    printf '%s\n' "$output"
    # The detected name must be exactly the selected chip (a CH32V002/CH32V006 mix-up is rejected, not substring-matched).
    detected="$(printf '%s\n' "$output" | sed -n 's/^Detected \(CH32V[0-9A-Za-z]*\) *$/\1/p' | sort -u)"
    if [[ $result -ne 0 ]] || [[ "$detected" != "$chip" ]] || [[ "$output" != *'Image written.'* ]] || [[ "$output" == *'No detected chip.'* ]] || [[ "$output" == *'Unknown chip'* ]]; then
      echo "FLASH FAILED: programmer failed or did not confirm $target and image write" >&2
      exit 1
    fi
    if [[ "$target" == ch32v006 ]]; then
      # CH32V006: a full-size readback must equal the artifact before any observation.
      size="$(stat -c %s "$bin")"
      rb="$(mktemp)"; trap 'rm -f "$rb"' EXIT
      rb_result=0
      rb_output="$("$minichlink_bin" -r "$rb" flash "$size" -b 2>&1)" || rb_result=$?
      printf '%s\n' "$rb_output"
      if [[ $rb_result -ne 0 || "$rb_output" == *'No detected chip.'* || "$rb_output" == *'Unknown chip'* ]] || ! cmp -s "$bin" "$rb"; then
        echo 'FLASH FAILED: readback is not identical to the artifact' >&2
        exit 1
      fi
      echo 'FLASH OK, READBACK MATCHED (runtime unverified)'
    else
      echo 'FLASH OK (runtime unverified)'
    fi;;
  *) echo "usage: $0 {check|build|programmer|flash} [ch32v003|ch32v002|ch32v006]" >&2; exit 2;;
esac
