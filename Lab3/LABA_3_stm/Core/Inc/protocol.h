/* protocol.h - Протокол связи с PC (окончательная версия) */

#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include "main.h"
#include "game_types.h"

// === СТАРТОВЫЕ И КОНЕЧНЫЕ БАЙТЫ ===
#define START_BYTE 0xAA
#define END_BYTE 0x55

// === ТИПЫ ПАКЕТОВ ===
#define PKT_GAME_STATE     0x01  // STM32 -> PC
#define PKT_ADD_ENEMY      0x02  // PC -> STM32
#define PKT_ADD_OBSTACLE   0x03  // PC -> STM32
#define PKT_CLEANUP        0x04  // PC -> STM32
#define PKT_INIT_GAME      0x05  // PC -> STM32
#define PKT_ADD_WHIRLPOOL  0x06  // PC -> STM32
#define PKT_DEBUG          0x07  // STM32 -> PC (новый!)

// Структура debug-пакета
#pragma pack(push, 1)
typedef struct {
    uint8_t header;              // PKT_DEBUG
    uint8_t received_packet_type; // Тип полученного пакета
    uint8_t packet_size;          // Размер полученного пакета
    uint8_t parse_state;          // Состояние парсера
    uint8_t crc_received;         // Полученный CRC
    uint8_t crc_calculated;       // Вычисленный CRC
    uint8_t success;              // 1 = успех, 0 = ошибка
    char message[32];             // Текстовое сообщение
    uint8_t crc;                  // CRC debug-пакета
    uint8_t end_byte;             // END_BYTE
} DebugPacket;
#pragma pack(pop)

// Добавьте прототип функции
void Protocol_SendDebug(uint8_t packet_type, uint8_t packet_size, uint8_t parse_state,
                       uint8_t crc_received, uint8_t crc_calculated, 
                       uint8_t success, const char* message);

// === ОПТИМИЗИРОВАННЫЕ РАЗМЕРЫ ПАКЕТОВ ===
#define MAX_ENEMIES_IN_PACKET 6      // Уменьшено для надежности
#define MAX_PROJECTILES_IN_PACKET 10 // Уменьшено для надежности
#define MAX_WHIRLPOOLS_IN_PACKET 3   // Уменьшено для надежности

// === СТРУКТУРЫ ПАКЕТОВ ===
#pragma pack(push, 1)
typedef struct {
    uint8_t header;              // PKT_GAME_STATE
    
    // Игрок
    float player_x;
    float player_y;
    float player_angle;
    int16_t player_health;
    uint16_t player_score;
    uint16_t player_shoot_cooldown;
    
    // Враги
    uint8_t enemy_count;
    struct {
        uint8_t type;
        float x;
        float y;
        int8_t health;
    } enemies[MAX_ENEMIES_IN_PACKET];
    
    // Снаряды
    uint8_t projectile_count;
    struct {
        float x;
        float y;
        uint8_t is_player_shot;
    } projectiles[MAX_PROJECTILES_IN_PACKET];
    
    // Водовороты
    uint8_t whirlpool_count;
    struct {
        float x;
        float y;
        uint8_t used;
    } whirlpools[MAX_WHIRLPOOLS_IN_PACKET];
    
    float camera_y;
    uint32_t frame_counter;
    uint8_t crc;                 // CRC8 для проверки целостности
    uint8_t end_byte;            // Должен быть равен END_BYTE
} GameStatePacket;
#pragma pack(pop)

// Пакет добавления врага (PC -> STM32)
typedef struct __attribute__((packed)) {
    uint8_t header;              // PKT_ADD_ENEMY
    uint8_t type;                // 0=simple, 1=hard
    float x;
    float y;
    uint8_t crc;
    uint8_t end_byte;
} AddEnemyPacket;

// Пакет добавления препятствия (PC -> STM32)
typedef struct __attribute__((packed)) {
    uint8_t header;              // PKT_ADD_OBSTACLE
    uint8_t type;                // 0=island, 1=shore_left, 2=shore_right
    float x;
    float y;
    float radius;
    uint8_t crc;
    uint8_t end_byte;
} AddObstaclePacket;

// Пакет добавления водоворота (PC -> STM32)
typedef struct __attribute__((packed)) {
    uint8_t header;              // PKT_ADD_WHIRLPOOL
    float x;
    float y;
    uint8_t crc;
    uint8_t end_byte;
} AddWhirlpoolPacket;

// Пакет очистки (PC -> STM32)
typedef struct __attribute__((packed)) {
    uint8_t header;              // PKT_CLEANUP
    float threshold_y;
    uint8_t crc;
    uint8_t end_byte;
} CleanupPacket;

// === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
extern uint8_t rx_buffer[RX_BUFFER_SIZE];
extern volatile uint16_t rx_write_pos;  // Позиция записи в буфере
extern volatile uint8_t uart_tx_busy;

// === API ФУНКЦИИ ===
void Protocol_Init(UART_HandleTypeDef* huart);
void Protocol_SendGameState(GameState* state);
void Protocol_ProcessIncoming(GameState* state);
void Protocol_CleanupRxBuffer(void);
uint8_t Protocol_CalculateCRC(uint8_t* data, uint16_t len);

#endif // PROTOCOL_H