
#ifndef WORLD_GENERATION_H
#define WORLD_GENERATION_H

#include "game_types.h"

 
void WorldGen_GenerateSegment(GameState* state);

 
void WorldGen_GenerateEnemies(GameState* state, float segment_start, float segment_end);

 
void WorldGen_GenerateWhirlpools(GameState* state, float segment_start, float segment_end);

 
uint8_t WorldGen_CanPlaceEnemy(GameState* state, float x, float y, float radius);

 
uint8_t WorldGen_CanPlaceWhirlpool(GameState* state, float x, float y);

#endif  