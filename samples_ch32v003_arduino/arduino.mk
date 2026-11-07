# Arduino Core CH32 サンプル共通のビルド規則（design D4）。
# make build は scripts/arduino.sh で sketch.yaml の profile（固定 core）を使って compile し、
# 成果物を main.bin / main.elf にコピーする。PREFIX は ch32fun サンプルとの互換のために受け取り、使わない。
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
SKETCH_DIR := $(abspath .)
SKETCH := $(notdir $(SKETCH_DIR))
DEVICE_DIR := $(notdir $(abspath ..))
PROFILE ?= ch32v003
SUPPLIER ?= official
BUILD_DIR := $(ROOT)/.arduino/build/$(DEVICE_DIR)/$(SKETCH)
ARDUINO_FLAGS ?=
PREFIX ?=

.PHONY: all build clean
all: build

build:
	rm -f main.bin main.elf
	$(ROOT)/scripts/arduino.sh compile $(SUPPLIER) $(SKETCH_DIR) --profile $(PROFILE) --build-path $(BUILD_DIR) $(ARDUINO_FLAGS)
	cp $(BUILD_DIR)/$(SKETCH).ino.bin main.bin
	cp $(BUILD_DIR)/$(SKETCH).ino.elf main.elf
	@echo "BUILD OK: $(SKETCH_DIR)/main.bin"

clean:
	rm -rf main.bin main.elf $(BUILD_DIR)
