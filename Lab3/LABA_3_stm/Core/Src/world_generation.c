/* world_generation.c - Генерация игрового мира */

#include "world_generation.h"
#include "whirlpool.h"
#include "utils.h"
#include <math.h>

// Константы генерации (из Python config.py)
#define WORLD_SEGMENT_HEIGHT 2000
#define WORLD_ENEMY_SPAWN_DISTANCE -1500
#define WORLD_ENEMY_STEP_MIN 100
#define WORLD_ENEMY_STEP_MAX 300
#define ENEMY_CLEARANCE_EXTRA 50.0f
#define SPAWN_CLEARANCE_RADIUS 50.0f

void WorldGen_GenerateSegment(GameState* state) {
    float segment_start = state->world_top - WORLD_SEGMENT_HEIGHT;
    float segment_end = state->world_top;
    
    // Генерация врагов
    WorldGen_GenerateEnemies(state, segment_start, segment_end);
    
    // Генерация водоворотов
    WorldGen_GenerateWhirlpools(state, segment_start, segment_end);
    
    // Обновляем верхнюю границу мира
    state->world_top = segment_start;
}

void WorldGen_GenerateEnemies(GameState* state, float segment_start, float segment_end) {
    float current_y = segment_start;
    
    while (current_y < segment_end) {
        // Генерируем врагов только если они будут ниже игрока
        if (current_y < state->player.position.y + WORLD_ENEMY_SPAWN_DISTANCE) {
            // Простые враги (30% шанс)
            if (Utils_RandomFloat() < ENEMY_SIMPLE_SPAWN_CHANCE) {
                // До 10 попыток найти подходящее место
                for (uint8_t attempt = 0; attempt < 10; attempt++) {
                    float x = Utils_RandomRangeFloat(250, SCREEN_WIDTH - 250);
                    
                    if (WorldGen_CanPlaceEnemy(state, x, current_y, COLLISION_RADIUS_ENEMY_SIMPLE)) {
                        // Проверяем, есть ли место в массиве
                        if (state->enemy_simple_count < MAX_ENEMIES_SIMPLE) {
                            EnemySimple* enemy = &state->enemies_simple[state->enemy_simple_count];
                            
                            enemy->position.x = x;
                            enemy->position.y = current_y;
                            enemy->initial_y = current_y;
                            enemy->velocity.x = 0;
                            enemy->velocity.y = 0;
                            enemy->target_angle = Utils_DegToRad(90); // Вниз
                            
                            enemy->health = ENEMY_SIMPLE_HEALTH;
                            enemy->max_health = ENEMY_SIMPLE_HEALTH;
                            enemy->shoot_cooldown = 0;
                            enemy->shoot_delay = ENEMY_SIMPLE_SHOOT_DELAY;
                            enemy->radius = COLLISION_RADIUS_ENEMY_SIMPLE;
                            enemy->points = ENEMY_SIMPLE_POINTS;
                            
                            enemy->active = 0; // Будет активирован при приближении игрока
                            enemy->alive = 1;
                            enemy->current_direction = 2; // down
                            
                            // AI параметры
                            enemy->wander_angle = Utils_RandomRangeFloat(-PI/6, PI/6);
                            enemy->wander_timer = Utils_RandomRange(90, 180);
                            enemy->strategy = STRATEGY_PATROL; // Будет определена при активации
                            
                            state->enemy_simple_count++;
                        }
                        break;
                    }
                }
            }
            
            // Сложные враги (15% шанс)
            if (Utils_RandomFloat() < ENEMY_HARD_SPAWN_CHANCE) {
                for (uint8_t attempt = 0; attempt < 10; attempt++) {
                    float x = Utils_RandomRangeFloat(300, SCREEN_WIDTH - 300);
                    
                    if (WorldGen_CanPlaceEnemy(state, x, current_y, COLLISION_RADIUS_ENEMY_HARD)) {
                        if (state->enemy_hard_count < MAX_ENEMIES_HARD) {
                            EnemyHard* enemy = &state->enemies_hard[state->enemy_hard_count];
                            
                            enemy->position.x = x;
                            enemy->position.y = current_y;
                            enemy->initial_y = current_y;
                            enemy->velocity.x = 0;
                            enemy->velocity.y = 0;
                            enemy->target_angle = Utils_DegToRad(90); // Вниз
                            
                            enemy->health = ENEMY_HARD_HEALTH;
                            enemy->max_health = ENEMY_HARD_HEALTH;
                            enemy->shoot_cooldown = 0;
                            enemy->shoot_delay = ENEMY_HARD_SHOOT_DELAY;
                            enemy->radius = COLLISION_RADIUS_ENEMY_HARD;
                            enemy->points = ENEMY_HARD_POINTS;
                            enemy->armor_timer = 0;
                            
                            enemy->active = 0;
                            enemy->alive = 1;
                            enemy->current_direction = 2; // down
                            
                            // AI параметры
                            enemy->wander_angle = Utils_RandomRangeFloat(-PI/6, PI/6);
                            enemy->wander_timer = Utils_RandomRange(180, 300);
                            enemy->strategy = STRATEGY_PATROL; // Будет определена при активации
                            enemy->pursuit_timer = 0;
                            enemy->pursuit_direction = 0;
                            enemy->patrol_point_index = 0;
                            enemy->patrol_points_count = 0;
                            
                            state->enemy_hard_count++;
                        }
                        break;
                    }
                }
            }
        }
        
        // Переходим к следующей позиции
        current_y += Utils_RandomRange(WORLD_ENEMY_STEP_MIN, WORLD_ENEMY_STEP_MAX);
    }
}

void WorldGen_GenerateWhirlpools(GameState* state, float segment_start, float segment_end) {
    if (!state->whirlpool_manager) {
        return;
    }
    
    // Проверяем, не превышен ли лимит водоворотов
    if (state->whirlpool_manager->whirlpool_count >= WHIRLPOOL_MAX_COUNT) {
        return;
    }
    
    float current_y = segment_start;
    
    while (current_y < segment_end) {
        // 10% шанс создания водоворота
        if (Utils_RandomFloat() < WHIRLPOOL_SPAWN_CHANCE) {
            float x = Utils_RandomRangeFloat(WHIRLPOOL_EDGE_MARGIN, 
                                            SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN);
            
            // Проверяем возможность размещения
            if (WorldGen_CanPlaceWhirlpool(state, x, current_y)) {
                WhirlpoolManager_Add(state->whirlpool_manager, x, current_y);
            }
        }
        
        current_y += Utils_RandomRange(200, 400);
    }
}

uint8_t WorldGen_CanPlaceEnemy(GameState* state, float x, float y, float radius) {
    // Проверка краёв экрана
    if (x < SHORE_EDGE_MARGIN || x > SCREEN_WIDTH - SHORE_EDGE_MARGIN) {
        return 0;
    }
    
    // Проверка расстояния до препятствий (островов)
    for (uint8_t i = 0; i < state->obstacle_count; i++) {
        if (!state->obstacles[i].active) continue;
        
        float dx = x - state->obstacles[i].position.x;
        float dy = y - state->obstacles[i].position.y;
        float dist = sqrtf(dx*dx + dy*dy);
        
        if (dist < state->obstacles[i].radius + radius + ENEMY_CLEARANCE_EXTRA) {
            return 0;
        }
    }
    
    // Проверка расстояния до других простых врагов
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
        if (!state->enemies_simple[i].alive) continue;
        
        float dx = x - state->enemies_simple[i].position.x;
        float dy = y - state->enemies_simple[i].position.y;
        float dist = sqrtf(dx*dx + dy*dy);
        
        if (dist < radius + COLLISION_RADIUS_ENEMY_SIMPLE + 100) {
            return 0;
        }
    }
    
    // Проверка расстояния до сложных врагов
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        if (!state->enemies_hard[i].alive) continue;
        
        float dx = x - state->enemies_hard[i].position.x;
        float dy = y - state->enemies_hard[i].position.y;
        float dist = sqrtf(dx*dx + dy*dy);
        
        if (dist < radius + COLLISION_RADIUS_ENEMY_HARD + 100) {
            return 0;
        }
    }
    
    return 1;
}

uint8_t WorldGen_CanPlaceWhirlpool(GameState* state, float x, float y) {
    if (!state->whirlpool_manager) {
        return 0;
    }
    
    // Проверка краёв
    if (x < WHIRLPOOL_EDGE_MARGIN || x > SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN) {
        return 0;
    }
    
    // Проверка расстояния до препятствий
    for (uint8_t i = 0; i < state->obstacle_count; i++) {
        if (!state->obstacles[i].active) continue;
        
        float dx = x - state->obstacles[i].position.x;
        float dy = y - state->obstacles[i].position.y;
        float dist = sqrtf(dx*dx + dy*dy);
        
        float safe_distance = state->obstacles[i].radius + WHIRLPOOL_ISLAND_SAFE_DISTANCE;
        if (dist < safe_distance) {
            return 0;
        }
    }
    
    // Проверка расстояния до других водоворотов
    for (uint8_t i = 0; i < state->whirlpool_manager->whirlpool_count; i++) {
        Whirlpool* whirlpool = &state->whirlpool_manager->whirlpools[i];
        
        float dx = x - whirlpool->position.x;
        float dy = y - whirlpool->position.y;
        float dist = sqrtf(dx*dx + dy*dy);
        
        if (dist < WHIRLPOOL_MIN_DISTANCE * 2.5f) {
            return 0;
        }
    }
    
    return 1;
}