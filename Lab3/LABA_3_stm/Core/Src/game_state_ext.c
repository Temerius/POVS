/* game_state_ext.c - Реализация расширенного состояния игры */

#include "game_state_ext.h"
#include <stdlib.h>

void GameState_ExtendedInit(GameState* state) {
    // Выделяем память для менеджера водоворотов
    state->whirlpool_manager = (WhirlpoolManager*)malloc(sizeof(WhirlpoolManager));
    if (state->whirlpool_manager) {
        WhirlpoolManager_Init(state->whirlpool_manager);
    }
}

void GameState_ExtendedCleanup(GameState* state) {
    // Освобождаем память менеджера водоворотов
    if (state->whirlpool_manager) {
        free(state->whirlpool_manager);
        state->whirlpool_manager = NULL;
    }
}