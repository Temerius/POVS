/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body - Gamepad with calibration
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dma.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "stdio.h"
#include "string.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define SEND_INTERVAL_MS  20  // ???????? 20?? (50 Hz)
#define CALIBRATION_SAMPLES 50
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
uint16_t adc_buffer[2];
char uart_buf[128];
uint32_t send_counter = 0;
volatile uint8_t adc_ready = 0;

// ????????????? ???????? ??? ?????????
uint16_t joy_x_min = 0;
uint16_t joy_x_max = 4095;
uint16_t joy_x_center = 2048;

uint16_t joy_y_min = 0;
uint16_t joy_y_max = 4095;
uint16_t joy_y_center = 2048;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
int16_t transform_axe_calibrated(uint16_t raw, uint16_t min_val, uint16_t max_val, uint16_t center);
void Send_Data(void);
void Calibrate_Joystick(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

// ?????????????? ? ?????? ?????????? - ???????????? ????? -100..+100
int16_t transform_axe_calibrated(uint16_t raw, uint16_t min_val, uint16_t max_val, uint16_t center)
{
    int32_t result;
    
    if (raw < center)
    {
        // ????????????? ?????: min_val..center -> -100..0
        if (center == min_val) return 0;
        result = ((int32_t)raw - (int32_t)center) * 100 / ((int32_t)center - (int32_t)min_val);
    }
    else
    {
        // ????????????? ?????: center..max_val -> 0..+100
        if (max_val == center) return 0;
        result = ((int32_t)raw - (int32_t)center) * 100 / ((int32_t)max_val - (int32_t)center);
    }
    
    // ????????????
    if (result < -100) result = -100;
    if (result > 100) result = 100;
    
    return (int16_t)result;
}

void Calibrate_Joystick(void)
{
    char msg[64];
    uint32_t sum_x = 0, sum_y = 0;
    
    HAL_UART_Transmit(&huart3, (uint8_t*)"[CAL] Reading center...\r\n", 25, 100);
    
    // ?????? ????? (???????? ? ?????)
    for (int i = 0; i < CALIBRATION_SAMPLES; i++)
    {
        HAL_Delay(10);
        sum_x += adc_buffer[0];
        sum_y += adc_buffer[1];
    }
    
    joy_x_center = sum_x / CALIBRATION_SAMPLES;
    joy_y_center = sum_y / CALIBRATION_SAMPLES;
    
    // ????????????? ???????? min/max ?? ?????? ??????
    // ???????????? ???????????? ???????? ?? ??????
    uint16_t range_x = (joy_x_center < 2048) ? joy_x_center : (4095 - joy_x_center);
    uint16_t range_y = (joy_y_center < 2048) ? joy_y_center : (4095 - joy_y_center);
    
    joy_x_min = joy_x_center - range_x;
    joy_x_max = joy_x_center + range_x;
    joy_y_min = joy_y_center - range_y;
    joy_y_max = joy_y_center + range_y;
    
    int len = snprintf(msg, sizeof(msg), "[CAL] X: center=%d, range=%d-%d\r\n", 
                       joy_x_center, joy_x_min, joy_x_max);
    HAL_UART_Transmit(&huart3, (uint8_t*)msg, len, 100);
    
    len = snprintf(msg, sizeof(msg), "[CAL] Y: center=%d, range=%d-%d\r\n", 
                   joy_y_center, joy_y_min, joy_y_max);
    HAL_UART_Transmit(&huart3, (uint8_t*)msg, len, 100);
    
    HAL_UART_Transmit(&huart3, (uint8_t*)"[CAL] Done!\r\n", 13, 100);
}

void Send_Data(void)
{
    send_counter++;

    int16_t x_val = transform_axe_calibrated(adc_buffer[0], joy_x_min, joy_x_max, joy_x_center);
    int16_t y_val = transform_axe_calibrated(adc_buffer[1], joy_y_min, joy_y_max, joy_y_center);

    int len = snprintf(uart_buf, sizeof(uart_buf),
        "X=%d;Y=%d;UP=%d;RIGHT=%d;LEFT=%d;DOWN=%d;E=%d;F=%d;JOYSTICK=%d;CNT=%lu\r\n",
        x_val,
        y_val,
        HAL_GPIO_ReadPin(BUTTON_UP_GPIO_Port, BUTTON_UP_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(BUTTON_RIGHT_GPIO_Port, BUTTON_RIGHT_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(BUTTON_LEFT_GPIO_Port, BUTTON_LEFT_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(BUTTON_DOWN_GPIO_Port, BUTTON_DOWN_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(BUTTON_E_GPIO_Port, BUTTON_E_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(BUTTON_F_GPIO_Port, BUTTON_F_Pin) == GPIO_PIN_RESET ? 1 : 0,
        HAL_GPIO_ReadPin(BUTTON_JOYSTICK_GPIO_Port, BUTTON_JOYSTICK_Pin) == GPIO_PIN_RESET ? 1 : 0,
        send_counter
    );

    HAL_UART_Transmit(&huart3, (uint8_t*)uart_buf, len, 100);
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
    if (hadc->Instance == ADC1)
    {
        adc_ready = 1;
    }
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */
  uint32_t last_send_tick = 0;
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/
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
  MX_ADC1_Init();
  MX_USART3_UART_Init();
  
  /* USER CODE BEGIN 2 */
  
  HAL_ADCEx_Calibration_Start(&hadc1);
  HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, 2);
  
  char startup_msg[] = "=== STM32 Gamepad Started ===\r\n";
  HAL_UART_Transmit(&huart3, (uint8_t*)startup_msg, strlen(startup_msg), 100);
  
  // ?????? - ?? ?????? ????????
  for(int i = 0; i < 3; i++)
  {
      HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_SET);
      HAL_Delay(100);
      HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_RESET);
      HAL_Delay(100);
  }
  
  // ???? ???????????? ADC
  HAL_Delay(200);
  
  // ????????? ????????
  Calibrate_Joystick();
  
  // ????? - ??????? ???????
  for(int i = 0; i < 5; i++)
  {
      HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_SET);
      HAL_Delay(50);
      HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_RESET);
      HAL_Delay(50);
  }
  
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    if (HAL_GetTick() - last_send_tick >= SEND_INTERVAL_MS)
    {
        last_send_tick = HAL_GetTick();
        Send_Data();
        
        if (send_counter % 50 == 0)
        {
            HAL_GPIO_TogglePin(LD2_GPIO_Port, LD2_Pin);
        }
    }
    
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
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL16;
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
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV8;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
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

/* USER CODE BEGIN 4 */
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
