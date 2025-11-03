/* input.c - Реализация ввода */

#include "input.h"
#include "main.h"

void Input_Init(void) {
    
}

void Input_Update(InputState* input) {
    // Сохраняем предыдущее состояние
    input->left_prev = input->left_pressed;
    input->right_prev = input->right_pressed;
    input->shoot_prev = input->shoot_pressed;
    
    // Читаем текущее состояние кнопок (активны при HIGH)
    input->left_pressed = HAL_GPIO_ReadPin(CANON_LEFT_GPIO_Port, CANON_LEFT_Pin);
    input->right_pressed = HAL_GPIO_ReadPin(CANON_RIGHT_GPIO_Port, CANON_RIGHT_Pin);
    input->shoot_pressed = HAL_GPIO_ReadPin(CANON_FIRE_GPIO_Port, CANON_FIRE_Pin);
}

uint8_t Input_IsPressed(InputState* input, Button button) {
    switch (button) {
        case BTN_LEFT:
            return input->left_pressed;
        case BTN_RIGHT:
            return input->right_pressed;
        case BTN_SHOOT:
            return input->shoot_pressed;
        default:
            return 0;
    }
}

uint8_t Input_JustPressed(InputState* input, Button button) {
    switch (button) {
        case BTN_LEFT:
            return input->left_pressed && !input->left_prev;
        case BTN_RIGHT:
            return input->right_pressed && !input->right_prev;
        case BTN_SHOOT:
            return input->shoot_pressed && !input->shoot_prev;
        default:
            return 0;
    }
}