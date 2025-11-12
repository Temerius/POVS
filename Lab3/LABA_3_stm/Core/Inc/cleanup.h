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

// НОВАЯ: Экстренная очистка при переполнении
void Cleanup_EmergencyCleanup(GameState* state);

#endif // CLEANUP_H