/* USER CODE BEGIN Header */
/**
  * @file           : main.c
  * @brief          : USART2 DMA Test - Space Defender Init
  */
/* USER CODE END Header */

#include "main.h"
#include <string.h>
#include <stdio.h>

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart2;
DMA_HandleTypeDef hdma_usart2_tx;
DMA_HandleTypeDef hdma_usart2_rx;

/* USER CODE BEGIN PV */
volatile uint8_t uart_tx_busy = 0;
static uint32_t message_counter = 0;

// RX DMA buffer
#define RX_BUFFER_SIZE 32
static uint8_t rx_buffer[RX_BUFFER_SIZE];
static volatile uint16_t rx_write_pos = 0;

// Display variables
volatile uint8_t disp_buf[4] = {0, 0, 0, 0};
static uint32_t last_refresh_tick = 0;
static uint8_t current_digit = 0;
#define DIGIT_ON_MS 2

// Segment patterns for digits 0-9 (common cathode)
static const uint8_t seg_digits[10] = {
    0b00111111, /* 0 */ 0b00000110, /* 1 */ 0b01011011, /* 2 */ 0b01001111, /* 3 */
    0b01100110, /* 4 */ 0b01101101, /* 5 */ 0b01111101, /* 6 */ 0b00000111, /* 7 */
    0b01111111, /* 8 */ 0b01101111  /* 9 */
};

static uint8_t received_number = 0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_USART2_UART_Init(void);

/* USER CODE BEGIN PFP */
static void uart_print_dma(const char *s);
static void shift_out_byte(uint8_t b);
static void latch_pulse(void);
static void prepare_display_buffer(uint8_t number);
static void display_refresh_cycle(void);
static void process_rx_data(void);
/* USER CODE END PFP */

/* USER CODE BEGIN 0 */

static void uart_print_dma(const char *s)
{
    uint16_t len = (uint16_t)strlen(s);
    if (len == 0) return;
    
    // ???? ???????????? ?????????? ????????
    while(uart_tx_busy);
    
    if (HAL_UART_Transmit_DMA(&huart2, (uint8_t *)s, len) == HAL_OK)
    {
        uart_tx_busy = 1;
    }
}

static void shift_out_byte(uint8_t b)
{
    for (int i = 7; i >= 0; --i)
    {
        uint8_t bit = (b >> i) & 0x1;
        HAL_GPIO_WritePin(DATA_DISP_GPIO_Port, DATA_DISP_Pin, 
                         bit ? GPIO_PIN_SET : GPIO_PIN_RESET);
        HAL_GPIO_WritePin(CLK_DISP_GPIO_Port, CLK_DISP_Pin, GPIO_PIN_SET);
        HAL_GPIO_WritePin(CLK_DISP_GPIO_Port, CLK_DISP_Pin, GPIO_PIN_RESET);
    }
}

static void latch_pulse(void)
{
    HAL_GPIO_WritePin(LATCH_DISP_GPIO_Port, LATCH_DISP_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(LATCH_DISP_GPIO_Port, LATCH_DISP_Pin, GPIO_PIN_RESET);
}

static void prepare_display_buffer(uint8_t number)
{
    // ???????????? ?? 99
    if (number > 99) number = 99;
    
    uint8_t d1 = number / 10;  // ???????
    uint8_t d0 = number % 10;  // ???????
    
    // ????????? ????? (?????????? ????????, ???????? ????? ??? ??????)
    disp_buf[0] = 0;              // digit 3 - ?????
    disp_buf[1] = 0;              // digit 2 - ?????  
    disp_buf[2] = seg_digits[d1]; // digit 1 - ???????
    disp_buf[3] = seg_digits[d0]; // digit 0 - ???????
}

static void display_refresh_cycle(void)
{
    uint32_t now = HAL_GetTick();
    
    if ((now - last_refresh_tick) >= DIGIT_ON_MS)
    {
        // ????? ?????? ??? ???????? ???????
        uint8_t segments = disp_buf[current_digit];
        uint8_t digit_mask = (1 << current_digit);
        
        // ?????: ??????? ????????, ????? ????? ???????!
        shift_out_byte(~segments);    // ??????????? ??? ?????? ??????
        shift_out_byte(digit_mask);   // ????? ??????? (????? ?????? ????????)
        latch_pulse();                // ???????????
        
        current_digit++;
        if (current_digit >= 4) current_digit = 0;
        
        last_refresh_tick = now;
    }
}

static void process_rx_data(void)
{
    // ???????? ??????? ??????? ?????? DMA
    uint16_t dma_pos = RX_BUFFER_SIZE - __HAL_DMA_GET_COUNTER(&hdma_usart2_rx);
    
    // ???????????? ????? ??????
    while(rx_write_pos != dma_pos)
    {
        uint8_t byte = rx_buffer[rx_write_pos];
        
        // ???? ??? ????? ASCII (0-9)
        if(byte >= '0' && byte <= '9')
        {
            received_number = byte - '0';
            prepare_display_buffer(received_number);
            
            // ?????????? ????????????? ???????
            char ack[32];
            sprintf(ack, "Received: %d\r\n", received_number);
            uart_print_dma(ack);
        }
        // ???? ?????????? ????? (10-99)
        else if(byte >= 10 && byte <= 99)
        {
            received_number = byte;
            prepare_display_buffer(received_number);
            
            char ack[32];
            sprintf(ack, "Received: %d\r\n", received_number);
            uart_print_dma(ack);
        }
        
        rx_write_pos++;
        if(rx_write_pos >= RX_BUFFER_SIZE) rx_write_pos = 0;
    }
}

/* USER CODE END 0 */

int main(void)
{
  /* USER CODE BEGIN 1 */
  char message_buf[64];
  /* USER CODE END 1 */

  HAL_Init();
  SystemClock_Config();

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_USART2_UART_Init();
  
  /* USER CODE BEGIN 2 */
  
  // ????????????? ???????????
  HAL_GPIO_WritePin(LED_D12_GPIO_Port, LED_D12_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(LED_D11_GPIO_Port, LED_D11_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(LED_D10_GPIO_Port, LED_D10_Pin, GPIO_PIN_RESET);
  
  // ????????????? ???????
  HAL_GPIO_WritePin(CLK_DISP_GPIO_Port, CLK_DISP_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(DATA_DISP_GPIO_Port, DATA_DISP_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(LATCH_DISP_GPIO_Port, LATCH_DISP_Pin, GPIO_PIN_RESET);
  
  // ????????? ????? ????? DMA ? ??????????? ??????
  HAL_UART_Receive_DMA(&huart2, rx_buffer, RX_BUFFER_SIZE);
  
  // ????????? ???????? ?? ???????
  prepare_display_buffer(0);
  last_refresh_tick = HAL_GetTick();
  
  // ????????? ?????????
  uart_print_dma("\r\n=================================\r\n");
  uart_print_dma("Space Defender - USART+DMA Test\r\n");
  uart_print_dma("STM32F103 Ready!\r\n");
  uart_print_dma("TX: Sending messages...\r\n");
  uart_print_dma("RX: Waiting for numbers (0-99)\r\n");
  uart_print_dma("=================================\r\n\r\n");
  
  HAL_Delay(500);
  
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    
    // ????????? ??????? (?????????, ??????? ?????????)
    display_refresh_cycle();
    
    // ???????????? ???????? ?????? ?? USART
    process_rx_data();
    
    // ?????????? ????????? ??? ? ???????
    static uint32_t last_tx_time = 0;
    uint32_t now = HAL_GetTick();
    
    if((now - last_tx_time) >= 1000)
    {
        // ????????? ????????? ?? ?????????
        char message_buf[64];
        sprintf(message_buf, "[%lu] Display shows: %d\r\n", message_counter++, received_number);
        
        // ?????????? ????? DMA
        uart_print_dma(message_buf);
        
        // ?????? ??????????? ??? ?????????
        HAL_GPIO_TogglePin(LED_D12_GPIO_Port, LED_D12_Pin);
        
        last_tx_time = now;
    }
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI_DIV2;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL16;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{
  /* DMA controller clock enable */
  __HAL_RCC_DMA1_CLK_ENABLE();

  /* DMA interrupt init */
  /* DMA1_Channel7_IRQn interrupt configuration (USART2_TX) */
  HAL_NVIC_SetPriority(DMA1_Channel7_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel7_IRQn);
  
  /* DMA1_Channel6_IRQn interrupt configuration (USART2_RX) */
  HAL_NVIC_SetPriority(DMA1_Channel6_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel6_IRQn);
}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, LED_D12_Pin|LED_D11_Pin|CLK_DISP_Pin|DATA_DISP_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOB, LED_D10_Pin|LATCH_DISP_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : LED_D12_Pin LED_D11_Pin */
  GPIO_InitStruct.Pin = LED_D12_Pin|LED_D11_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : CLK_DISP_Pin DATA_DISP_Pin */
  GPIO_InitStruct.Pin = CLK_DISP_Pin|DATA_DISP_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_PULLDOWN;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : LED_D10_Pin LATCH_DISP_Pin */
  GPIO_InitStruct.Pin = LED_D10_Pin|LATCH_DISP_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_PULLDOWN;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pins : CANON_LEFT_Pin CANON_RIGHT_Pin (?? ?????????? ????) */
  GPIO_InitStruct.Pin = CANON_LEFT_Pin|CANON_RIGHT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLDOWN;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pin : CANON_FIRE_Pin (?? ?????????? ????) */
  GPIO_InitStruct.Pin = CANON_FIRE_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLDOWN;
  HAL_GPIO_Init(CANON_FIRE_GPIO_Port, &GPIO_InitStruct);
}

/* USER CODE BEGIN 4 */

// Callback: DMA ???????? ?????????
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
  if(huart->Instance == USART2)
  {
    uart_tx_busy = 0;
  }
}

/* USER CODE END 4 */

void Error_Handler(void)
{
  __disable_irq();
  while (1)
  {
  }
}

#ifdef  USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
}
#endif