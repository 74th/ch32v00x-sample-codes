# Shared build rules for official WCH SDK samples (CH32V006; SDK from the CH32V002/4/5/6/7 repository). Included by each
# sample's Makefile, like the CH32V003 wch.mk:
#   PERIPH := adc dma          # extra official drivers (gpio, rcc, usart are always built: debug.c needs them)
#   SAMPLE_SOURCES := main.c   # optional; default main.c
#   EXTRA_CFLAGS=-DFOO=1       # optional, usually given on the make command line (then `make clean` first)
#   include ../wch.mk
# Only ./sdk is used; the references under externals/ are never build dependencies.
# Differences from the CH32V003 setup: -DCH32V006 (explicit; the official ch32v00X.h also defaults to CH32V006), Link.ld 62K flash / 8K RAM (the official default),
# upper-case X in the SDK file names, Zmmul in -march (as ch32fun uses for the non-003 CH32V00x parts).
WCH_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
ROOT := $(abspath $(WCH_DIR)/..)
TOOLCHAIN ?= $(ROOT)/.arduino/official/data/packages/WCH/tools/riscv-wch-gcc/15.2.0
WCH_PREFIX ?= $(TOOLCHAIN)/bin/riscv32-wch-elf-
CC := $(WCH_PREFIX)gcc
OBJCOPY := $(WCH_PREFIX)objcopy
SIZE := $(WCH_PREFIX)size
SDK := $(WCH_DIR)sdk
SAMPLE_SOURCES ?= main.c
PERIPH_ALL := $(sort gpio rcc usart $(PERIPH))
SOURCES := $(SAMPLE_SOURCES) $(SDK)/Debug/debug.c $(SDK)/System/system_ch32v00X.c $(SDK)/Core/core_riscv.c \
  $(foreach p,$(PERIPH_ALL),$(SDK)/Peripheral/src/ch32v00X_$(p).c) $(SDK)/Startup/startup_ch32v00X.S
# Every SDK header, sample header and this file are rebuild triggers (make does not track includes itself).
HEADERS := $(wildcard $(SDK)/Debug/*.h $(SDK)/Core/*.h $(SDK)/System/*.h $(SDK)/Compat/*.h $(SDK)/Peripheral/inc/*.h *.h)
ARCH := -march=rv32ec_zmmul_zicsr -mabi=ilp32e
CPPFLAGS := -DCH32V006 -I. -I$(SDK)/Compat -I$(SDK)/Debug -I$(SDK)/Core -I$(SDK)/System -I$(SDK)/Peripheral/inc
CFLAGS := $(ARCH) -Os -g -Wall -Wextra -ffunction-sections -fdata-sections -msmall-data-limit=8 -mno-save-restore $(EXTRA_CFLAGS)
LDFLAGS := $(ARCH) -nostartfiles --specs=nano.specs --specs=nosys.specs -T$(SDK)/Ld/Link.ld -Wl,--gc-sections,-Map=main.map,--print-memory-usage
.PHONY: build check clean
build: main.bin main.hex
check:
	$(CC) --version
main.elf: $(SOURCES) $(HEADERS) $(SDK)/Ld/Link.ld Makefile $(WCH_DIR)wch.mk
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SOURCES) $(LDFLAGS) -o $@
	$(SIZE) $@
main.bin: main.elf
	$(OBJCOPY) -O binary $< $@
main.hex: main.elf
	$(OBJCOPY) -O ihex $< $@
clean:
	$(RM) main.elf main.bin main.hex main.map
