/* player.h - Интерфейс игрока (окончательная версия) */

#ifndef PLAYER_H
#define PLAYER_H

#include "game_config.h"
#include "game_types.h"
#include "input.h"  // ВАЖНО: input.h должен быть включен ДО объявления функций

// Обновление состояния игрока
void Player_Update(Player* player, InputState* input, Obstacle* obstacles, uint8_t obstacle_count);

// Обработка поворота корпуса
void Player_HandleRotation(Player* player, InputState* input);

// Обработка движения и коллизий
void Player_HandleMovement(Player* player, Obstacle* obstacles, uint8_t obstacle_count);

// Проверка коллизий
uint8_t Player_CheckCollisions(Player* player, Obstacle* obstacles, uint8_t obstacle_count);

// Обновление таймера перезарядки
void Player_UpdateCooldown(Player* player);

// Стрельба
void Player_Shoot(GameState* state);

#endif // PLAYER_H