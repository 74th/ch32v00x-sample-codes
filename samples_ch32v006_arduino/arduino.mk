# CH32V006F8P6 用の Arduino Core CH32 サンプル共通のビルド規則。
# 公式配布 core 1.0.6 の CH32VM00X_EVT / CH32V006K8 定義（62 KiB Flash / 8 KiB RAM、48 MHz HSI）をそのまま使う。
# CH32V002 用の Flash/RAM・_eusrstack・_heap_end の上書きは持ち込まない。
PROFILE ?= ch32v006
include $(dir $(lastword $(MAKEFILE_LIST)))../samples_ch32v003_arduino/arduino.mk
