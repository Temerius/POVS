/* enemies.h - Интерфейс врагов */

#ifndef ENEMIES_H
#define ENEMIES_H

#include "game_types.h"

// Обновление всех врагов
void Enemies_Update(GameState* state);

void EnemySimple_UpdateAI(EnemySimple* enemy, Player* player, Obstacle* obstacles, uint8_t obstacle_count);

// Обновление AI сложного врага
void EnemyHard_UpdateAI(EnemyHard* enemy, Player* player, Obstacle* obstacles, uint8_t obstacle_count);

// Генерация точек патрулирования для сложного врага
void Enemies_GeneratePatrolPoints(EnemyHard* enemy, Player* player);

// Проверка видимости игрока простым врагом
uint8_t Enemies_CanSeePlayer(EnemySimple* enemy, Player* player);

// Проверка видимости игрока сложным врагом
uint8_t Enemies_CanSeePlayerHard(EnemyHard* enemy, Player* player);

// Стрельба простого врага
void Enemies_ShootAtPlayer(GameState* state, EnemySimple* enemy);

// Стрельба сложного врага
void Enemies_ShootHardAtPlayer(GameState* state, EnemyHard* enemy);

// Проверка коллизий врага с препятствиями
uint8_t Enemies_CheckCollision(GameState* state, float x, float y, float radius);

// Удаление врагов
void Enemies_RemoveSimple(GameState* state, uint8_t index);
void Enemies_RemoveHard(GameState* state, uint8_t index);

#endif // ENEMIES_H