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