
#include "collisions.h"
#include "projectiles.h"
#include "enemies.h"
#include "utils.h"
#include <string.h>

void Projectiles_CheckCollisions(GameState* state) {
    for (uint8_t i = 0; i < state->projectile_count; i++) {
        Projectile* proj = &state->projectiles[i];
        
        if (!proj->active) continue;
        
         
        uint8_t obstacle_hit = 0;
        
         
        if (proj->is_player_shot) {
            for (uint8_t j = 0; j < state->enemy_simple_count; j++) {
                EnemySimple* enemy = &state->enemies_simple[j];
                
                if (!enemy->alive || !enemy->active) continue;
                
                float dx = proj->position.x - enemy->position.x;
                float dy = proj->position.y - enemy->position.y;
                float dist = Utils_Distance(0, 0, dx, dy);
                
                if (dist < proj->radius + enemy->radius) {
                     
                    enemy->health--;
                    
                     
                    if (enemy->health <= 0) {
                        state->player.score += enemy->points;
                        Enemies_RemoveSimple(state, j);
                    }
                    
                     
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
                     
                    enemy->health--;
                    enemy->armor_timer = ENEMY_HARD_ARMOR_FLASH_DURATION;
                    
                     
                    if (enemy->health <= 0) {
                        state->player.score += enemy->points;
                        Enemies_RemoveHard(state, j);
                    }
                    
                     
                    Projectiles_Remove(state, i);
                    i--;
                    break;
                }
            }
        }
         
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
        
         
        if (i < state->projectile_count) {
            for (uint8_t j = 0; j < state->obstacle_count; j++) {
                if (!state->obstacles[j].active) continue;
                
                if (Projectile_CollidesWith(proj, &state->obstacles[j])) {
                    obstacle_hit = 1;
                    break;
                }
            }
            
             
            if (obstacle_hit) {
                Projectiles_Remove(state, i);
                i--;
            }
        }
        
         
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
     
    Player_CheckEnemyCollisions(state);
    
     
    Projectiles_CheckCollisions(state);
}

void Player_CheckEnemyCollisions(GameState* state) {
     
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
        EnemySimple* enemy = &state->enemies_simple[i];
        
        if (!enemy->alive || !enemy->active) continue;
        
        float dx = state->player.position.x - enemy->position.x;
        float dy = state->player.position.y - enemy->position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < state->player.radius + enemy->radius) {
             
            state->player.health -= ENEMY_SIMPLE_TORPEDO_DAMAGE;
            
             
            Enemies_RemoveSimple(state, i);
            i--;
        }
    }
    
     
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        EnemyHard* enemy = &state->enemies_hard[i];
        
        if (!enemy->alive || !enemy->active) continue;
        
        float dx = state->player.position.x - enemy->position.x;
        float dy = state->player.position.y - enemy->position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < state->player.radius + enemy->radius) {
             
            state->player.health -= ENEMY_HARD_TORPEDO_DAMAGE;
            
             
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