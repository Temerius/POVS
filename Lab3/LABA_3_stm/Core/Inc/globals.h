
#ifndef GLOBALS_H
#define GLOBALS_H

#include <stdint.h>
#include "game_config.h"

 
extern uint32_t Utils_RandomSeed;

 
extern uint8_t rx_buffer[RX_BUFFER_SIZE];
extern uint8_t tx_buffer[TX_BUFFER_SIZE];
extern volatile uint8_t uart_tx_busy;
extern volatile uint16_t rx_write_pos;

#endif  