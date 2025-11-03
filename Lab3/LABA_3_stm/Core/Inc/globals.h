/* globals.h - Объявления глобальных переменных */

#ifndef GLOBALS_H
#define GLOBALS_H

#include <stdint.h>
#include "game_config.h"

// Глобальная переменная для генератора случайных чисел
extern uint32_t Utils_RandomSeed;

// Переменные для протокола
extern uint8_t rx_buffer[RX_BUFFER_SIZE];
extern uint8_t tx_buffer[TX_BUFFER_SIZE];
extern volatile uint8_t uart_tx_busy;

#endif // GLOBALS_H