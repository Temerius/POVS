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
#include "cleanup.h"
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
    state->skipped_packets = 0;
    
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
    

    if (state->frame_counter % AUTO_CLEANUP_INTERVAL == 0) {
        // Порог очистки: игрок.y + безопасное расстояние
        float cleanup_threshold = state->player.position.y + ENEMY_DELETE_DISTANCE;
        
        // Очистка всех типов объектов
        Enemies_CleanupOld(state, cleanup_threshold);
        Obstacles_CleanupOld(state, cleanup_threshold);
        
        if (state->whirlpool_manager) {
            WhirlpoolManager_Cleanup(state->whirlpool_manager, cleanup_threshold);
        }
        
    }

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