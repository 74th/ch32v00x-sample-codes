/* WWDG (window watchdog) sample, based on the official EVT example EXAM/WWDG (not in the CH32V003 book).
 * Config: HCLK 48 MHz, WDGTB prescaler /8 -> one count = 4096*8/48 MHz = ~683 us. The 7-bit counter starts at 0x7F and the
 * chip is reset when it falls below 0x40 (~43.7 ms), or when it is fed while it is still >= the window value 0x5F (the
 * first ~22.5 ms after a feed).
 * Behaviour is selected at build time with -DWWDG_MODE=<n> (make clean first):
 *   0 (default) feed inside the window: every 5 ms loop the counter T[6:0] is read and fed only if it is below the window
 *   1 feed too early: feed unconditionally every 5 ms loop (counter ~0x77 > 0x5F) -> WWDG reset (after one dot)
 *   2 never feed -> WWDG reset when the counter reaches 0x3F (after 9 dots)
 * Changes from the official example:
 *  - no early wakeup interrupt (EWI), no NVIC setup: EWI is not covered here.
 *  - UART (USART1 TX = PD5, 115200) output through USART_Printf_Init, as in the other samples. At start the reset cause is
 *    read from RCC (WWDGRSTF, IWDGRSTF), printed as "cause=WWDG|IWDG|other" and cleared. After a WAIT time the WWDG is
 *    enabled; each loop prints "." (so the number of dots after the start text shows how long the chip survived).
 *    The text is kept short ("\n" only, no extra lines) so that one 32-byte capture of the fixture's UART holds two starts.
 *  - a wait of WWDG_WAIT_MS (default 1500 ms) before enabling: once enabled the WWDG cannot be stopped, and a chip that
 *    resets right after start could not be reprogrammed through the debug interface.
 * Not covered: EWI, behaviour while debugging, absolute reset time accuracy (HSI is not calibrated here). */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

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

// One character straight to USART1 (stdio would hold a lone "." until the next newline)
static void put_dot(void)
{
  while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET)
  {
  }
  USART_SendData(USART1, '.');
}

int main(void)
{
  NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
  SystemCoreClockUpdate();
  Delay_Init();
  USART_Printf_Init(115200);

  // Reset cause (cleared so that the next reset shows its own cause)
  const char *cause = RCC_GetFlagStatus(RCC_FLAG_WWDGRST) == SET   ? "WWDG"
                      : RCC_GetFlagStatus(RCC_FLAG_IWDGRST) == SET ? "IWDG"
                                                                   : "other";
  RCC_ClearFlag();
  printf("cause=%s\n", cause);
  Delay_Ms(WWDG_WAIT_MS);

  // WWDG: counter 0x7F, window 0x5F, prescaler /8 (48 MHz / 4096 / 8), then enable (cannot be stopped)
  RCC_PB1PeriphClockCmd(RCC_PB1Periph_WWDG, ENABLE);
  WWDG_SetCounter(WWDG_CNT);
  WWDG_SetPrescaler(WWDG_Prescaler_8);
  WWDG_SetWindowValue(WWDG_WINDOW);
  WWDG_Enable(WWDG_CNT);

  while (1)
  {
    // dot first, then the 5 ms: a feed that resets the chip must not cut a dot that is still being sent
    put_dot();
    Delay_Ms(5);
#if WWDG_MODE == 0
    if ((WWDG->CTLR & 0x7F) < WWDG_WINDOW)
    {
      WWDG_SetCounter(WWDG_CNT);
    }
#elif WWDG_MODE == 1
    WWDG_SetCounter(WWDG_CNT);
#endif
  }
}
