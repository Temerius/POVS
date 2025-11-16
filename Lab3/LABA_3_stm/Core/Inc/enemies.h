

#ifndef ENEMIES_H
#define ENEMIES_H

#include "game_types.h"

 
void Enemies_Update(GameState* state);

void EnemySimple_UpdateAI(EnemySimple* enemy, Player* player, Obstacle* obstacles, uint8_t obstacle_count);

 
void EnemyHard_UpdateAI(EnemyHard* enemy, Player* player, Obstacle* obstacles, uint8_t obstacle_count);

 
void Enemies_GeneratePatrolPoints(EnemyHard* enemy, Player* player);

 
uint8_t Enemies_CanSeePlayer(EnemySimple* enemy, Player* player);

 
uint8_t Enemies_CanSeePlayerHard(EnemyHard* enemy, Player* player);

 
void Enemies_ShootAtPlayer(GameState* state, EnemySimple* enemy);

 
void Enemies_ShootHardAtPlayer(GameState* state, EnemyHard* enemy);

 
uint8_t Enemies_CheckCollision(GameState* state, float x, float y, float radius);

 
void Enemies_RemoveSimple(GameState* state, uint8_t index);
void Enemies_RemoveHard(GameState* state, uint8_t index);

#endif  