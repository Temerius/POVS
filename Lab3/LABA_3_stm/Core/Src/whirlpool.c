
#include "whirlpool.h"
#include <string.h>
#include <math.h>

void WhirlpoolManager_Init(struct WhirlpoolManager* manager) {
    memset(manager->whirlpools, 0, sizeof(manager->whirlpools));
    manager->whirlpool_count = 0;
}

void WhirlpoolManager_Update(struct WhirlpoolManager* manager, GameState* state) {
     
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        Whirlpool* whirlpool = &manager->whirlpools[i];
        
         
        whirlpool->rotation = fmodf(whirlpool->rotation + WHIRLPOOL_ROTATION_SPEED, 360.0f);
        whirlpool->animation_phase = fmodf(whirlpool->animation_phase + WHIRLPOOL_ANIMATION_SPEED, 2.0f * PI);
        
         
        if (whirlpool->cooldown_timer > 0) {
            whirlpool->cooldown_timer--;
            if (whirlpool->cooldown_timer == 0) {
                whirlpool->used_recently = 0;
            }
        }
    }
    
     
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        Whirlpool* whirlpool = &manager->whirlpools[i];
        
         
        if (whirlpool->used_recently) {
            continue;
        }
        
         
        float dx = state->player.position.x - whirlpool->position.x;
        float dy = state->player.position.y - whirlpool->position.y;
        float dist = sqrtf(dx*dx + dy*dy);
        
         
        if (dist < whirlpool->radius + COLLISION_RADIUS_PLAYER) {
             
            Whirlpool* target = WhirlpoolManager_FindTarget(manager, whirlpool, state->world_top);
            
             
            if (!target && manager->whirlpool_count < WHIRLPOOL_MAX_COUNT) {
                target = WhirlpoolManager_CreateForTeleport(manager, 
                                                          whirlpool, 
                                                          state->world_top,
                                                          state->obstacles,
                                                          state->obstacle_count);
            }
            
             
            if (target) {
                WhirlpoolManager_TeleportPlayer(manager, whirlpool, target, &state->player);
                return;  
            }
        }
    }
}

uint8_t WhirlpoolManager_Add(struct WhirlpoolManager* manager, float x, float y) {
    if (manager->whirlpool_count >= WHIRLPOOL_MAX_COUNT) {
        return 0;
    }
    
    Whirlpool* whirlpool = &manager->whirlpools[manager->whirlpool_count];
    whirlpool->position.x = x;
    whirlpool->position.y = y;
    whirlpool->radius = WHIRLPOOL_RADIUS;
    whirlpool->rotation = 0.0f;
    whirlpool->used_recently = 0;
    whirlpool->cooldown_timer = 0;
    whirlpool->animation_phase = 0.0f;
    
    manager->whirlpool_count++;
    return 1;
}

void WhirlpoolManager_Cleanup(struct WhirlpoolManager* manager, float threshold_y) {
     
     
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        if (manager->whirlpools[i].position.y > threshold_y) {
             
            if (i < manager->whirlpool_count - 1) {
                manager->whirlpools[i] = manager->whirlpools[manager->whirlpool_count - 1];
            }
            manager->whirlpool_count--;
            i--;  
        }
    }
}

uint8_t Whirlpool_CollidesWith(Whirlpool* whirlpool, float x, float y, float radius) {
     
    if (whirlpool->used_recently) {
        return 0;
    }
    
    float dx = x - whirlpool->position.x;
    float dy = y - whirlpool->position.y;
    float dist = Utils_Distance(0, 0, dx, dy);
    
    return (dist < whirlpool->radius + radius);
}

Whirlpool* WhirlpoolManager_FindTarget(struct WhirlpoolManager* manager, Whirlpool* current, float world_top) {
    Whirlpool* best_candidate = NULL;
    float best_score = 0;
    
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        Whirlpool* candidate = &manager->whirlpools[i];
        
         
        if (candidate == current || candidate->used_recently) {
            continue;
        }
        
         
        float distance = current->position.y - candidate->position.y;
        
         
         
         
         
        if (distance >= WHIRLPOOL_TELEPORT_DISTANCE && 
            distance < WHIRLPOOL_TELEPORT_DISTANCE * 2.0f &&
            candidate->position.y < world_top) {
            
             
            float score = fabsf(distance - WHIRLPOOL_TELEPORT_DISTANCE);
            
             
            if (!best_candidate || score < best_score) {
                best_candidate = candidate;
                best_score = score;
            }
        }
    }
    
    return best_candidate;
}

Whirlpool* WhirlpoolManager_CreateForTeleport(struct WhirlpoolManager* manager, 
                                            Whirlpool* current, 
                                            float world_top,
                                            Obstacle* obstacles,
                                            uint8_t obstacle_count) {
     
    if (manager->whirlpool_count >= WHIRLPOOL_MAX_COUNT) {
        return NULL;
    }
    
     
    for (uint8_t attempt = 0; attempt < WHIRLPOOL_PLACEMENT_ATTEMPTS; attempt++) {
         
        float new_y = current->position.y - WHIRLPOOL_TELEPORT_DISTANCE - 
                     Utils_RandomRangeFloat(0, 500);
        float new_x = Utils_RandomRangeFloat(WHIRLPOOL_EDGE_MARGIN, 
                                            SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN);
        
         
        uint8_t safe = 1;
        
         
        for (uint8_t i = 0; i < obstacle_count; i++) {
            if (!obstacles[i].active) continue;
            
            float dx = new_x - obstacles[i].position.x;
            float dy = new_y - obstacles[i].position.y;
            float dist = Utils_Distance(0, 0, dx, dy);
            
            if (dist < obstacles[i].radius + WHIRLPOOL_ISLAND_SAFE_DISTANCE) {
                safe = 0;
                break;
            }
        }
        
         
        if (new_y < world_top) {
            safe = 0;
        }
        
         
        if (safe) {
            for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
                float dx = new_x - manager->whirlpools[i].position.x;
                float dy = new_y - manager->whirlpools[i].position.y;
                float dist = Utils_Distance(0, 0, dx, dy);
                
                if (dist < WHIRLPOOL_MIN_DISTANCE * 2.5f) {
                    safe = 0;
                    break;
                }
            }
        }
        
         
        if (safe) {
            Whirlpool* new_whirlpool = &manager->whirlpools[manager->whirlpool_count];
            new_whirlpool->position.x = new_x;
            new_whirlpool->position.y = new_y;
            new_whirlpool->radius = WHIRLPOOL_RADIUS;
            new_whirlpool->rotation = 0.0f;
            new_whirlpool->used_recently = 0;
            new_whirlpool->cooldown_timer = 0;
            new_whirlpool->animation_phase = 0.0f;
            
            manager->whirlpool_count++;
            return new_whirlpool;
        }
    }
    
     
     
    float new_y = current->position.y - WHIRLPOOL_TELEPORT_DISTANCE - 
                 Utils_RandomRangeFloat(0, 500);
    float new_x = Utils_RandomRangeFloat(WHIRLPOOL_EDGE_MARGIN, 
                                        SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN);
    
     
    if (new_y < world_top) {
        new_y = world_top + 100;
    }
    
    Whirlpool* new_whirlpool = &manager->whirlpools[manager->whirlpool_count];
    new_whirlpool->position.x = new_x;
    new_whirlpool->position.y = new_y;
    new_whirlpool->radius = WHIRLPOOL_RADIUS;
    new_whirlpool->rotation = 0.0f;
    new_whirlpool->used_recently = 0;
    new_whirlpool->cooldown_timer = 0;
    new_whirlpool->animation_phase = 0.0f;
    
    manager->whirlpool_count++;
    return new_whirlpool;
}

void WhirlpoolManager_TeleportPlayer(struct WhirlpoolManager* manager, 
                                   Whirlpool* source, 
                                   Whirlpool* target, 
                                   Player* player) {
     
    player->position.x = target->position.x;
    player->position.y = target->position.y + WHIRLPOOL_PLAYER_OFFSET;
    
     
    source->used_recently = 1;
    source->cooldown_timer = WHIRLPOOL_COOLDOWN;
    
    target->used_recently = 1;
    target->cooldown_timer = WHIRLPOOL_COOLDOWN;
}