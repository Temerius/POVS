/* game_state_ext.h - Расширенное состояние игры с водоворотами */

#ifndef GAME_STATE_EXT_H
#define GAME_STATE_EXT_H

#include "game_types.h"
#include "whirlpool.h"

// Инициализация расширенного состояния игры
void GameState_ExtendedInit(GameState* state);

// Очистка расширенного состояния игры
void GameState_ExtendedCleanup(GameState* state);

#endif // GAME_STATE_EXT_H