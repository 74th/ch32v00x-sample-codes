# 診断ソース（change fix-ch32v00x-sample-findings）

- 記録: 2026-11-08 JST。[本体のログ](2026-11-08-2137-fix-ch32v00x-sample-findings.md) と [006 のログ](2026-11-08-2237-ch32v006-sample-findings.md) で使った使い捨ての診断ファームとホスト側スクリプトの全文。サンプルとしては維持しない。
- build: ch32fun 版は `samples_ch32v00x_ch32fun/target.mk` と固定 ch32fun の `ch32fun.mk` を include する Makefile で `make build PREFIX=riscv64-unknown-elf TARGET_MCU=CH32V00x`（funconfig.h は `HSI_VALUE 24000000`。`diag_swio` だけ `FUNCONF_USE_DEBUGPRINTF 1` を追加）。WCH SDK 版は `samples_ch32v00{2,6}_wch/wch.mk` を include（`PERIPH :=`）。Arduino 版は各デバイスの `sketch.yaml` と `arduino.mk`。i2c_slave の診断は `make build SAMPLE_SOURCES=<複製>`。
- ホスト側は `uv run python <script>` で実行（`tests/hil` のヘルパーと `ch32hil` を利用）。

## diag_analog/main.c

```c
/* DIAGNOSTIC (not a maintained sample): does the pinned ch32fun funAnalogInit()/funAnalogRead() return on CH32V00x?
 * UART PD5 115200. Boot: "A" before funAnalogInit, "B" after it returns, then every 200 ms "r<PA1 ch1 value>\n".
 * A SysTick compare interrupt fires 300 ms after "A" (and after each read start); if the stage is still before "B" (or inside a read) it prints
 * "T<stage>:<CTLR2 hex>\n" (timeout report) and stops. PA1 is driven by the fixture (GP12) through its RC. */
#include "ch32fun.h"
static volatile int stage;
static void put(uint8_t c) { while (!(USART1->STATR & USART_FLAG_TXE)) {} USART1->DATAR = c; }
static void puts_(const char *s) { while (*s) put(*s++); }
static void hex(uint32_t v) { const char *h = "0123456789abcdef"; int s = 28; while (s > 0 && !((v >> s) & 15)) s -= 4; for (; s >= 0; s -= 4) put(h[(v >> s) & 15]); }
static void dec(uint32_t v) { char b[11]; int i = 0; do { b[i++] = '0' + v % 10; v /= 10; } while (v); while (i) put(b[--i]); }
void SysTick_Handler(void) __attribute__((interrupt));
void SysTick_Handler(void)
{
	SysTick->SR = 0;
	SysTick->CTLR &= ~SYSTICK_CTLR_STIE;   /* one shot; the counter keeps running for Delay_Ms */
	if (stage == 1 || stage == 3) { put('T'); put('0' + stage); put(':'); hex(ADC1->CTLR2); put('\n'); while (1) {} }
}
static void arm(void)   /* compare match 300 ms from now (SysTick counts HCLK, set up by SystemInit) */
{
	SysTick->SR = 0;
	SysTick->CMP = SysTick->CNT + FUNCONF_SYSTEM_CORE_CLOCK / 1000 * 300;
	SysTick->CTLR |= SYSTICK_CTLR_STIE;
}
int main(void)
{
	SystemInit();
	RCC->APB2PCENR |= RCC_APB2Periph_GPIOD | RCC_APB2Periph_GPIOA | RCC_APB2Periph_USART1;
	GPIOD->CFGLR &= ~(0xf << (4 * 5));
	GPIOD->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5);
	GPIOA->CFGLR &= ~(0xf << (4 * 1));           /* PA1 analog input (CNF 00, MODE 0) */
	USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
	USART1->CTLR2 = USART_StopBits_1;
	USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
	USART1->CTLR1 |= CTLR1_UE_Set;
	Delay_Ms(50);
	puts_("A");
	stage = 1;
	NVIC_EnableIRQ(SysTick_IRQn);
	arm();
	funAnalogInit();
	stage = 2;
	puts_("B:"); hex(ADC1->CTLR2); put('\n');
	while (1) {
		stage = 3; arm();
		int v = funAnalogRead(1);
		stage = 4; SysTick->CTLR &= ~SYSTICK_CTLR_STIE;
		put('r'); dec(v); put('\n');
		Delay_Ms(200);
	}
}
```

## diag_ws/main.c

```c
/* DIAGNOSTIC (not maintained): idle level of PC6 (SPI1 MOSI) around one WS2812 frame from the pinned helper.
 * t=0..1.5 s: WS2812BDMAInit() only (no frame); t=1.5 s: one frame (6 LEDs); t=3.0 s: SPI1 disabled (SPE=0);
 * t=4.0 s: PC6 switched to a plain GPIO output driven Low. The host samples GP7 every 20 ms. */
#include "ch32fun.h"
#include <stdint.h>
#define WS2812DMA_IMPLEMENTATION
#define WSGRB
#define LED_NUM 6
#include "ws2812b_dma_spi_led_driver.h"
uint32_t WS2812BLEDCallback(int ledno) { return 0x00A5FF + ledno; }
int main()
{
	SystemInit();
	WS2812BDMAInit();
	Delay_Ms(1500);
	WS2812BDMAStart(LED_NUM);
	while (WS2812BLEDInUse) {}
	Delay_Ms(1500);
	SPI1->CTLR1 &= ~CTLR1_SPE_Set;
	Delay_Ms(1000);
	GPIOC->CFGLR &= ~(0xf << (4 * 6));
	GPIOC->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP) << (4 * 6);
	GPIOC->BSHR = 1u << (16 + 6);
	while (1) {}
}
```

## diag_mul_fun/main.c

```c
/* DIAGNOSTIC (not maintained): ch32fun build (-march=rv32ec_zmmul). Prints "H<hash>\n" every 300 ms on PD5. */
#include "ch32fun.h"
#include "mulcore.h"
static void put(uint8_t c) { while (!(USART1->STATR & USART_FLAG_TXE)) {} USART1->DATAR = c; }
int main(void)
{
	SystemInit();
	RCC->APB2PCENR |= RCC_APB2Periph_GPIOD | RCC_APB2Periph_USART1;
	GPIOD->CFGLR &= ~(0xf << (4 * 5));
	GPIOD->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5);
	USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
	USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
	USART1->CTLR1 |= CTLR1_UE_Set;
	while (1) {
		uint32_t h = mul_hash();
		put('H'); for (int s = 28; s >= 0; s -= 4) put("0123456789abcdef"[(h >> s) & 15]); put('\n');
		Delay_Ms(300);
	}
}
```

## diag_mul_wch002/main.c

```c
/* DIAGNOSTIC (not maintained): official WCH SDK build (-march=rv32ec_zmmul_zicsr). Prints "H<hash>\n" every 300 ms. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>
#include "mulcore.h"
int main(void)
{
	SystemCoreClockUpdate();
	Delay_Init();
	USART_Printf_Init(115200);
	while (1) { printf("H%08lx\n", (unsigned long)mul_hash()); Delay_Ms(300); }
}
```

## mulcore.h

```c
/* DIAGNOSTIC (not maintained): multiply instruction check. Inputs are volatile so nothing is folded at compile time.
 * For every pair (a,b) of the 12 inputs: lo = a*b (mul), hs = high32(int64 a*b) (mulh), hu = high32(uint64 a*b) (mulhu),
 * hsu = high32(int64 a * uint64 b) (mulhsu). FNV-1a 32 over the 4 result words (little-endian bytes) of all 144 pairs. */
#include <stdint.h>
static volatile uint32_t mul_in[12] = {0u, 1u, 0xffffffffu, 2u, 0x7fffffffu, 0x80000000u, 0x12345678u, 0xdeadbeefu,
                                       3u, 0xfffffffdu, 0xffffu, 0x10000u};
__attribute__((noinline)) static uint32_t m_lo(uint32_t a, uint32_t b) { return a * b; }
__attribute__((noinline)) static uint32_t m_hs(int32_t a, int32_t b) { return (uint32_t)(((int64_t)a * (int64_t)b) >> 32); }
__attribute__((noinline)) static uint32_t m_hu(uint32_t a, uint32_t b) { return (uint32_t)(((uint64_t)a * (uint64_t)b) >> 32); }
__attribute__((noinline)) static uint32_t m_hsu(int32_t a, uint32_t b) { return (uint32_t)(((int64_t)a * (int64_t)(uint64_t)b) >> 32); }
static uint32_t fnv(uint32_t h, uint32_t w) { for (int i = 0; i < 4; i++) { h ^= (w >> (8 * i)) & 0xff; h *= 16777619u; } return h; }
static uint32_t mul_hash(void)
{
	uint32_t h = 2166136261u;
	for (int i = 0; i < 12; i++)
		for (int j = 0; j < 12; j++) {
			uint32_t a = mul_in[i], b = mul_in[j];
			h = fnv(h, m_lo(a, b)); h = fnv(h, m_hs((int32_t)a, (int32_t)b));
			h = fnv(h, m_hu(a, b)); h = fnv(h, m_hsu((int32_t)a, b));
		}
	return h;
}
```

## diag_gpio/main.c

```c
/* DIAGNOSTIC (not maintained): GPIO modes on the fixed fixture wiring, driven by 1-character commands on USART1
 * (PD6 RX <- Pico GP8, PD5 TX -> Pico GP9, 115200 8N1). Replies are short lines.
 *  F/U/D : PA1 floating / pull-up (ODR=1) / pull-down (ODR=0) input; then sample PA1 every 1 ms for 1000 ms and reply
 *          "<c><initial>,<ms of first change or -1>,<final>\n" (PA1 has 10 kOhm + 1 uF from GP12).
 *  1/2/3 : PC0 push-pull output with raw MODE bits = 1/2/3 (CNF=00), level high; '!' then sets it low. Reply "m<n>\n".
 *  o / z : PC0 open-drain output (MODE=1, CNF=01) with ODR 1 / 0. Reply "o\n" / "z\n".
 *  q / w : PC1 open-drain output (4.7 kOhm pull-up on the fixture) with ODR 1 / 0. Reply "q\n" / "w\n".
 *  E     : EXTI line 1 = PA1, rising and falling, counters reset. Reply "E\n".  C : reply "C<rising>,<falling>\n". */
#include "ch32fun.h"
static volatile uint32_t n_rise, n_fall;
static void put(uint8_t c) { while (!(USART1->STATR & USART_FLAG_TXE)) {} USART1->DATAR = c; }
static void puts_(const char *s) { while (*s) put(*s++); }
static void dec(int32_t v) { char b[12]; int i = 0; if (v < 0) { put('-'); v = -v; } do { b[i++] = '0' + v % 10; v /= 10; } while (v); while (i) put(b[--i]); }
static int getc_(void) { while (!(USART1->STATR & USART_FLAG_RXNE)) {} return USART1->DATAR & 0xff; }
static void cfg(GPIO_TypeDef *g, int pin, uint32_t v) { g->CFGLR = (g->CFGLR & ~(0xfu << (4 * pin))) | (v << (4 * pin)); }
static int pa1(void) { return (GPIOA->INDR >> 1) & 1; }
void EXTI7_0_IRQHandler(void) __attribute__((interrupt));
void EXTI7_0_IRQHandler(void)
{
	if (EXTI->INTFR & EXTI_Line1) { EXTI->INTFR = EXTI_Line1; if (pa1()) n_rise++; else n_fall++; }
}
static void pulltest(int c)
{
	if (c == 'F') cfg(GPIOA, 1, GPIO_CNF_IN_FLOATING);
	else { GPIOA->BSHR = (c == 'U') ? (1u << 1) : (1u << (16 + 1)); cfg(GPIOA, 1, GPIO_CNF_IN_PUPD); }
	int first = pa1(), changed = -1;
	for (int ms = 1; ms <= 1000; ms++) { Delay_Ms(1); if (changed < 0 && pa1() != first) changed = ms; }
	put(c); dec(first); put(','); dec(changed); put(','); dec(pa1()); put('\n');
}
int main(void)
{
	SystemInit();
	RCC->APB2PCENR |= RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOC | RCC_APB2Periph_GPIOD | RCC_APB2Periph_USART1 | RCC_APB2Periph_AFIO;
	cfg(GPIOD, 5, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF);
	cfg(GPIOD, 6, GPIO_CNF_IN_FLOATING);
	cfg(GPIOA, 1, GPIO_CNF_IN_FLOATING);
	USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx | USART_Mode_Rx;
	USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
	USART1->CTLR1 |= CTLR1_UE_Set;
	puts_("R\n");
	while (1) {
		int c = getc_();
		switch (c) {
		case 'F': case 'U': case 'D': pulltest(c); break;
		case '1': case '2': case '3': GPIOC->BSHR = 1u << 0; cfg(GPIOC, 0, (uint32_t)(c - '0')); put('m'); put(c); put('\n'); break;
		case '!': GPIOC->BSHR = 1u << 16; puts_("L\n"); break;
		case 'o': GPIOC->BSHR = 1u << 0; cfg(GPIOC, 0, 1 | GPIO_CNF_OUT_OD); puts_("o\n"); break;
		case 'z': GPIOC->BSHR = 1u << 16; cfg(GPIOC, 0, 1 | GPIO_CNF_OUT_OD); puts_("z\n"); break;
		case 'q': GPIOC->BSHR = 1u << 1; cfg(GPIOC, 1, 1 | GPIO_CNF_OUT_OD); puts_("q\n"); break;
		case 'w': GPIOC->BSHR = 1u << 17; cfg(GPIOC, 1, 1 | GPIO_CNF_OUT_OD); puts_("w\n"); break;
		case 'E':
			cfg(GPIOA, 1, GPIO_CNF_IN_FLOATING);
			AFIO->EXTICR &= ~(3u << 2);          /* line 1 <- port A (00) */
			EXTI->RTENR |= EXTI_Line1; EXTI->FTENR |= EXTI_Line1; EXTI->INTFR = EXTI_Line1;
			n_rise = n_fall = 0; EXTI->INTENR |= EXTI_Line1; NVIC_EnableIRQ(EXTI7_0_IRQn); puts_("E\n"); break;
		case 'C': put('C'); dec(n_rise); put(','); dec(n_fall); put('\n'); break;
		default: break;
		}
	}
}
```

## diag_comm/main.c

```c
/* DIAGNOSTIC (not maintained): USART1 baud/parity/error handling and SPI1 16-bit frames on the fixed fixture.
 * USART1 PD5 TX / PD6 RX. Bytes other than the commands are echoed. Commands:
 *  'b' <digit> : reply "B<d>\n" at the current setting, then switch: 0 115200 8N1, 1 57600, 2 38400, 3 19200, 4 9600,
 *                5 2400 (all 8N1), 6 115200 8E1, 7 115200 8O1 (parity: 9-bit word incl. parity, PCE=1).
 *  's'         : reply "S<pe>,<fe>,<ne>,<ore>\n" (error counts since the last 's'), then clear them.
 *  'x'         : reply "x\n", then after 300 ms send five SPI1 16-bit frames (mode 0, MSB first, /64, DFF=1) of 0xA55A, each
 *                with PC0 as software CS, 300 ms apart; the first reply is remembered. 'y' replies "Y<rx hex>\n". */
#include "ch32fun.h"
static volatile uint32_t pe, fe, ne, ore; static uint16_t spi_rx;
static void put(uint8_t c) { while (!(USART1->STATR & USART_FLAG_TXE)) {} USART1->DATAR = c; }
static void dec(uint32_t v) { char b[11]; int i = 0; do { b[i++] = '0' + v % 10; v /= 10; } while (v); while (i) put(b[--i]); }
static void hex4(uint32_t v) { for (int s = 12; s >= 0; s -= 4) put("0123456789abcdef"[(v >> s) & 15]); }
static int getc_(void)
{
	while (1) {
		uint32_t st = USART1->STATR;
		if (st & (USART_FLAG_RXNE | USART_FLAG_ORE | USART_FLAG_FE | USART_FLAG_PE | USART_FLAG_NE)) {
			int d = USART1->DATAR & 0xff;   /* reading STATR then DATAR clears the error flags */
			if (st & USART_FLAG_PE) pe++;
			if (st & USART_FLAG_FE) fe++;
			if (st & USART_FLAG_NE) ne++;
			if (st & USART_FLAG_ORE) ore++;
			if (st & USART_FLAG_RXNE) return d;
		}
	}
}
static const uint32_t bauds[] = {115200, 57600, 38400, 19200, 9600, 2400, 115200, 115200};
static void setcfg(int i)
{
	while (!(USART1->STATR & USART_FLAG_TC)) {}
	USART1->CTLR1 = 0;
	USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + bauds[i] / 2) / bauds[i];
	uint32_t c = USART_Mode_Tx | USART_Mode_Rx;
	if (i == 6) c |= USART_WordLength_9b | USART_Parity_Even;
	if (i == 7) c |= USART_WordLength_9b | USART_Parity_Odd;
	USART1->CTLR1 = c | CTLR1_UE_Set;
}
static void spi16(void)
{
	SPI1->CTLR1 = SPI_CTLR1_MSTR | SPI_CTLR1_SSI | SPI_CTLR1_SSM | SPI_CTLR1_BR_2 | SPI_CTLR1_BR_0 | SPI_CTLR1_DFF;
	SPI1->CTLR1 |= SPI_CTLR1_SPE;
	for (int k = 0; k < 5; k++) {
		Delay_Ms(300);
		GPIOC->BSHR = 1u << 16;
		while (!(SPI1->STATR & SPI_STATR_TXE)) {}
		SPI1->DATAR = 0xA55A;
		while (!(SPI1->STATR & SPI_STATR_RXNE)) {}
		uint16_t v = SPI1->DATAR; if (k == 0) spi_rx = v;   /* the Pico slave answers only the first frame */
		while (SPI1->STATR & SPI_STATR_BSY) {}
		GPIOC->BSHR = 1u << 0;
	}
}
int main(void)
{
	SystemInit();
	RCC->APB2PCENR |= RCC_APB2Periph_GPIOC | RCC_APB2Periph_GPIOD | RCC_APB2Periph_USART1 | RCC_APB2Periph_SPI1;
	GPIOD->CFGLR = (GPIOD->CFGLR & ~((0xfu << 20) | (0xfu << 24))) | ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << 20) | (GPIO_CNF_IN_FLOATING << 24);
	GPIOC->CFGLR = (GPIOC->CFGLR & ~((0xfu << 0) | (0xfu << 20) | (0xfu << 24) | (0xfu << 28))) |
		((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP) << 0) | ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << 20) |
		((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << 24) | (GPIO_CNF_IN_FLOATING << 28);
	GPIOC->BSHR = 1u << 0;
	setcfg(0);
	while (1) {
		int c = getc_();
		if (c == 'b') { int d = getc_() - '0'; if (d < 0 || d > 7) continue; put('B'); put('0' + d); put('\n'); setcfg(d); }
		else if (c == 's') { put('S'); dec(pe); put(','); dec(fe); put(','); dec(ne); put(','); dec(ore); put('\n'); pe = fe = ne = ore = 0; }
		else if (c == 'x') { put('x'); put('\n'); spi16(); }
		else if (c == 'y') { put('Y'); hex4(spi_rx); put('\n'); }
		else put((uint8_t)c);
	}
}
```

## diag_stby/main.c

```c
/* DIAGNOSTIC (not maintained): ch32fun Standby woken by an EXTI event on PA1 (rising and falling edge).
 * 5 s initial wait (recovery window; prints "W\n"), then: PA1 floating input, EXTI line 1 <- port A as an EVENT
 * (EVENR, RTENR, FTENR), PDDS=1, SLEEPDEEP=1, loop { __WFE(); SystemInit(); wait 800 ms; print "K<n>,<PA1>\n" } on PD5.
 * n lives in RAM, so consecutive numbers show that execution resumed (no reset). Based on ch32fun examples/standby_btn. */
#include "ch32fun.h"
static void put(uint8_t c) { while (!(USART1->STATR & USART_FLAG_TXE)) {} USART1->DATAR = c; }
static void dec(uint32_t v) { char b[11]; int i = 0; do { b[i++] = '0' + v % 10; v /= 10; } while (v); while (i) put(b[--i]); }
static void uart(void)
{
	RCC->APB2PCENR |= RCC_APB2Periph_GPIOD | RCC_APB2Periph_USART1;
	GPIOD->CFGLR = (GPIOD->CFGLR & ~(0xfu << 20)) | ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << 20);
	USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
	USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
	USART1->CTLR1 |= CTLR1_UE_Set;
}
int main(void)
{
	SystemInit();
	uart();
	put('W'); put('\n');
	Delay_Ms(5000);
	RCC->APB2PCENR |= RCC_APB2Periph_GPIOA | RCC_AFIOEN;
	RCC->APB1PCENR |= RCC_APB1Periph_PWR;
	GPIOA->CFGLR = (GPIOA->CFGLR & ~(0xfu << 4)) | (GPIO_CNF_IN_FLOATING << 4);
	AFIO->EXTICR &= ~(3u << 2);
	EXTI->EVENR |= EXTI_Line1; EXTI->RTENR |= EXTI_Line1; EXTI->FTENR |= EXTI_Line1;
	PWR->CTLR |= PWR_CTLR_PDDS;
	PFIC->SCTLR |= (1 << 2);
	put('S'); put('\n');
	while (!(USART1->STATR & USART_FLAG_TC)) {}
	uint32_t n = 0;
	for (;;) {
		__WFE();
		SystemInit();
		uart();
		Delay_Ms(800);
		put('K'); dec(n++); put(','); put('0' + ((GPIOA->INDR >> 1) & 1)); put('\n');
		while (!(USART1->STATR & USART_FLAG_TC)) {}
	}
}
```

## diag_iwdg/main.c

```c
/* DIAGNOSTIC (not maintained): IWDG time to reset with the WCH watchdog sample's setting (prescaler 128, reload 2000).
 * Boot: print "<PSCR digit><Y if RLDR reads 2000 else N><I if IWDGRSTF else o>\n" (read back after PVU/RVU cleared). No
 * feeding. After 1.5 s (HSI-timed), print 'A'+k every 100 ms (k = 0, 1, ...). The last letter before the next header
 * gives the time to reset: between 1.5 + 0.1*k and 1.5 + 0.1*(k+1) s (plus the boot time). Fits a 32-byte capture. */
#include "ch32fun.h"
static void put(uint8_t c) { while (!(USART1->STATR & USART_FLAG_TXE)) {} USART1->DATAR = c; }
static void dec(uint32_t v) { char b[11]; int i = 0; do { b[i++] = '0' + v % 10; v /= 10; } while (v); while (i) put(b[--i]); }
int main(void)
{
	SystemInit();
	uint32_t rst = (RCC->RSTSCKR >> 29) & 1;   /* IWDGRSTF */
	RCC->RSTSCKR |= (1u << 24);                 /* RMVF: clear the reset flags */
	RCC->APB2PCENR |= RCC_APB2Periph_GPIOD | RCC_APB2Periph_USART1;
	GPIOD->CFGLR = (GPIOD->CFGLR & ~(0xfu << 20)) | ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << 20);
	USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
	USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
	USART1->CTLR1 |= CTLR1_UE_Set;
	IWDG->CTLR = 0x5555;
	IWDG->PSCR = 5;              /* /128 */
	IWDG->RLDR = 2000;
	IWDG->CTLR = 0xAAAA;
	IWDG->CTLR = 0xCCCC;         /* start (the reload just happened) */
	while (IWDG->STATR & (IWDG_PVU | IWDG_RVU)) {}
	put('0' + (IWDG->PSCR & 7)); put((IWDG->RLDR & 0xfff) == 2000 ? 'Y' : 'N'); put(rst ? 'I' : 'o'); put('\n');
	Delay_Ms(1500);
	for (int k = 0;; k++) { put('A' + k); Delay_Ms(100); }
}
```

## diag_swio/main.c

```c
/* DIAGNOSTIC (not maintained): printf over SWIO (ch32fun debug printf). Prints "swio <n>" every 300 ms. */
#include "ch32fun.h"
#include <stdio.h>
int main(void) { SystemInit(); for (int n = 0;; n++) { printf("swio %d\n", n); Delay_Ms(300); } }
```

## diag_pc4/main.c

```c
/* DIAGNOSTIC (not maintained): PC4 as a plain push-pull GPIO output (no timer), toggled every 20 ms, to separate the
 * pin/wiring path (PC4 -> GP15) from the TIM1_CH4 function. PC0 toggles in phase as a reference (-> GP5). */
#include "ch32fun.h"
int main(void)
{
	SystemInit();
	RCC->APB2PCENR |= RCC_APB2Periph_GPIOC;
	GPIOC->CFGLR = (GPIOC->CFGLR & ~((0xfu << 16) | 0xfu)) | ((GPIO_Speed_10MHz | GPIO_CNF_OUT_PP) << 16) | (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
	for (;;) { GPIOC->BSHR = (1u << 4) | 1u; Delay_Ms(20); GPIOC->BSHR = (1u << 20) | (1u << 16); Delay_Ms(20); }
}
```

## ard_a/diag_printf_a/diag_printf_a.ino

```cpp
// DIAGNOSTIC (not maintained): printf after USART_Printf_Init only (no Serial.begin), as the book tried.
#include <stdio.h>
uint32_t n = 0;
void setup() { USART_Printf_Init(115200); printf("P1\r\n"); }
void loop() { printf("p%lu\r\n", (unsigned long)n++); delay(300); }
```

## ard_b/diag_printf_b/diag_printf_b.ino

```cpp
// DIAGNOSTIC (not maintained): printf after Serial.begin (Serial on USART1 PD5), plus Serial.print for comparison.
#include <stdio.h>
uint32_t n = 0;
void setup() { Serial.begin(115200); printf("Q1\r\n"); Serial.print("S\r\n"); }
void loop() { printf("q%lu\r\n", (unsigned long)n++); Serial.print("s\r\n"); delay(300); }
```

## i2c_slave_diag_after.c

`e8f76c4` の `samples_ch32v002_wch/i2c_slave/main.c` に対する差分（before 版は ClockSpeed の行がなく、DIAG の printf だけ）:

```diff
@@ -122,6 +122,7 @@
   NVIC_Init(&NVIC_InitStructure);
 
   // I2Cの設定
+  I2C_InitTSturcture.I2C_ClockSpeed = 100000; /* DIAG: proposed fix */
   I2C_InitTSturcture.I2C_Mode = I2C_Mode_I2C;
   // I2Cスレーブアドレスを指定
   I2C_InitTSturcture.I2C_OwnAddress1 = I2C_ADDRESS << 1;
@@ -142,6 +143,7 @@
   NVIC_SetPriority(I2C1_EV_IRQn, 2 << 4);
   NVIC_EnableIRQ(I2C1_ER_IRQn);
 
+  printf("C2=%x CK=%x\r\n", I2C1->CTLR2, I2C1->CKCFGR); /* DIAG */
   // printf("I2C1->CTLR1: %4x\r\n", I2C1->CTLR1);
   // printf("I2C1->CTLR2: %4x\r\n", I2C1->CTLR2);
   // printf("I2C1->CKCFGR: %4x\r\n", I2C1->CKCFGR);
```

## diag_uart.py

```python
"""Diagnostic: flash an already-built artifact (guarded), read back, then reset and capture DUT UART (PD5) from boot.
usage: uv run python diag_uart.py <device> <framework> <sample_dir> <count> <timeout_ms> [baud] [--noflash]"""
import sys, tempfile
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil")]
from serial.tools import list_ports
from ch32hil.dut import Dut
from ch32hil.pico import discover
from arduino.common import reset_and_capture_uart
from test_blink_and_read import _prepare
dev, fw, sd, count, tmo = sys.argv[1], sys.argv[2], Path(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
baud = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].isdigit() else 115200
dut = Dut(sd, target=dev, framework=fw)
port = discover(list_ports.comports, None, 30)
_prepare(port, 5)
if "--noflash" not in sys.argv:
    print("artifact", dut.binary, flush=True)
    dut.flash(); 
    with tempfile.TemporaryDirectory() as t: dut.readback(Path(t))
    print("flash+readback OK, chip_id", hex(dut.chip_id or 0), flush=True)
from arduino import common as c
rx, f = c.reset_during(dut, lambda: c.uart_receive(port, count, tmo, baud), tmo / 1000, 0.3)
print("fields", {k: v for k, v in f.items() if k != "rx"})
print(repr(rx.decode("latin-1")))
```

## diag_i2c_tail.py

```python
"""Diagnostic: reset the DUT, then Pico master reads 4 bytes from pointer 0x2E of the DUT slave 0x10 (array 0x30)."""
import sys, time
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil")]
from serial.tools import list_ports
from ch32hil.dut import Dut
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client
dev, fw, sd = sys.argv[1], sys.argv[2], Path(sys.argv[3])
dut = Dut(sd, target=dev, framework=fw)
port = discover(list_ports.comports, None, 30)
for trial in range(int(sys.argv[4]) if len(sys.argv) > 4 else 3):
    _prepare(port, 5)
    dut.reset(); time.sleep(1.0)
    def act(c):
        c.negotiate(["I2C_MASTER"])
        out = []
        for tx, n in (("2e", 0), ("-", 4), ("2c", 4)):
            r = c.request("I2C_MASTER", 0x10, tx, n, 500); out.append((tx, n, r.ok, r.fields)); time.sleep(0.3)
        return out
    for row in _with_client(port, 8, act): print(trial, row)
```

## diag_helper_cb.py

```python
"""Diagnostic for ch32fun i2c_slave_helper: does a read-only transfer trigger the write callback?
Flash (guarded) + readback the built artifact, reset, then: obs, read-only x2, obs, write 1 byte, obs, pointer-only, obs.
obs = one transaction: write pointer 00 then repeated-START read 5 (write_count, write_reg, write_len, read_count, read_reg)."""
import sys, time, tempfile
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil")]
from serial.tools import list_ports
from ch32hil.dut import Dut
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client
dev = sys.argv[1]
dut = Dut(ROOT / "samples_ch32v00x_ch32fun/i2c_slave_helper", target=dev, framework="ch32fun")
port = discover(list_ports.comports, None, 30)
_prepare(port, 5)
if "--noflash" not in sys.argv:
    dut.flash()
    with tempfile.TemporaryDirectory() as t: dut.readback(Path(t))
    print("flash+readback OK", dut.binary, flush=True)
for trial in range(3):
    _prepare(port, 5); dut.reset(); time.sleep(1.0)
    def act(c):
        c.negotiate(["I2C_MASTER"])
        log = []
        def req(name, tx, n):
            r = c.request("I2C_MASTER", 0x42, tx, n, 500); time.sleep(0.2)
            f = dict(x.split("=", 1) for x in r.fields if "=" in x); log.append((name, r.ok, f.get("rx"))); return f.get("rx")
        req("obs0", "00", 5)
        req("readonly_a", "-", 4); req("readonly_b", "-", 2)
        req("obs1", "00", 5)
        req("write_0x11_1byte", "115a", 0)
        req("obs2", "00", 5)
        req("pointer_only_0x20", "20", 0)
        req("obs3", "00", 5)
        return log
    for row in _with_client(port, 10, act): print(trial, row)
```

## diag_analog_run.py

```python
"""Run the funAnalogInit diagnostic: guarded flash+readback, boot capture, PA1 driven high/low (GP12) captures,
then restore ch32fun blink_and_read (flash + readback). usage: diag_analog_run.py <device>"""
import sys, tempfile, time
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil")]
from serial.tools import list_ports
from ch32hil.dut import Dut
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client
from arduino import common as c
dev = sys.argv[1]
S = Path(__file__).parent
dut = Dut(S / "diag_analog", target=dev, framework="ch32fun")
port = discover(list_ports.comports, None, 30)
_prepare(port, 5)
dut.flash()
with tempfile.TemporaryDirectory() as t: dut.readback(Path(t))
print("diag flash+readback OK", dut.binary, "chip", hex(dut.chip_id or 0), flush=True)
for i in range(3):
    rx, f = c.reset_during(dut, lambda: c.uart_receive(port, 32, 1500), 1.5, 0.3)
    print("boot", i, f.get("uart_errors"), repr(rx.decode("latin-1")), flush=True)
def drive(level):
    _with_client(port, 4, lambda cl: cl.request("GPIO_DRIVE", 12, level, 500))
for level in (1, 0, 1, 0):
    drive(level); rx, f = c.uart_receive(port, 32, 1000)
    print("PA1 driven", level, repr(rx.decode("latin-1")), flush=True)
blink = Dut(ROOT / "samples_ch32v00x_ch32fun/blink_and_read", target=dev, framework="ch32fun")
blink.build(); blink.flash()
with tempfile.TemporaryDirectory() as t: blink.readback(Path(t))
print("restored blink_and_read (flash+readback OK)", blink.binary)
```

## diag_pulse.py

```python
"""Diagnostic: build+flash (guarded)+readback a sample, then GPIO_PULSE on a Pico pin N times.
usage: diag_pulse.py <device> <framework> <sample_dir> <pico_pin> <count> [timeout_ms] [--noflash] [make args...]"""
import sys, tempfile, time
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil")]
from serial.tools import list_ports
from ch32hil.dut import Dut
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client
a = [x for x in sys.argv[1:] if not x.startswith("--")]
dev, fw, sd, pin, count = a[0], a[1], Path(a[2]), int(a[3]), int(a[4])
tmo = int(a[5]) if len(a) > 5 else 2000
make = tuple(x for x in sys.argv[1:] if "=" in x and not x.startswith("--"))
a = [x for x in a if "=" not in x]
dev, fw, sd, pin, count = a[0], a[1], Path(a[2]), int(a[3]), int(a[4])
tmo = int(a[5]) if len(a) > 5 else 2000
dut = Dut(sd, target=dev, framework=fw, make_args=make)
port = discover(list_ports.comports, None, 30)
_prepare(port, 5)
if "--noflash" not in sys.argv:
    dut.build(); dut.flash()
    with tempfile.TemporaryDirectory() as t: dut.readback(Path(t))
    print("flash+readback OK", dut.binary, flush=True)
    dut.reset(); time.sleep(1.5)
for i in range(count):
    r = _with_client(port, tmo / 1000 + 3, lambda c: c.request("GPIO_PULSE", pin, tmo))
    print(i, r.ok, r.fields, flush=True)
```

## diag_ws_run.py

```python
"""Run the WS2812 idle-level diagnostic: guarded flash+readback, then reset during a 250 x 20 ms GPIO_SAMPLE of GP7."""
import sys, tempfile, itertools
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil")]
from serial.tools import list_ports
from ch32hil.dut import Dut
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client
from arduino import common as c
dev = sys.argv[1]
dut = Dut(Path(__file__).parent / "diag_ws", target=dev, framework="ch32fun")
port = discover(list_ports.comports, None, 30)
_prepare(port, 5)
dut.flash()
with tempfile.TemporaryDirectory() as t: dut.readback(Path(t))
print("flash+readback OK", dut.binary, flush=True)
for i in range(3):
    def op():
        return _with_client(port, 9, lambda cl: cl.request("GPIO_SAMPLE", 7, 250, 20000))
    r = c.reset_during(dut, op, 6, 0.3)
    s = dict(x.split("=", 1) for x in r.fields if "=" in x)["samples"]
    print(i, [(v, len(list(g))) for v, g in itertools.groupby(s)], flush=True)
```

## diag_gpio_run.py

```python
"""Run the GPIO diagnostic (see diag_gpio/main.c): guarded flash+readback, then command/response over UART with Pico
GPIO_DRIVE (GP12 -> PA1 RC) and GPIO_SAMPLE (GP5 = PC0, GP10 = PC1). usage: diag_gpio_run.py <device> [--noflash]"""
import sys, tempfile, time, itertools
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil")]
from serial.tools import list_ports
from ch32hil.dut import Dut
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client
dev = sys.argv[1]
dut = Dut(Path(__file__).parent / "diag_gpio", target=dev, framework="ch32fun")
port = discover(list_ports.comports, None, 30)
_prepare(port, 5)
if "--noflash" not in sys.argv:
    dut.flash()
    with tempfile.TemporaryDirectory() as t: dut.readback(Path(t))
    print("flash+readback OK", dut.binary, "chip", hex(dut.chip_id or 0), flush=True)
dut.reset(); time.sleep(1.0)
def cmd(c, ms=300, n=16):
    r = _with_client(port, ms / 1000 + 3, lambda cl: cl.request("UART_XFER", "DUT", 115200, 8, "N", 1, c.encode().hex(), n, ms))
    f = dict(x.split("=", 1) for x in r.fields if "=" in x)
    return bytes.fromhex(f["rx"]).decode("latin-1") if f.get("rx", "-") != "-" else ""
def drive(level, ms=500):
    _with_client(port, 4, lambda cl: cl.request("GPIO_DRIVE", 12, level, ms))
def sample(pin, n=50, us=1000):
    r = _with_client(port, 4, lambda cl: cl.request("GPIO_SAMPLE", pin, n, us))
    s = dict(x.split("=", 1) for x in r.fields if "=" in x)["samples"]
    return [(v, len(list(g))) for v, g in itertools.groupby(s)]
for rep in range(2):
    print("-- rep", rep)
    for c, pre in (("F", 1), ("D", 1), ("F", 0), ("U", 0)):
        drive(pre); print(f"pull {c} after drive {pre}:", repr(cmd(c, 1500)), flush=True)
    for m in "123":
        a = cmd(m); hi = sample(5); b = cmd("!"); lo = sample(5)
        print(f"PC0 MODE={m}: {a!r} high-> {hi}  {b!r} low-> {lo}", flush=True)
    a = cmd("1"); pp = sample(5, 100)
    a = cmd("o"); od1 = sample(5, 100); b = cmd("z"); od0 = sample(5, 100)
    print("PC0 PP high", pp, "| OD odr=1", od1, "| OD odr=0", od0, flush=True)
    a = cmd("q"); q = sample(10, 100); b = cmd("w"); w = sample(10, 100)
    print("PC1 OD odr=1 (pull-up 4.7k)", q, "| OD odr=0", w, flush=True)
    drive(0, 500); print("EXTI arm", repr(cmd("E")))
    for k in range(3):
        drive(1, 300); drive(0, 300)
    print("EXTI counts after 3 high/low cycles (rising,falling):", repr(cmd("C")), flush=True)
```

## diag_comm_run.py

```python
"""Run the communication diagnostic (diag_comm/main.c): guarded flash+readback, UART baud/parity/error checks with the
Pico UART_XFER (DUT mode), SPI 16-bit frame with Pico SPI_SLAVE. usage: diag_comm_run.py <device> [--noflash]"""
import sys, tempfile, time
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil")]
from serial.tools import list_ports
from ch32hil.dut import Dut
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client
dev = sys.argv[1]
dut = Dut(Path(__file__).parent / "diag_comm", target=dev, framework="ch32fun")
port = discover(list_ports.comports, None, 30)
_prepare(port, 5)
if "--noflash" not in sys.argv:
    dut.flash()
    with tempfile.TemporaryDirectory() as t: dut.readback(Path(t))
    print("flash+readback OK", dut.binary, flush=True)
dut.reset(); time.sleep(1.0)
def x(data, n, baud=115200, par="N", ms=600):
    r = _with_client(port, ms / 1000 + 3, lambda cl: cl.request("UART_XFER", "DUT", baud, 8, par, 1, data.encode("latin-1").hex(), n, ms))
    f = dict(v.split("=", 1) for v in r.fields if "=" in v)
    return (bytes.fromhex(f["rx"]).decode("latin-1") if f.get("rx", "-") != "-" else ""), f.get("uart_errors"), f.get("actual_baud")
for d, baud in ((1, 57600), (2, 38400), (3, 19200), (4, 9600), (5, 2400), (0, 115200)):
    a = x(f"b{d}", 3)
    e = x("HELLO123", 8, baud, ms=1500)
    s = x("s", 9, baud, ms=1500)
    back = x("b0", 3, baud, ms=1500)
    print(f"baud {baud}: switch {a[0]!r} | echo {e[0]!r} pico_err={e[1]} pico_actual={e[2]} | {s[0]!r} | back {back[0]!r}", flush=True)
print("parity even DUT:", x("b6", 3))
print("  Pico 8E1 ->", x("HELLO", 5, par="E"), x("s", 9, par="E"))
print("  Pico 8O1 ->", x("HELLO", 5, par="O"), x("s", 9, par="E"))
print("  Pico 8N1 ->", x("HELLO", 5, par="N"), x("s", 9, par="E"))
print("  back", x("b0", 3, par="E"))
print("framing: DUT 115200 8N1, Pico sends 'UUUU' at 57600 ->", x("UUUU", 8, 57600, ms=500), x("s", 9))
print("framing: Pico sends 0x00 x4 at 57600 ->", x("\x00\x00\x00\x00", 8, 57600, ms=500), x("s", 9))
print("SPI16: arm", x("x", 2))
r = _with_client(port, 6, lambda cl: cl.request("SPI_SLAVE", "3cc3", "MODE0"))
print("  Pico SPI_SLAVE:", r.ok, r.fields)
time.sleep(1.5)
print("  DUT rx:", x("y", 6))
```

## diag_log_run.py

```python
"""Try to receive the Serial/printf text that follows an emulated sensor transaction: serve the transaction with the Pico
(I2C_SLAVE SHT31 / SPI_SLAVE ADT7310 / I2C_MASTER to the WCH slave), then start a 32-byte UART capture at once.
usage: diag_log_run.py <device> <which: i2c_master|spi_master|wch_i2c_slave|i2c_slave_test_master>"""
import sys, tempfile, time
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil"), str(ROOT / "tests/hil/arduino")]
from serial.tools import list_ports
from ch32hil.dut import Dut
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client
from arduino.common import uart_receive
from arduino.test_i2c import _slave, SHT31, SHT31_REPLY
from arduino.test_spi import _spi, VALID
dev, which = sys.argv[1], sys.argv[2]
if which == "wch_i2c_slave": sd, fw = ROOT / f"samples_{dev}_wch/i2c_slave", "wch"
else: sd, fw = ROOT / f"samples_{dev}_arduino/{which}", "arduino"
dut = Dut(sd, target=dev, framework=fw)
port = discover(list_ports.comports, None, 30)
_prepare(port, 5)
dut.build(); dut.flash()
with tempfile.TemporaryDirectory() as t: dut.readback(Path(t))
print("flash+readback OK", dut.binary, flush=True)
dut.reset(); time.sleep(0.5)
for i in range(4):
    if which == "i2c_master":
        s = _slave(port, SHT31, 2, SHT31_REPLY, 7000); tag = f"served rx={s.get('rx')} sent={s.get('sent')}"
    elif which == "spi_master":
        s = _spi(port, VALID); tag = f"served rx={s.get('rx')}"
    elif which == "wch_i2c_slave":
        r = _with_client(port, 4, lambda c: c.request("I2C_MASTER", 0x10, "20", 4, 500)); tag = f"read {r.fields}"
    else:
        s = _slave(port, 0x10, 5, "00102030", 7000); tag = f"served {s}"
    rx, f = uart_receive(port, 32, 1500)
    print(i, tag, "->", repr(rx.decode("latin-1")), f.get("uart_errors"), flush=True)
```

## diag_stby_run.py

```python
"""Run the Standby+EXTI diagnostic: guarded flash+readback, reset, wait for Standby, then: idle capture (no edge), and
PA1 edges from GP12 (drive 300 ms, then capture). Recovery: cycle the WCH-LinkE 3.3 V and flash ch32fun blink_and_read
inside the 5 s window, then read back. usage: diag_stby_run.py <device>"""
import sys, tempfile, time, subprocess
from pathlib import Path
ROOT = Path("<repo>")
sys.path[:0] = [str(ROOT), str(ROOT / "hardware/pico-tester"), str(ROOT / "tests/hil")]
from serial.tools import list_ports
from ch32hil.dut import Dut, MINICHLINK
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client
from arduino.common import uart_receive
dev = sys.argv[1]
dut = Dut(Path(__file__).parent / "diag_stby", target=dev, framework="ch32fun")
port = discover(list_ports.comports, None, 30)
_prepare(port, 5)
try:
    dut.flash()
    with tempfile.TemporaryDirectory() as t: dut.readback(Path(t))
    print("flash+readback OK", dut.binary, flush=True)
    _with_client(port, 4, lambda c: c.request("GPIO_DRIVE", 12, 0, 500))
    dut.reset(); time.sleep(6.5)
    r = subprocess.run([str(MINICHLINK), "-i"], capture_output=True, text=True, timeout=30)
    print("debugger during Standby:", (r.stdout + r.stderr).strip().splitlines()[-1:], flush=True)
    rx, f = uart_receive(port, 32, 2000); print("idle 2 s, no edge:", repr(rx.decode("latin-1")), flush=True)
    for k in range(3):
        for level in (1, 0):
            _with_client(port, 4, lambda c: c.request("GPIO_DRIVE", 12, level, 300))
            rx, f = uart_receive(port, 32, 1500)
            print(f"edge to {level}:", repr(rx.decode("latin-1")), flush=True)
finally:
    blink = Dut(ROOT / "samples_ch32v00x_ch32fun/blink_and_read", target=dev, framework="ch32fun", ready_timeout=0)
    blink.build()
    subprocess.run([str(MINICHLINK), "-t"], capture_output=True, timeout=30); time.sleep(1.5)
    subprocess.run([str(MINICHLINK), "-3"], capture_output=True, timeout=30)
    r = subprocess.run([str(MINICHLINK), "-w", str(blink.binary), "flash", "-b"], capture_output=True, text=True, timeout=60)
    print("recovery write:", "Image written." in r.stdout + r.stderr, flush=True)
    blink.ready_timeout = 20.0
    with tempfile.TemporaryDirectory() as t: blink.readback(Path(t))
    print("recovery readback OK", blink.binary)
```

