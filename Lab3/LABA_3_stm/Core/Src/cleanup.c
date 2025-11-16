
#include "cleanup.h"
#include "enemies.h"
#include "utils.h"
#include "whirlpool.h"

void Enemies_CleanupOld(GameState* state, float threshold_y) {
    uint8_t cleaned_simple = 0;
    uint8_t cleaned_hard = 0;
    
     
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
         
        if (state->enemies_simple[i].position.y > threshold_y) {
            Enemies_RemoveSimple(state, i);
            i--;  
            cleaned_simple++;
        }
    }
    
     
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        if (state->enemies_hard[i].position.y > threshold_y) {
            Enemies_RemoveHard(state, i);
            i--;
            cleaned_hard++;
        }
    }
    
     
    if (state->whirlpool_manager) {
        WhirlpoolManager_Cleanup(state->whirlpool_manager, threshold_y);
    }
    
     
    if ((cleaned_simple + cleaned_hard) > 0) {
         
    }
}

void Obstacles_CleanupOld(GameState* state, float threshold_y) {
    uint8_t cleaned = 0;
    
    for (uint8_t i = 0; i < state->obstacle_count; i++) {
        if (state->obstacles[i].active && 
            state->obstacles[i].position.y > threshold_y) {
            
            Obstacles_Remove(state, i);
            i--;
            cleaned++;
        }
    }
}

void Obstacles_Remove(GameState* state, uint8_t index) {
    if (index < state->obstacle_count - 1) {
        state->obstacles[index] = state->obstacles[state->obstacle_count - 1];
    }
    state->obstacle_count--;
}

 
void Cleanup_EmergencyCleanup(GameState* state) {
     
    float player_y = state->player.position.y;
    
     
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
        if (state->enemies_simple[i].position.y > player_y + 2000) {
            Enemies_RemoveSimple(state, i);
            i--;
        }
    }
    
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        if (state->enemies_hard[i].position.y > player_y + 2000) {
            Enemies_RemoveHard(state, i);
            i--;
        }
    }
    
     
    for (uint8_t i = 0; i < state->projectile_count; i++) {
        if (state->projectiles[i].lifetime < 90) {  
             
            if (i < state->projectile_count - 1) {
                state->projectiles[i] = state->projectiles[state->projectile_count - 1];
            }
            state->projectile_count--;
            i--;
        }
    }
}