

#ifndef CLEANUP_H
#define CLEANUP_H

#include "game_types.h"

 
void Enemies_CleanupOld(GameState* state, float threshold_y);

 
void Obstacles_CleanupOld(GameState* state, float threshold_y);

 
void Obstacles_Remove(GameState* state, uint8_t index);

 
void Cleanup_EmergencyCleanup(GameState* state);

#endif  