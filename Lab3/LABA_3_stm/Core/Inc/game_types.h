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