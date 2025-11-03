/* globals.c - Глобальные переменные проекта */

#include "utils.h"
#include "protocol.h"

// Глобальная переменная для генератора случайных чисел
uint32_t Utils_RandomSeed = 0;

// Переменные для протокола
uint8_t rx_buffer[RX_BUFFER_SIZE];
uint8_t tx_buffer[TX_BUFFER_SIZE];
volatile uint8_t uart_tx_busy = 0;