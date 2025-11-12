/* cleanup.c - Очистка старых объектов (ИСПРАВЛЕНО) */

#include "cleanup.h"
#include "enemies.h"
#include "utils.h"
#include "whirlpool.h"

void Enemies_CleanupOld(GameState* state, float threshold_y) {
    uint8_t cleaned_simple = 0;
    uint8_t cleaned_hard = 0;
    
    // КРИТИЧНО: Очистка простых врагов
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
        // Удаляем врагов, которые НИЖЕ порога (больше Y, т.к. Y растёт вниз)
        if (state->enemies_simple[i].position.y > threshold_y) {
            Enemies_RemoveSimple(state, i);
            i--; // Проверяем этот индекс снова
            cleaned_simple++;
        }
    }
    
    // Очистка сложных врагов
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        if (state->enemies_hard[i].position.y > threshold_y) {
            Enemies_RemoveHard(state, i);
            i--;
            cleaned_hard++;
        }
    }
    
    // Очистка водоворотов
    if (state->whirlpool_manager) {
        WhirlpoolManager_Cleanup(state->whirlpool_manager, threshold_y);
    }
    
    // Debug: если удалили объекты, можно отправить статистику
    if ((cleaned_simple + cleaned_hard) > 0) {
        // Опционально: отправить debug-пакет
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

// НОВАЯ ФУНКЦИЯ: Принудительная очистка при переполнении
void Cleanup_EmergencyCleanup(GameState* state) {
    // Удаляем самых дальних врагов
    float player_y = state->player.position.y;
    
    // Удаляем врагов дальше 2000 пикселей позади игрока
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
    
    // Удаляем старые снаряды (старше 3 секунд)
    for (uint8_t i = 0; i < state->projectile_count; i++) {
        if (state->projectiles[i].lifetime < 90) { // Меньше 1.5 секунд жизни
            // Удаляем снаряд
            if (i < state->projectile_count - 1) {
                state->projectiles[i] = state->projectiles[state->projectile_count - 1];
            }
            state->projectile_count--;
            i--;
        }
    }
}