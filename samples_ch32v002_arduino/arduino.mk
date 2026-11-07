# CH32V002F4P6 用の Arduino Core CH32 サンプル共通のビルド規則。
# 公式配布 core 1.0.6 には CH32V002 のボード定義がないため、sketch.yaml の profile ch32v002 で
# CH32VM00X / CH32V006K8 を流用し、ここで次を上書きする（okf/log/2026-11-07-2125-arduino-ch32v002-survey.md）。
# - サイズ検査: Flash 16 KB / RAM 4 KB
# - 流用元の Link.ld は MEMORY を 62K/8K に固定し __FLASH_SIZE/__RAM_SIZE を参照しないため、
#   SP の初期値（_eusrstack）と _sbrk の上限（_heap_end）を 4 KB RAM 内へ移す。
#   サイズだけの上書きでは SP が 0x20002000（RAM の外）になり動作しない（実測）。
PROFILE ?= ch32v002
CH32V002_FLAGS := --build-property upload.maximum_size=16384 --build-property upload.maximum_data_size=4096 \
	--build-property "compiler.c.elf.extra_flags=-Wl,--defsym=__FLASH_SIZE=16384 -Wl,--defsym=__RAM_SIZE=4096 -Wl,--defsym=_eusrstack=0x20001000 -Wl,--defsym=_heap_end=0x20000e00"
ARDUINO_FLAGS ?=
override ARDUINO_FLAGS := $(CH32V002_FLAGS) $(ARDUINO_FLAGS)
include $(dir $(lastword $(MAKEFILE_LIST)))../samples_ch32v003_arduino/arduino.mk
