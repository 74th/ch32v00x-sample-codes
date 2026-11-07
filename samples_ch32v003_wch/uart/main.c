/* Official-SDK port of book-code uart-wch_sdk (CH32V003): CO2 sensor over USART1.
 * Sensor link: USART1 on PD5 (TX) / PD6 (RX), 9600 8N1 (book default is the PC0/PC1 remap, used with SDI printf).
 * Changes from the book, for the fixture:
 *  - pins PD5/PD6 so the Pico can play the sensor; no SDI printf. Results are written as text on the same TX line
 *    but only after a command/response exchange has completed, so frames and text never overlap.
 *  - the per-byte receive timeout is 500 ms (polled with Delay_Us), not a loop count, so a host-driven sensor
 *    emulation has time to answer. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>
#include "co2.h"

#define RX_TIMEOUT_MS 500

static const uint8_t CMD_READ_CO2[CO2_FRAME_LEN] = {0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79};
static const uint8_t CMD_SELF_CAL_ON[CO2_FRAME_LEN] = {0xFF, 0x01, 0x79, 0xA0, 0x00, 0x00, 0x00, 0x00, 0xE6};

static void write_uart(const uint8_t *buf, uint16_t len)
{
    for (uint16_t i = 0; i < len; i++) {
        while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET) {}
        USART_SendData(USART1, buf[i]);
    }
    while (USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET) {}
}

static void print(const char *s)
{
    while (*s) {
        while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET) {}
        USART_SendData(USART1, (uint8_t)*s++);
    }
    while (USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET) {}
}

/* Returns the number of bytes received before a RX_TIMEOUT_MS gap. */
static uint16_t read_uart_with_timeout(uint8_t *buf, uint16_t len)
{
    for (uint16_t i = 0; i < len; i++) {
        uint32_t wait = RX_TIMEOUT_MS * 10;  /* 100 us steps */
        while (wait && USART_GetFlagStatus(USART1, USART_FLAG_RXNE) == RESET) {
            Delay_Us(100);
            wait--;
        }
        if (wait == 0) return i;
        buf[i] = (uint8_t)USART_ReceiveData(USART1);
    }
    return len;
}

static void loop_once(void)
{
    uint8_t buf[CO2_FRAME_LEN] = {0};
    write_uart(CMD_READ_CO2, CO2_FRAME_LEN);

    /* Skip bytes until 0xff 0x86 (noise on the idle line is tolerated). */
    for (;;) {
        if (read_uart_with_timeout(&buf[0], 1) == 0) { print("read timeout\r\n"); Delay_Ms(1000); return; }
        if (buf[0] != 0xff) continue;
        if (read_uart_with_timeout(&buf[1], 1) == 0) { print("read timeout\r\n"); Delay_Ms(1000); return; }
        if (buf[1] != 0x86) continue;
        break;
    }
    if (read_uart_with_timeout(&buf[2], 7) < 7) {
        print("timeout\r\n");
        Delay_Ms(1000);
        return;
    }
    uint16_t ppm = 0;
    co2_status_t st = co2_parse(buf, &ppm);
    if (st == CO2_BAD_CHECKSUM) print("invalid checksum\r\n");
    char line[24];
    snprintf(line, sizeof line, "CO2: %5d ppm\r\n", ppm);
    print(line);
}

int main(void)
{
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
    SystemCoreClockUpdate();
    Delay_Init();
    Delay_Ms(100);

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOD | RCC_APB2Periph_USART1, ENABLE);
    GPIO_InitTypeDef gpio = {0};
    gpio.GPIO_Pin = GPIO_Pin_5;  /* PD5 TX */
    gpio.GPIO_Speed = GPIO_Speed_30MHz;
    gpio.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_Init(GPIOD, &gpio);
    gpio.GPIO_Pin = GPIO_Pin_6;  /* PD6 RX */
    gpio.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(GPIOD, &gpio);

    USART_InitTypeDef usart = {0};
    usart.USART_BaudRate = 9600;
    usart.USART_WordLength = USART_WordLength_8b;
    usart.USART_StopBits = USART_StopBits_1;
    usart.USART_Parity = USART_Parity_No;
    usart.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    usart.USART_Mode = USART_Mode_Tx | USART_Mode_Rx;
    USART_Init(USART1, &usart);
    USART_Cmd(USART1, ENABLE);
    Delay_Ms(100);

    /* Enable self calibration; the 9-byte answer is discarded. */
    write_uart(CMD_SELF_CAL_ON, CO2_FRAME_LEN);
    uint8_t ack[CO2_FRAME_LEN];
    uint16_t n = read_uart_with_timeout(ack, CO2_FRAME_LEN);
    if (n < CO2_FRAME_LEN) print("timeout\r\n");
    print("start\r\n");

    for (;;) {
        Delay_Ms(1000);  /* wait first, so a host-side sensor emulation can re-arm after "start" */
        loop_once();
    }
}
