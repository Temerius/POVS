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
extern int btn_a;
extern int btn_b;
extern int btn_c;
extern int btn_d;
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
#define X_AXES_Pin GPIO_PIN_0
#define X_AXES_GPIO_Port GPIOA
#define Y_AXES_Pin GPIO_PIN_1
#define Y_AXES_GPIO_Port GPIOA
#define LD2_Pin GPIO_PIN_5
#define LD2_GPIO_Port GPIOA
#define BUTTON_E_Pin GPIO_PIN_0
#define BUTTON_E_GPIO_Port GPIOB
#define BUTTON_F_Pin GPIO_PIN_1
#define BUTTON_F_GPIO_Port GPIOB
#define BUTTON_JOYSTICK_Pin GPIO_PIN_10
#define BUTTON_JOYSTICK_GPIO_Port GPIOB
#define BUTTON_UP_Pin GPIO_PIN_10
#define BUTTON_UP_GPIO_Port GPIOA
#define BUTTON_RIGHT_Pin GPIO_PIN_3
#define BUTTON_RIGHT_GPIO_Port GPIOB
#define BUTTON_LEFT_Pin GPIO_PIN_4
#define BUTTON_LEFT_GPIO_Port GPIOB
#define BUTTON_DOWN_Pin GPIO_PIN_5
#define BUTTON_DOWN_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
