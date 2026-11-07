TARGET := main
TARGET_MCU := CH32V003
CH32FUN := ../../externals/ch32fun/ch32fun
# Helper dependency: pinned submodule's examples/i2c_slave/i2c_slave.h (not copied, not modified).
EXTRA_CFLAGS += -I../../externals/ch32fun/examples/i2c_slave
override GENERATED_LD_FILE := generated_ch32v003.ld
include $(CH32FUN)/ch32fun.mk
all: build
