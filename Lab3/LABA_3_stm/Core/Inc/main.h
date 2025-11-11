/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "game_config.h"
#include "game_types.h"
#include "utils.h"
#include "input.h"
#include "protocol.h"
#include "game_state.h"
#include "player.h"
#include "world_generation.h"
/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define CANON_LEFT_Pin GPIO_PIN_1
#define CANON_LEFT_GPIO_Port GPIOA
#define CANON_LEFT_EXTI_IRQn EXTI1_IRQn
#define USART_TX_Pin GPIO_PIN_2
#define USART_TX_GPIO_Port GPIOA
#define USART_RX_Pin GPIO_PIN_3
#define USART_RX_GPIO_Port GPIOA
#define CANON_RIGHT_Pin GPIO_PIN_4
#define CANON_RIGHT_GPIO_Port GPIOA
#define CANON_RIGHT_EXTI_IRQn EXTI4_IRQn
#define LED_D12_Pin GPIO_PIN_6
#define LED_D12_GPIO_Port GPIOA
#define LED_D11_Pin GPIO_PIN_7
#define LED_D11_GPIO_Port GPIOA
#define CANON_FIRE_Pin GPIO_PIN_0
#define CANON_FIRE_GPIO_Port GPIOB
#define CANON_FIRE_EXTI_IRQn EXTI0_IRQn
#define CLK_DISP_Pin GPIO_PIN_8
#define CLK_DISP_GPIO_Port GPIOA
#define DATA_DISP_Pin GPIO_PIN_9
#define DATA_DISP_GPIO_Port GPIOA
#define USER_BUZZER_Pin GPIO_PIN_3
#define USER_BUZZER_GPIO_Port GPIOB
#define LATCH_DISP_Pin GPIO_PIN_5
#define LATCH_DISP_GPIO_Port GPIOB
#define LED_D10_Pin GPIO_PIN_6
#define LED_D10_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
