/* protocol.h - Протокол связи с PC (окончательная версия) */

#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include "main.h"
#include "game_types.h"

// === ТИПЫ ПАКЕТОВ ===
#define PKT_GAME_STATE     0x01  // STM32 -> PC
#define PKT_ADD_ENEMY      0x02  // PC -> STM32
#define PKT_ADD_OBSTACLE   0x03  // PC -> STM32
#define PKT_CLEANUP        0x04  // PC -> STM32
#define PKT_INIT_GAME      0x05  // PC -> STM32
#define PKT_ADD_WHIRLPOOL  0x06  // PC -> STM32

// === СТРУКТУРЫ ПАКЕТОВ ===

// Пакет состояния игры (STM32 -> PC)
typedef struct __attribute__((packed)) {
    uint8_t header;              // PKT_GAME_STATE
    
    // Игрок
    float player_x;
    float player_y;
    float player_angle;
    int16_t player_health;
    uint16_t player_score;
    
    // Враги (сжато)
    uint8_t enemy_count;         // общее количество
    struct __attribute__((packed)) {
        uint8_t type;            // 0=simple, 1=hard
        float x;
        float y;
        int8_t health;
    } enemies[15];               // максимум 15 для экономии
    
    // Снаряды (сжато)
    uint8_t projectile_count;
    struct __attribute__((packed)) {
        float x;
        float y;
        uint8_t is_player_shot;
    } projectiles[30];           // максимум 30
    
    // Водовороты
    uint8_t whirlpool_count;
    struct __attribute__((packed)) {
        float x;
        float y;
        uint8_t used;
    } whirlpools[WHIRLPOOL_MAX_COUNT];  // максимум WHIRLPOOL_MAX_COUNT водоворотов
    
    float camera_y;
    uint16_t checksum;
} GameStatePacket;

// Пакет добавления врага (PC -> STM32)
typedef struct __attribute__((packed)) {
    uint8_t header;              // PKT_ADD_ENEMY
    uint8_t type;                // 0=simple, 1=hard
    float x;
    float y;
    uint16_t checksum;
} AddEnemyPacket;

// Пакет добавления препятствия (PC -> STM32)
typedef struct __attribute__((packed)) {
    uint8_t header;              // PKT_ADD_OBSTACLE
    uint8_t type;                // 0=island, 1=shore_left, 2=shore_right
    float x;
    float y;
    float radius;
    uint16_t checksum;
} AddObstaclePacket;

// Пакет добавления водоворота (PC -> STM32)
typedef struct __attribute__((packed)) {
    uint8_t header;              // PKT_ADD_WHIRLPOOL
    float x;
    float y;
    uint16_t checksum;
} AddWhirlpoolPacket;

// Пакет очистки (PC -> STM32)
typedef struct __attribute__((packed)) {
    uint8_t header;              // PKT_CLEANUP
    float threshold_y;
    uint16_t checksum;
} CleanupPacket;

// === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
extern uint8_t rx_buffer[RX_BUFFER_SIZE];
extern uint8_t tx_buffer[TX_BUFFER_SIZE];
extern volatile uint8_t uart_tx_busy;

// === API ФУНКЦИИ ===

// Инициализация протокола
void Protocol_Init(UART_HandleTypeDef* huart);

// Отправка состояния игры
void Protocol_SendGameState(GameState* state);

// Обработка входящих данных
void Protocol_ProcessIncoming(GameState* state);

// Расчёт контрольной суммы
uint16_t Protocol_CalculateChecksum(uint8_t* data, uint16_t len);

#endif // PROTOCOL_H