
#ifndef WHIRLPOOL_H
#define WHIRLPOOL_H

#include "game_config.h"
#include "game_types.h"
#include "utils.h"

 
typedef struct {
    Vector2 position;
    float radius;
    float rotation;
    uint8_t used_recently;
    uint16_t cooldown_timer;
    float animation_phase;
} Whirlpool;

 
struct WhirlpoolManager {
    Whirlpool whirlpools[WHIRLPOOL_MAX_COUNT];
    uint8_t whirlpool_count;
};

 
void WhirlpoolManager_Init(struct WhirlpoolManager* manager);

 
void WhirlpoolManager_Update(struct WhirlpoolManager* manager, GameState* state);

 
uint8_t WhirlpoolManager_Add(struct WhirlpoolManager* manager, float x, float y);

 
void WhirlpoolManager_Cleanup(struct WhirlpoolManager* manager, float threshold_y);

 
uint8_t Whirlpool_CollidesWith(Whirlpool* whirlpool, float x, float y, float radius);

 
Whirlpool* WhirlpoolManager_FindTarget(struct WhirlpoolManager* manager, Whirlpool* current, float world_top);

 
Whirlpool* WhirlpoolManager_CreateForTeleport(struct WhirlpoolManager* manager, 
                                             Whirlpool* current, 
                                             float world_top,
                                             Obstacle* obstacles,
                                             uint8_t obstacle_count);

 
void WhirlpoolManager_TeleportPlayer(struct WhirlpoolManager* manager, 
                                    Whirlpool* source, 
                                    Whirlpool* target, 
                                    Player* player);

#endif  