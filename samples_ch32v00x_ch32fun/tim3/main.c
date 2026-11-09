/* TIM3 (streamlined timer) sample, plain ch32fun register access (CH32V006 only; not in the book). Same behaviour as
 * samples_ch32v006_wch/tim3 (based on the official EVT example EXAM/TIM/SLTIM_DMA): TIM3 has no output pin, so its CC3 DMA
 * request drives DMA1 channel 1 (RM Table 8-1: on CH32V006 TIM3_CH3 can only trigger DMA1 channel 1), which copies two words
 * alternately to GPIOC->BSHR (set PC0, reset PC0) from a circular 2-entry buffer. TIM3 counts HCLK (48 MHz, no prescaler,
 * counts down): ATRLR = 47999 -> one DMA request, and one PC0 edge, per 1 ms, so PC0 is a 500 Hz square wave.
 *
 * Header gap: the pinned ch32fun (b28d285) declares `#define TIM3 ((ALTM_TypeDef *)TIM3_BASE)` in ch32x00xhw.h but no header
 * defines ALTM_TypeDef, so `TIM3->...` does not compile. The registers are described here instead, as in RM chapter 13
 * (Table 13-2: 16-bit registers at a 4-byte pitch: CTLR 0x00, DMAINTENR 0x04, CNT 0x08, ATRLR 0x0C, CH1CVR..CH4CVR 0x10..0x1C),
 * and the pinned ch32fun is not modified (see also TIM3_CLOCK_EN below). TIM3_BASE and the TIM3_CTLR_* / TIM3_DMAINTENR_* bit macros are from ch32fun.
 * The same offsets are what the WCH SDK's TIM_TypeDef overlay (TIM3_CTLR ... TIM3_CH4CVR) uses. Recheck when ch32fun is updated.
 * CH32V002 has no TIM3: the build stops with #error. USART1 (PD5) prints one line at start. */
#include "ch32fun.h"

#ifndef CH32V006
#error "tim3 needs TIM3, which only the CH32V006 has (CH32V002 has none); build with TARGET_MCU=CH32V006"
#endif

typedef struct {
    volatile uint16_t CTLR;       uint16_t RESERVED0;
    volatile uint16_t DMAINTENR;  uint16_t RESERVED1;
    volatile uint16_t CNT;        uint16_t RESERVED2;
    volatile uint16_t ATRLR;      uint16_t RESERVED3;
    volatile uint16_t CH1CVR;     uint16_t RESERVED4;
    volatile uint16_t CH2CVR;     uint16_t RESERVED5;
    volatile uint16_t CH3CVR;     uint16_t RESERVED6;
    volatile uint16_t CH4CVR;     uint16_t RESERVED7;
} Sltm_t;
#define SLTM3 ((Sltm_t *)TIM3_BASE)

/* Second header gap: the pinned ch32fun's RCC_TIM3EN is 0x2, but the WCH SDK's RCC_PB1Periph_TIM3 and ch32fun's own RCC_TIM3RST are 0x4
 * (PB1PCENR/PB1PRSTR bit 2). With 0x2 TIM3 gets no clock (measured: no PC0 edge), so the bit is written explicitly. */
#define TIM3_CLOCK_EN (1u << 2)
#define TIM3_RELOAD 47999 /* 48 MHz / 48000 = 1 kHz request rate */
#define PC0_SET (1u << 0)
#define PC0_RESET (1u << (16 + 0))

static uint32_t pc0_bshr[2] = {PC0_SET, PC0_RESET};

static void put(uint8_t c)
{
    while (!(USART1->STATR & USART_FLAG_TXE)) {}
    USART1->DATAR = c;
}

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOC | RCC_APB2Periph_GPIOD | RCC_APB2Periph_USART1;
    RCC->PB1PCENR |= TIM3_CLOCK_EN;
    RCC->HBPCENR |= RCC_DMA1EN | RCC_SRAMEN;
    GPIOD->CFGLR &= ~(0xf << (4 * 5));
    GPIOD->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5);
    USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
    USART1->CTLR2 = USART_StopBits_1;
    USART1->CTLR3 = USART_HardwareFlowControl_None;
    USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
    USART1->CTLR1 |= CTLR1_UE_Set;
    for (const char *s = "init tim3 dma toggle pc0 half_period_us=1000\r\n"; *s; ++s) put(*s);

    GPIOC->CFGLR &= ~(0xf << (4 * 0));
    GPIOC->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP) << (4 * 0);

    /* DMA1 channel 1: memory -> GPIOC->BSHR, 32-bit, memory increment, circular, high priority */
    DMA1_Channel1->CFGR = 0;
    DMA1_Channel1->PADDR = (uint32_t)&GPIOC->BSHR;
    DMA1_Channel1->MADDR = (uint32_t)pc0_bshr;
    DMA1_Channel1->CNTR = 2;
    DMA1_Channel1->CFGR = DMA_CFGR1_DIR | DMA_CFGR1_CIRC | DMA_CFGR1_MINC | DMA_CFGR1_PSIZE_1 | DMA_CFGR1_MSIZE_1 | DMA_CFGR1_PL_1;
    DMA1_Channel1->CFGR |= DMA_CFGR1_EN;

    SLTM3->CTLR = TIM3_CTLR_DIR;           /* count down */
    SLTM3->ATRLR = TIM3_RELOAD;
    SLTM3->CH3CVR = 0x10;
    SLTM3->CTLR |= TIM3_CTLR_ARPE;
    SLTM3->DMAINTENR |= TIM3_DMAINTENR_CC3DE;
    SLTM3->CTLR |= TIM3_CTLR_CEN;

    while (1) {
    }
}
