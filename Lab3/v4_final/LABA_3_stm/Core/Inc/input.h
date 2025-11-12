/* input.h - Обработка ввода с кнопок */

#ifndef INPUT_H
#define INPUT_H

#include <stdint.h>
#include "main.h"

// Кнопки
typedef enum {
    BTN_LEFT = 0,
    BTN_RIGHT = 1,
    BTN_SHOOT = 2
} Button;

// Состояние ввода
typedef struct {
    uint8_t left_pressed;
    uint8_t right_pressed;
    uint8_t shoot_pressed;
    
    uint8_t left_prev;
    uint8_t right_prev;
    uint8_t shoot_prev;
} InputState;

// Инициализация (пины уже настроены в MX_GPIO_Init)
void Input_Init(void);

// Обновление состояния кнопок
void Input_Update(InputState* input);

// Проверка нажатия
uint8_t Input_IsPressed(InputState* input, Button button);

// Проверка только что нажали (edge detection)
uint8_t Input_JustPressed(InputState* input, Button button);

#endif // INPUT_H