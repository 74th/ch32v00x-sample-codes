# Design

## Context

See `proposal.md` for motivation. The current repository contains the upstream book samples under ignored `externals/ch32v003-book-code`; its `blink_and_read-ch32fun` sample selects `CH32V003` and includes `../ch32fun/ch32fun/ch32fun.mk`. The referenced ch32fun submodule is currently uninitialized at gitlink revision `2679ac059f3ada402731e5a10818cc0814e9ec4c`.

The WCH CH32V003 and CH32V00x repositories are also available under `externals/` as comparison sources. Datasheets and reference manuals are private source material under `xprivate/`; their full Markdown conversions must remain ignored. Documentation extraction and toolchain setup can proceed independently, but both must complete before the CH32V003 hardware baseline is finalized.

## Goals / Non-Goals

**Goals:**

- Establish a known-good CH32V003/ch32fun baseline before introducing CH32V002 differences.
- Make build, flash, and runtime observation separate, repeatable stages.
- Keep upstream checkouts read-only and put maintained project artifacts outside `externals/`.
- Preserve the exact source revisions, tool versions, commands, device identity, wiring, and observed result.
- Produce a minimal CH32V002 GPIO sample whose differences from the CH32V003 baseline are explainable from sources.

**Non-Goals:**

- Building the complete multi-peripheral Pico/pytest HIL system beyond the minimum GPIO observation stub.
- Porting every book sample or peripheral.
- Supporting CH32V004/005/006/007 in this change.
- Publishing PDF-to-Markdown conversions or copied manual content.

## Decisions

### 1. Validate the upstream CH32V003 sample before creating a maintained copy

First initialize the book repository's ch32fun submodule at its recorded gitlink and exercise one existing GPIO sample without changing upstream files. Record separate build-only, flash, and runtime-observation commands. After the baseline succeeds, create or adapt project-owned sample and support files outside `externals/`.

This order proves the inherited toolchain independently from repository-owned changes. Copying the sample first was rejected because a failure would combine environment setup with local modifications.

### 2. Use a deterministic GPIO pattern as the minimum runtime contract

Use one documented output pin and a pattern that is distinguishable from reset, constant-high, and constant-low states. Record the pin by MCU port name and physical package pin. Observation may initially use a logic analyzer, oscilloscope, or other explicit measurement; visual LED confirmation alone is insufficient for the recorded baseline.

A peripheral-heavy example was rejected because it adds clock, protocol, and fixture variables before the basic build/flash path is known.

### 3. Gate CH32V002 work on the CH32V003 runtime baseline

The CH32V002 phase begins only after a CH32V003 artifact has been built, flashed, and observed on hardware. The CH32V002 work starts from the smallest proven sample and changes only the target definition, device-dependent initialization, memory configuration, and selected GPIO details that are required.

Working on both devices in parallel was rejected because it would weaken the baseline's value in diagnosing failures.

### 4. Introduce a narrow Raspberry Pi Pico observation stub

Create a minimal Pico firmware and PC-side command path that samples one DUT GPIO, returns a bounded result, and supports timeout and mismatch reporting. Keep its protocol small but versioned so later HIL work can extend it. This change does not require UART/I2C/SPI/ADC stimulus, power switching, or a general fixture framework.

Manual-only observation was rejected because the baseline must support repeatable, machine-readable evidence. Building the complete fixture now was rejected because it would delay validation of the toolchain and first GPIO sample.

### 5. Keep source evidence private and publish derived knowledge

The prerequisite issue converts the CH32V003 datasheet and reference manual into private Markdown under `xprivate/converted/`, with a conversion manifest that records source file identity and conversion method. Implementation may use those files for search and comparison, but only independently summarized facts, source document/version/page references, and validation status may be added to `okf/`.

Committing converted manuals was rejected because the conversion can reproduce substantial copyrighted content.

### 6. Record stage-specific evidence

Each run records four independent states: environment readiness, build, flash, and runtime observation. A later stage cannot turn an earlier failure into a pass. Evidence includes versions and immutable source revisions as well as the commands and observations.

A single pass/fail flag was rejected because it cannot distinguish a compiler problem from a programmer or firmware problem.

## Risks / Trade-offs

- **[The pinned historical ch32fun revision may not support CH32V002]** → Use it only to reproduce the CH32V003 baseline first, then evaluate a newer revision deliberately and document the compatibility change if required.
- **[The default Makefile target may flash as part of `make`]** → Identify or add distinct build-only and flash entry points in project-owned tooling so stages can be reported separately.
- **[Hardware or programmer availability may block runtime validation]** → Report the exact completed stage and leave the result as unverified; never substitute build success for hardware success.
- **[Pin selection may differ by package or conflict with SWIO]** → Confirm the exact package, physical pin, reset state, and alternate functions from the private source extraction before wiring.
- **[Private extracted text may contain OCR or layout errors]** → Retain page references and cross-check critical values against the original PDF and, later, hardware measurements.

## Migration Plan

1. In parallel, complete the private CH32V003 documentation extraction, initialize the pinned ch32fun dependency and capture the tool environment, and build the minimum Pico GPIO observation stub.
2. After those three work streams complete, build, flash, and observe the unchanged CH32V003 baseline.
3. Add project-owned reproducible commands, documentation, and result recording.
4. Derive the CH32V002 changes from the proven baseline and source evidence.
5. Build, flash, and observe the CH32V002 sample, then record the device differences in `okf/`.

Rollback consists of removing project-owned samples and support tooling; upstream checkouts and private source materials remain unchanged.
