

// ===== File: ./Inc\cleanup.h =====

/* cleanup.h - Интерфейс очистки старых объектов */

#ifndef CLEANUP_H
#define CLEANUP_H

#include "game_types.h"

// Очистка старых врагов
void Enemies_CleanupOld(GameState* state, float threshold_y);

// Очистка старых препятствий
void Obstacles_CleanupOld(GameState* state, float threshold_y);

// Удаление препятствия
void Obstacles_Remove(GameState* state, uint8_t index);

#endif // CLEANUP_H

// ===== File: ./Inc\collisions.h =====

/* collisions.h - Интерфейс проверки коллизий */

#ifndef COLLISIONS_H
#define COLLISIONS_H

#include "game_types.h"

// Проверка всех коллизий в игре
void GameState_CheckCollisions(GameState* state);

// Проверка столкновений игрока с врагами
void Player_CheckEnemyCollisions(GameState* state);

#endif // COLLISIONS_H

// ===== File: ./Inc\enemies.h =====

/* enemies.h - Интерфейс врагов */

#ifndef ENEMIES_H
#define ENEMIES_H

#include "game_types.h"

// Обновление всех врагов
void Enemies_Update(GameState* state);

// Обновление AI простого врага
void EnemySimple_UpdateAI(EnemySimple* enemy, Player* player);

// Обновление AI сложного врага
void EnemyHard_UpdateAI(EnemyHard* enemy, Player* player, Obstacle* obstacles, uint8_t obstacle_count);

// Генерация точек патрулирования для сложного врага
void Enemies_GeneratePatrolPoints(EnemyHard* enemy, Player* player);

// Проверка видимости игрока простым врагом
uint8_t Enemies_CanSeePlayer(EnemySimple* enemy, Player* player);

// Проверка видимости игрока сложным врагом
uint8_t Enemies_CanSeePlayerHard(EnemyHard* enemy, Player* player);

// Стрельба простого врага
void Enemies_ShootAtPlayer(GameState* state, EnemySimple* enemy);

// Стрельба сложного врага
void Enemies_ShootHardAtPlayer(GameState* state, EnemyHard* enemy);

// Проверка коллизий врага с препятствиями
uint8_t Enemies_CheckCollision(GameState* state, float x, float y, float radius);

// Удаление врагов
void Enemies_RemoveSimple(GameState* state, uint8_t index);
void Enemies_RemoveHard(GameState* state, uint8_t index);

#endif // ENEMIES_H

// ===== File: ./Inc\game_config.h =====

/* game_config.h - Централизованная конфигурация игры */

#ifndef GAME_CONFIG_H
#define GAME_CONFIG_H

#include <stdint.h>

// === БУФЕРЫ USART ===
#define RX_BUFFER_SIZE 1024
#define TX_BUFFER_SIZE 512

// === ПАРАМЕТРЫ ЭКРАНА ===
#define SCREEN_WIDTH 1200
#define SCREEN_HEIGHT 800
#define FPS 60
#define FRAME_TIME_MS (1000 / FPS)


#define MAX_ENEMIES_IN_PACKET 6      
#define MAX_PROJECTILES_IN_PACKET 10
#define MAX_WHIRLPOOLS_IN_PACKET 3   

#define GAME_STATE_SEND_INTERVAL 3

// === ИГРОК ===
#define PLAYER_SIZE 50
#define PLAYER_BASE_SPEED 3.0f
#define PLAYER_MAX_HEALTH 100
#define PLAYER_MAX_ANGLE 45.0f
#define PLAYER_ROTATION_SPEED 1.0f
#define PLAYER_AUTO_RETURN_SPEED 1.5f
#define PLAYER_SIDE_SPEED_MULTIPLIER 3.0f
#define PLAYER_SHOOT_COOLDOWN 30  // frames
#define PLAYER_SHOOT_ANGLE_OFFSET 20.0f  // градусы
#define PLAYER_MIN_ANGLE_FOR_SIDE_SHOT 5.0f
#define PLAYER_COLLISION_DAMAGE 2
#define PLAYER_COLLISION_PUSHBACK 15.0f
#define PLAYER_EDGE_MARGIN 100.0f

// === СНАРЯДЫ ===
#define PROJECTILE_SPEED 4.0f
#define PROJECTILE_LIFETIME 270  // frames (4.5 секунды при 60 FPS)
#define PROJECTILE_RADIUS 5.0f
#define PROJECTILE_DAMAGE_TO_PLAYER 20

// === ВРАГИ - ПРОСТЫЕ ===
#define ENEMY_SIMPLE_SIZE 40
#define ENEMY_SIMPLE_BASE_SPEED 2.2f
#define ENEMY_SIMPLE_HEALTH 1
#define ENEMY_SIMPLE_SHOOT_DELAY 150  // frames
#define ENEMY_SIMPLE_POINTS 100
#define ENEMY_SIMPLE_DETECTION_RANGE 250.0f
#define ENEMY_SIMPLE_AVOIDANCE_FORCE 0.15f
#define ENEMY_SIMPLE_TURN_SMOOTHNESS 0.05f
#define ENEMY_SIMPLE_ATTACK_CHANCE 0.8f  // 80%
#define ENEMY_SIMPLE_PROJECTILE_SPEED 3.5f
#define ENEMY_SIMPLE_TORPEDO_DAMAGE 30
#define ENEMY_SIMPLE_CAN_SEE_RANGE_X 400.0f
#define ENEMY_SIMPLE_CAN_SEE_RANGE_Y 300.0f

// === ВРАГИ - СЛОЖНЫЕ ===
#define ENEMY_HARD_SIZE 60
#define ENEMY_HARD_BASE_SPEED 1.6f
#define ENEMY_HARD_HEALTH 3
#define ENEMY_HARD_SHOOT_DELAY 240  // frames
#define ENEMY_HARD_POINTS 300
#define ENEMY_HARD_DETECTION_RANGE 300.0f
#define ENEMY_HARD_AVOIDANCE_FORCE 0.2f
#define ENEMY_HARD_TURN_SMOOTHNESS 0.03f
#define ENEMY_HARD_AGGRESSIVE_CHANCE 0.7f  // 70%
#define ENEMY_HARD_PURSUIT_TIMER 120  // frames
#define ENEMY_HARD_PROJECTILES_COUNT 3
#define ENEMY_HARD_PROJECTILE_SPEED 2.8f
#define ENEMY_HARD_PROJECTILE_SPREAD 0.15f  // радианы
#define ENEMY_HARD_TORPEDO_DAMAGE 1000
#define ENEMY_HARD_CAN_SEE_RANGE_X 500.0f
#define ENEMY_HARD_CAN_SEE_RANGE_Y 400.0f
#define ENEMY_HARD_ARMOR_FLASH_DURATION 20  // frames
#define ENEMY_HARD_MIN_PATROL_DISTANCE 300.0f
#define ENEMY_HARD_PATROL_POINTS_MAX 4

// === ФИЗИКА ===
#define COLLISION_RADIUS_PLAYER (PLAYER_SIZE / 2.0f)
#define COLLISION_RADIUS_ENEMY_SIMPLE (ENEMY_SIMPLE_SIZE / 2.0f)
#define COLLISION_RADIUS_ENEMY_HARD (ENEMY_HARD_SIZE / 2.0f)

// === АКТИВАЦИЯ И ОЧИСТКА ===
#define ENEMY_ACTIVATION_DISTANCE -2  // экранов от игрока
#define ENEMY_DELETE_DISTANCE 3000.0f  // пикселей позади игрока

// === МАТЕМАТИКА ===
#define PI 3.14159265358979323846f
#define DEG_TO_RAD(deg) ((deg) * PI / 180.0f)
#define RAD_TO_DEG(rad) ((rad) * 180.0f / PI)

// === ЛИМИТЫ МАССИВОВ ===
#define MAX_ENEMIES_SIMPLE 15
#define MAX_ENEMIES_HARD 10
#define MAX_PROJECTILES 50
#define MAX_OBSTACLES 50

// БЕРЕГ
#define SHORE_WIDTH 150
#define SHORE_INDENT_MIN 40
#define SHORE_INDENT_MAX 100
#define SHORE_SEGMENT_HEIGHT_MIN 80
#define SHORE_SEGMENT_HEIGHT_MAX 150
#define SHORE_EDGE_MARGIN 200


// КАМЕРА
#define CAMERA_OFFSET 200



// === ВОДОВОРОТЫ ===
#define WHIRLPOOL_RADIUS 45.0f
#define WHIRLPOOL_ROTATION_SPEED 8.0f
#define WHIRLPOOL_ANIMATION_SPEED 0.1f
#define WHIRLPOOL_PULSE_AMOUNT 5.0f
#define WHIRLPOOL_COOLDOWN 180  // frames (3 секунды)
#define WHIRLPOOL_MIN_DISTANCE 300.0f
#define WHIRLPOOL_TELEPORT_DISTANCE 1200.0f
#define WHIRLPOOL_SPAWN_CHANCE 0.1f
#define WHIRLPOOL_PLAYER_OFFSET -150.0f  // offset от целевого водоворота
#define WHIRLPOOL_EDGE_MARGIN 300.0f
#define WHIRLPOOL_ISLAND_SAFE_DISTANCE 50.0f
#define WHIRLPOOL_MAX_COUNT 6
#define WHIRLPOOL_PLACEMENT_ATTEMPTS 20


#endif // GAME_CONFIG_H

// ===== File: ./Inc\game_state.h =====

/* game_state.h - Управление игровым состоянием (окончательная версия) */

#ifndef GAME_STATE_H
#define GAME_STATE_H

#include "game_config.h"
#include "game_types.h"
#include "input.h"

// Инициализация игрового состояния
void GameState_Init(GameState* state);

// Обновление игрового состояния
void GameState_Update(GameState* state, InputState* input);

// Проверка коллизий в игровом состоянии
void GameState_CheckCollisions(GameState* state);

// Очистка игрового состояния
void GameState_Cleanup(GameState* state);

#endif // GAME_STATE_H

// ===== File: ./Inc\game_state_ext.h =====

/* game_state_ext.h - Расширенное состояние игры с водоворотами */

#ifndef GAME_STATE_EXT_H
#define GAME_STATE_EXT_H

#include "game_types.h"
#include "whirlpool.h"

// Инициализация расширенного состояния игры
void GameState_ExtendedInit(GameState* state);

// Очистка расширенного состояния игры
void GameState_ExtendedCleanup(GameState* state);

#endif // GAME_STATE_EXT_H

// ===== File: ./Inc\game_types.h =====

/* game_types.h - Структуры данных игры (окончательная версия) */

#ifndef GAME_TYPES_H
#define GAME_TYPES_H

#include "game_config.h"
#include <stdint.h>

// === БАЗОВЫЕ ТИПЫ ===

// Вектор 2D
typedef struct {
    float x;
    float y;
} Vector2;

// === ИГРОК ===

typedef struct {
    Vector2 position;
    float hull_angle;           // -45 до 45 градусов
    float base_speed;
    int16_t health;
    int16_t max_health;
    uint16_t shoot_cooldown;
    uint32_t score;
    float radius;
} Player;

// === ВРАГИ ===

// Стратегия AI
typedef enum {
    STRATEGY_PATROL = 0,
    STRATEGY_ATTACK = 1,
    STRATEGY_AGGRESSIVE = 2
} EnemyStrategy;

// Простой враг
typedef struct {
    Vector2 position;
    Vector2 velocity;
    float target_angle;
    float initial_y;
    
    int8_t health;
    int8_t max_health;
    uint16_t shoot_cooldown;
    uint16_t shoot_delay;
    float radius;
    uint16_t points;
    
    uint8_t active;
    uint8_t alive;
    
    // AI параметры
    float wander_angle;
    uint16_t wander_timer;
    EnemyStrategy strategy;
} EnemySimple;

// Сложный враг
typedef struct {
    Vector2 position;
    Vector2 velocity;
    float target_angle;
    float initial_y;
    
    int8_t health;
    int8_t max_health;
    uint16_t shoot_cooldown;
    uint16_t shoot_delay;
    float radius;
    uint16_t points;
    uint16_t armor_timer;
    
    uint8_t active;
    uint8_t alive;
    
    // AI параметры расширенные
    float wander_angle;
    uint16_t wander_timer;
    EnemyStrategy strategy;
    uint16_t pursuit_timer;
    float pursuit_direction;
    
    Vector2 patrol_points[ENEMY_HARD_PATROL_POINTS_MAX];
    uint8_t patrol_point_index;
    uint8_t patrol_points_count;
} EnemyHard;

// === СНАРЯДЫ ===

typedef struct {
    Vector2 position;
    float angle;
    float speed;
    uint16_t lifetime;
    float radius;
    uint8_t is_player_shot;
    uint8_t active;
} Projectile;

// === ПРЕПЯТСТВИЯ ===

typedef enum {
    OBSTACLE_ISLAND = 0,
    OBSTACLE_SHORE_LEFT = 1,
    OBSTACLE_SHORE_RIGHT = 2
} ObstacleType;

typedef struct {
    Vector2 position;
    float radius;
    ObstacleType type;
    uint8_t active;
} Obstacle;

// === ГЛАВНОЕ СОСТОЯНИЕ ИГРЫ ===
// Предварительное объявление структуры менеджера водоворотов
struct WhirlpoolManager;

typedef struct {
    Player player;
    
    EnemySimple enemies_simple[MAX_ENEMIES_SIMPLE];
    EnemyHard enemies_hard[MAX_ENEMIES_HARD];
    uint8_t enemy_simple_count;
    uint8_t enemy_hard_count;
    
    Projectile projectiles[MAX_PROJECTILES];
    uint8_t projectile_count;
    
    Obstacle obstacles[MAX_OBSTACLES];
    uint8_t obstacle_count;
    
    // Указатель на менеджер водоворотов
    struct WhirlpoolManager* whirlpool_manager;
    
    float camera_y;
    float world_top;
    
    uint8_t game_running;
    uint32_t frame_counter;
} GameState;

#endif // GAME_TYPES_H

// ===== File: ./Inc\globals.h =====

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
extern volatile uint16_t rx_write_pos;

#endif // GLOBALS_H

// ===== File: ./Inc\input.h =====

/* input.h - Обработка ввода с кнопок (окончательная версия) */

#ifndef INPUT_H
#define INPUT_H

#include "game_config.h"

#include <stdint.h>

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

// ===== File: ./Inc\main.h =====

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
#include "game_config.h"
#include "game_types.h"
#include "utils.h"
#include "input.h"
#include "protocol.h"
#include "game_state.h"
#include "player.h"
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
#define CANON_LEFT_Pin GPIO_PIN_1
#define CANON_LEFT_GPIO_Port GPIOA
#define CANON_LEFT_EXTI_IRQn EXTI1_IRQn
#define USART_TX_Pin GPIO_PIN_2
#define USART_TX_GPIO_Port GPIOA
#define USART_RX_Pin GPIO_PIN_3
#define USART_RX_GPIO_Port GPIOA
#define CANON_RIGHT_Pin GPIO_PIN_4
#define CANON_RIGHT_GPIO_Port GPIOA
#define CANON_RIGHT_EXTI_IRQn EXTI4_IRQn
#define LED_D12_Pin GPIO_PIN_6
#define LED_D12_GPIO_Port GPIOA
#define LED_D11_Pin GPIO_PIN_7
#define LED_D11_GPIO_Port GPIOA
#define CANON_FIRE_Pin GPIO_PIN_0
#define CANON_FIRE_GPIO_Port GPIOB
#define CANON_FIRE_EXTI_IRQn EXTI0_IRQn
#define CLK_DISP_Pin GPIO_PIN_8
#define CLK_DISP_GPIO_Port GPIOA
#define DATA_DISP_Pin GPIO_PIN_9
#define DATA_DISP_GPIO_Port GPIOA
#define USER_BUZZER_Pin GPIO_PIN_3
#define USER_BUZZER_GPIO_Port GPIOB
#define LATCH_DISP_Pin GPIO_PIN_5
#define LATCH_DISP_GPIO_Port GPIOB
#define LED_D10_Pin GPIO_PIN_6
#define LED_D10_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */


// ===== File: ./Inc\player.h =====

/* player.h - Интерфейс игрока (окончательная версия) */

#ifndef PLAYER_H
#define PLAYER_H

#include "game_config.h"
#include "game_types.h"
#include "input.h"  // ВАЖНО: input.h должен быть включен ДО объявления функций

// Обновление состояния игрока
void Player_Update(Player* player, InputState* input, Obstacle* obstacles, uint8_t obstacle_count);

// Обработка поворота корпуса
void Player_HandleRotation(Player* player, InputState* input);

// Обработка движения и коллизий
void Player_HandleMovement(Player* player, Obstacle* obstacles, uint8_t obstacle_count);

// Проверка коллизий
uint8_t Player_CheckCollisions(Player* player, Obstacle* obstacles, uint8_t obstacle_count);

// Обновление таймера перезарядки
void Player_UpdateCooldown(Player* player);

// Стрельба
void Player_Shoot(GameState* state);

#endif // PLAYER_H

// ===== File: ./Inc\projectiles.h =====

/* projectiles.h - Интерфейс снарядов */

#ifndef PROJECTILES_H
#define PROJECTILES_H

#include "game_types.h"

// Обновление всех снарядов
void Projectiles_Update(GameState* state);

// Удаление снаряда по индексу
void Projectiles_Remove(GameState* state, uint8_t index);

// Проверка столкновения снаряда с препятствием
uint8_t Projectile_CollidesWith(Projectile* proj, Obstacle* obstacle);

#endif // PROJECTILES_H

// ===== File: ./Inc\protocol.h =====

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

// ===== File: ./Inc\utils.h =====

/* utils.h - Математические утилиты */

#ifndef UTILS_H
#define UTILS_H

#include <stdint.h>
#include <math.h>
#include "game_config.h"
#include "globals.h"

// === МАТЕМАТИКА ===

// Ограничение значения
static inline float Utils_Clamp(float value, float min, float max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

// Линейная интерполяция
static inline float Utils_Lerp(float a, float b, float t) {
    return a + (b - a) * t;
}

// Преобразование радианы -> градусы
static inline float Utils_RadToDeg(float rad) {
    return RAD_TO_DEG(rad);
}

// Преобразование градусы -> радианы
static inline float Utils_DegToRad(float deg) {
    return DEG_TO_RAD(deg);
}

// Нормализация угла в диапазон [-PI, PI]
static inline float Utils_NormalizeAngle(float angle) {
    while (angle > PI) angle -= 2.0f * PI;
    while (angle < -PI) angle += 2.0f * PI;
    return angle;
}

// Расстояние между двумя точками
static inline float Utils_Distance(float x1, float y1, float x2, float y2) {
    float dx = x2 - x1;
    float dy = y2 - y1;
    return sqrtf(dx * dx + dy * dy);
}



static inline void Utils_SeedRandom(uint32_t seed) {
    Utils_RandomSeed = seed;
}

static inline uint32_t Utils_Random(void) {
    Utils_RandomSeed = (Utils_RandomSeed * 1103515245 + 12345) & 0x7fffffff;
    return Utils_RandomSeed;
}

static inline int Utils_RandomRange(int min, int max) {
    return min + (Utils_Random() % (max - min + 1));
}

static inline float Utils_RandomFloat(void) {
    return (float)Utils_Random() / (float)0x7fffffff;
}

static inline float Utils_RandomRangeFloat(float min, float max) {
    return min + Utils_RandomFloat() * (max - min);
}

// Абсолютное значение
static inline float Utils_Abs(float value) {
    return (value < 0) ? -value : value;
}

// Минимум/максимум
static inline float Utils_Min(float a, float b) {
    return (a < b) ? a : b;
}

static inline float Utils_Max(float a, float b) {
    return (a > b) ? a : b;
}

#endif // UTILS_H

// ===== File: ./Inc\whirlpool.h =====

/* whirlpool.h - Водовороты с полной логикой на STM32 */

#ifndef WHIRLPOOL_H
#define WHIRLPOOL_H

#include "game_config.h"
#include "game_types.h"
#include "utils.h"

// Водоворот
typedef struct {
    Vector2 position;
    float radius;
    float rotation;
    uint8_t used_recently;
    uint16_t cooldown_timer;
    float animation_phase;
} Whirlpool;

// Полное определение менеджера водоворотов
struct WhirlpoolManager {
    Whirlpool whirlpools[WHIRLPOOL_MAX_COUNT];
    uint8_t whirlpool_count;
};

// Инициализация менеджера водоворотов
void WhirlpoolManager_Init(struct WhirlpoolManager* manager);

// Обновление всех водоворотов и обработка коллизий
void WhirlpoolManager_Update(struct WhirlpoolManager* manager, GameState* state);

// Добавление нового водоворота
uint8_t WhirlpoolManager_Add(struct WhirlpoolManager* manager, float x, float y);

// Очистка старых водоворотов
void WhirlpoolManager_Cleanup(struct WhirlpoolManager* manager, float threshold_y);

// Проверка коллизии водоворота с точкой
uint8_t Whirlpool_CollidesWith(Whirlpool* whirlpool, float x, float y, float radius);

// Поиск подходящего водоворота для телепортации
Whirlpool* WhirlpoolManager_FindTarget(struct WhirlpoolManager* manager, Whirlpool* current, float world_top);

// Создание нового водоворота для телепортации
Whirlpool* WhirlpoolManager_CreateForTeleport(struct WhirlpoolManager* manager, 
                                             Whirlpool* current, 
                                             float world_top,
                                             Obstacle* obstacles,
                                             uint8_t obstacle_count);

// Телепортация игрока
void WhirlpoolManager_TeleportPlayer(struct WhirlpoolManager* manager, 
                                    Whirlpool* source, 
                                    Whirlpool* target, 
                                    Player* player);

#endif // WHIRLPOOL_H

// ===== File: ./Src\cleanup.c =====

/* cleanup.c - Очистка старых объектов (окончательная версия) */

#include "cleanup.h"
#include "enemies.h"
#include "utils.h"

void Enemies_CleanupOld(GameState* state, float threshold_y) {
    // Очистка простых врагов
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
        if (state->enemies_simple[i].position.y > threshold_y) {
            Enemies_RemoveSimple(state, i);
            i--;
        }
    }
    
    // Очистка сложных врагов
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        if (state->enemies_hard[i].position.y > threshold_y) {
            Enemies_RemoveHard(state, i);
            i--;
        }
    }
}

void Obstacles_CleanupOld(GameState* state, float threshold_y) {
    for (uint8_t i = 0; i < state->obstacle_count; i++) {
        if (state->obstacles[i].position.y > threshold_y) {
            Obstacles_Remove(state, i);
            i--;
        }
    }
}

void Obstacles_Remove(GameState* state, uint8_t index) {
    if (index < state->obstacle_count - 1) {
        state->obstacles[index] = state->obstacles[state->obstacle_count - 1];
    }
    state->obstacle_count--;
}

// ===== File: ./Src\collisions.c =====

/* collisions.c - Проверка коллизий (окончательная версия) */

#include "collisions.h"
#include "projectiles.h"
#include "enemies.h"
#include "utils.h"
#include <string.h>

void Projectiles_CheckCollisions(GameState* state) {
    for (uint8_t i = 0; i < state->projectile_count; i++) {
        Projectile* proj = &state->projectiles[i];
        
        if (!proj->active) continue;
        
        // Проверка столкновения с препятствиями
        uint8_t obstacle_hit = 0;
        
        // Проверка столкновения с врагами (если снаряд игрока)
        if (proj->is_player_shot) {
            for (uint8_t j = 0; j < state->enemy_simple_count; j++) {
                EnemySimple* enemy = &state->enemies_simple[j];
                
                if (!enemy->alive || !enemy->active) continue;
                
                float dx = proj->position.x - enemy->position.x;
                float dy = proj->position.y - enemy->position.y;
                float dist = Utils_Distance(0, 0, dx, dy);
                
                if (dist < proj->radius + enemy->radius) {
                    // Наносим урон врагу
                    enemy->health--;
                    
                    // Если враг убит
                    if (enemy->health <= 0) {
                        state->player.score += enemy->points;
                        Enemies_RemoveSimple(state, j);
                    }
                    
                    // Удаляем снаряд
                    Projectiles_Remove(state, i);
                    i--;
                    break;
                }
            }
            
            if (i >= state->projectile_count) continue;
            
            for (uint8_t j = 0; j < state->enemy_hard_count; j++) {
                EnemyHard* enemy = &state->enemies_hard[j];
                
                if (!enemy->alive || !enemy->active) continue;
                
                float dx = proj->position.x - enemy->position.x;
                float dy = proj->position.y - enemy->position.y;
                float dist = Utils_Distance(0, 0, dx, dy);
                
                if (dist < proj->radius + enemy->radius) {
                    // Наносим урон врагу
                    enemy->health--;
                    enemy->armor_timer = ENEMY_HARD_ARMOR_FLASH_DURATION;
                    
                    // Если враг убит
                    if (enemy->health <= 0) {
                        state->player.score += enemy->points;
                        Enemies_RemoveHard(state, j);
                    }
                    
                    // Удаляем снаряд
                    Projectiles_Remove(state, i);
                    i--;
                    break;
                }
            }
        }
        // Проверка столкновения вражеских снарядов с игроком
        else {
            float dx = proj->position.x - state->player.position.x;
            float dy = proj->position.y - state->player.position.y;
            float dist = Utils_Distance(0, 0, dx, dy);
            
            if (dist < proj->radius + state->player.radius) {
                state->player.health -= PROJECTILE_DAMAGE_TO_PLAYER;
                Projectiles_Remove(state, i);
                i--;
            }
        }
        
        // Проверка столкновения с препятствиями
        if (i < state->projectile_count) {
            for (uint8_t j = 0; j < state->obstacle_count; j++) {
                if (!state->obstacles[j].active) continue;
                
                if (Projectile_CollidesWith(proj, &state->obstacles[j])) {
                    obstacle_hit = 1;
                    break;
                }
            }
            
            // Удаление снаряда при столкновении с препятствием
            if (obstacle_hit) {
                Projectiles_Remove(state, i);
                i--;
            }
        }
        
        // Проверка на истечение срока жизни или выход за границы экрана
        if (i < state->projectile_count && (proj->lifetime <= 0 || 
            proj->position.x < 0 || 
            proj->position.x > SCREEN_WIDTH ||
            proj->position.y < state->camera_y - 200 || 
            proj->position.y > state->camera_y + SCREEN_HEIGHT + 200)) {
            Projectiles_Remove(state, i);
            i--;
        }
    }
}

void GameState_CheckCollisions(GameState* state) {
    // Проверка столкновений игрока с врагами
    Player_CheckEnemyCollisions(state);
    
    // Проверка столкновений снарядов
    Projectiles_CheckCollisions(state);
}

void Player_CheckEnemyCollisions(GameState* state) {
    // Проверка столкновений с простыми врагами
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
        EnemySimple* enemy = &state->enemies_simple[i];
        
        if (!enemy->alive || !enemy->active) continue;
        
        float dx = state->player.position.x - enemy->position.x;
        float dy = state->player.position.y - enemy->position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < state->player.radius + enemy->radius) {
            // Наносим урон игроку
            state->player.health -= ENEMY_SIMPLE_TORPEDO_DAMAGE;
            
            // Удаляем врага
            Enemies_RemoveSimple(state, i);
            i--;
        }
    }
    
    // Проверка столкновений со сложными врагами
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        EnemyHard* enemy = &state->enemies_hard[i];
        
        if (!enemy->alive || !enemy->active) continue;
        
        float dx = state->player.position.x - enemy->position.x;
        float dy = state->player.position.y - enemy->position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < state->player.radius + enemy->radius) {
            // Наносим урон игроку
            state->player.health -= ENEMY_HARD_TORPEDO_DAMAGE;
            
            // Удаляем врага
            Enemies_RemoveHard(state, i);
            i--;
        }
    }
}



uint8_t Projectile_CollidesWith(Projectile* proj, Obstacle* obstacle) {
    float dx = proj->position.x - obstacle->position.x;
    float dy = proj->position.y - obstacle->position.y;
    float dist = Utils_Distance(0, 0, dx, dy);
    
    return (dist < proj->radius + obstacle->radius);
}

// ===== File: ./Src\enemies.c =====

/* enemies.c - Логика врагов */

#include "game_config.h"
#include "enemies.h"
#include "utils.h"
#include <math.h>

void Enemies_Update(GameState* state) {
    // Обновление простых врагов
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
        EnemySimple* enemy = &state->enemies_simple[i];
        
        if (!enemy->alive || !enemy->active) continue;
        
        // Активация врага при приближении к игроку
        if (!enemy->active && enemy->position.y > state->player.position.y + ENEMY_ACTIVATION_DISTANCE * SCREEN_HEIGHT) {
            enemy->active = 1;
            enemy->strategy = (Utils_RandomFloat() < ENEMY_SIMPLE_ATTACK_CHANCE) ? STRATEGY_ATTACK : STRATEGY_PATROL;
        }
        
        // Удаление врага, если он слишком далеко позади игрока
        if (enemy->position.y > state->player.position.y + ENEMY_DELETE_DISTANCE) {
            Enemies_RemoveSimple(state, i);
            i--;
            continue;
        }
        
        // Обновление AI
        EnemySimple_UpdateAI(enemy, &state->player);
        
        // Применение движения
        float angle_diff = enemy->target_angle - atan2f(enemy->velocity.y, enemy->velocity.x);
        angle_diff = Utils_NormalizeAngle(angle_diff);
        float turn_amount = angle_diff * ENEMY_SIMPLE_TURN_SMOOTHNESS;
        
        enemy->velocity.x = cosf(enemy->target_angle + turn_amount) * ENEMY_SIMPLE_BASE_SPEED;
        enemy->velocity.y = sinf(enemy->target_angle + turn_amount) * ENEMY_SIMPLE_BASE_SPEED;
        
        float prev_x = enemy->position.x;
        float prev_y = enemy->position.y;
        
        enemy->position.x += enemy->velocity.x;
        enemy->position.y += enemy->velocity.y;
        
        // Проверка коллизий с препятствиями
        if (Enemies_CheckCollision(state, enemy->position.x, enemy->position.y, enemy->radius)) {
            enemy->position.x = prev_x;
            enemy->position.y = prev_y;
            enemy->target_angle += Utils_DegToRad(Utils_RandomRange(90, 270));
        }
        
        // Ограничение по краям
        if (enemy->position.x < SHORE_EDGE_MARGIN - 80) {
            enemy->position.x = SHORE_EDGE_MARGIN - 80;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(30, 150));
        }
        else if (enemy->position.x > SCREEN_WIDTH - SHORE_EDGE_MARGIN + 80) {
            enemy->position.x = SCREEN_WIDTH - SHORE_EDGE_MARGIN + 80;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(210, 330));
        }
        
        // Обновление таймеров
        if (enemy->wander_timer > 0) {
            enemy->wander_timer--;
        }
        
        if (enemy->shoot_cooldown > 0) {
            enemy->shoot_cooldown--;
        }
        
        // Стрельба
        if (enemy->shoot_cooldown == 0 && Enemies_CanSeePlayer(enemy, &state->player)) {
            Enemies_ShootAtPlayer(state, enemy);
        }
    }
    
    // Обновление сложных врагов (аналогично, но с более сложной логикой)
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        EnemyHard* enemy = &state->enemies_hard[i];
        
        if (!enemy->alive || !enemy->active) continue;
        
        // Активация врага
        if (!enemy->active && enemy->position.y > state->player.position.y + ENEMY_ACTIVATION_DISTANCE * SCREEN_HEIGHT) {
            enemy->active = 1;
            enemy->strategy = (Utils_RandomFloat() < ENEMY_HARD_AGGRESSIVE_CHANCE) ? STRATEGY_AGGRESSIVE : STRATEGY_PATROL;
            
            if (enemy->strategy == STRATEGY_PATROL) {
                Enemies_GeneratePatrolPoints(enemy, &state->player);
            }
        }
        
        // Удаление врага
        if (enemy->position.y > state->player.position.y + ENEMY_DELETE_DISTANCE) {
            Enemies_RemoveHard(state, i);
            i--;
            continue;
        }
        
        // Обновление AI
        EnemyHard_UpdateAI(enemy, &state->player, state->obstacles, state->obstacle_count);
        
        // Применение движения
        float prev_x = enemy->position.x;
        float prev_y = enemy->position.y;
        
        enemy->position.x += cosf(enemy->target_angle) * ENEMY_HARD_BASE_SPEED;
        enemy->position.y += sinf(enemy->target_angle) * ENEMY_HARD_BASE_SPEED;
        
        // Проверка коллизий
        if (Enemies_CheckCollision(state, enemy->position.x, enemy->position.y, enemy->radius)) {
            enemy->position.x = prev_x;
            enemy->position.y = prev_y;
            enemy->target_angle += Utils_DegToRad(Utils_RandomRange(90, 270));
        }
        
        // Ограничение по краям
        if (enemy->position.x < SHORE_WIDTH) {
            enemy->position.x = SHORE_WIDTH;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(30, 150));
        }
        else if (enemy->position.x > SCREEN_WIDTH - SHORE_WIDTH) {
            enemy->position.x = SCREEN_WIDTH - SHORE_WIDTH;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(210, 330));
        }
        
        // Обновление таймеров
        if (enemy->armor_timer > 0) {
            enemy->armor_timer--;
        }
        
        if (enemy->shoot_cooldown > 0) {
            enemy->shoot_cooldown--;
        }
        
        // Стрельба
        if (enemy->shoot_cooldown == 0 && Enemies_CanSeePlayerHard(enemy, &state->player)) {
            Enemies_ShootHardAtPlayer(state, enemy);
        }
    }
}

void EnemySimple_UpdateAI(EnemySimple* enemy, Player* player) {
    // Проверка видимости игрока
    uint8_t can_see_player = Enemies_CanSeePlayer(enemy, player);
    
    if (enemy->strategy == STRATEGY_ATTACK && can_see_player) {
        // Целевой угол - направление к игроку
        enemy->target_angle = atan2f(player->position.y - enemy->position.y, 
                                   player->position.x - enemy->position.x);
    }
    else {
        // Патрулирование
        enemy->wander_timer--;
        if (enemy->wander_timer == 0) {
            enemy->wander_timer = Utils_RandomRange(90, 180);
            enemy->wander_angle = Utils_RandomRangeFloat(-PI/6, PI/6);
        }
        
        enemy->target_angle = Utils_DegToRad(90) + enemy->wander_angle;
    }
}

void EnemyHard_UpdateAI(EnemyHard* enemy, Player* player, Obstacle* obstacles, uint8_t obstacle_count) {
    // Проверка видимости игрока
    uint8_t can_see_player = Enemies_CanSeePlayerHard(enemy, player);
    
    if (enemy->strategy == STRATEGY_AGGRESSIVE) {
        if (can_see_player) {
            // Предсказание движения игрока
            float predict_x = player->position.x + (player->hull_angle / 45) * 50;
            float predict_y = player->position.y - 50;
            
            enemy->target_angle = atan2f(predict_y - enemy->position.y, 
                                       predict_x - enemy->position.x);
            enemy->pursuit_timer = ENEMY_HARD_PURSUIT_TIMER;
            enemy->pursuit_direction = enemy->target_angle;
        }
        else if (enemy->pursuit_timer > 0) {
            enemy->pursuit_timer--;
            enemy->target_angle = enemy->pursuit_direction;
        }
        else {
            // Блуждание
            enemy->wander_timer--;
            if (enemy->wander_timer <= 0) {
                enemy->wander_timer = Utils_RandomRange(180, 300);
                enemy->wander_angle += Utils_RandomRangeFloat(-0.05f, 0.05f);
                enemy->wander_angle = Utils_Clamp(enemy->wander_angle, -PI/6, PI/6);
            }
            enemy->target_angle = Utils_DegToRad(90) + enemy->wander_angle;
        }
    }
    else { // STRATEGY_PATROL
        if (enemy->patrol_point_index >= enemy->patrol_points_count) {
            Enemies_GeneratePatrolPoints(enemy, player);
        }
        
        if (enemy->patrol_points_count > 0) {
            Vector2* target = &enemy->patrol_points[enemy->patrol_point_index];
            float dx = target->x - enemy->position.x;
            float dy = target->y - enemy->position.y;
            float distance = Utils_Distance(0, 0, dx, dy);
            
            if (distance < ENEMY_HARD_MIN_PATROL_DISTANCE) {
                enemy->patrol_point_index++;
                if (enemy->patrol_point_index >= enemy->patrol_points_count) {
                    Enemies_GeneratePatrolPoints(enemy, player);
                }
            }
            
            if (enemy->patrol_point_index < enemy->patrol_points_count) {
                target = &enemy->patrol_points[enemy->patrol_point_index];
                dx = target->x - enemy->position.x;
                dy = target->y - enemy->position.y;
                enemy->target_angle = atan2f(dy, dx);
            }
        }
    }
}

void Enemies_GeneratePatrolPoints(EnemyHard* enemy, Player* player) {
    enemy->patrol_point_index = 0;
    enemy->patrol_points_count = 0;
    
    float start_x = enemy->position.x;
    float start_y = enemy->position.y + 200;
    
    uint8_t num_points = Utils_RandomRange(2, 4);
    
    for (uint8_t i = 0; i < num_points && i < ENEMY_HARD_PATROL_POINTS_MAX; i++) {
        float y_offset = Utils_RandomRange(400, 800);
        float x_offset = Utils_RandomRangeFloat(-300, 300);
        
        float x = Utils_Clamp(start_x + x_offset, 300, SCREEN_WIDTH - 300);
        float y = start_y + y_offset;
        
        // Избегаем близости к игроку
        float dx = x - player->position.x;
        float dy = y - player->position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < 300) {
            if (dist > 0) {
                x += (dx / dist) * 300;
                y += (dy / dist) * 300;
            }
        }
        
        enemy->patrol_points[i].x = x;
        enemy->patrol_points[i].y = y;
        
        start_x = x;
        start_y = y;
        enemy->patrol_points_count++;
    }
    
    // Добавляем финальную точку
    if (enemy->patrol_points_count < ENEMY_HARD_PATROL_POINTS_MAX) {
        float final_x = Utils_RandomRange(300, SCREEN_WIDTH - 300);
        float final_y = start_y + Utils_RandomRange(400, 800);
        
        enemy->patrol_points[enemy->patrol_points_count].x = final_x;
        enemy->patrol_points[enemy->patrol_points_count].y = final_y;
        enemy->patrol_points_count++;
    }
}

uint8_t Enemies_CanSeePlayer(EnemySimple* enemy, Player* player) {
    float dx = fabsf(enemy->position.x - player->position.x);
    float dy = fabsf(enemy->position.y - player->position.y);
    
    return (dx < ENEMY_SIMPLE_CAN_SEE_RANGE_X && dy < ENEMY_SIMPLE_CAN_SEE_RANGE_Y);
}

uint8_t Enemies_CanSeePlayerHard(EnemyHard* enemy, Player* player) {
    float dx = fabsf(enemy->position.x - player->position.x);
    float dy = fabsf(enemy->position.y - player->position.y);
    
    return (dx < ENEMY_HARD_CAN_SEE_RANGE_X && dy < ENEMY_HARD_CAN_SEE_RANGE_Y);
}

void Enemies_ShootAtPlayer(GameState* state, EnemySimple* enemy) {
    enemy->shoot_cooldown = enemy->shoot_delay;
    
    // Создание снаряда
    if (state->projectile_count < MAX_PROJECTILES) {
        float dx = state->player.position.x - enemy->position.x;
        float dy = state->player.position.y - enemy->position.y;
        float angle = atan2f(dy, dx);
        
        Projectile* proj = &state->projectiles[state->projectile_count];
        proj->position.x = enemy->position.x;
        proj->position.y = enemy->position.y;
        proj->angle = angle;
        proj->speed = ENEMY_SIMPLE_PROJECTILE_SPEED;
        proj->lifetime = PROJECTILE_LIFETIME;
        proj->radius = PROJECTILE_RADIUS;
        proj->is_player_shot = 0;
        proj->active = 1;
        
        state->projectile_count++;
    }
}

void Enemies_ShootHardAtPlayer(GameState* state, EnemyHard* enemy) {
    enemy->shoot_cooldown = enemy->shoot_delay;
    
    float base_angle = atan2f(state->player.position.y - enemy->position.y, 
                             state->player.position.x - enemy->position.x);
    
    // Создание трех снарядов (веер)
    for (int i = -1; i <= 1; i++) {
        if (state->projectile_count >= MAX_PROJECTILES) break;
        
        float angle = base_angle + i * ENEMY_HARD_PROJECTILE_SPREAD;
        
        Projectile* proj = &state->projectiles[state->projectile_count];
        proj->position.x = enemy->position.x;
        proj->position.y = enemy->position.y;
        proj->angle = angle;
        proj->speed = ENEMY_HARD_PROJECTILE_SPEED;
        proj->lifetime = PROJECTILE_LIFETIME;
        proj->radius = PROJECTILE_RADIUS;
        proj->is_player_shot = 0;
        proj->active = 1;
        
        state->projectile_count++;
    }
}

uint8_t Enemies_CheckCollision(GameState* state, float x, float y, float radius) {
    for (uint8_t i = 0; i < state->obstacle_count; i++) {
        if (!state->obstacles[i].active) continue;
        
        float dx = x - state->obstacles[i].position.x;
        float dy = y - state->obstacles[i].position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < radius + state->obstacles[i].radius) {
            return 1;
        }
    }
    return 0;
}

void Enemies_RemoveSimple(GameState* state, uint8_t index) {
    if (index < state->enemy_simple_count - 1) {
        state->enemies_simple[index] = state->enemies_simple[state->enemy_simple_count - 1];
    }
    state->enemy_simple_count--;
}

void Enemies_RemoveHard(GameState* state, uint8_t index) {
    if (index < state->enemy_hard_count - 1) {
        state->enemies_hard[index] = state->enemies_hard[state->enemy_hard_count - 1];
    }
    state->enemy_hard_count--;
}

// ===== File: ./Src\game_state.c =====

/* game_state.c - Инициализация и обновление игрового состояния (окончательная версия) */

#include "game_config.h"
#include "game_types.h"
#include "input.h"
#include "utils.h"
#include "globals.h"
#include "game_state.h"
#include "player.h"
#include "enemies.h"
#include "projectiles.h"
#include "collisions.h"
#include "whirlpool.h"
#include <string.h>
#include <stdlib.h>

void GameState_Init(GameState* state) {
    // Инициализация игрока
    state->player.position.x = SCREEN_WIDTH / 2.0f;
    state->player.position.y = SCREEN_HEIGHT - 150.0f;
    state->player.hull_angle = 0.0f;
    state->player.base_speed = PLAYER_BASE_SPEED;
    state->player.health = PLAYER_MAX_HEALTH;
    state->player.max_health = PLAYER_MAX_HEALTH;
    state->player.shoot_cooldown = 0;
    state->player.score = 0;
    state->player.radius = COLLISION_RADIUS_PLAYER;
    
    // Инициализация врагов (простые)
    memset(state->enemies_simple, 0, sizeof(state->enemies_simple));
    state->enemy_simple_count = 0;
    
    // Инициализация врагов (сложные)
    memset(state->enemies_hard, 0, sizeof(state->enemies_hard));
    state->enemy_hard_count = 0;
    
    // Инициализация снарядов
    memset(state->projectiles, 0, sizeof(state->projectiles));
    state->projectile_count = 0;
    
    // Инициализация препятствий
    memset(state->obstacles, 0, sizeof(state->obstacles));
    state->obstacle_count = 0;
    
    // Выделяем память для менеджера водоворотов
    state->whirlpool_manager = (struct WhirlpoolManager*)malloc(sizeof(struct WhirlpoolManager));
    if (state->whirlpool_manager) {
        WhirlpoolManager_Init(state->whirlpool_manager);
    }
    
    // Инициализация камеры
    state->camera_y = state->player.position.y - SCREEN_HEIGHT + CAMERA_OFFSET;
    
    // Инициализация мира
    state->world_top = state->player.position.y - SCREEN_HEIGHT * 2.0f;
    
    // Игра запущена
    state->game_running = 1;
    state->frame_counter = 0;
}

void GameState_Update(GameState* state, InputState* input) {
    // Обновление игрока
    Player_Update(&state->player, input, state->obstacles, state->obstacle_count);
    
    // Обновление врагов
    Enemies_Update(state);
    
    // Обновление снарядов
    Projectiles_Update(state);
    
    // Обновление водоворотов
    if (state->whirlpool_manager) {
        WhirlpoolManager_Update(state->whirlpool_manager, state);
    }
    
    // Проверка коллизий
    GameState_CheckCollisions(state);
    
    // Обновление камеры
    state->camera_y = state->player.position.y - SCREEN_HEIGHT + CAMERA_OFFSET;
    
    // Проверка окончания игры
    if (state->player.health <= 0) {
        state->game_running = 0;
    }
}

void GameState_Cleanup(GameState* state) {
    // Освобождаем память менеджера водоворотов
    if (state->whirlpool_manager) {
        free(state->whirlpool_manager);
        state->whirlpool_manager = NULL;
    }
}

// ===== File: ./Src\game_state_ext.c =====

/* game_state_ext.c - Реализация расширенного состояния игры */

#include "game_state_ext.h"
#include <stdlib.h>

void GameState_ExtendedInit(GameState* state) {
    // Выделяем память для менеджера водоворотов
    state->whirlpool_manager = (WhirlpoolManager*)malloc(sizeof(WhirlpoolManager));
    if (state->whirlpool_manager) {
        WhirlpoolManager_Init(state->whirlpool_manager);
    }
}

void GameState_ExtendedCleanup(GameState* state) {
    // Освобождаем память менеджера водоворотов
    if (state->whirlpool_manager) {
        free(state->whirlpool_manager);
        state->whirlpool_manager = NULL;
    }
}

// ===== File: ./Src\globals.c =====

/* globals.c - Глобальные переменные проекта */

#include "globals.h"

// Глобальная переменная для генератора случайных чисел
uint32_t Utils_RandomSeed = 0;

// // Переменные для протокола
// uint8_t rx_buffer[RX_BUFFER_SIZE];
// uint8_t tx_buffer[TX_BUFFER_SIZE];
// volatile uint8_t uart_tx_busy = 0;
// volatile uint16_t rx_write_pos = 0;

// ===== File: ./Src\input.c =====

/* input.c - Реализация ввода */

#include "input.h"
#include "main.h"

void Input_Init(void) {
    
}

void Input_Update(InputState* input) {
    input->left_prev = input->left_pressed;
    input->right_prev = input->right_pressed;
    input->shoot_prev = input->shoot_pressed;
    
    // Инвертируем логику: 0 = нажата, 1 = отпущена
    input->left_pressed = !HAL_GPIO_ReadPin(CANON_LEFT_GPIO_Port, CANON_LEFT_Pin);
    input->right_pressed = !HAL_GPIO_ReadPin(CANON_RIGHT_GPIO_Port, CANON_RIGHT_Pin);
    input->shoot_pressed = !HAL_GPIO_ReadPin(CANON_FIRE_GPIO_Port, CANON_FIRE_Pin);
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

// ===== File: ./Src\main.c =====

/* main.c - Endless Sea Battle Ship - STM32 Main Loop */

#include "main.h"
#include <string.h>

/* Private variables */
UART_HandleTypeDef huart2;
DMA_HandleTypeDef hdma_usart2_rx;
DMA_HandleTypeDef hdma_usart2_tx;

GameState game;
InputState input;

/* Private function prototypes */
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_USART2_UART_Init(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    /* Initialize peripherals */
    MX_GPIO_Init();
    MX_DMA_Init();
    MX_USART2_UART_Init();

    /* Initialize game systems */
    Utils_SeedRandom(HAL_GetTick());
    Input_Init();
    Protocol_Init(&huart2);
    GameState_Init(&game);
    
    uint32_t last_tick = HAL_GetTick();
    
    while (1)
    {
        uint32_t current_tick = HAL_GetTick();
        
        if (current_tick - last_tick >= FRAME_TIME_MS) {
            last_tick = current_tick;
            
            // 1. Process incoming packets from PC
            Protocol_ProcessIncoming(&game);
            
            // 2. Update button states
            Input_Update(&input);
            
            // 3. Handle shooting
            if (Input_JustPressed(&input, BTN_SHOOT)) {
                Player_Shoot(&game);
            }
            
            // 4. Update game state if running
            if (game.game_running) {
                GameState_Update(&game, &input);
            }
            
            // 5. Send game state to PC (с ограничением частоты)
            if (game.frame_counter % 3 == 0) {
                Protocol_SendGameState(&game);
            }
            
            game.frame_counter++;
        }
        
        // Периодическая очистка буфера
        if (game.frame_counter % 60 == 0) {
            Protocol_CleanupRxBuffer();
        }
    }
}

/* UART Callbacks */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2) {
        uart_tx_busy = 0;
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2) {
        uart_tx_busy = 0;
        // Перезапуск приёма DMA
        HAL_UART_Receive_DMA(&huart2, rx_buffer, RX_BUFFER_SIZE);
    }
}


/* System Clock Configuration */
void SystemClock_Config(void)
{
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    RCC_OscInitStruct.HSIState = RCC_HSI_ON;
    RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
    RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI_DIV2;
    RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL16;
    HAL_RCC_OscConfig(&RCC_OscInitStruct);

    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                                |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
    HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2);
}

/* USART2 Initialization */
static void MX_USART2_UART_Init(void)
{
    huart2.Instance = USART2;
    huart2.Init.BaudRate = 115200;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart2);
}

/* DMA Initialization */
static void MX_DMA_Init(void)
{
    __HAL_RCC_DMA1_CLK_ENABLE();

    HAL_NVIC_SetPriority(DMA1_Channel6_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel6_IRQn);
    
    HAL_NVIC_SetPriority(DMA1_Channel7_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel7_IRQn);
}

/* GPIO Initialization */
static void MX_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* Configure button pins */
    GPIO_InitStruct.Pin = CANON_LEFT_Pin|CANON_RIGHT_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = CANON_FIRE_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT; 
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(CANON_FIRE_GPIO_Port, &GPIO_InitStruct);

    /* EXTI interrupts */
    HAL_NVIC_SetPriority(EXTI0_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);

    HAL_NVIC_SetPriority(EXTI1_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(EXTI1_IRQn);

    HAL_NVIC_SetPriority(EXTI4_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(EXTI4_IRQn);
}

void Error_Handler(void)
{
    __disable_irq();
    while (1)
    {
        GameState_Cleanup(&game);
    }
}

// ===== File: ./Src\player.c =====

/* player.c - Логика игрока (окончательная версия) */

#include "player.h"
#include "utils.h"
#include <math.h>

void Player_Update(Player* player, InputState* input, Obstacle* obstacles, uint8_t obstacle_count) {
    // Обработка поворота корпуса
    Player_HandleRotation(player, input);
    
    // Обработка движения и коллизий
    Player_HandleMovement(player, obstacles, obstacle_count);
    
    // Обновление таймера перезарядки
    Player_UpdateCooldown(player);
}

void Player_HandleRotation(Player* player, InputState* input) {
    if (Input_IsPressed(input, BTN_LEFT) && player->hull_angle > -PLAYER_MAX_ANGLE) {
        player->hull_angle -= PLAYER_ROTATION_SPEED;
    } 
    else if (Input_IsPressed(input, BTN_RIGHT) && player->hull_angle < PLAYER_MAX_ANGLE) {
        player->hull_angle += PLAYER_ROTATION_SPEED;
    }
    else {
        // Автовозврат к прямому курсу
        if (Utils_Abs(player->hull_angle) < PLAYER_AUTO_RETURN_SPEED) {
            player->hull_angle = 0.0f;
        }
        else if (player->hull_angle > 0) {
            player->hull_angle -= PLAYER_AUTO_RETURN_SPEED;
        }
        else {
            player->hull_angle += PLAYER_AUTO_RETURN_SPEED;
        }
    }
    
    // Ограничение угла
    player->hull_angle = Utils_Clamp(player->hull_angle, -PLAYER_MAX_ANGLE, PLAYER_MAX_ANGLE);
}

void Player_HandleMovement(Player* player, Obstacle* obstacles, uint8_t obstacle_count) {
    float old_x = player->position.x;
    float old_y = player->position.y;
    
    // Движение вперёд и боковое смещение
    player->position.y -= player->base_speed;
    float side_speed = (player->hull_angle / PLAYER_MAX_ANGLE) * PLAYER_SIDE_SPEED_MULTIPLIER;
    player->position.x += side_speed;
    
    // Ограничение краёв экрана
    player->position.x = Utils_Clamp(player->position.x, PLAYER_EDGE_MARGIN, SCREEN_WIDTH - PLAYER_EDGE_MARGIN);
    
    // Проверка коллизий
    if (Player_CheckCollisions(player, obstacles, obstacle_count)) {
        // Обработка столкновения
        player->health -= PLAYER_COLLISION_DAMAGE;
        player->position.x = old_x;
        player->position.y = old_y;
        player->position.y += PLAYER_COLLISION_PUSHBACK;
    }
}

uint8_t Player_CheckCollisions(Player* player, Obstacle* obstacles, uint8_t obstacle_count) {
    for (uint8_t i = 0; i < obstacle_count; i++) {
        if (!obstacles[i].active) continue;
        
        float dx = player->position.x - obstacles[i].position.x;
        float dy = player->position.y - obstacles[i].position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < player->radius + obstacles[i].radius) {
            return 1;
        }
    }
    return 0;
}

void Player_UpdateCooldown(Player* player) {
    if (player->shoot_cooldown > 0) {
        player->shoot_cooldown--;
    }
}

void Player_Shoot(GameState* state) {
    if (state->player.shoot_cooldown > 0) {
        return;
    }
    
    state->player.shoot_cooldown = PLAYER_SHOOT_COOLDOWN;
    
    // Базовый угол - вверх
    float angle = Utils_DegToRad(-90.0f);
    
    // Корректировка угла в зависимости от поворота
    if (state->player.hull_angle > PLAYER_MIN_ANGLE_FOR_SIDE_SHOT) {
        angle += Utils_DegToRad(PLAYER_SHOOT_ANGLE_OFFSET);
    }
    else if (state->player.hull_angle < -PLAYER_MIN_ANGLE_FOR_SIDE_SHOT) {
        angle -= Utils_DegToRad(PLAYER_SHOOT_ANGLE_OFFSET);
    }
    
    // Добавление снаряда
    if (state->projectile_count < MAX_PROJECTILES) {
        Projectile* proj = &state->projectiles[state->projectile_count];
        proj->position.x = state->player.position.x;
        proj->position.y = state->player.position.y;
        proj->angle = angle;
        proj->speed = PROJECTILE_SPEED;
        proj->lifetime = PROJECTILE_LIFETIME;
        proj->radius = PROJECTILE_RADIUS;
        proj->is_player_shot = 1;
        proj->active = 1;
        
        state->projectile_count++;
    }
}

// ===== File: ./Src\projectiles.c =====

/* projectiles.c - Логика снарядов (окончательная версия) */

#include "projectiles.h"
#include "utils.h"
#include <math.h>

void Projectiles_Update(GameState* state) {
    // Обновление существующих снарядов
    for (uint8_t i = 0; i < state->projectile_count; i++) {
        Projectile* proj = &state->projectiles[i];
        
        if (!proj->active) continue;
        
        // Обновление позиции
        proj->position.x += cosf(proj->angle) * proj->speed;
        proj->position.y += sinf(proj->angle) * proj->speed;
        proj->lifetime--;
    }
}

void Projectiles_Remove(GameState* state, uint8_t index) {
    if (index < state->projectile_count - 1) {
        // Перемещаем последний снаряд на место удаляемого
        state->projectiles[index] = state->projectiles[state->projectile_count - 1];
    }
    state->projectile_count--;
}

// ===== File: ./Src\protocol.c =====

/* protocol.c - Надежная реализация протокола */

#include "protocol.h"
#include "cleanup.h"
#include "whirlpool.h"
#include <string.h>

static UART_HandleTypeDef* huart_handle = NULL;

// Глобальные переменные (уже объявлены в globals.h)
volatile uint8_t uart_tx_busy = 0;
uint8_t tx_buffer[TX_BUFFER_SIZE];
uint8_t rx_buffer[RX_BUFFER_SIZE];
volatile uint16_t rx_write_pos = 0;

// Состояние парсинга входящих данных
static uint8_t packet_state = 0;
static uint8_t packet_type = 0;
static uint8_t packet_data[512];
static uint16_t packet_idx = 0;

uint8_t Protocol_CalculateCRC(uint8_t* data, uint16_t len) {
    uint8_t crc = 0;
    for (uint16_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x80)
                crc = (crc << 1) ^ 0x07;
            else
                crc <<= 1;
        }
    }
    return crc;
}

void Protocol_Init(UART_HandleTypeDef* huart) {
    huart_handle = huart;
    
    // Инициализируем состояние парсинга
    packet_state = 0;
    packet_type = 0;
    packet_idx = 0;
    
    // Запускаем приём DMA в циклическом режиме
    HAL_UART_Receive_DMA(huart, rx_buffer, RX_BUFFER_SIZE);
}

void Protocol_SendGameState(GameState* state) {
    if (uart_tx_busy || huart_handle == NULL) {
        return;
    }
    
    // Формируем пакет
    uint16_t idx = 0;
    tx_buffer[idx++] = START_BYTE;
    tx_buffer[idx++] = PKT_GAME_STATE;
    
    // Данные игрока
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.x + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.x + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.x + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.x + 3);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.y + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.y + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.y + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.y + 3);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.hull_angle + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.hull_angle + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->player.hull_angle + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->player.hull_angle + 3);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.health + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.health + 1);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.score + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.score + 1);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.shoot_cooldown + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.shoot_cooldown + 1);
    
    // Сохраняем позицию для счетчика врагов
    uint16_t enemy_count_pos = idx++;
    
    // Враги
    uint8_t enemy_count = 0;
    for (uint8_t i = 0; i < state->enemy_simple_count && enemy_count < MAX_ENEMIES_IN_PACKET; i++) {
        if (state->enemies_simple[i].alive && state->enemies_simple[i].active) {
            tx_buffer[idx++] = 0;  // тип: простой враг
            
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.x + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.x + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.x + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.x + 3);
            
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.y + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.y + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.y + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.y + 3);
            
            tx_buffer[idx++] = state->enemies_simple[i].health;
            
            enemy_count++;
        }
    }
    
    for (uint8_t i = 0; i < state->enemy_hard_count && enemy_count < MAX_ENEMIES_IN_PACKET; i++) {
        if (state->enemies_hard[i].alive && state->enemies_hard[i].active) {
            tx_buffer[idx++] = 1;  // тип: сложный враг
            
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.x + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.x + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.x + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.x + 3);
            
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.y + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.y + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.y + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.y + 3);
            
            tx_buffer[idx++] = state->enemies_hard[i].health;
            
            enemy_count++;
        }
    }
    
    // Устанавливаем реальное количество врагов
    tx_buffer[enemy_count_pos] = enemy_count;
    
    // Сохраняем позицию для счетчика снарядов
    uint16_t projectile_count_pos = idx++;
    
    // Снаряды
    uint8_t projectile_count = 0;
    for (uint8_t i = 0; i < state->projectile_count && projectile_count < MAX_PROJECTILES_IN_PACKET; i++) {
        if (state->projectiles[i].active) {
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.x + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.x + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.x + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.x + 3);
            
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.y + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.y + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.y + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.y + 3);
            
            tx_buffer[idx++] = state->projectiles[i].is_player_shot;
            
            projectile_count++;
        }
    }
    
    // Устанавливаем реальное количество снарядов
    tx_buffer[projectile_count_pos] = projectile_count;
    
    // Сохраняем позицию для счетчика водоворотов
    uint16_t whirlpool_count_pos = idx++;
    
    // Водовороты
    uint8_t whirlpool_count = 0;
    if (state->whirlpool_manager) {
        whirlpool_count = state->whirlpool_manager->whirlpool_count;
        if (whirlpool_count > MAX_WHIRLPOOLS_IN_PACKET) {
            whirlpool_count = MAX_WHIRLPOOLS_IN_PACKET;
        }
        
        for (uint8_t i = 0; i < whirlpool_count; i++) {
            Whirlpool* whirlpool = &state->whirlpool_manager->whirlpools[i];
            
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.x + 0);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.x + 1);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.x + 2);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.x + 3);
            
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.y + 0);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.y + 1);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.y + 2);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.y + 3);
            
            tx_buffer[idx++] = whirlpool->used_recently;
        }
    }
    
    // Устанавливаем реальное количество водоворотов
    tx_buffer[whirlpool_count_pos] = whirlpool_count;
    
    // Camera и frame counter
    tx_buffer[idx++] = *((uint8_t*)&state->camera_y + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->camera_y + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->camera_y + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->camera_y + 3);
    
    tx_buffer[idx++] = *((uint8_t*)&state->frame_counter + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->frame_counter + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->frame_counter + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->frame_counter + 3);
    
    // Вычисляем и добавляем CRC
    uint8_t crc = Protocol_CalculateCRC(&tx_buffer[1], idx - 1);
    tx_buffer[idx++] = crc;
    
    // Добавляем конечный байт
    tx_buffer[idx++] = END_BYTE;
    
    // Отправка через DMA
    if (HAL_UART_Transmit_DMA(huart_handle, tx_buffer, idx) == HAL_OK) {
        uart_tx_busy = 1;
    }
}

void Protocol_CleanupRxBuffer(void) {
    uint16_t dma_pos = RX_BUFFER_SIZE - __HAL_DMA_GET_COUNTER(huart_handle->hdmarx);
    
    // Если заполнено больше 90%, сбрасываем буфер
    uint16_t used = (dma_pos >= rx_write_pos) ? 
                    (dma_pos - rx_write_pos) : 
                    (RX_BUFFER_SIZE - rx_write_pos + dma_pos);
    
    if (used > (RX_BUFFER_SIZE * 9 / 10)) {
        rx_write_pos = dma_pos;
    }
}

void Protocol_ProcessIncoming(GameState* state) {
    if (huart_handle == NULL) return;
    
    Protocol_CleanupRxBuffer();
    
    uint16_t dma_pos = RX_BUFFER_SIZE - __HAL_DMA_GET_COUNTER(huart_handle->hdmarx);
    
    // Обрабатываем все доступные данные
    while (rx_write_pos != dma_pos) {
        uint8_t byte = rx_buffer[rx_write_pos];
        
        switch (packet_state) {
            case 0: // Ожидание стартового байта
                if (byte == START_BYTE) {
                    packet_state = 1;
                    packet_idx = 0;
                }
                break;
                
            case 1: // Получение типа пакета
                packet_type = byte;
                packet_data[packet_idx++] = byte;
                packet_state = 2;
                break;
                
            case 2: // Получение данных пакета
                packet_data[packet_idx++] = byte;
                
                // Проверка завершения пакета на основе типа
                switch (packet_type) {
                    case PKT_ADD_ENEMY: {
                        // Проверяем, что пришел конечный байт
                        if (byte == END_BYTE) {
                            // Вычисляем ожидаемый размер пакета
                            uint16_t expected_size = 1 +  // type
                                                   1 +  // enemy_type
                                                   4 +  // x
                                                   4 +  // y
                                                   1;   // crc (END_BYTE уже пришел)
                            
                            // Проверяем, что длина пакета правильная
                            if (packet_idx == expected_size) {
                                // Проверка CRC
                                uint8_t crc_calculated = Protocol_CalculateCRC(&packet_data[0], packet_idx - 1);
                                if (crc_calculated == packet_data[packet_idx - 2]) {
                                    // Обработка пакета
                                    uint8_t enemy_type = packet_data[1];
                                    float x = *(float*)&packet_data[2];
                                    float y = *(float*)&packet_data[6];
                                    
                                    if (enemy_type == 0 && state->enemy_simple_count < MAX_ENEMIES_SIMPLE) {
                                        EnemySimple* enemy = &state->enemies_simple[state->enemy_simple_count];
                                        
                                        enemy->position.x = x;
                                        enemy->position.y = y;
                                        enemy->initial_y = y;
                                        enemy->health = ENEMY_SIMPLE_HEALTH;
                                        enemy->max_health = ENEMY_SIMPLE_HEALTH;
                                        enemy->shoot_cooldown = 0;
                                        enemy->shoot_delay = ENEMY_SIMPLE_SHOOT_DELAY;
                                        enemy->radius = COLLISION_RADIUS_ENEMY_SIMPLE;
                                        enemy->points = ENEMY_SIMPLE_POINTS;
                                        enemy->active = 0; // Активируется при приближении к игроку
                                        enemy->alive = 1;
                                        enemy->wander_angle = 0;
                                        enemy->wander_timer = 0;
                                        enemy->strategy = STRATEGY_ATTACK;
                                        
                                        state->enemy_simple_count++;
                                    }
                                    else if (enemy_type == 1 && state->enemy_hard_count < MAX_ENEMIES_HARD) {
                                        EnemyHard* enemy = &state->enemies_hard[state->enemy_hard_count];
                                        
                                        enemy->position.x = x;
                                        enemy->position.y = y;
                                        enemy->initial_y = y;
                                        enemy->health = ENEMY_HARD_HEALTH;
                                        enemy->max_health = ENEMY_HARD_HEALTH;
                                        enemy->shoot_cooldown = 0;
                                        enemy->shoot_delay = ENEMY_HARD_SHOOT_DELAY;
                                        enemy->radius = COLLISION_RADIUS_ENEMY_HARD;
                                        enemy->points = ENEMY_HARD_POINTS;
                                        enemy->armor_timer = 0;
                                        enemy->active = 0;
                                        enemy->alive = 1;
                                        enemy->wander_angle = 0;
                                        enemy->wander_timer = 0;
                                        enemy->pursuit_timer = 0;
                                        enemy->pursuit_direction = 0;
                                        enemy->patrol_point_index = 0;
                                        enemy->patrol_points_count = 0;
                                        enemy->strategy = STRATEGY_AGGRESSIVE;
                                        
                                        state->enemy_hard_count++;
                                    }
                                }
                            }
                        }
                        packet_state = 0;
                        break;
                    }
                    
                    case PKT_ADD_OBSTACLE: {
                        if (byte == END_BYTE) {
                            uint16_t expected_size = 1 +  // type
                                                   1 +  // obstacle_type
                                                   4 +  // x
                                                   4 +  // y
                                                   4 +  // radius
                                                   1;   // crc
                            
                            if (packet_idx == expected_size) {
                                uint8_t crc_calculated = Protocol_CalculateCRC(&packet_data[0], packet_idx - 1);
                                if (crc_calculated == packet_data[packet_idx - 2]) {
                                    uint8_t obstacle_type = packet_data[1];
                                    float x = *(float*)&packet_data[2];
                                    float y = *(float*)&packet_data[6];
                                    float radius = *(float*)&packet_data[10];
                                    
                                    if (state->obstacle_count < MAX_OBSTACLES) {
                                        Obstacle* obstacle = &state->obstacles[state->obstacle_count];
                                        
                                        obstacle->position.x = x;
                                        obstacle->position.y = y;
                                        obstacle->radius = radius;
                                        obstacle->type = (ObstacleType)obstacle_type;
                                        obstacle->active = 1;
                                        
                                        state->obstacle_count++;
                                    }
                                }
                            }
                        }
                        packet_state = 0;
                        break;
                    }
                    
                    case PKT_ADD_WHIRLPOOL: {
                        if (byte == END_BYTE) {
                            uint16_t expected_size = 1 +  // type
                                                   4 +  // x
                                                   4 +  // y
                                                   1;   // crc
                            
                            if (packet_idx == expected_size) {
                                uint8_t crc_calculated = Protocol_CalculateCRC(&packet_data[0], packet_idx - 1);
                                if (crc_calculated == packet_data[packet_idx - 2]) {
                                    float x = *(float*)&packet_data[1];
                                    float y = *(float*)&packet_data[5];
                                    
                                    if (state->whirlpool_manager) {
                                        WhirlpoolManager_Add(state->whirlpool_manager, x, y);
                                    }
                                }
                            }
                        }
                        packet_state = 0;
                        break;
                    }
                    
                    case PKT_CLEANUP: {
                        if (byte == END_BYTE) {
                            uint16_t expected_size = 1 +  // type
                                                   4 +  // threshold_y
                                                   1;   // crc
                            
                            if (packet_idx == expected_size) {
                                uint8_t crc_calculated = Protocol_CalculateCRC(&packet_data[0], packet_idx - 1);
                                if (crc_calculated == packet_data[packet_idx - 2]) {
                                    float threshold_y = *(float*)&packet_data[1];
                                    
                                    Enemies_CleanupOld(state, threshold_y);
                                    Obstacles_CleanupOld(state, threshold_y);
                                    if (state->whirlpool_manager) {
                                        WhirlpoolManager_Cleanup(state->whirlpool_manager, threshold_y);
                                    }
                                }
                            }
                        }
                        packet_state = 0;
                        break;
                    }
                    
                    case PKT_INIT_GAME:
                        if (byte == END_BYTE) {
                            GameState_Cleanup(state);
                            GameState_Init(state);
                            packet_state = 0;
                        }
                        break;
                }
                break;
        }
        
        // Перемещаем позицию записи
        rx_write_pos++;
        if (rx_write_pos >= RX_BUFFER_SIZE) {
            rx_write_pos = 0;
        }
    }
}

// ===== File: ./Src\whirlpool.c =====

/* whirlpool.c - Реализация водоворотов с полной логикой на STM32 */

#include "whirlpool.h"
#include <string.h>
#include <math.h>

void WhirlpoolManager_Init(struct WhirlpoolManager* manager) {
    memset(manager->whirlpools, 0, sizeof(manager->whirlpools));
    manager->whirlpool_count = 0;
}

void WhirlpoolManager_Update(struct WhirlpoolManager* manager, GameState* state) {
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        Whirlpool* whirlpool = &manager->whirlpools[i];
        
        // Обновление анимации
        whirlpool->rotation = fmodf(whirlpool->rotation + WHIRLPOOL_ROTATION_SPEED, 360.0f);
        whirlpool->animation_phase = fmodf(whirlpool->animation_phase + WHIRLPOOL_ANIMATION_SPEED, 2.0f * PI);
        
        // Обновление cooldown
        if (whirlpool->cooldown_timer > 0) {
            whirlpool->cooldown_timer--;
            if (whirlpool->cooldown_timer == 0) {
                whirlpool->used_recently = 0;
            }
        }
        
        // Проверка коллизии с игроком
        if (!whirlpool->used_recently && 
            Whirlpool_CollidesWith(whirlpool, 
                                  state->player.position.x, 
                                  state->player.position.y, 
                                  COLLISION_RADIUS_PLAYER)) {
            
            // Поиск подходящего водоворота для телепортации
            Whirlpool* target = WhirlpoolManager_FindTarget(manager, whirlpool, state->world_top);
            
            // Если не найден подходящий, создаем новый
            if (!target) {
                target = WhirlpoolManager_CreateForTeleport(manager, 
                                                          whirlpool, 
                                                          state->world_top,
                                                          state->obstacles,
                                                          state->obstacle_count);
            }
            
            // Если удалось найти или создать целевой водоворот
            if (target) {
                // Выполняем телепортацию
                WhirlpoolManager_TeleportPlayer(manager, whirlpool, target, &state->player);
            }
        }
    }
}

uint8_t WhirlpoolManager_Add(struct WhirlpoolManager* manager, float x, float y) {
    if (manager->whirlpool_count >= WHIRLPOOL_MAX_COUNT) {
        return 0;
    }
    
    // Добавляем водоворот
    Whirlpool* whirlpool = &manager->whirlpools[manager->whirlpool_count];
    whirlpool->position.x = x;
    whirlpool->position.y = y;
    whirlpool->radius = WHIRLPOOL_RADIUS;
    whirlpool->rotation = 0.0f;
    whirlpool->used_recently = 0;
    whirlpool->cooldown_timer = 0;
    whirlpool->animation_phase = 0.0f;
    
    manager->whirlpool_count++;
    return 1;
}

void WhirlpoolManager_Cleanup(struct WhirlpoolManager* manager, float threshold_y) {
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        if (manager->whirlpools[i].position.y > threshold_y) {
            // Удаляем водоворот (перемещаем последний на место удаляемого)
            if (i < manager->whirlpool_count - 1) {
                manager->whirlpools[i] = manager->whirlpools[manager->whirlpool_count - 1];
            }
            manager->whirlpool_count--;
            i--;
        }
    }
}

uint8_t Whirlpool_CollidesWith(Whirlpool* whirlpool, float x, float y, float radius) {
    if (whirlpool->used_recently) {
        return 0;
    }
    
    float dx = x - whirlpool->position.x;
    float dy = y - whirlpool->position.y;
    float dist = Utils_Distance(0, 0, dx, dy);
    
    return (dist < whirlpool->radius + radius);
}

Whirlpool* WhirlpoolManager_FindTarget(struct WhirlpoolManager* manager, Whirlpool* current, float world_top) {
    Whirlpool* best_candidate = NULL;
    float best_distance = 0;
    
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        Whirlpool* candidate = &manager->whirlpools[i];
        
        // Пропускаем текущий водоворот и уже использованные
        if (candidate == current || candidate->used_recently) {
            continue;
        }
        
        // Проверяем, что водоворот находится достаточно далеко позади
        float distance = current->position.y - candidate->position.y;
        if (distance >= WHIRLPOOL_TELEPORT_DISTANCE && 
            distance < WHIRLPOOL_TELEPORT_DISTANCE * 1.5f &&  // Ограничиваем максимальное расстояние
            candidate->position.y > world_top) {
            
            // Выбираем водоворот, который ближе всего к идеальному расстоянию
            float score = fabsf(distance - WHIRLPOOL_TELEPORT_DISTANCE);
            if (!best_candidate || score < best_distance) {
                best_candidate = candidate;
                best_distance = score;
            }
        }
    }
    
    return best_candidate;
}

Whirlpool* WhirlpoolManager_CreateForTeleport(struct WhirlpoolManager* manager, 
                                            Whirlpool* current, 
                                            float world_top,
                                            Obstacle* obstacles,
                                            uint8_t obstacle_count) {
    // Попытка найти подходящее место для нового водоворота
    for (uint8_t attempt = 0; attempt < WHIRLPOOL_PLACEMENT_ATTEMPTS; attempt++) {
        // Генерируем координаты для нового водоворота
        float new_y = current->position.y - WHIRLPOOL_TELEPORT_DISTANCE - 
                     Utils_RandomRangeFloat(0, 500);
        float new_x = Utils_RandomRangeFloat(WHIRLPOOL_EDGE_MARGIN, 
                                            SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN);
        
        // Проверяем безопасность размещения
        uint8_t safe = 1;
        
        // Проверка расстояния до препятствий
        for (uint8_t i = 0; i < obstacle_count; i++) {
            if (!obstacles[i].active) continue;
            
            float dx = new_x - obstacles[i].position.x;
            float dy = new_y - obstacles[i].position.y;
            float dist = Utils_Distance(0, 0, dx, dy);
            
            if (dist < obstacles[i].radius + WHIRLPOOL_ISLAND_SAFE_DISTANCE) {
                safe = 0;
                break;
            }
        }
        
        // Проверка нахождения в пределах мира
        if (new_y <= world_top) {
            safe = 0;
        }
        
        // Если место безопасно, создаем водоворот
        if (safe && manager->whirlpool_count < WHIRLPOOL_MAX_COUNT) {
            Whirlpool* new_whirlpool = &manager->whirlpools[manager->whirlpool_count];
            new_whirlpool->position.x = new_x;
            new_whirlpool->position.y = new_y;
            new_whirlpool->radius = WHIRLPOOL_RADIUS;
            new_whirlpool->rotation = 0.0f;
            new_whirlpool->used_recently = 0;
            new_whirlpool->cooldown_timer = 0;
            new_whirlpool->animation_phase = 0.0f;
            
            manager->whirlpool_count++;
            return new_whirlpool;
        }
    }
    
    // Если не удалось найти безопасное место, возвращаем NULL
    return NULL;
}

void WhirlpoolManager_TeleportPlayer(struct WhirlpoolManager* manager, 
                                   Whirlpool* source, 
                                   Whirlpool* target, 
                                   Player* player) {
    // Телепортация игрока
    player->position.x = target->position.x;
    player->position.y = target->position.y + WHIRLPOOL_PLAYER_OFFSET;
    
    // Помечаем оба водоворота как использованные
    source->used_recently = 1;
    source->cooldown_timer = WHIRLPOOL_COOLDOWN;
    
    target->used_recently = 1;
    target->cooldown_timer = WHIRLPOOL_COOLDOWN;
}