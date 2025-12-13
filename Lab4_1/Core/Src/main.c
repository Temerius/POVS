/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body with DEBUG
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define DEBUG_ENABLED 1
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;
DMA_HandleTypeDef hdma_adc1;

TIM_HandleTypeDef htim2;

UART_HandleTypeDef huart2;
DMA_HandleTypeDef hdma_usart2_tx;

/* USER CODE BEGIN PV */
uint16_t adc_buffer[2] = {0, 0};
char uart_buf[128];
volatile uint32_t dma_complete_count = 0;
volatile uint32_t loop_count = 0;
volatile uint8_t adc_dma_error = 0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_ADC1_Init(void);
static void MX_TIM2_Init(void);
/* USER CODE BEGIN PFP */
void Debug_LED_Blink(uint8_t times, uint32_t delay_ms);
void Debug_SendString(const char* str);
void Debug_SendStatus(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

// ??????? LED ??? ???????
void Debug_LED_Blink(uint8_t times, uint32_t delay_ms)
{
    for(uint8_t i = 0; i < times; i++)
    {
        HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_SET);
        HAL_Delay(delay_ms);
        HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_RESET);
        HAL_Delay(delay_ms);
    }
}

// ???????? ?????? ????? UART (???????????)
void Debug_SendString(const char* str)
{
    HAL_UART_Transmit(&huart2, (uint8_t*)str, strlen(str), 500);
}

// ???????? ??????? ???????
void Debug_SendStatus(void)
{
    char buf[200];
    int len = snprintf(buf, sizeof(buf),
        "[DEBUG] Loop:%lu DMA_Done:%lu ADC_Err:%d ADC_State:%d DMA_State:%d RAW_ADC0:%u RAW_ADC1:%u\r\n",
        loop_count,
        dma_complete_count,
        adc_dma_error,
        (int)HAL_ADC_GetState(&hadc1),
        (int)HAL_DMA_GetState(&hdma_adc1),
        adc_buffer[0],
        adc_buffer[1]
    );
    HAL_UART_Transmit(&huart2, (uint8_t*)buf, len, 500);
}

int16_t transform_axe(int v)
{
    int32_t centered = v - 2048;
    int32_t scaled = centered * 100 / 2048;
    return (int16_t)scaled;
}

void Send_Data(void)
{
    int len = snprintf(uart_buf, sizeof(uart_buf),
        "X=%d;Y=%d;E=%d;F=%d;JS=%d;UP=%d;RIGHT=%d;LEFT=%d;DOWN=%d\r\n",
        transform_axe(adc_buffer[0]),
        transform_axe(adc_buffer[1]),
        HAL_GPIO_ReadPin(GPIOB, BUTTON_E_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(GPIOB, BUTTON_F_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(GPIOB, BUTTON_JOYSTICK_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(GPIOA, BUTTON_UP_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(GPIOB, BUTTON_RIGHT_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(GPIOB, BUTTON_LEFT_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(GPIOB, BUTTON_DOWN_Pin) == GPIO_PIN_RESET ? 1 : 0
    );

    HAL_StatusTypeDef status = HAL_UART_Transmit(&huart2, (uint8_t*)uart_buf, len, 100);
    
    // ???? UART ?????? ?????? - ??????? ???????
    if(status != HAL_OK)
    {
        Debug_LED_Blink(10, 50);
    }
}

// Callback ????? DMA ???????? ???????? (???????? ??????)
void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef* hadc)
{
    // ?? ??????????, ?? ????? ???????? ???????
}

// Callback ????? DMA ???????? ?????? ????????
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
    if(hadc->Instance == ADC1)
    {
        dma_complete_count++;
    }
}

// Callback ??? ?????? ADC
void HAL_ADC_ErrorCallback(ADC_HandleTypeDef *hadc)
{
    adc_dma_error = 1;
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */
  HAL_StatusTypeDef status;
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_USART2_UART_Init();
  
  /* USER CODE BEGIN 2 */
  // === ???? 1: ??????? ????????????? ?????? ===
  Debug_LED_Blink(2, 200);  // 2 ??????? = GPIO + DMA + UART ??????
  
  Debug_SendString("\r\n\r\n");
  Debug_SendString("================================\r\n");
  Debug_SendString("=== STM32 GAMEPAD CONTROLLER ===\r\n");
  Debug_SendString("================================\r\n");
  Debug_SendString("[BOOT] GPIO Init: OK\r\n");
  Debug_SendString("[BOOT] DMA Init: OK\r\n");
  Debug_SendString("[BOOT] UART Init: OK\r\n");
  
  /* USER CODE END 2 */
  
  MX_ADC1_Init();
  
  /* USER CODE BEGIN 2.5 */
  Debug_SendString("[BOOT] ADC1 Init: OK\r\n");
  
  MX_TIM2_Init();
  Debug_SendString("[BOOT] TIM2 Init: OK\r\n");
  
  // === ???? 2: ?????????? ADC ===
  Debug_SendString("[BOOT] Starting ADC calibration...\r\n");
  status = HAL_ADCEx_Calibration_Start(&hadc1);
  if(status != HAL_OK)
  {
      Debug_SendString("[ERROR] ADC Calibration FAILED!\r\n");
      Debug_LED_Blink(20, 100);  // ????? ??????? ??????? = ??????
  }
  else
  {
      Debug_SendString("[BOOT] ADC Calibration: OK\r\n");
  }
  
  // === ???? 3: ?????? ADC ? DMA ===
  Debug_SendString("[BOOT] Starting ADC DMA...\r\n");
  
  // ???????? ????????? DMA ????? ????????
  char dbg[100];
  snprintf(dbg, sizeof(dbg), "[DEBUG] DMA State before start: %d\r\n", 
           (int)HAL_DMA_GetState(&hdma_adc1));
  Debug_SendString(dbg);
  
  status = HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, 2);
  if(status != HAL_OK)
  {
      snprintf(dbg, sizeof(dbg), "[ERROR] ADC DMA Start FAILED! Status=%d\r\n", (int)status);
      Debug_SendString(dbg);
      Debug_LED_Blink(30, 50);  // ????? ????? ??????? ??????? = ??????????? ??????
  }
  else
  {
      Debug_SendString("[BOOT] ADC DMA: STARTED OK\r\n");
  }
  
  Debug_LED_Blink(3, 100);  // 3 ???????? ??????? = ??? ????????????????
  
  Debug_SendString("[BOOT] Waiting 500ms for ADC to collect data...\r\n");
  HAL_Delay(500);  // ????? ????? ADC ??????? ??????
  
  // ????????, ???? ?? ??????
  snprintf(dbg, sizeof(dbg), "[TEST] ADC Buffer: [0]=%u [1]=%u\r\n", 
           adc_buffer[0], adc_buffer[1]);
  Debug_SendString(dbg);
  
  snprintf(dbg, sizeof(dbg), "[TEST] DMA Complete count: %lu\r\n", dma_complete_count);
  Debug_SendString(dbg);
  
  Debug_SendString("[BOOT] Entering main loop...\r\n");
  Debug_SendString("================================\r\n\r\n");
  /* USER CODE END 2.5 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    loop_count++;
    
    // ?????? 50 ???????? (???????? ??? ? ???????) ?????? LED
    if(loop_count % 50 == 0)
    {
        HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);
    }
    
    // ?????? 100 ???????? ?????????? ?????????? ??????????
    #if DEBUG_ENABLED
    if(loop_count % 100 == 0)
    {
        Debug_SendStatus();
    }
    #endif
    
    // ?????????? ???????? ??????
    Send_Data();
    
    HAL_Delay(20);
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
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
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI_DIV2;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC;
  PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV2;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC1_Init(void)
{

  /* USER CODE BEGIN ADC1_Init 0 */
  // ?????: ??????? ??????????? DMA, ????? ADC!
  hdma_adc1.Instance = DMA1_Channel1;
  hdma_adc1.Init.Direction = DMA_PERIPH_TO_MEMORY;
  hdma_adc1.Init.PeriphInc = DMA_PINC_DISABLE;
  hdma_adc1.Init.MemInc = DMA_MINC_ENABLE;
  hdma_adc1.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
  hdma_adc1.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
  hdma_adc1.Init.Mode = DMA_CIRCULAR;
  hdma_adc1.Init.Priority = DMA_PRIORITY_HIGH;
  if (HAL_DMA_Init(&hdma_adc1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE END ADC1_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */

  /** Common config
  */
  hadc1.Instance = ADC1;
  hadc1.Init.ScanConvMode = ADC_SCAN_ENABLE;
  hadc1.Init.ContinuousConvMode = ENABLE;
  hadc1.Init.DiscontinuousConvMode = DISABLE;
  hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc1.Init.NbrOfConversion = 2;
  if (HAL_ADC_Init(&hadc1) != HAL_OK)
  {
    Error_Handler();
  }
  
  /* USER CODE BEGIN ADC1_Init 1.5 */
  // ????????? DMA ? ADC ????? ????????????? ADC
  __HAL_LINKDMA(&hadc1, DMA_Handle, hdma_adc1);
  /* USER CODE END ADC1_Init 1.5 */

  /** Configure Regular Channel
  */
  sConfig.Channel = ADC_CHANNEL_0;
  sConfig.Rank = ADC_REGULAR_RANK_1;
  sConfig.SamplingTime = ADC_SAMPLETIME_239CYCLES_5;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Regular Channel
  */
  sConfig.Channel = ADC_CHANNEL_1;
  sConfig.Rank = ADC_REGULAR_RANK_2;
  sConfig.SamplingTime = ADC_SAMPLETIME_239CYCLES_5;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief TIM2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM2_Init(void)
{

  /* USER CODE BEGIN TIM2_Init 0 */

  /* USER CODE END TIM2_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM2_Init 1 */

  /* USER CODE END TIM2_Init 1 */
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 0;
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 1632;
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_UPDATE;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM2_Init 2 */

  /* USER CODE END TIM2_Init 2 */

}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
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
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{

  /* DMA controller clock enable */
  __HAL_RCC_DMA1_CLK_ENABLE();

  /* DMA interrupt init */
  /* DMA1_Channel1_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel1_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel1_IRQn);
  /* DMA1_Channel7_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel7_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel7_IRQn);

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
/* USER CODE BEGIN MX_GPIO_Init_1 */
/* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin : B1_Pin */
  GPIO_InitStruct.Pin = B1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(B1_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : LD2_Pin */
  GPIO_InitStruct.Pin = LD2_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LD2_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : BUTTON_E_Pin BUTTON_F_Pin BUTTON_JOYSTICK_Pin BUTTON_RIGHT_Pin
                           BUTTON_LEFT_Pin BUTTON_DOWN_Pin */
  GPIO_InitStruct.Pin = BUTTON_E_Pin|BUTTON_F_Pin|BUTTON_JOYSTICK_Pin|BUTTON_RIGHT_Pin
                          |BUTTON_LEFT_Pin|BUTTON_DOWN_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pin : BUTTON_UP_Pin */
  GPIO_InitStruct.Pin = BUTTON_UP_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(BUTTON_UP_GPIO_Port, &GPIO_InitStruct);

  /* EXTI interrupt init*/
  HAL_NVIC_SetPriority(EXTI15_10_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);

/* USER CODE BEGIN MX_GPIO_Init_2 */
/* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* ??????? ??????? ??? Error_Handler - ????? ??????? ??????? */
  __disable_irq();
  while (1)
  {
    HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);
    // ??????????? ???????? ??? HAL (?.?. ?????????? ?????????)
    for(volatile uint32_t i = 0; i < 100000; i++);
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
}
#endif /* USE_FULL_ASSERT */