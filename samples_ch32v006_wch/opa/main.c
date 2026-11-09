/* OPA (PGA) sample (CH32V006 only; not in the book). Based on the official EVT example EXAM/OPA/OPA_PGA (single-ended
 * variant, "OPA_PGA_No_Dif"): OPA positive input CHP0 = PA2, internal negative path with the PGA gain (4x or 8x, selected
 * with -DOPA_GAIN=<4|8>, make clean first), output OUT0 = PD4. The ADC reads the input (PA2, ADC_IN0) and the OPA output
 * (PD4, ADC_IN7) back to back and prints "opa gain=<g> in=<raw> out=<raw>" on USART1 (PD5, 115200) every 200 ms.
 * Changes from the EVT example: single-ended only (no CMP bias / PGADIF), the ADC reads both the input and the output,
 * gain selectable at build time, and the log is a fixed one-line format for the HIL test.
 * Not covered: offset, noise, bandwidth, the differential mode, the CMP (CH32V007 only according to the RM). */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

#ifndef OPA_GAIN
#define OPA_GAIN 4
#endif
#if OPA_GAIN == 4
#define OPA_NSEL CHN_PGA_4xIN
#elif OPA_GAIN == 8
#define OPA_NSEL CHN_PGA_8xIN
#else
#error "OPA_GAIN must be 4 or 8"
#endif

static void opa_init(void)
{
    GPIO_InitTypeDef gpio = {0};
    OPA_InitTypeDef opa = {0};
    RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOA, ENABLE);
    gpio.GPIO_Pin = GPIO_Pin_2;
    gpio.GPIO_Mode = GPIO_Mode_AIN;
    GPIO_Init(GPIOA, &gpio);

    opa.PSEL = CHP0;
    opa.NSEL = OPA_NSEL;
    opa.Mode = OUT_IO_OUT0;
    opa.FB = FB_ON;
    opa.OPA_HS = HS_ON;
    OPA_Init(&opa);
    OPA_Cmd(ENABLE);
}

static void adc_init(void)
{
    GPIO_InitTypeDef gpio = {0};
    ADC_InitTypeDef adc = {0};
    RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOD | RCC_PB2Periph_ADC1, ENABLE);
    RCC_ADCCLKConfig(RCC_PCLK2_Div8);
    gpio.GPIO_Pin = GPIO_Pin_4;
    gpio.GPIO_Mode = GPIO_Mode_AIN;
    GPIO_Init(GPIOD, &gpio);

    ADC_DeInit(ADC1);
    adc.ADC_Mode = ADC_Mode_Independent;
    adc.ADC_ScanConvMode = DISABLE;
    adc.ADC_ContinuousConvMode = DISABLE;
    adc.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
    adc.ADC_DataAlign = ADC_DataAlign_Right;
    adc.ADC_NbrOfChannel = 1;
    ADC_Init(ADC1, &adc);
    ADC_Cmd(ADC1, ENABLE);
}

static uint16_t adc_read(uint8_t channel)
{
    ADC_RegularChannelConfig(ADC1, channel, 1, ADC_SampleTime_CyclesMode7);
    ADC_SoftwareStartConvCmd(ADC1, ENABLE);
    while (!ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC))
    {
    }
    return ADC_GetConversionValue(ADC1);
}

int main(void)
{
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    printf("init opa gain=%d\r\n", OPA_GAIN);

    OPA_Unlock();
    OPA_CMP_Unlock();
    opa_init();
    adc_init();

    while (1)
    {
        uint16_t in = adc_read(ADC_Channel_0);   // PA2 (OPA P0)
        uint16_t out = adc_read(ADC_Channel_7);  // PD4 (OPA OUT0)
        printf("opa gain=%d in=%d out=%d\r\n", OPA_GAIN, in, out);
        Delay_Ms(200);
    }
}
