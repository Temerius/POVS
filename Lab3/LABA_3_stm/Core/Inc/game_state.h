
#ifndef GAME_STATE_H
#define GAME_STATE_H

#include "game_config.h"
#include "game_types.h"
#include "input.h"

 
void GameState_Init(GameState* state);

 
void GameState_Update(GameState* state, InputState* input);

 
void GameState_CheckCollisions(GameState* state);

 
void GameState_Cleanup(GameState* state);

#endif  