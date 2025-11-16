
#ifndef PROJECTILES_H
#define PROJECTILES_H

#include "game_types.h"

 
void Projectiles_Update(GameState* state);

 
void Projectiles_Remove(GameState* state, uint8_t index);

 
uint8_t Projectile_CollidesWith(Projectile* proj, Obstacle* obstacle);

#endif  