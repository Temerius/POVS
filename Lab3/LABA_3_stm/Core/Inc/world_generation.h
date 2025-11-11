/* world_generation.h - Генерация игрового мира */

#ifndef WORLD_GENERATION_H
#define WORLD_GENERATION_H

#include "game_types.h"

// Генерация сегмента мира (враги, водовороты)
void WorldGen_GenerateSegment(GameState* state);

// Генерация врагов в сегменте
void WorldGen_GenerateEnemies(GameState* state, float segment_start, float segment_end);

// Генерация водоворотов в сегменте
void WorldGen_GenerateWhirlpools(GameState* state, float segment_start, float segment_end);

// Проверка возможности размещения врага
uint8_t WorldGen_CanPlaceEnemy(GameState* state, float x, float y, float radius);

// Проверка возможности размещения водоворота
uint8_t WorldGen_CanPlaceWhirlpool(GameState* state, float x, float y);

#endif // WORLD_GENERATION_H