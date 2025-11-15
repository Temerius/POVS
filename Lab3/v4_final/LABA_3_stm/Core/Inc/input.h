

#ifndef INPUT_H
#define INPUT_H

#include <stdint.h>
#include "main.h"


typedef enum {
    BTN_LEFT = 0,
    BTN_RIGHT = 1,
    BTN_SHOOT = 2
} Button;


typedef struct {
    uint8_t left_pressed;
    uint8_t right_pressed;
    uint8_t shoot_pressed;
    
    uint8_t left_prev;
    uint8_t right_prev;
    uint8_t shoot_prev;
} InputState;


void Input_Init(void);


void Input_Update(InputState* input);


uint8_t Input_IsPressed(InputState* input, Button button);


uint8_t Input_JustPressed(InputState* input, Button button);

#endif