/* game_state.h - Управление игровым состоянием (окончательная версия) */

#ifndef GAME_STATE_H
#define GAME_STATE_H

#include "game_config.h"
#include "game_types.h"
#include "input.h"

// Инициализация игрового состояния
void GameState_Init(GameState* state);

// Обновление игрового состояния
void GameState_Update(GameState* state, InputState* input);

// Проверка коллизий в игровом состоянии
void GameState_CheckCollisions(GameState* state);

// Очистка игрового состояния
void GameState_Cleanup(GameState* state);

#endif // GAME_STATE_H