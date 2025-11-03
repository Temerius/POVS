/* collisions.h - Интерфейс проверки коллизий */

#ifndef COLLISIONS_H
#define COLLISIONS_H

#include "game_types.h"

// Проверка всех коллизий в игре
void GameState_CheckCollisions(GameState* state);

// Проверка столкновений игрока с врагами
void Player_CheckEnemyCollisions(GameState* state);

#endif // COLLISIONS_H