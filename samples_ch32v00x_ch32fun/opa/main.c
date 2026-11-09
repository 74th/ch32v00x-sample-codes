/* OPA (PGA) sample, plain ch32fun register access (CH32V006 only; not in the book). Same behaviour as
 * samples_ch32v006_wch/opa (based on the official EVT example EXAM/OPA/OPA_PGA, single-ended variant): OPA positive input
 * CHP0 = PA2, internal negative path with the PGA gain (4x or 8x, -DOPA_GAIN=<4|8>, make clean first), output OUT0 = PD4.
 * The ADC reads the input (PA2, ADC_IN0) and the OPA output (PD4, ADC_IN7) back to back and prints
 * "opa gain=<g> in=<raw> out=<raw>" on USART1 (PD5, 115200) every 200 ms.
 *
 * Register values (from the WCH SDK's OPA_Unlock / OPA_Init / OPA_Cmd, ch32v00X_opa.c, with the same arguments as the WCH sample:
 * PSEL = CHP0 (0), NSEL = CHN_PGA_4xIN (3) or CHN_PGA_8xIN (4), Mode = OUT_IO_OUT0 (0), FB = FB_ON (1), PGADIF off, OPA_HS = HS_ON (1)):
 *   OPA->OPA_KEY = 0x45670123, then 0xCDEF89AB (unlock); OPA->CMP_KEY gets the same pair (the WCH sample calls OPA_CMP_Unlock too)
 *   OPA->CFGR1 &= 0xF1C0FA02 (all poll/interrupt fields 0)
 *   OPA->CTLR1 = (CTLR1 & 0xFFE0E0C9) | NSEL << 8 | FB << 11 | HS << 20 | EN (bit 0)
 * The ch32fun OPA_TypeDef (CFGR1, CTLR1, CFGR2, CTLR2, OPA_KEY, CMP_KEY, POLL_KEY) has the same order and 4-byte pitch as the SDK's
 * (..., OPAKEY, CMPKEY, POLLKEY). Not covered: offset, noise, bandwidth, the differential mode, the CMP.
 * The key values (0x45670123, 0xCDEF89AB) are ch32fun's OPA_KEY1/OPA_KEY2. CH32V002 has no OPA: the build stops with #error. */
#include "ch32fun.h"

#ifndef CH32V006
#error "opa needs the OPA, which only the CH32V006 has (CH32V002 has none); build with TARGET_MCU=CH32V006"
#endif

#ifndef OPA_GAIN
#define OPA_GAIN 4
#endif
#if OPA_GAIN == 4
#define OPA_NSEL 3 /* CHN_PGA_4xIN */
#elif OPA_GAIN == 8
#define OPA_NSEL 4 /* CHN_PGA_8xIN */
#else
#error "OPA_GAIN must be 4 or 8"
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

static uint16_t adc_read(uint8_t channel)
{
    ADC1->RSQR3 = channel;
    ADC1->SAMPTR2 = (ADC1->SAMPTR2 & ~(7u << (3 * channel))) | (7u << (3 * channel)); /* 239.5 cycles */
    ADC1->CTLR2 |= ADC_SWSTART;
    while (!(ADC1->STATR & ADC_EOC)) {}
    return ADC1->RDATAR & 0xfff;
}

int main(void)
{
    SystemInit();
    RCC->APB2PCENR |= RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOD | RCC_APB2Periph_ADC1 | RCC_APB2Periph_USART1;
    GPIOD->CFGLR &= ~((0xf << (4 * 5)) | (0xf << (4 * 4)));  /* PD4 analog (OPA output, ADC_IN7) */
    GPIOD->CFGLR |= (GPIO_Speed_10MHz | GPIO_CNF_OUT_PP_AF) << (4 * 5);
    GPIOA->CFGLR &= ~(0xf << (4 * 2));                       /* PA2 analog (OPA P0, ADC_IN0) */
    USART1->CTLR1 = USART_WordLength_8b | USART_Parity_No | USART_Mode_Tx;
    USART1->CTLR2 = USART_StopBits_1;
    USART1->CTLR3 = USART_HardwareFlowControl_None;
    USART1->BRR = (FUNCONF_SYSTEM_CORE_CLOCK + 115200 / 2) / 115200;
    USART1->CTLR1 |= CTLR1_UE_Set;
    put_str("init opa gain="); put_dec(OPA_GAIN); put_str("\r\n");

    OPA->OPA_KEY = OPA_KEY1; OPA->OPA_KEY = OPA_KEY2;
    OPA->CMP_KEY = OPA_KEY1; OPA->CMP_KEY = OPA_KEY2;
    OPA->CFGR1 &= 0xF1C0FA02u;
    OPA->CTLR1 = (OPA->CTLR1 & 0xFFE0E0C9u) | (OPA_NSEL << 8) | (1u << 11) | (1u << 20);
    OPA->CTLR1 |= 1u;

    RCC->CFGR0 = (RCC->CFGR0 & ~RCC_ADCPRE) | RCC_ADCPRE_DIV8;  /* same as RCC_PCLK2_Div8 */
    ADC1->RSQR1 = 0;                                            /* one conversion in the sequence */
    ADC1->CTLR2 = ADC_ADON | ADC_EXTSEL | ADC_EXTTRIG;         /* software trigger; CH32V00x needs EXTTRIG too */

    while (1) {
        uint16_t in = adc_read(0);   /* PA2 (OPA P0) */
        uint16_t out = adc_read(7);  /* PD4 (OPA OUT0) */
        put_str("opa gain="); put_dec(OPA_GAIN);
        put_str(" in="); put_dec(in);
        put_str(" out="); put_dec(out);
        put_str("\r\n");
        Delay_Ms(200);
    }
}
