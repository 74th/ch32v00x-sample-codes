/* Official-SDK port of book-code i2c_slave-wch_sdk (CH32V003): register-style I2C slave at 0x10 on PC1 (SDA)/PC2 (SCL).
 * 0x30 registers; the first byte after the address (write) sets the register pointer, further bytes are stored and
 * advance it; reads return bytes from the pointer, advancing it. Registers 0x20..0x23 start as 00 10 20 30.
 * Handled in the official I2C1 event/error interrupts. The book's code is kept unchanged except for dropping the
 * NMI/HardFault declarations/definitions (the official startup supplies defaults) and the `stdio.h` include for
 * printf, and setting I2C_ClockSpeed = 100000 (the book left it 0, which made I2C_Init() divide by zero; see below).
 * The pointer moves on every received byte (not on STOP), so a repeated-START read uses the new pointer. */
#include <ch32v00x.h>
#include <debug.h>
#include <stdio.h>

#define I2C_ADDRESS 0x10

void I2C1_EV_IRQHandler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void I2C1_ER_IRQHandler(void) __attribute__((interrupt("WCH-Interrupt-fast")));

volatile uint8_t i2c_registers[0x30] = {0x00};
volatile uint8_t i2c_start_position = 0;
volatile uint8_t i2c_position = 0;
volatile uint8_t i2c_first_receive = 0;
uint8_t i2c_request_available = 0;
uint8_t i2c_receive_available = 0;

void I2C1_EV_IRQHandler(void)
{
  uint32_t event = I2C_GetLastEvent(I2C1);

  // これがないと動かない？？
  I2C_AcknowledgeConfig(I2C1, ENABLE);

  if (event == I2C_EVENT_SLAVE_RECEIVER_ADDRESS_MATCHED)
  {
    // 最初のイベント
    i2c_first_receive = 1;
  }
  if (event == I2C_EVENT_SLAVE_BYTE_RECEIVED)
  {
    // 1byte の受信イベント（slave -> master）
    uint8_t v = I2C_ReceiveData(I2C1);
    if (i2c_first_receive)
    {
      // 1バイト目の受信
      i2c_position = v;
      i2c_start_position = v;
      i2c_first_receive = 0;
    }
    else if (i2c_position < sizeof(i2c_registers))
    {
      // 2バイト目以降の受信
      i2c_registers[i2c_position] = v;
      i2c_position++;
      i2c_receive_available += 1;
    }
    else
    {
      // 2バイト目以降の受信、レジスタ範囲外
      // 何もしない
    }
  }
  if (event == I2C_EVENT_SLAVE_TRANSMITTER_ADDRESS_MATCHED ||
      event == I2C_EVENT_SLAVE_BYTE_TRANSMITTED)
  {
    // 1byte の送信イベント（master -> slave）
    I2C_SendData(I2C1, i2c_registers[i2c_position]);
    i2c_position++;
    i2c_request_available++;
  }
}

void I2C1_ER_IRQHandler(void)
{
  if (I2C_GetITStatus(I2C1, I2C_IT_AF))
  {
    I2C_ClearITPendingBit(I2C1, I2C_IT_AF);
  }
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
  NVIC_InitTypeDef NVIC_InitStructure = {0};

  RCC_PB2PeriphClockCmd(RCC_PB2Periph_GPIOC | RCC_PB2Periph_AFIO, ENABLE);
  RCC_PB1PeriphClockCmd(RCC_PB1Periph_I2C1, ENABLE);

  // PC1: SDA, PC2: SCL
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1 | GPIO_Pin_2;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_30MHz;
  GPIO_Init(GPIOC, &GPIO_InitStructure);

  // I2C1の割込チャンネル
  NVIC_InitStructure.NVIC_IRQChannel = I2C1_EV_IRQn;
  // 優先度0（最高）
  NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0;
  // サブ優先度0（最高）
  NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
  // 有効化
  NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
  // 設定の適用
  NVIC_Init(&NVIC_InitStructure);

  // I2C1のエラーチャンネル
  NVIC_InitStructure.NVIC_IRQChannel = I2C1_ER_IRQn;
  // 設定の適用
  NVIC_Init(&NVIC_InitStructure);

  // I2Cの設定
  // スレーブの SCL は master が駆動するが、SDK の I2C_Init() は ClockSpeed から CKCFGR を計算する。
  // 書籍のコードは未設定（0）で、pclk1 / (0 << 1) の0除算になり、CKCFGR が 0xCFFF（FS=1、CCR=0xFFF）になっていた（実測）。
  // master（Pico、100 kHz）と同じ標準モードの 100 kHz を設定する（CKCFGR = 48MHz / 200kHz = 240 = 0x00F0、実測）。
  I2C_InitTSturcture.I2C_ClockSpeed = 100000;
  I2C_InitTSturcture.I2C_Mode = I2C_Mode_I2C;
  // I2Cスレーブアドレスを指定
  I2C_InitTSturcture.I2C_OwnAddress1 = I2C_ADDRESS << 1;
  I2C_InitTSturcture.I2C_Ack = I2C_Ack_Enable;
  I2C_InitTSturcture.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
  I2C_Init(I2C1, &I2C_InitTSturcture);

  // I2Cの有効化
  I2C_Cmd(I2C1, ENABLE);
  // I2C ACKの有効化
  I2C_AcknowledgeConfig(I2C1, ENABLE);

  // I2Cの割込の有効化
  I2C_ITConfig(I2C1, I2C_IT_EVT, ENABLE);
  I2C_ITConfig(I2C1, I2C_IT_ERR, ENABLE);
  I2C_ITConfig(I2C1, I2C_IT_BUF, ENABLE);
  NVIC_EnableIRQ(I2C1_EV_IRQn);
  NVIC_SetPriority(I2C1_EV_IRQn, 2 << 4);
  NVIC_EnableIRQ(I2C1_ER_IRQn);

  // printf("I2C1->CTLR1: %4x\r\n", I2C1->CTLR1);
  // printf("I2C1->CTLR2: %4x\r\n", I2C1->CTLR2);
  // printf("I2C1->CKCFGR: %4x\r\n", I2C1->CKCFGR);
  // printf("I2C1->OADDR1: %4x\r\n", I2C1->OADDR1);

  for (int i = 0; i < 4; i++)
  {
    i2c_registers[0x20 + i] = 0x10 * i;
  }

  Delay_Ms(100);

  printf("start\r\n");

  while (1)
  {
    if (i2c_request_available > 0)
    {
      printf("request: count=%d, start=%x, length=%d\r\n", i2c_request_available, i2c_start_position, i2c_position - i2c_start_position);
      printf("reg[0x20]: %x %x %x %x\r\n", i2c_registers[0x20], i2c_registers[0x21], i2c_registers[0x22], i2c_registers[0x23]);
      i2c_request_available = 0;
    }

    if (i2c_receive_available > 0)
    {
      printf("receive: count=%d, start=%x, length=%d\r\n", i2c_receive_available, i2c_start_position, i2c_position - i2c_start_position);
      printf("reg[0x10]: %x %x %x %x\r\n", i2c_registers[0x10], i2c_registers[0x11], i2c_registers[0x12], i2c_registers[0x13]);
      i2c_receive_available = 0;
    }
  }
}
