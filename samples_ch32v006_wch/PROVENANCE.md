# CH32V006用SDKの出所と利用条件

コピー元: https://github.com/openwch/ch32v002_004_005_006_007
固定revision: `a835ede9ff3e2dca2c6aa652809b85c9775475d2`（`externals/ch32v002_004_005_006_007`のHEAD。調査用のexternalsで、ビルド依存ではない）

CH32V003用（`../samples_ch32v003_wch/PROVENANCE.md`）とは別のSDK（`../samples_ch32v002_wch/sdk`と同じrevisionのコピーだが、独立して維持する）で、ファイル名は`ch32v00X`（大文字X）、RCCのAPIも`RCC_PB2Periph…`/`RCC_HBPeriph…`と異なる。CH32V003用ヘッダを型番だけ変えて流用していない。
対象ファイルの元の著作権・利用条件を保持する。コピーしたファイルにはApache-2.0の表示はなく、次のWCH製マイコンへの使用条件がある。リポジトリ全体をApache-2.0として扱わない。

> Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
> Attention: This software (modified or not) and binary are used for
> microcontroller manufactured by Nanjing Qinheng Microelectronics.

本作業で作成したもの（WCH由来ではない）: `sdk/System/ch32v00X_conf.h`（コピーしたドライバのヘッダ集約。1行目のコメントのみ006向けに記述）、`sdk/Compat/ch32v00x.h`（`<ch32v00x.h>`を`<ch32v00X.h>`へ橋渡しする1行のヘッダ）、`wch.mk`（`-DCH32V006`、002用LD変更なし）、各サンプルのMakefileとmain.c（書籍コードは`../samples_ch32v003_wch`と同様に移植）。
下表のSHA-256はコピー元（変更前）の値。

| 配置先 | コピー元 | SHA-256 | 変更 |
|---|---|---|---|
| `sdk/Core/core_riscv.c` | `EVT/EXAM/SRC/Core/core_riscv.c` | `077a299ae66bc525d4f44ff36c19addc23537accd399b70d09a9f470957c0439` |  |
| `sdk/Core/core_riscv.h` | `EVT/EXAM/SRC/Core/core_riscv.h` | `9bac791a67ac56c7c0d423cd89144846584ed7d4b6ce85074d26c9e879335b18` |  |
| `sdk/Debug/debug.c` | `EVT/EXAM/SRC/Debug/debug.c` | `87e6ff8e63c80a592f4968a8cc0fe77af0ee5de5af6ccad081b79c3f4010bd41` |  |
| `sdk/Debug/debug.h` | `EVT/EXAM/SRC/Debug/debug.h` | `1bfaf27b932314e5c1233b2d306522ce83a127ae730c5b74eb3e0dac4e243fef` |  |
| `sdk/Ld/Link.ld` | `EVT/EXAM/SRC/Ld/Link.ld` | `21006edc954a7ef3bf759469f003ea6ee1e0fc9ef14c6c728b854bc6d07d676b` | 無改変（既定でCH32V006の62K/8Kブロックが有効、CH32V002/004/005は注釈化）|
| `sdk/Startup/startup_ch32v00X.S` | `EVT/EXAM/SRC/Startup/startup_ch32v00X.S` | `41d831ce3f5bb1f7500cf578b30a3e90cf5aa09b94f026696afc1c6f1e5b2b04` |  |
| `sdk/System/system_ch32v00X.c` | `EVT/EXAM/GPIO/GPIO_Toggle/User/system_ch32v00X.c` | `6f00bb81e9154cdbeae9261245b62824bc7ba8fb3a4eaa710139f8a77675eb9b` | 無改変（既定で`SYSCLK_FREQ_48MHZ_HSI`） |
| `sdk/System/system_ch32v00X.h` | `EVT/EXAM/GPIO/GPIO_Toggle/User/system_ch32v00X.h` | `c607c2db0074dc5419e058c4ad715300547ce94fa13e68f02262c080ee137577` |  |
| `sdk/Peripheral/inc/ch32v00X.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X.h` | `ef1e341b7512da8a7c5380e08abae36c5ae86a6d6a342375516f9ad2caeb5ceb` | 無改変（既定はCH32V006。`wch.mk`は`-DCH32V006`を明示） |
| `sdk/Peripheral/inc/ch32v00X_gpio.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_gpio.h` | `17f7343a5ecb586d551c7345e8df9cea2179c7e0028ca3d7b6db02016ec5d963` |  |
| `sdk/Peripheral/src/ch32v00X_gpio.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_gpio.c` | `21bc1461bfd762dcdac43a6e40cc1f5518217da8af27aa920f86f85f70f5222e` |  |
| `sdk/Peripheral/inc/ch32v00X_rcc.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_rcc.h` | `52cab5112fae29ea0570e84e1a01ac2a4d236f50e7fc8c9868a0024bb299689a` |  |
| `sdk/Peripheral/src/ch32v00X_rcc.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_rcc.c` | `bd3b94ba52399a82a14a655d2751a74acd282cf9ab2d487fa9158b23b5ca2fb7` |  |
| `sdk/Peripheral/inc/ch32v00X_usart.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_usart.h` | `38a08cb679776d90f483a165691254110fd2adfea2015fdf42ed183ff216c365` |  |
| `sdk/Peripheral/src/ch32v00X_usart.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_usart.c` | `570a9c11e3ce4b092d300f5c9650441e29024f232bdcaa1b41e1b2b1971f0218` |  |
| `sdk/Peripheral/inc/ch32v00X_adc.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_adc.h` | `45aa015742aaea8166b90f05c46bd403c9b8225862dff89817606eb9aa2776f6` |  |
| `sdk/Peripheral/src/ch32v00X_adc.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_adc.c` | `ee12c5b54b8615b086f5179bf6fdb8b42b1ae78a9fe8f69a88da015da5e4bc6a` |  |
| `sdk/Peripheral/inc/ch32v00X_dma.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_dma.h` | `5ea3d2a4e1dcbb59f2095feadd054050a7435fa56cc969e4996d521664d49e43` |  |
| `sdk/Peripheral/src/ch32v00X_dma.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_dma.c` | `36e52fabfba35c20c6a8a13cd0ad16899a8730b54cc06052c91c1fcf9115661e` |  |
| `sdk/Peripheral/inc/ch32v00X_i2c.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_i2c.h` | `fe5335779ac63425f4a66b106c1948fe39ebf26d759b523cce126e6398951ba8` |  |
| `sdk/Peripheral/src/ch32v00X_i2c.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_i2c.c` | `6c9ed9266914ea8771563146c4829141f816f38fc066aeb96ec31c95250a9744` |  |
| `sdk/Peripheral/inc/ch32v00X_spi.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_spi.h` | `ea5a7b212cc6ca97e2d2dbc5469180131549a13e7cdfcd9e930d0433432f9fb3` |  |
| `sdk/Peripheral/src/ch32v00X_spi.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_spi.c` | `1ba19da44d1aca24f1c78813d84cc9d18234461d009b665024041f9adccf5342` |  |
| `sdk/Peripheral/inc/ch32v00X_tim.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_tim.h` | `c12b6cc3e2d2736a1a6c05b77b3717391833bc9cd11ef604afd2b704264707d2` |  |
| `sdk/Peripheral/src/ch32v00X_tim.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_tim.c` | `ca3ed1a1cb029c2130bb946c4db944ae5be225860712ea6a3a37e11611c8dd4f` |  |
| `sdk/Peripheral/inc/ch32v00X_iwdg.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_iwdg.h` | `d0bb83fb21b4f2ce13bbdef897661f44eeb8a6a9ac4639e99f6474e9d24de8c2` |  |
| `sdk/Peripheral/src/ch32v00X_iwdg.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_iwdg.c` | `38e31a6410046ddf7dad5406b7b973f52fd5720744112ec6e4cf54bd9e4b19f3` |  |
| `sdk/Peripheral/inc/ch32v00X_pwr.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_pwr.h` | `33c9f0e2baff1159f052a03e0b7808a0d1522abc26c9d5a9d36d9e054779fbe1` |  |
| `sdk/Peripheral/src/ch32v00X_pwr.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_pwr.c` | `d9a5a7bed8f079d87e9a4f059cbb3be4798e15671176466743128c136e75f943` |  |
| `sdk/Peripheral/inc/ch32v00X_exti.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_exti.h` | `c9c6e1bdba5d99e7bee966487ac62e2babdd17bc14f1c638b0f2ac9e89ef2128` |  |
| `sdk/Peripheral/src/ch32v00X_exti.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_exti.c` | `d0d1328129c2992857e3b57f93a345df349970cb46d85093082d510f3aa64498` |  |
| `sdk/Peripheral/inc/ch32v00X_misc.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_misc.h` | `22776dc052eca4b3db08577f8c4c3a09733ca7ff119394ba68d5da326bbd5da4` |  |
| `sdk/Peripheral/src/ch32v00X_misc.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_misc.c` | `5bedd3080cdea6c52a789c6ece760f8ca933d8a12aa2b75fd62cdef75170096b` |  |
| `sdk/Peripheral/inc/ch32v00X_wwdg.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_wwdg.h` | `1784101ecb86cce5705d4f8d60819797cf44546e08215ac240e51cdabbe1fed3` | 無改変（change `add-wwdg-sample` で追加。`sdk/System/ch32v00X_conf.h` の集約にも追加） |
| `sdk/Peripheral/src/ch32v00X_wwdg.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_wwdg.c` | `d68fd78e4373d36a4bdd1ecf00fef1ef7435fe721454423a66b56b11cf661fb7` | 無改変（同上） |
| `sdk/Peripheral/inc/ch32v00X_opa.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00X_opa.h` | `96f297b42ca19aa2f79d095ac658bc85a6276aec335be30addfbc45cb07aa10a` | 無改変（change `add-ch32v006-only-feature-samples` で追加。`sdk/System/ch32v00X_conf.h` の集約にも追加） |
| `sdk/Peripheral/src/ch32v00X_opa.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00X_opa.c` | `78bedd24b12e959f8ee95aa64ba55fa628e989373ba241c94ce9f1a46b524c51` | 無改変（同上） |
