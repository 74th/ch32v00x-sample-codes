# Include AFTER $(CH32FUN)/ch32fun.mk: compile the real main.c instead of $(TARGET).c (recipes expand this lazily).
FILES_TO_COMPILE := $(SYSTEM_C) main.$(TARGET_EXT) $(ADDITIONAL_C_FILES)
