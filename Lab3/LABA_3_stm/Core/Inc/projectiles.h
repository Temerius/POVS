/* projectiles.h - Интерфейс снарядов */

#ifndef PROJECTILES_H
#define PROJECTILES_H

#include "game_types.h"

// Обновление всех снарядов
void Projectiles_Update(GameState* state);

// Удаление снаряда по индексу
void Projectiles_Remove(GameState* state, uint8_t index);

// Проверка столкновения снаряда с препятствием
uint8_t Projectile_CollidesWith(Projectile* proj, Obstacle* obstacle);

#endif // PROJECTILES_H