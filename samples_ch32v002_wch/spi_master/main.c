/* Official-SDK port of book-code spi_master-wch_sdk (CH32V003): ADT7310-style temperature sensor over SPI1
 * (PC5 SCK, PC6 MOSI, PC7 MISO; mode 0, MSB first, prescaler 256 = 187.5 kHz).
 * Sequence (book): CS high 500 ms; reset frame FF FF FF FF, 100 ms, command 0x54, 300 ms; loop: read 2 bytes,
 * convert the signed 13-bit value (adt7310.c) and print raw / raw_int / temp on USART1 TX (PD5), 1 s period.
 * Changes from the book, for the fixture:
 *  - CS is PC0 (book: PC1, which is the fixture's I2C SDA) and is raised after the reset/config frame and after every
 *    2-byte read; the book keeps CS low for the whole run. The Pico SPI slave handles exactly two bytes per CS
 *    assertion, so it cannot follow a CS held low. The reset frame (FF x4, 0x54) stays within one CS-low period.
 *  - the text is printed 300 ms after the read and the final delay is 700 ms (same 1 s period): the Pico runs one
 *    command at a time, so the text can be captured after the SPI frame has been served.
 * The SPI configuration and transfer helpers are the book's. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>
#include "adt7310.h"

#define CS_PIN GPIO_Pin_0

uint8_t transfer_spi(uint8_t data)
{
  // 常に書き込みと読み込みを両方行う
  // 送信バッファが空になるのを待つ
  while (SPI_I2S_GetFlagStatus(SPI1, SPI_I2S_FLAG_TXE) == RESET)
    ;
  // 1バイトの送信
  SPI_I2S_SendData(SPI1, data);

  // 受信バッファにデータが入るのを待つ
  while (SPI_I2S_GetFlagStatus(SPI1, SPI_I2S_FLAG_RXNE) == RESET)
    ;

  // 1バイトの受信
  return SPI_I2S_ReceiveData(SPI1);
}


// 送信
void send_spi_data(uint8_t *data, uint8_t length)
{
  for (int i = 0; i < length; i++)
  {
    transfer_spi(data[i]);
  }
}

// 受信
void read_spi_data(uint8_t *data, uint8_t length)
{
  for (int i = 0; i < length; i++)
  {
    data[i] = transfer_spi(0);
  }
}

int main(void)
{
  NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
  SystemCoreClockUpdate();
  Delay_Init();

  // USART1 printf (PD5)
  USART_Printf_Init(115200);

  Delay_Ms(100);

  printf("init\r\n");

  GPIO_InitTypeDef GPIO_InitStructure = {0};
  SPI_InitTypeDef SPI_InitStructure = {0};

  RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOC | RCC_PB2Periph_AFIO | RCC_PB2Periph_SPI1, ENABLE);

  // PC0: CS (book: PC1)
  GPIO_InitStructure.GPIO_Pin = CS_PIN;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
  GPIO_Init(GPIOC, &GPIO_InitStructure);

  // PC5: SCK
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
  GPIO_Init(GPIOC, &GPIO_InitStructure);

  // PC7: MISO
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
  GPIO_Init(GPIOC, &GPIO_InitStructure);

  // PC6: MOSI
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
  GPIO_Init(GPIOC, &GPIO_InitStructure);

  SPI_InitStructure.SPI_Direction = SPI_Direction_2Lines_FullDuplex;
  SPI_InitStructure.SPI_Mode = SPI_Mode_Master;
  SPI_InitStructure.SPI_DataSize = SPI_DataSize_8b;
  SPI_InitStructure.SPI_CPOL = SPI_CPOL_Low;
  SPI_InitStructure.SPI_CPHA = SPI_CPHA_1Edge;
  SPI_InitStructure.SPI_NSS = SPI_NSS_Soft;
  SPI_InitStructure.SPI_BaudRatePrescaler = SPI_BaudRatePrescaler_256;
  SPI_InitStructure.SPI_FirstBit = SPI_FirstBit_MSB;
  SPI_InitStructure.SPI_CRCPolynomial = 7;
  SPI_Init(SPI1, &SPI_InitStructure);

  SPI_Cmd(SPI1, ENABLE);

  GPIO_SetBits(GPIOC, CS_PIN);

  Delay_Ms(500);

  GPIO_ResetBits(GPIOC, CS_PIN);

  printf("software reset\r\n");

  uint8_t buf1[4] = {0xff, 0xff, 0xff, 0xff};
  send_spi_data(buf1, sizeof(buf1));
  Delay_Ms(100);

  uint8_t buf2[1] = {0x54};
  send_spi_data(buf2, sizeof(buf2));
  Delay_Ms(300);
  GPIO_SetBits(GPIOC, CS_PIN);

  printf("start\r\n");

  int count = 0;

  while (1)
  {
    printf("loop %d\r\n", count++);

    uint8_t buf[2] = {0x00, 0x00};
    GPIO_ResetBits(GPIOC, CS_PIN);
    read_spi_data(buf, sizeof(buf));
    GPIO_SetBits(GPIOC, CS_PIN);

    uint16_t raw = (buf[0] << 8) | buf[1];
    adt7310_temp_t t = adt7310_convert(raw);

    Delay_Ms(300);
    printf("raw: %04x\r\n", raw);
    printf("raw_int: %d\r\n", (int)t.raw_int);
    printf("temp:%3d.%04d\r\n", (int)t.int_temp, (int)(t.frac_temp * 625));

    Delay_Ms(700);
  }
}
