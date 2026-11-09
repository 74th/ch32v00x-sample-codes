/* TIM3 (streamlined timer, SLTM) sample (CH32V006 only; not in the book). Based on the official EVT example
 * EXAM/TIM/SLTIM_DMA. TIM3 has no output pin, so its CC3 DMA request drives DMA1 channel 1 (RM Table 8-1: TIM3_CH3 can only
 * trigger DMA1 channel 1 on CH32V006), which copies two words alternately to GPIOC->BSHR (set PC0, reset PC0) from a
 * circular 2-entry buffer. TIM3 counts HCLK (48 MHz, no prescaler): ATRLR = 47999 -> one DMA request, and one PC0 edge,
 * per 1 ms, so PC0 is a 500 Hz square wave (period 2 ms). The CPU only prints the configuration on USART1 (PD5) and idles.
 * Changes from the EVT example: the DMA moves a GPIO pattern instead of TIM1->ATRLR into RAM; TIM1 is not used; no
 * interrupts. DMA is used, not the CPU. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

#define TIM3_RELOAD 47999        /* 48 MHz / 48000 = 1 kHz request rate */
#define PC0_SET (1u << 0)
#define PC0_RESET (1u << (16 + 0))

static uint32_t pc0_bshr[2] = {PC0_SET, PC0_RESET};

int main(void)
{
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    printf("init tim3 dma toggle pc0 half_period_us=%d\r\n", (TIM3_RELOAD + 1) / 48);

    GPIO_InitTypeDef gpio = {0};
    DMA_InitTypeDef dma = {0};
    RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOC, ENABLE);
    RCC_PB1PeriphClockCmd(RCC_PB1Periph_TIM3, ENABLE);
    RCC_HBPeriphClockCmd(RCC_HBPeriph_DMA1, ENABLE);
    RCC_HBPeriphClockCmd(RCC_HBPeriph_SRAM, ENABLE);

    gpio.GPIO_Pin = GPIO_Pin_0;
    gpio.GPIO_Mode = GPIO_Mode_Out_PP;
    gpio.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(GPIOC, &gpio);

    DMA_DeInit(DMA1_Channel1);
    dma.DMA_PeripheralBaseAddr = (uint32_t)&GPIOC->BSHR;
    dma.DMA_MemoryBaseAddr = (uint32_t)pc0_bshr;
    dma.DMA_DIR = DMA_DIR_PeripheralDST;
    dma.DMA_BufferSize = 2;
    dma.DMA_PeripheralInc = DMA_PeripheralInc_Disable;
    dma.DMA_MemoryInc = DMA_MemoryInc_Enable;
    dma.DMA_PeripheralDataSize = DMA_PeripheralDataSize_Word;
    dma.DMA_MemoryDataSize = DMA_MemoryDataSize_Word;
    dma.DMA_Mode = DMA_Mode_Circular;
    dma.DMA_Priority = DMA_Priority_High;
    dma.DMA_M2M = DMA_M2M_Disable;
    DMA_Init(DMA1_Channel1, &dma);
    DMA_Cmd(DMA1_Channel1, ENABLE);

    TIM_CounterModeConfig(TIM3, TIM_CounterMode_Down);
    TIM_SetAutoreload(TIM3, TIM3_RELOAD);
    TIM_SetCompare3(TIM3, 0x10);
    TIM_ARRPreloadConfig(TIM3, ENABLE);
    TIM_DMACmd(TIM3, TIM_DMA_CC3, ENABLE);
    TIM_Cmd(TIM3, ENABLE);

    while (1)
    {
    }
}
