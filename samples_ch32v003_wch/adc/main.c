/* Official-SDK port of book-code adc-wch_sdk (CH32V003): two single-shot ADC channels.
 * PA1 = ADC1 channel 1 ("x"), PA2 = ADC1 channel 0 ("y"). 10-bit result, right aligned, 241-cycle sample time,
 * calibrated at start. Every 200 ms prints "x: <0..1023>, y: <0..1023>" on USART1 TX (PD5), as the book does.
 * Differences from the book: none in the ADC setup (only the NMI/HardFault handler declarations are dropped;
 * the official startup already provides default handlers). */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

#define VRX_PIN GPIO_Pin_1
#define VRY_PIN GPIO_Pin_2

static uint16_t read_channel(uint8_t channel)
{
    ADC_RegularChannelConfig(ADC1, channel, 1, ADC_SampleTime_241Cycles);
    ADC_SoftwareStartConvCmd(ADC1, ENABLE);
    while (!ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC)) {}
    return ADC_GetConversionValue(ADC1);
}

int main(void)
{
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    printf("init\r\n");

    GPIO_InitTypeDef gpio = {0};
    ADC_InitTypeDef adc = {0};
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1 | RCC_APB2Periph_GPIOC | RCC_APB2Periph_GPIOA, ENABLE);

    gpio.GPIO_Pin = VRX_PIN;
    gpio.GPIO_Mode = GPIO_Mode_AIN;
    GPIO_Init(GPIOA, &gpio);
    gpio.GPIO_Pin = VRY_PIN;
    GPIO_Init(GPIOA, &gpio);

    ADC_DeInit(ADC1);
    adc.ADC_Mode = ADC_Mode_Independent;
    adc.ADC_ScanConvMode = DISABLE;
    adc.ADC_ContinuousConvMode = DISABLE;
    adc.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
    adc.ADC_DataAlign = ADC_DataAlign_Right;
    adc.ADC_NbrOfChannel = 1;
    ADC_Init(ADC1, &adc);
    ADC_Calibration_Vol(ADC1, ADC_CALVOL_50PERCENT);
    ADC_Cmd(ADC1, ENABLE);

    ADC_ResetCalibration(ADC1);
    while (ADC_GetResetCalibrationStatus(ADC1)) {}
    ADC_StartCalibration(ADC1);
    while (ADC_GetCalibrationStatus(ADC1)) {}
    printf("start\r\n");

    int count = 0;
    for (;;) {
        printf("loop %d\r\n", count++);
        uint16_t x = read_channel(ADC_Channel_1);
        uint16_t y = read_channel(ADC_Channel_0);
        printf("x: %d, y: %d\r\n", x, y);
        Delay_Ms(200);
    }
}
