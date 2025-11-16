
#ifndef PLAYER_H
#define PLAYER_H

#include "game_config.h"
#include "game_types.h"
#include "input.h"   

 
void Player_Update(Player* player, InputState* input, Obstacle* obstacles, uint8_t obstacle_count);

 
void Player_HandleRotation(Player* player, InputState* input);

 
void Player_HandleMovement(Player* player, Obstacle* obstacles, uint8_t obstacle_count);

 
uint8_t Player_CheckCollisions(Player* player, Obstacle* obstacles, uint8_t obstacle_count);

 
void Player_UpdateCooldown(Player* player);

 
void Player_Shoot(GameState* state);

#endif  