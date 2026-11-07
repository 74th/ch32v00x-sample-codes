# SDKの出所と利用条件

コピー元: https://github.com/openwch/ch32v003
固定revision: `4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7`

対象ファイルの元の著作権・利用条件を保持する。現行ファイルにはApache-2.0の表示はなく、以下のWCH製マイコンへの使用条件がある。リポジトリ全体をApache-2.0として扱わない。

> Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
> Attention: This software (modified or not) and binary are used for
> microcontroller manufactured by Nanjing Qinheng Microelectronics.

`system_ch32v00x.c`だけ、外部水晶を使わない48 MHz HSI設定に変更し、その旨をファイル内に記載した。他のコピーは無改変。`ch32v00x_conf.h`（コピーした公式ドライバのヘッダ集約）、Makefile、`wch.mk`、サンプルmain.cは本作業で作成。

参考にしたCLIビルド例（コードのコピーなし）:
- https://github.com/wuxx/CH32V003-makefile-example/blob/master/Makefile
- https://github.com/cjacker/ch32v_evt_makefile_gcc_project_template

必要なCoreヘッダ、Startup、リンカスクリプト、System、GPIO/RCCドライバ、および公式Delay関数を使うためのDebugとそのUART依存ドライバをコピー。サンプルではDelay関数だけを使用し、未使用関数はリンク時に除去する。ビルド時にexternalsの公式SDKを参照しない。

下表のSHA-256はコピー元（変更前）の値。

| 配置先 | コピー元 | SHA-256 |
|---|---|---|
| `sdk/Core/core_riscv.h` | `EVT/EXAM/SRC/Core/core_riscv.h` | `04e0ca5c7f2832a8c4f5054ea461522b461c99246464dc6f6939cc87dde9c5d2` |
| `sdk/Startup/startup_ch32v00x.S` | `EVT/EXAM/SRC/Startup/startup_ch32v00x.S` | `a6965f9cba4b522459bf777bdb5f01aaf6600f4c2f079485a5e698ce37155009` |
| `sdk/Ld/Link.ld` | `EVT/EXAM/SRC/Ld/Link.ld` | `3a26b485bfc1666f7caa6253983678f47235dfa8ee829133bf89449bce703b8a` |
| `sdk/Peripheral/inc/ch32v00x.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x.h` | `3462556b6040bfbc09139931d0da732822a4876d30b1ea015aad7d8f267a2bf3` |
| `sdk/Peripheral/inc/ch32v00x_gpio.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_gpio.h` | `bad5cacb2e7aa99bad14e735442ff47e59ad3666836d51ebf6176bc6d1962aaf` |
| `sdk/Peripheral/inc/ch32v00x_rcc.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_rcc.h` | `11d1b071225b5d8d3b7d1ff7a4cb2c4babe623be1f7c2685b1a2b6f54c785e5b` |
| `sdk/Peripheral/src/ch32v00x_gpio.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_gpio.c` | `f50c5113885af92c0eed7fbdfbf91d61d63f068d73bfab25eee3e98dc3388637` |
| `sdk/Peripheral/src/ch32v00x_rcc.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_rcc.c` | `5d0ae70b301aa9dd88cacbcd4007f7c2c37d327afac7c5b4928c4c91e9c5ae12` |
| `sdk/System/system_ch32v00x.c` | `EVT/EXAM/GPIO/GPIO_Toggle/User/system_ch32v00x.c` | `6f88861a19676065b8ca1d5662b41666cd9e0be4528bcf31d3e54008c9d59063` |
| `sdk/System/system_ch32v00x.h` | `EVT/EXAM/GPIO/GPIO_Toggle/User/system_ch32v00x.h` | `4cc94c5ef68d12c7b15e78b08be14c86e67d6088d07f42a568da29ee0e24895e` |

| `sdk/Debug/debug.c` | `EVT/EXAM/SRC/Debug/debug.c` | `54708ad1b1fc2e4ed65092e4ed3b3d20149854308ed789968756961705454b4a` |
| `sdk/Debug/debug.h` | `EVT/EXAM/SRC/Debug/debug.h` | `ca1df930465755a0c7672f930dbf0f7df6d91850be5b197c7ae1701701e1362f` |
| `sdk/Peripheral/inc/ch32v00x_usart.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_usart.h` | `180d8d95d1c5eb9dac962683096d619a6515ae4e12e6147d1f9e33107a55a8a9` |
| `sdk/Peripheral/src/ch32v00x_usart.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_usart.c` | `316d5582ccb41ac0f4696a6f1cb3de80564c695f0b05f34e8640d9c8b5173ee5` |

追加コピー（周辺サンプル用、全て無改変・同一revision、上と同じWCH製マイコン向け使用条件）。書籍wch_sdk例が使うADC、DMA、I2C、SPI、TIM、IWDG、PWR、EXTI、NVICのためのmiscのみ。

| 配置先 | コピー元 | SHA-256 |
|---|---|---|
| `sdk/Peripheral/inc/ch32v00x_adc.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_adc.h` | `5c40f05d909e718a95933cb5c02fb85e241471d67cb588af779f987d6197720b` |
| `sdk/Peripheral/src/ch32v00x_adc.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_adc.c` | `100092a8f683aca9097a5bf15e933f2b5750284853647a78bdc4e5c637e587e3` |
| `sdk/Peripheral/inc/ch32v00x_dma.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_dma.h` | `70e3e96c6f45b26fb599c4749c1fa93492ae676a499b53bc526bb2961c878509` |
| `sdk/Peripheral/src/ch32v00x_dma.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_dma.c` | `7ed553d998d7f6278411536e967d7b3afa40ed0bc6e42371df42b7160203f3bb` |
| `sdk/Peripheral/inc/ch32v00x_i2c.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_i2c.h` | `db8b81a779be5d60dae90c70656a58969040883f56de7a951d8a5d8265a76c75` |
| `sdk/Peripheral/src/ch32v00x_i2c.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_i2c.c` | `2dbab71655cdba0999bcdb400e4b1eab95f67372e0fe581efefe2f46a10596ce` |
| `sdk/Peripheral/inc/ch32v00x_spi.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_spi.h` | `057ea1a147302bfbe507e18382b65f023503ed1a7775ba5ce430340901097a1b` |
| `sdk/Peripheral/src/ch32v00x_spi.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_spi.c` | `e4f204b1b7a2a47701eaef69475aa80f1ff036d24d0f2b3523ad88174a59d18f` |
| `sdk/Peripheral/inc/ch32v00x_tim.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_tim.h` | `104f3baadc05ec8ee1ab321b19e627421315fe0758b616bee90e57b29832e1a9` |
| `sdk/Peripheral/src/ch32v00x_tim.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_tim.c` | `1b6a7f74e67d5c7a51dd4c3d8ed9b8cf750a7dd2da37efe46ddda5548662bd35` |
| `sdk/Peripheral/inc/ch32v00x_iwdg.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_iwdg.h` | `9e5f04a17cad8b7d48849b91c81e8ccd217bda372e7731ed26bd64b3d5ed1126` |
| `sdk/Peripheral/src/ch32v00x_iwdg.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_iwdg.c` | `611e902eb4d1edb0e5c84ccb195d06a00b21a216bc9eb34739ceada77687e7a5` |
| `sdk/Peripheral/inc/ch32v00x_pwr.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_pwr.h` | `777414840b69849a0f688387e078fd061adb8393c2ea2366b2d3b17cb69d1d2c` |
| `sdk/Peripheral/src/ch32v00x_pwr.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_pwr.c` | `63973a45fd4c598f5509a6e20c5af01681d480d1ab2188e99b1d9518cfa7a0c0` |
| `sdk/Peripheral/inc/ch32v00x_exti.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_exti.h` | `4bfb0c43bf236cb78142e5f0f6164f50effa7d9858b6c69a3b7fd5d1d2dcf69c` |
| `sdk/Peripheral/src/ch32v00x_exti.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_exti.c` | `4437f6b60677015da0eadde62b3090f79acba37d5398f9db34590e948532a8ae` |
| `sdk/Peripheral/inc/ch32v00x_misc.h` | `EVT/EXAM/SRC/Peripheral/inc/ch32v00x_misc.h` | `5457b507473de3fe01f3b87f6df84a08b87da299883cac9ba240d452d273167d` |
| `sdk/Peripheral/src/ch32v00x_misc.c` | `EVT/EXAM/SRC/Peripheral/src/ch32v00x_misc.c` | `5b6c6aa0f762571fef90cf33e9ad27b5a12bb276c054d7879ae0446df5ba1ff9` |

追加コピー（`__WFI`/`__WFE`が参照する`WFE`の実体。無改変・同一revision、同じWCH製マイコン向け使用条件）。

| 配置先 | コピー元 | SHA-256 |
|---|---|---|
| `sdk/Core/core_riscv.c` | `EVT/EXAM/SRC/Core/core_riscv.c` | `847fe62d585aab6e6c2ee860429d2567bba3218733d0ebe41f06cee1d3c248f1` |
