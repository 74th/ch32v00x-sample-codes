/* WWDG (window watchdog) with plain ch32fun register access; same behaviour and window as samples_ch32v00{2,6}_wch/wwdg
 * (based on the official EVT example EXAM/WWDG; not in the CH32V003 book). Shared source for CH32V002 and CH32V006.
 * Config: HCLK 48 MHz (24 MHz HSI x2, see funconfig.h), WDGTB prescaler /8 -> one count = 4096*8/48 MHz = ~683 us. The
 * 7-bit counter starts at 0x7F and the chip is reset when it falls below 0x40 (~43.7 ms), or when it is fed while it is
 * still >= the window value 0x5F (the first ~22.5 ms after a feed).
 * Behaviour is selected with -DWWDG_MODE=<n> (e.g. make build EXTRA_CFLAGS=-DWWDG_MODE=1 after make clean):
 *   0 (default) feed inside the window: every 5 ms loop the counter T[6:0] is read and fed only if it is below the window
 *   1 feed too early: feed unconditionally every 5 ms loop -> WWDG reset (after one dot)
 *   2 never feed -> WWDG reset (after 9 dots)
 * UART (USART1 TX = PD5, 115200): at start "cause=WWDG|IWDG|other\n" (RCC_RSTSCKR flags, then cleared), then after
 * WWDG_WAIT_MS (default 1500 ms) the WWDG is enabled and every loop prints ".". The wait is there because an enabled WWDG
 * cannot be stopped and a chip that resets right after start could not be reprogrammed through the debug interface.
 * The text is short so that one 32-byte capture of the fixture's UART holds two starts.
 * Not covered: early wakeup interrupt (EWI), behaviour while debugging, absolute reset time accuracy. */
#include "ch32fun.h"

#ifndef WWDG_MODE
#define WWDG_MODE 0
#endif
#if WWDG_MODE < 0 || WWDG_MODE > 2
#error "WWDG_MODE must be 0 (feed in window), 1 (feed too early) or 2 (never feed)"
#endif
#ifndef WWDG_WAIT_MS
#define WWDG_WAIT_MS 1500
#endif

#define WWDG_CNT 0x7F
#define WWDG_WINDOW 0x5F

static void put(uint8_t c)
{
    while (!(USART1->STATR & USART_FLAG_TXE)) {}
    USART1->DATAR = c;
}

static void puts_raw(const char *s)
{
    while (*s) put(*s++);
}

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOD | RCC_APB2Periph_USART1;
    GPIOD->CFGLR &= ~(0xf << (4 * 5));
    GPIOD->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5);
    USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
    USART1->CTLR2 = USART_StopBits_1;
    USART1->CTLR3 = USART_HardwareFlowControl_None;
    USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
    USART1->CTLR1 |= CTLR1_UE_Set;

    uint32_t rst = RCC->RSTSCKR;
    puts_raw(rst & RCC_WWDGRSTF ? "cause=WWDG\n" : rst & RCC_IWDGRSTF ? "cause=IWDG\n" : "cause=other\n");
    RCC->RSTSCKR |= RCC_RMVF;   /* clear the flags so that the next reset shows its own cause */
    Delay_Ms(WWDG_WAIT_MS);

    /* WWDG clock on, counter 0x7F, window 0x5F, prescaler /8, then enable (WDGA cannot be cleared by software) */
    RCC->PB1PCENR |= RCC_WWDGEN;
    WWDG->CTLR = WWDG_CNT;
    WWDG->CFGR = WWDG_WINDOW | WWDG_CFGR_WDGTB;   /* WDGTB = 3 (/8) */
    WWDG->CTLR = WWDG_CTLR_WDGA | WWDG_CNT;

    while (1) {
        /* dot first, then the 5 ms: a feed that resets the chip must not cut a dot that is still being sent */
        put('.');
        Delay_Ms(5);
#if WWDG_MODE == 0
        if ((WWDG->CTLR & WWDG_CTLR_T) < WWDG_WINDOW) WWDG->CTLR = WWDG_CTLR_WDGA | WWDG_CNT;
#elif WWDG_MODE == 1
        WWDG->CTLR = WWDG_CTLR_WDGA | WWDG_CNT;
#endif
    }
}
