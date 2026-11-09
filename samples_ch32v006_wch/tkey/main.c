/* TKEY (touch key) sample (CH32V006 only; not in the book). Based on the official EVT example EXAM/TOUCHKEY/TKEY (channel 2 =
 * PC4 there). The TKEY measures the charge/discharge time of an ADC external channel; it is read here on two channels
 * with different loads and printed on USART1 (PD5, 115200) every 500 ms:
 *   ch7 = PD4 (nothing wired: a floating pin)           ch0 = PA2 (10 kOhm and 1 uF to GND on the fixture: a large load)
 * The values are a reference observation of how the TKEY value depends on the load; they do not judge a touch.
 * Changes from the EVT example: PD4 and PA2 instead of PC4 (PC4 does not pass a signal on the CH32V006 used here), two
 * channels, a fixed one-line log. Charging time IDATAR1 = 0x20 and discharging time RDATAR = 0x8 are the EVT values. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

static void tkey_init(void)
{
    GPIO_InitTypeDef gpio = {0};
    ADC_InitTypeDef adc = {0};
    RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOA | RCC_PB2Periph_GPIOD | RCC_PB2Periph_ADC1, ENABLE);
    gpio.GPIO_Mode = GPIO_Mode_AIN;
    gpio.GPIO_Pin = GPIO_Pin_4;
    GPIO_Init(GPIOD, &gpio);
    gpio.GPIO_Pin = GPIO_Pin_2;
    GPIO_Init(GPIOA, &gpio);

    RCC_ADCCLKConfig(RCC_PCLK2_Div8);
    adc.ADC_Mode = ADC_Mode_Independent;
    adc.ADC_ScanConvMode = DISABLE;
    adc.ADC_ContinuousConvMode = DISABLE;
    adc.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
    adc.ADC_DataAlign = ADC_DataAlign_Right;
    adc.ADC_NbrOfChannel = 1;
    ADC_Init(ADC1, &adc);
    ADC_Cmd(ADC1, ENABLE);
    ADC_BufferCmd(ADC1, ENABLE);
    ADC_TKeyCmd(ADC1, ENABLE);
}

static uint16_t tkey_read(uint8_t channel)
{
    ADC_RegularChannelConfig(ADC1, channel, 1, ADC_SampleTime_CyclesMode7);
    TKey1->IDATAR1 = 0x20;  // charging time
    TKey1->RDATAR = 0x8;    // discharging time
    while (!ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC))
    {
    }
    return (uint16_t)TKey1->RDATAR;
}

int main(void)
{
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    printf("init tkey\r\n");
    tkey_init();
    while (1)
    {
        uint16_t floating = tkey_read(ADC_Channel_7);  // PD4
        uint16_t loaded = tkey_read(ADC_Channel_0);    // PA2
        printf("tkey pd4=%d pa2=%d\r\n", floating, loaded);
        Delay_Ms(500);
    }
}
