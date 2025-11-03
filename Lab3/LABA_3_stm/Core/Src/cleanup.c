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