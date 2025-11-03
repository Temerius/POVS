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