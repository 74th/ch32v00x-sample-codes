/* Official-SDK port of book-code i2c_master-wch_sdk (CH32V003): SHT31 (0x44) over I2C1 at 400 kHz.
 * Sequence: soft reset 30 A2, 300 ms, clear status 30 41, 300 ms; then every loop 24 00 (single shot), 300 ms,
 * read 6 bytes, convert (sht31.c), print "Temperature: <t>, Humidity: <h>" on USART1 TX (PD5).
 * Changes from the book, for the fixture:
 *  - USE_REMAP 0: SDA=PC1, SCL=PC2 (the fixture's I2C pair); the book default is the PC6/PC5 remap.
 *  - the result is printed 300 ms after the read and the final delay shortened to 4700 ms (same 5.3 s period),
 *    because the Pico runs one command at a time: the text can then be captured after it has served the read.
 *  - read_i2c_data returns 0 at its end (the book has no return statement there) and NACKs the last byte: with the
 *    book's always-ACK read the Pico SHT31 emulation was asked for a 7th byte (observed: sent=7, ERR I2C).
 * I2C helper functions and the init sequence are otherwise the book's. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>
#include "sht31.h"

#define TIMEOUT_MAX 100000
#define SHT31_I2C_ADDR 0x44
#define USE_REMAP 0

// 送信
int8_t send_i2c_data(uint8_t address, uint8_t *data, uint8_t length)
{
  int32_t timeout;

  // I2Cのバスがビジーでなくなるまで待つ
  timeout = TIMEOUT_MAX;
  while (timeout-- && I2C_GetFlagStatus(I2C1, I2C_FLAG_BUSY) != RESET)
    ;

  if (timeout < 0)
  {
    printf("i2c error: i2c bus busy\r\n");
    return -1;
  }

  // 通信の開始の送信
  I2C_GenerateSTART(I2C1, ENABLE);

  // マスターモードに準備できるまで待つ
  timeout = TIMEOUT_MAX;
  while (timeout-- && !I2C_CheckEvent(I2C1, I2C_EVENT_MASTER_MODE_SELECT))
    ;
  if (timeout < 0)
  {
    printf("i2c error: i2c start error\r\n");
    return -1;
  }

  // スレーブアドレスをマスターからスレーブへの通信として送信
  I2C_Send7bitAddress(I2C1, address << 1, I2C_Direction_Transmitter);

  // トランスミッターモードに準備できるまで待つ
  timeout = TIMEOUT_MAX;
  while (timeout-- && !I2C_CheckEvent(I2C1, I2C_EVENT_MASTER_TRANSMITTER_MODE_SELECTED))
    ;
  if (timeout < 0)
  {
    printf("i2c error: i2c address error\r\n");
    return -1;
  }

  for (int i = 0; i < length; i++)
  {
    // 送信バッファが空になるまで待つ
    while (timeout-- && I2C_GetFlagStatus(I2C1, I2C_FLAG_TXE) == RESET)
      ;
    if (timeout < 0)
    {
      printf("i2c error: i2c tx empty error\r\n");
      return -1;
    }

    // 1バイトのデータ送信
    I2C_SendData(I2C1, data[i]);
  }

  // 送信完了イベントを待つ
  timeout = TIMEOUT_MAX;
  while (timeout-- && !I2C_CheckEvent(I2C1, I2C_EVENT_MASTER_BYTE_TRANSMITTED))
    ;
  if (timeout < 0)
  {
    printf("i2c error: i2c tx complete error\r\n");
    return -1;
  }

  // 通信の終了の送信
  I2C_GenerateSTOP(I2C1, ENABLE);

  return 0;
}

// 受信
int8_t read_i2c_data(uint8_t address, uint8_t *data, uint8_t length)
{
  int32_t timeout;

  // I2Cのバスがビジーでなくなるまで待つ
  timeout = TIMEOUT_MAX;
  while (timeout-- && I2C_GetFlagStatus(I2C1, I2C_FLAG_BUSY) != RESET)
    ;
  if (timeout < 0)
  {
    printf("i2c error: i2c bus busy\r\n");
    return -1;
  }

  // 通信の開始の送信
  I2C_GenerateSTART(I2C1, ENABLE);

  // マスターモードに準備できるまで待つ
  timeout = TIMEOUT_MAX;
  while (timeout-- && !I2C_CheckEvent(I2C1, I2C_EVENT_MASTER_MODE_SELECT))
    ;
  if (timeout < 0)
  {
    printf("i2c error: i2c start error\r\n");
    return -1;
  }

  // スレーブアドレスをマスターからスレーブへの通信として送信
  I2C_Send7bitAddress(I2C1, address << 1, I2C_Direction_Receiver);

  // マスターモードに準備できるまで待つ
  timeout = TIMEOUT_MAX;
  while (timeout-- && !I2C_CheckEvent(I2C1, I2C_EVENT_MASTER_RECEIVER_MODE_SELECTED))
    ;
  if (timeout < 0)
  {
    printf("i2c error: i2c address error\r\n");
    return -1;
  }

  for (int i = 0; i < length; i++)
  {
    // NACK the last byte (not in the book: the book keeps ACK enabled, so the slave is clocked for one extra byte)
    if (i == length - 1)
    {
      I2C_AcknowledgeConfig(I2C1, DISABLE);
    }

    // 受信完了イベントを待つ
    timeout = TIMEOUT_MAX;
    while (timeout-- && !I2C_CheckEvent(I2C1, I2C_EVENT_MASTER_BYTE_RECEIVED))
      ;
    if (timeout < 0)
    {
      printf("i2c error: i2c rx complete error\r\n");
      return -1;
    }

    // 受信データの受信
    data[i] = I2C_ReceiveData(I2C1);
  }

  // 通信の終了の送信
  I2C_GenerateSTOP(I2C1, ENABLE);
  I2C_AcknowledgeConfig(I2C1, ENABLE);

  return 0; // the book falls off the end of this non-void function
}

int main(void)
{
  NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);
  SystemCoreClockUpdate();
  Delay_Init();

  // SDI printf の有効化
  // ビルドフラグ SDI_PRINT=1 が必要
  // wlink sdi-print enable を実行し、USBシリアルをリスンする
  // SDI_Printf_Enable();

  // USART1 printf の有効化
  USART_Printf_Init(115200);

  Delay_Ms(100);

  printf("init\r\n");

  GPIO_InitTypeDef GPIO_InitStructure = {0};
  I2C_InitTypeDef I2C_InitTSturcture = {0};

  RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOC, ENABLE);
  RCC_PB1PeriphClockCmd(RCC_PB1Periph_I2C1, ENABLE);
#if USE_REMAP
  RCC_PB2PeriphClockCmd(RCC_PB2Periph_AFIO, ENABLE);
#endif

#if USE_REMAP
  // I2Cのリマップ
  // GPIO_PartialRemap_I2C1
  // GPIO_FullRemap_I2C1
  GPIO_PinRemapConfig(GPIO_FullRemap_I2C1, ENABLE);
  // PC6: SDA, PC5: SCL
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_5;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
  GPIO_Init(GPIOC, &GPIO_InitStructure);
#else
  // PC1: SDA, PC2: SCL
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1 | GPIO_Pin_2;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
  GPIO_Init(GPIOC, &GPIO_InitStructure);
#endif

  // I2C1の設定
  // クロック速度
  I2C_InitTSturcture.I2C_ClockSpeed = 400000;
  // モード（固定値）
  I2C_InitTSturcture.I2C_Mode = I2C_Mode_I2C;
  // デューティサイクル
  I2C_InitTSturcture.I2C_DutyCycle = I2C_DutyCycle_2;
  // Ackを有効にする
  I2C_InitTSturcture.I2C_Ack = I2C_Ack_Enable;
  // Ackアドレスのビット数
  I2C_InitTSturcture.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
  // 設定の有効化
  I2C_Init(I2C1, &I2C_InitTSturcture);

  // I2Cの有効化
  I2C_Cmd(I2C1, ENABLE);
  I2C_AcknowledgeConfig(I2C1, ENABLE);

  Delay_Ms(100);

  printf("first send\r\n");

  uint8_t buf1[2] = {0x30, 0xA2};
  send_i2c_data(SHT31_I2C_ADDR, buf1, 2);
  Delay_Ms(300);

  uint8_t buf2[2] = {0x30, 0x41};
  send_i2c_data(SHT31_I2C_ADDR, buf2, 2);
  Delay_Ms(300);

  printf("start\r\n");

  int count = 0;

  while (1)
  {
    printf("loop %d\r\n", count++);

    uint8_t dac[6];
    uint32_t temperature, humidity;

    uint8_t buf[2] = {0x24, 0x00};
    send_i2c_data(SHT31_I2C_ADDR, buf, 2);

    Delay_Ms(300);

    read_i2c_data(SHT31_I2C_ADDR, dac, sizeof(dac));
    sht31_convert(dac, &temperature, &humidity);

    Delay_Ms(300);
    printf("Temperature: %lu, Humidity: %lu\r\n", temperature, humidity);

    Delay_Ms(4700);
  }
}
