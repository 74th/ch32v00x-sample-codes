# Original minimal CLI rules; WCH SDK sources are vendored in ../sdk.
ROOT := $(abspath ../..)
TOOLCHAIN ?= $(ROOT)/.arduino/official/data/packages/WCH/tools/riscv-wch-gcc/15.2.0
WCH_PREFIX ?= $(TOOLCHAIN)/bin/riscv32-wch-elf-
CC := $(WCH_PREFIX)gcc
OBJCOPY := $(WCH_PREFIX)objcopy
SIZE := $(WCH_PREFIX)size
SDK := ../sdk
SOURCES := main.c $(SDK)/Debug/debug.c $(SDK)/Peripheral/src/ch32v00x_usart.c $(SDK)/System/system_ch32v00x.c $(SDK)/Peripheral/src/ch32v00x_gpio.c $(SDK)/Peripheral/src/ch32v00x_rcc.c $(SDK)/Startup/startup_ch32v00x.S
HEADERS := $(wildcard $(SDK)/Debug/*.h $(SDK)/Core/*.h $(SDK)/System/*.h $(SDK)/Peripheral/inc/*.h)
ARCH := -march=rv32ec_zicsr -mabi=ilp32e
CPPFLAGS := -I$(SDK)/Debug -I$(SDK)/Core -I$(SDK)/System -I$(SDK)/Peripheral/inc
CFLAGS := $(ARCH) -Os -g -Wall -Wextra -ffunction-sections -fdata-sections -msmall-data-limit=8 -mno-save-restore
LDFLAGS := $(ARCH) -nostartfiles --specs=nano.specs --specs=nosys.specs -T$(SDK)/Ld/Link.ld -Wl,--gc-sections,-Map=main.map,--print-memory-usage
.PHONY: build check clean
build: main.bin main.hex
check:
	$(CC) --version
main.elf: $(SOURCES) $(HEADERS) $(SDK)/Ld/Link.ld Makefile
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SOURCES) $(LDFLAGS) -o $@
	$(SIZE) $@
main.bin: main.elf
	$(OBJCOPY) -O binary $< $@
main.hex: main.elf
	$(OBJCOPY) -O ihex $< $@
clean:
	$(RM) main.elf main.bin main.hex main.map
