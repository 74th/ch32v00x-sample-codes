/* Official-SDK port of book-code pwm-wch_sdk (CH32V003): TIM1 PWM on CH1 and CH4, 256 steps per period
 * (prescaler 1 -> 48 MHz / 2 / 256 = 93.75 kHz). Every 1/32 s the duty of CH1 ramps up in 1/32 steps while CH4 is set
 * to 128 * (33 - i) - 1, then the roles swap on the way down; "up"/"down" are printed on USART1 TX (PD5).
 * Change from the book: USE_REMAP 0, i.e. CH1 = PD2 and CH4 = PC4 (the fixture wires PD2 -> GP14 and PC4 -> GP15);
 * the book default is the partial remap PC6/PD3, which the fixture does not wire. Everything else is the book's code
 * (including the 128-step CH4 formula, which exceeds the 8-bit period: see README for its effect).
 * CH32V006 change (owner's decision, okf/log/2026-11-08-1550-ch32v006-arduino-hil-batch1-pwm-pc4.md): PC4 (TIM1_CH4)
 * shows no signal on this DUT (cause not identified), so the second channel is TIM2_CH3 on PC0 (USE_PC0 1, the
 * default; same period, prescaler and compare values). Build with EXTRA_CFLAGS=-DUSE_PC0=0 for the PC4 original. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

#define USE_REMAP 0

#ifndef USE_PC0
#define USE_PC0 1
#endif

#if USE_PC0
#define SET_CH2(v) TIM_SetCompare3(TIM2, (v))
#else
#define SET_CH2(v) TIM_SetCompare4(TIM1, (v))
#endif

void TIM1_PWMOut_Init()
{
    GPIO_InitTypeDef GPIO_InitStructure = {0};
    TIM_OCInitTypeDef TIM_OCInitStructure = {0};
    TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure = {0};

    // GPIO、Timerのクロック有効化
    RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOA | RCC_PB2Periph_GPIOC | RCC_PB2Periph_GPIOD | RCC_PB2Periph_TIM1, ENABLE);
#if USE_PC0
    RCC_PB1PeriphClockCmd(RCC_PB1Periph_TIM2, ENABLE);
#endif

#if USE_REMAP
    // AFIOクロック有効化
    RCC_PB2PeriphClockCmd(RCC_PB2Periph_AFIO, ENABLE);
#endif

#if USE_REMAP
    // Partial Remap 1を適用
    GPIO_PinRemapConfig(GPIO_PartialRemap1_TIM1, ENABLE);

    // TIM1_CH1_1 -> PC6
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(GPIOC, &GPIO_InitStructure);

    // TIM1_CH4_1 -> PD3
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(GPIOD, &GPIO_InitStructure);
#else
    // TIM1_CH1 -> PD2
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(GPIOD, &GPIO_InitStructure);

#if USE_PC0
    // TIM2_CH3 -> PC0
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;
#else
    // TIM1_CH4 -> PC4
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_4;
#endif
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
    GPIO_Init(GPIOC, &GPIO_InitStructure);
#endif

    // Timer1を256周期で有効か
    TIM_TimeBaseInitStructure.TIM_Period = 255;
    TIM_TimeBaseInitStructure.TIM_Prescaler = 1;
    TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM1, &TIM_TimeBaseInitStructure);

    // Timer1 CH1をPWMで有効化
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_Pulse = 0;
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;
    TIM_OC1Init(TIM1, &TIM_OCInitStructure);

#if USE_PC0
    // Timer2 を Timer1 と同じ 256 周期で設定し、CH3 を PWM で有効化
    TIM_TimeBaseInit(TIM2, &TIM_TimeBaseInitStructure);
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_Pulse = 0;
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;
    TIM_OC3Init(TIM2, &TIM_OCInitStructure);
#else
    // Timer1 CH4をPWMで有効化
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_Pulse = 0;
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;
    TIM_OC4Init(TIM1, &TIM_OCInitStructure);
#endif

    // カウンタの値を即時反映するため、プリロード機能をDisableにする
    TIM_OC1PreloadConfig(TIM1, TIM_OCPreload_Disable);
#if USE_PC0
    TIM_OC3PreloadConfig(TIM2, TIM_OCPreload_Disable);
    TIM_ARRPreloadConfig(TIM2, ENABLE);
#else
    TIM_OC4PreloadConfig(TIM1, TIM_OCPreload_Disable);
#endif
    TIM_ARRPreloadConfig(TIM1, ENABLE);

    // PWM出力の有効化
    TIM_CtrlPWMOutputs(TIM1, ENABLE);
    // Timerの有効化
#if USE_PC0
    TIM_Cmd(TIM2, ENABLE);
#endif
    TIM_Cmd(TIM1, ENABLE);
}

int main(void)
{
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();

#if SDI_PRINT
    SDI_Printf_Enable();
#else
    USART_Printf_Init(115200);
#endif

    printf("init\r\n");

    TIM1_PWMOut_Init();

    printf("start\r\n");

    while (1)
    {
        Delay_Ms(100);
        printf("up\r\n");
        for (int i = 1; i <= 32; i++)
        {
            TIM_SetCompare1(TIM1, 8 * i - 1);
            SET_CH2(128 * (33 - i) - 1);
            Delay_Us(1000000 / 32);
        }

        printf("down\r\n");
        for (int i = 1; i <= 32; i++)
        {
            TIM_SetCompare1(TIM1, 8 * (33 - i) - 1);
            SET_CH2(8 * i - 1);
            Delay_Us(1000000 / 32);
        }
    }
}
