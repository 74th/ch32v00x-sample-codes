# Tasks

## 1. Test foundation and scope inventory

- [ ] 1.1 Add `pyproject.toml` and `uv.lock` with supported Python, pytest, and pyserial; configure unit tests as the default and register explicit `hil` plus peripheral markers; verify `uv run pytest` performs no USB/programmer writes and passes on a host without hardware.
- [ ] 1.2 Move or adapt the existing `hardware/pico-tester/test_measure.py` cases into the unit-test layout without losing the six protocol/discovery cases; verify the old analysis behavior and exit classifications remain covered.
- [ ] 1.3 Create the CH32V003/ch32fun verification matrix covering existing manual checks and proposed GPIO, UART, I2C, SPI, ADC, timer/PWM, watchdog/sleep tests; classify each as direct port, equivalent standard-ch32fun test, extralibs-excluded, or not yet automatable and verify every book-code `*-ch32fun` sample is accounted for.
- [ ] 1.4 Define the public HIL configuration schema for DUT identity, Pico identity, pin/net mapping, voltage and protection conditions, timeouts, and readback policy; add validation tests for missing, conflicting, and unsafe settings.

## 2. Human wiring deliverables

- [ ] 2.1 Expand `hardware/wiring.md` with prerequisite voltage checks and power ownership, common-GND rules, prohibited Pico–DUT power connection, safe connect/disconnect sequence, Pico safe-state check, and recovery steps; verify a reviewer can follow the baseline GPIO setup without relying on prior chat or logs.
- [ ] 2.2 Add peripheral-specific tables to `hardware/wiring.md` for GPIO input/output, UART, I2C, SPI, PWM/timer measurement, and ADC stimulus, including CH32V003F4P6 and Pico physical pins, signal direction, series resistors, I2C pull-ups, ADC RC components, and manual switches; verify every table maps to a named HIL configuration.
- [ ] 2.3 Create a KiCad `.kicad_sch` representation under `hardware/` using the same net names and component values as the Markdown/configuration, and export an SVG or PDF for tool-free review; verify KiCad electrical-rule review is recorded and the source and export open successfully.
- [ ] 2.4 Add a repeatable consistency check or review script for Markdown/config/KiCad net names, pin numbers, and component values; verify intentional mismatch fixtures fail or document the fields that still require human review.

## 3. Pico protocol and safe GPIO baseline

- [ ] 3.1 Refactor the Pico firmware into protocol, pin ownership/safe-state, and capability modules; implement request IDs, version/capability query, classified errors, and `RESET_SAFE`; verify host-side unit tests cover valid, unknown, malformed, and timed-out requests.
- [ ] 3.2 Implement the Python fixture client with explicit serial selection, post-flash USB re-enumeration wait, capability negotiation, and legacy GPIO-v1 compatibility during migration; verify mocked zero/one/multiple-device and restart cases.
- [ ] 3.3 Implement GPIO drive, sample, and edge/period/duty commands with allowlisted pins and conflict rejection; verify firmware/host protocol tests and a documented Pico loopback HIL cover normal, boundary, timeout, and safe-reset behavior.
- [ ] 3.4 Build and flash the Pico using the pinned SDK/tool conditions, run the GPIO loopback on hardware, and write a timestamped `okf/log/` record containing wiring, commands, tool/source revisions, measured results, failures, and remaining uncertainty.

## 4. End-to-end CH32V003 GPIO HIL

- [ ] 4.1 Extract reusable DUT build, minichlink flash-output validation, binary-size readback, compare, and reset operations while keeping all programmer paths under `externals/ch32fun`; verify unit tests reject disconnected/unknown/wrong-device false-success output.
- [ ] 4.2 Add pytest fixtures that expose environment check, Pico prepare, DUT build, flash, readback, reset, measure/assert, and cleanup as separate reported phases; verify injected failures at every phase preserve the primary failure and report cleanup outcome.
- [ ] 4.3 Add the `blink_and_read` CH32V003 HIL test and a single documented command that performs the complete workflow; verify build, flash/readback, and runtime mismatch remain distinguishable.
- [ ] 4.4 Execute the complete GPIO HIL on the reviewed wiring, confirm safe state after both pass and intentional failure, and record the experiment in a timestamped `okf/log/` entry without claiming success for unobserved stages.

## 5. Pico UART capability, then DUT UART HIL

- [ ] 5.1 Implement configurable UART transmit/receive with received bytes, framing status, and timeout reporting; verify Pico loopback at supported boundary baud/frame settings before using it against a DUT.
- [ ] 5.2 Document and review the UART wiring/configuration, run the Pico UART self-test on hardware, and record measured results in `okf/log/`.
- [ ] 5.3 Add a minimal standard-ch32fun CH32V003 UART echo/known-frame sample under `samples_ch32v003_ch32fun/` without extralibs, with provenance and expected behavior; verify build independently of hardware.
- [ ] 5.4 Add and run the UART HIL for Pico-to-DUT and DUT-to-Pico data, verify byte/frame/timeout assertions and safe cleanup, and record the actual experiment.

## 6. Pico I2C capability, then DUT I2C HIL

- [ ] 6.1 Implement Pico I2C master and slave roles with address, direction, byte, ACK/NACK, timeout, and bus-error reporting; verify loopback or an independently known I2C target exercises both roles before DUT use.
- [ ] 6.2 Document and review open-drain wiring and external pull-up values, run Pico I2C self-tests on hardware, and record measured bus conditions and results in `okf/log/`.
- [ ] 6.3 Add minimal standard-ch32fun CH32V003 I2C master and slave samples without extralibs, with provenance and explicit transaction contracts; verify both build independently.
- [ ] 6.4 Add and run I2C HIL in both DUT roles, verify address/data/ACK/NACK and negative-address cases, and record actual results and limitations.

## 7. Pico SPI capability, then DUT SPI HIL

- [ ] 7.1 Implement Pico SPI master and slave roles with mode, bit order, clock, chip-select, and full-duplex data reporting; verify supported modes and timeout/error cases with loopback or an independent target.
- [ ] 7.2 Document and review SPI direction/chip-select wiring, run Pico SPI self-tests on hardware, and record settings and results in `okf/log/`.
- [ ] 7.3 Add a minimal standard-ch32fun CH32V003 SPI sample without `ch32v003_SPI.h` or other extralibs, with provenance and expected transfers; verify it builds independently.
- [ ] 7.4 Add and run SPI HIL for the DUT roles selected in the matrix, verify transfer data and mode mismatch detection, and record actual results.

## 8. Timing, PWM, and ADC capabilities

- [ ] 8.1 Implement edge-timestamp based frequency, period, pulse-width, and duty measurement with declared ranges/resolution; verify it against Pico-generated known waveforms at boundary settings and record the self-test.
- [ ] 8.2 Add standard-ch32fun CH32V003 timer/PWM samples and HIL assertions without extralibs; verify build first, then measure frequency/duty on hardware and record actual tolerances.
- [ ] 8.3 Implement ADC stimulus using Pico PWM plus the documented external RC, including settle time and safe range enforcement; calibrate against an independent voltage measurement and record the circuit, environmental conditions, errors, and valid tolerance.
- [ ] 8.4 Add a standard-ch32fun CH32V003 ADC sample without `ch32v003_GPIO_branchless.h`, then add multi-level and boundary HIL assertions; verify build, applied voltage, reported ADC range, and cleanup separately and record actual results.

## 9. Reset, watchdog, and sleep observations

- [ ] 9.1 Define observable GPIO/reset-signature sequences for watchdog and sleep tests that Pico can distinguish from power loss or fixture timeout; update the matrix and wiring docs and verify the expected state machine with unit tests.
- [ ] 9.2 Extend the Pico/host protocol for bounded long-running sequence and reappearance observations while retaining cancellation and safe reset; verify timeout, restart, and interrupted-run cases with self-tests.
- [ ] 9.3 Add standard-ch32fun CH32V003 watchdog/sleep samples selected by the matrix, without extralibs, and corresponding HIL tests; verify build, flash, observed transition/reset, and post-test recoverability separately and record actual results.

## 10. Integrated acceptance and handoff

- [ ] 10.1 Run all unit tests from a clean dependency sync and verify they pass without attached hardware or writes; run static/configuration checks including OpenSpec strict validation and wiring consistency.
- [ ] 10.2 Run each available HIL marker independently and the supported CH32V003 suite as one command on the reviewed setup; verify skips name missing capabilities or excluded extralibs rather than reporting false success.
- [ ] 10.3 Update README and Pico tester documentation with exact `uv` commands, destructive effects, prerequisites, marker selection, recovery, result interpretation, and known precision limits; verify commands against a clean checkout where practical.
- [ ] 10.4 Review all experiment logs for purpose, wiring/tools/source conditions, commands, results, failures, and unknowns; verify actual measurements, user reports, and inference are distinguished and no `xprivate/` content or secrets are included.

## Workflow follow-up

- Archive the change only after the selected HIL acceptance tests have been physically observed and the main specs are ready to sync.
- Keep extralibs-dependent book-code samples explicitly out of scope until a separate change is proposed.
