# Shared build settings for CH32V002 / CH32V006 ch32fun samples (same application sources, per-target outputs).
# Include this BEFORE the sample's own EXTRA_CFLAGS and BEFORE $(CH32FUN)/ch32fun.mk. The pinned submodule is not modified.
#   make build TARGET_MCU=CH32V006   -> build/ch32v006/main.{elf,bin,hex}, build/ch32v006/generated.ld
# A direct make defaults to CH32V002; HIL and scripts/ch32fun.sh always pass TARGET_MCU explicitly.
TARGET_MCU ?= CH32V002
SUPPORTED_TARGET_MCUS := CH32V002 CH32V006
ifeq ($(filter $(TARGET_MCU),$(SUPPORTED_TARGET_MCUS)),)
$(error TARGET_MCU=$(TARGET_MCU) is not supported here (use one of: $(SUPPORTED_TARGET_MCUS)))
endif
TARGET_DIR := build/$(if $(filter CH32V006,$(TARGET_MCU)),ch32v006,ch32v002)
$(shell mkdir -p $(TARGET_DIR))
TARGET := $(TARGET_DIR)/main
override GENERATED_LD_FILE := $(TARGET_DIR)/generated.ld
# ch32fun.mk names $(TARGET).c as an ELF prerequisite; the real source stays main.c (see target-post.mk).
$(TARGET).c: main.c ;
# make does not notice changed variables: record the effective configuration and rebuild the target's ELF when it changes.
$(TARGET_DIR)/config.stamp: FORCE
	@printf '%s\n' '$(TARGET_MCU) $(EXTRA_CFLAGS)' | cmp -s - $@ || printf '%s\n' '$(TARGET_MCU) $(EXTRA_CFLAGS)' > $@
FORCE:
EXTRA_ELF_DEPENDENCIES += $(TARGET_DIR)/config.stamp
.DEFAULT_GOAL := all
# Pinned ch32fun.mk only defines cv_clean (plain `clean` does not exist there). Clean only the selected target's outputs.
.PHONY: clean
clean:
	rm -rf $(TARGET_DIR)
