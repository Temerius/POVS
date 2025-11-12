/* protocol.h - Упрощённый протокол: кнопки -> PC, мили <- PC */

#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include "main.h"

// === СТАРТОВЫЕ И КОНЕЧНЫЕ БАЙТЫ ===
#define START_BYTE 0xAA
#define END_BYTE 0x55

// === ТИПЫ ПАКЕТОВ ===
#define PKT_BUTTONS        0x01  // STM32 -> PC (состояние кнопок)
#define PKT_MILES          0x02  // PC -> STM32 (счёт в милях)

// === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
extern uint8_t rx_buffer[64];
extern uint8_t tx_buffer[64];
extern volatile uint8_t uart_tx_busy;
extern volatile uint16_t rx_write_pos;

// === СТРУКТУРЫ ПАКЕТОВ ===
#pragma pack(push, 1)

// Пакет кнопок (STM32 -> PC)
typedef struct {
    uint8_t start_byte;    
    uint8_t type;    // PKT_BUTTONS
    uint8_t left_pressed;  // 0 или 1
    uint8_t right_pressed; // 0 или 1
    uint8_t fire_pressed;  // 0 или 1
    uint8_t crc;
    uint8_t end_byte;
} ButtonPacket;

// Пакет миль (PC -> STM32)
typedef struct {
    uint8_t header;        // PKT_MILES
    uint16_t miles;        // 0-9999
    uint8_t crc;
    uint8_t end_byte;
} MilesPacket;

#pragma pack(pop)

// === API ФУНКЦИИ ===
void Protocol_Init(UART_HandleTypeDef* huart);
void Protocol_SendButtons(uint8_t left, uint8_t right, uint8_t fire);
void Protocol_ProcessIncoming(uint16_t* miles_out);
uint8_t Protocol_CalculateCRC(uint8_t* data, uint16_t len);

#endif // PROTOCOL_H