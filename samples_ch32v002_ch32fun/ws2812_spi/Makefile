TARGET := main
TARGET_MCU := CH32V002
CH32FUN := ../../externals/ch32fun/ch32fun
# Helper dependency: pinned submodule's extralibs/ws2812b_dma_spi_led_driver.h (ch32fun.mk already adds extralibs to -I).
override GENERATED_LD_FILE := generated_ch32v002.ld
include $(CH32FUN)/ch32fun.mk
all: build
