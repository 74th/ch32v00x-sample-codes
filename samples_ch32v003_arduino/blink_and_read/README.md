# blink_and_read（Arduino Core CH32、CH32V003）

## 出典

`externals/ch32v003-book-code/blink_and_read-arduino_core_ch32/blink_and_read-arduino_core_ch32.ino`（book-code 4ce0a1b, CC0 1.0）をそのままコピーした。arduino-cli はスケッチのファイル名とディレクトリ名が一致している必要があるため、ファイル名だけを `blink_and_read.ino` に変えた。

## 変更点

- ソースの変更なし。
- 固定配線（`hardware/wiring-proposal.md`）とそのまま合う: PC0 → Pico GP5、PA1 ← Pico GP12（RC 経由）、PD5（USART1 TX）→ Pico GP9。

## 挙動（ソースから導いた期待値）

- `Serial.begin(115200)` の後に `init`、`start` を出力する。
- `loop()` のたびに `loop <n>`（n は 0 から 1 ずつ増える）を出力する。
- PA1（`INPUT_PULLUP`）が High のとき: PC0 を 500 ms High、500 ms Low（周期 1 s、デューティ 50%）。
- PA1 が Low のとき: PC0 は直前の Low のまま 1 s 待つ（点滅が止まる）。`loop <n>` の出力は約 1 s ごとに続く。

## ビルド

```sh
./scripts/arduino.sh setup
./scripts/arduino.sh core-install official
make -C samples_ch32v003_arduino/blink_and_read build PREFIX=riscv64-unknown-elf
```

`sketch.yaml` の profile `ch32v003` で、公式配布の `WCH:ch32v` 1.0.6 と FQBN `WCH:ch32v:CH32V00x_EVT:pnum=CH32V003F4,clock=48MHz_HSI` に固定している。成果物は `main.bin` / `main.elf`。書き込みは固定 minichlink（`ch32hil` / HIL テスト）で行い、`arduino-cli upload` は使わない。
