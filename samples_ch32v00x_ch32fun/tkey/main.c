/* TKEY (touch key) sample, plain ch32fun register access (CH32V006 only; not in the book). Same behaviour as
 * samples_ch32v006_wch/tkey (based on the official EVT example EXAM/TOUCHKEY/TKEY, channel 2 = PC4 there). The TKEY measures the
 * charge/discharge time of an ADC external channel; it is read on two channels with different loads and printed on USART1
 * (PD5, 115200) every 500 ms: ch7 = PD4 (a floating pin, or the 1 kOhm lead used as a touch electrode), ch0 = PA2 (10 kOhm and
 * 1 uF to GND on the fixture: a large load). The values are a reference observation of how the TKEY value depends on the load.
 * Registers (WCH SDK: ADC_BufferCmd = CTLR1 bit 26 (ADC_BUFEN), ADC_TKeyCmd = CTLR1 bit 24 (ADC_TKENABLE), TKey1 = ADC1):
 * the charging time IDATAR1 = 0x20 and the discharging time RDATAR = 0x8 are written before each conversion (EVT values); the
 * conversion result is read from RDATAR. As in the WCH sample no software start is given (EXTTRIG/SWSTART stay clear): writing
 * IDATAR1/RDATAR starts the TKEY conversion (a SWSTART in a first version of this sample made both channels read 0). CH32V002 has no TKEY: the build stops with #error. */
#include "ch32fun.h"

#ifndef CH32V006
#error "tkey needs the touch key, which only the CH32V006 has (CH32V002 has none); build with TARGET_MCU=CH32V006"
#endif

static void put(uint8_t c)
{
    while (!(USART1->STATR & USART_FLAG_TXE)) {}
    USART1->DATAR = c;
}

static void put_str(const char *s)
{
    while (*s) put(*s++);
}

static void put_dec(uint32_t v)
{
    char buf[11];
    int n = 0;
    do { buf[n++] = '0' + v % 10; v /= 10; } while (v);
    while (n) put(buf[--n]);
}

static uint16_t tkey_read(uint8_t channel)
{
    ADC1->RSQR3 = channel;
    ADC1->SAMPTR2 = (ADC1->SAMPTR2 & ~(7u << (3 * channel))) | (7u << (3 * channel)); /* 239.5 cycles */
    ADC1->IDATAR1 = 0x20;  /* charging time */
    ADC1->RDATAR = 0x8;    /* discharging time */
    while (!(ADC1->STATR & ADC_EOC)) {}
    return (uint16_t)ADC1->RDATAR;
}

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOD | RCC_APB2Periph_ADC1 | RCC_APB2Periph_USART1;
    GPIOD->CFGLR &= ~((0xf << (4 * 5)) | (0xf << (4 * 4)));  /* PD4 analog (ch7) */
    GPIOD->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5);
    GPIOA->CFGLR &= ~(0xf << (4 * 2));                       /* PA2 analog (ch0) */
    USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
    USART1->CTLR2 = USART_StopBits_1;
    USART1->CTLR3 = USART_HardwareFlowControl_None;
    USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
    USART1->CTLR1 |= CTLR1_UE_Set;
    put_str("init tkey\r\n");

    RCC->CFGR0 = (RCC->CFGR0 & ~RCC_ADCPRE) | RCC_ADCPRE_DIV8;  /* same as RCC_PCLK2_Div8 */
    ADC1->RSQR1 = 0;
    ADC1->CTLR2 = ADC_ADON | ADC_EXTSEL;   /* as ADC_Init(ExternalTrigConv_None) + ADC_Cmd: no EXTTRIG, no SWSTART */
    ADC1->CTLR1 |= ADC_BUFEN | ADC_TKENABLE;

    while (1) {
        uint16_t floating = tkey_read(7);  /* PD4 */
        uint16_t loaded = tkey_read(0);    /* PA2 */
        put_str("tkey pd4="); put_dec(floating);
        put_str(" pa2="); put_dec(loaded);
        put_str("\r\n");
        Delay_Ms(500);
    }
}
