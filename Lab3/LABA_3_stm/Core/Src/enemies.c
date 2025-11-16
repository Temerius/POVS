
#include "game_config.h"
#include "enemies.h"
#include "utils.h"
#include <math.h>

void Enemies_Update(GameState* state) {
     
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
        EnemySimple* enemy = &state->enemies_simple[i];
        
        if (!enemy->alive) continue;
        
         
        if (!enemy->active && enemy->position.y > state->player.position.y + ENEMY_ACTIVATION_DISTANCE * SCREEN_HEIGHT) {
            enemy->active = 1;
             
            enemy->strategy = (Utils_RandomFloat() < ENEMY_SIMPLE_ATTACK_CHANCE) ? STRATEGY_ATTACK : STRATEGY_PATROL;
            
             
            enemy->velocity.x = 0;
            enemy->velocity.y = ENEMY_SIMPLE_BASE_SPEED;
            enemy->target_angle = Utils_DegToRad(90);  
        }
        
        if (!enemy->active) continue;
        
         
        if (enemy->position.y > state->player.position.y + ENEMY_DELETE_DISTANCE) {
            Enemies_RemoveSimple(state, i);
            i--;
            continue;
        }
        
         
        EnemySimple_UpdateAI(enemy, &state->player, state->obstacles, state->obstacle_count);
        
         
        uint8_t can_see_player = Enemies_CanSeePlayer(enemy, &state->player);
        
         
        float base_target_angle;
        
        if (enemy->strategy == STRATEGY_ATTACK && can_see_player) {
             
            float dx = state->player.position.x - enemy->position.x;
            float dy = state->player.position.y - enemy->position.y;
            base_target_angle = atan2f(dy, dx);
        } else {
             
            enemy->wander_timer--;
            if (enemy->wander_timer <= 0) {
                enemy->wander_timer = Utils_RandomRange(90, 180);
                enemy->wander_angle = Utils_RandomRangeFloat(-PI/6, PI/6);
            }
            base_target_angle = Utils_DegToRad(90) + enemy->wander_angle;
        }
        
         
        float avoid_vector_x = 0;
        float avoid_vector_y = 0;
        
        int8_t angle_offsets[] = {-30, 0, 30};
        for (uint8_t j = 0; j < 3; j++) {
            float check_angle = enemy->target_angle + Utils_DegToRad(angle_offsets[j]);
            float check_dist = ENEMY_SIMPLE_DETECTION_RANGE;
            
            float check_x = enemy->position.x + cosf(check_angle) * check_dist;
            float check_y = enemy->position.y + sinf(check_angle) * check_dist;
            
             
            for (uint8_t k = 0; k < state->obstacle_count; k++) {
                if (!state->obstacles[k].active) continue;
                
                float dx_check = check_x - state->obstacles[k].position.x;
                float dy_check = check_y - state->obstacles[k].position.y;
                float dist_check = sqrtf(dx_check*dx_check + dy_check*dy_check);
                
                if (dist_check < state->obstacles[k].radius + 20) {
                    float dx = enemy->position.x - state->obstacles[k].position.x;
                    float dy = enemy->position.y - state->obstacles[k].position.y;
                    float dist = sqrtf(dx*dx + dy*dy);
                    
                    if (dist > 0) {
                        float strength = 1.0f / fmaxf(dist / 100.0f, 0.5f);
                        avoid_vector_x += (dx / dist) * strength;
                        avoid_vector_y += (dy / dist) * strength;
                    }
                }
            }
            
             
            if (check_x < SHORE_WIDTH + 20) {
                avoid_vector_x += 1.5f;
            } else if (check_x > SCREEN_WIDTH - SHORE_WIDTH - 20) {
                avoid_vector_x -= 1.5f;
            }
        }
        
         
        float avoid_magnitude = sqrtf(avoid_vector_x*avoid_vector_x + avoid_vector_y*avoid_vector_y);
        
        if (avoid_magnitude > 0.1f) {
            float avoid_angle = atan2f(avoid_vector_y, avoid_vector_x);
            enemy->target_angle = avoid_angle;
        } else {
            enemy->target_angle = base_target_angle;
        }
        
         
        float current_angle = atan2f(enemy->velocity.y, enemy->velocity.x);
        float angle_diff = enemy->target_angle - current_angle;
        angle_diff = Utils_NormalizeAngle(angle_diff);
        
        float turn_amount = angle_diff * ENEMY_SIMPLE_TURN_SMOOTHNESS;
        float new_angle = current_angle + turn_amount;
        
         
        enemy->velocity.x = cosf(new_angle) * ENEMY_SIMPLE_BASE_SPEED;
        enemy->velocity.y = sinf(new_angle) * ENEMY_SIMPLE_BASE_SPEED;
        
         
        if (fabsf(enemy->velocity.x) > fabsf(enemy->velocity.y) * 0.7f) {
            enemy->current_direction = (enemy->velocity.x > 0) ? 1 : 3;  
        } else {
            enemy->current_direction = (enemy->velocity.y > 0) ? 2 : 0;  
        }
        
         
        float prev_x = enemy->position.x;
        float prev_y = enemy->position.y;
        
        enemy->position.x += enemy->velocity.x;
        enemy->position.y += enemy->velocity.y;
        
         
        if (Enemies_CheckCollision(state, enemy->position.x, enemy->position.y, enemy->radius)) {
            enemy->position.x = prev_x;
            enemy->position.y = prev_y;
             
            enemy->target_angle += Utils_DegToRad(Utils_RandomRange(90, 270));
            enemy->target_angle = Utils_NormalizeAngle(enemy->target_angle);
        }
        
         
        if (enemy->position.x < SHORE_EDGE_MARGIN - 80) {
            enemy->position.x = SHORE_EDGE_MARGIN - 80;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(30, 150));
        } else if (enemy->position.x > SCREEN_WIDTH - SHORE_EDGE_MARGIN + 80) {
            enemy->position.x = SCREEN_WIDTH - SHORE_EDGE_MARGIN + 80;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(210, 330));
        }
        
         
        if (enemy->shoot_cooldown > 0) {
            enemy->shoot_cooldown--;
        }
        
         
        if (enemy->shoot_cooldown == 0 && can_see_player) {
            Enemies_ShootAtPlayer(state, enemy);
        }
    }
    
     
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        EnemyHard* enemy = &state->enemies_hard[i];
        
        if (!enemy->alive) continue;
        
         
        if (!enemy->active && enemy->position.y > state->player.position.y + ENEMY_ACTIVATION_DISTANCE * SCREEN_HEIGHT) {
            enemy->active = 1;
            enemy->strategy = (Utils_RandomFloat() < ENEMY_HARD_AGGRESSIVE_CHANCE) ? STRATEGY_AGGRESSIVE : STRATEGY_PATROL;
            
            enemy->velocity.x = 0;
            enemy->velocity.y = ENEMY_HARD_BASE_SPEED;
            enemy->target_angle = Utils_DegToRad(90);
            
            if (enemy->strategy == STRATEGY_PATROL) {
                Enemies_GeneratePatrolPoints(enemy, &state->player);
            }
        }
        
        if (!enemy->active) continue;
        
         
        if (enemy->position.y > state->player.position.y + ENEMY_DELETE_DISTANCE) {
            Enemies_RemoveHard(state, i);
            i--;
            continue;
        }
        
         
        EnemyHard_UpdateAI(enemy, &state->player, state->obstacles, state->obstacle_count);
        
         
        uint8_t can_see_player = Enemies_CanSeePlayerHard(enemy, &state->player);
        
         
        float base_target_angle;
        
        if (enemy->strategy == STRATEGY_AGGRESSIVE) {
            if (can_see_player) {
                 
                float predict_x = state->player.position.x + (state->player.hull_angle / 45) * 50;
                float predict_y = state->player.position.y - 50;
                
                base_target_angle = atan2f(predict_y - enemy->position.y, 
                                           predict_x - enemy->position.x);
                enemy->pursuit_timer = ENEMY_HARD_PURSUIT_TIMER;
                enemy->pursuit_direction = base_target_angle;
            } else if (enemy->pursuit_timer > 0) {
                enemy->pursuit_timer--;
                base_target_angle = enemy->pursuit_direction;
            } else {
                enemy->wander_timer--;
                if (enemy->wander_timer <= 0) {
                    enemy->wander_timer = Utils_RandomRange(180, 300);
                    enemy->wander_angle += Utils_RandomRangeFloat(-0.05f, 0.05f);
                    enemy->wander_angle = Utils_Clamp(enemy->wander_angle, -PI/6, PI/6);
                }
                base_target_angle = Utils_DegToRad(90) + enemy->wander_angle;
            }
        } else {  
            if (enemy->patrol_point_index >= enemy->patrol_points_count) {
                Enemies_GeneratePatrolPoints(enemy, &state->player);
            }
            
            if (enemy->patrol_points_count > 0) {
                Vector2* target = &enemy->patrol_points[enemy->patrol_point_index];
                float dx = target->x - enemy->position.x;
                float dy = target->y - enemy->position.y;
                float distance = sqrtf(dx*dx + dy*dy);
                
                if (distance < ENEMY_HARD_MIN_PATROL_DISTANCE) {
                    enemy->patrol_point_index++;
                    if (enemy->patrol_point_index >= enemy->patrol_points_count) {
                        Enemies_GeneratePatrolPoints(enemy, &state->player);
                    }
                }
                
                if (enemy->patrol_point_index < enemy->patrol_points_count) {
                    target = &enemy->patrol_points[enemy->patrol_point_index];
                    dx = target->x - enemy->position.x;
                    dy = target->y - enemy->position.y;
                    base_target_angle = atan2f(dy, dx);
                } else {
                    base_target_angle = Utils_DegToRad(90);
                }
            } else {
                base_target_angle = Utils_DegToRad(90);
            }
        }
        
         
        float avoid_vector_x = 0;
        float avoid_vector_y = 0;
        
        int8_t angle_offsets_hard[] = {-45, -22, 0, 22, 45};
        for (uint8_t j = 0; j < 5; j++) {
            float check_angle = enemy->target_angle + Utils_DegToRad(angle_offsets_hard[j]);
            float check_dist = ENEMY_HARD_DETECTION_RANGE;
            
            float check_x = enemy->position.x + cosf(check_angle) * check_dist;
            float check_y = enemy->position.y + sinf(check_angle) * check_dist;
            
            for (uint8_t k = 0; k < state->obstacle_count; k++) {
                if (!state->obstacles[k].active) continue;
                
                float dx_check = check_x - state->obstacles[k].position.x;
                float dy_check = check_y - state->obstacles[k].position.y;
                float dist_check = sqrtf(dx_check*dx_check + dy_check*dy_check);
                
                if (dist_check < state->obstacles[k].radius + 30) {
                    float dx = enemy->position.x - state->obstacles[k].position.x;
                    float dy = enemy->position.y - state->obstacles[k].position.y;
                    float dist = sqrtf(dx*dx + dy*dy);
                    
                    if (dist > 0) {
                        float strength = 1.2f / fmaxf(dist / 100.0f, 0.3f);
                        avoid_vector_x += (dx / dist) * strength;
                        avoid_vector_y += (dy / dist) * strength;
                    }
                }
            }
            
            if (check_x < SHORE_WIDTH + 30) {
                avoid_vector_x += 2.0f;
            } else if (check_x > SCREEN_WIDTH - SHORE_WIDTH - 30) {
                avoid_vector_x -= 2.0f;
            }
        }
        
         
        float avoid_magnitude = sqrtf(avoid_vector_x*avoid_vector_x + avoid_vector_y*avoid_vector_y);
        
        if (avoid_magnitude > 0.1f) {
            float avoid_angle = atan2f(avoid_vector_y, avoid_vector_x);
            enemy->target_angle = avoid_angle;
        } else {
            enemy->target_angle = base_target_angle;
        }
        
         
        float current_angle = atan2f(enemy->velocity.y, enemy->velocity.x);
        float angle_diff = enemy->target_angle - current_angle;
        angle_diff = Utils_NormalizeAngle(angle_diff);
        
        float turn_amount = angle_diff * ENEMY_HARD_TURN_SMOOTHNESS;
        float new_angle = current_angle + turn_amount;
        
        enemy->velocity.x = cosf(new_angle) * ENEMY_HARD_BASE_SPEED;
        enemy->velocity.y = sinf(new_angle) * ENEMY_HARD_BASE_SPEED;
        
         
        if (fabsf(enemy->velocity.x) > fabsf(enemy->velocity.y) * 0.7f) {
            enemy->current_direction = (enemy->velocity.x > 0) ? 1 : 3;
        } else {
            enemy->current_direction = (enemy->velocity.y > 0) ? 2 : 0;
        }
        
         
        float prev_x = enemy->position.x;
        float prev_y = enemy->position.y;
        
        enemy->position.x += enemy->velocity.x;
        enemy->position.y += enemy->velocity.y;
        
        if (Enemies_CheckCollision(state, enemy->position.x, enemy->position.y, enemy->radius)) {
            enemy->position.x = prev_x;
            enemy->position.y = prev_y;
            enemy->target_angle += Utils_DegToRad(Utils_RandomRange(90, 270));
            enemy->target_angle = Utils_NormalizeAngle(enemy->target_angle);
        }
        
         
        if (enemy->position.x < SHORE_WIDTH) {
            enemy->position.x = SHORE_WIDTH;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(30, 150));
        } else if (enemy->position.x > SCREEN_WIDTH - SHORE_WIDTH) {
            enemy->position.x = SCREEN_WIDTH - SHORE_WIDTH;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(210, 330));
        }
        
         
        if (enemy->armor_timer > 0) {
            enemy->armor_timer--;
        }
        
        if (enemy->shoot_cooldown > 0) {
            enemy->shoot_cooldown--;
        }
        
         
        if (enemy->shoot_cooldown == 0 && can_see_player) {
            Enemies_ShootHardAtPlayer(state, enemy);
        }
    }
}

void EnemySimple_UpdateAI(EnemySimple* enemy, Player* player, Obstacle* obstacles, uint8_t obstacle_count) {
     
     
}

void EnemyHard_UpdateAI(EnemyHard* enemy, Player* player, Obstacle* obstacles, uint8_t obstacle_count) {
     
     
}

void Enemies_GeneratePatrolPoints(EnemyHard* enemy, Player* player) {
    enemy->patrol_point_index = 0;
    enemy->patrol_points_count = 0;
    
    float start_x = enemy->position.x;
    float start_y = enemy->position.y + 200;
    
    uint8_t num_points = Utils_RandomRange(2, 4);
    
    for (uint8_t i = 0; i < num_points && i < ENEMY_HARD_PATROL_POINTS_MAX; i++) {
        float y_offset = Utils_RandomRange(400, 800);
        float x_offset = Utils_RandomRangeFloat(-300, 300);
        
        float x = Utils_Clamp(start_x + x_offset, 300, SCREEN_WIDTH - 300);
        float y = start_y + y_offset;
        
         
        float dx = x - player->position.x;
        float dy = y - player->position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < 300) {
            if (dist > 0) {
                x += (dx / dist) * 300;
                y += (dy / dist) * 300;
            }
        }
        
        enemy->patrol_points[i].x = x;
        enemy->patrol_points[i].y = y;
        
        start_x = x;
        start_y = y;
        enemy->patrol_points_count++;
    }
    
     
    if (enemy->patrol_points_count < ENEMY_HARD_PATROL_POINTS_MAX) {
        float final_x = Utils_RandomRange(300, SCREEN_WIDTH - 300);
        float final_y = start_y + Utils_RandomRange(400, 800);
        
        enemy->patrol_points[enemy->patrol_points_count].x = final_x;
        enemy->patrol_points[enemy->patrol_points_count].y = final_y;
        enemy->patrol_points_count++;
    }
}

uint8_t Enemies_CanSeePlayer(EnemySimple* enemy, Player* player) {
    float dx = fabsf(enemy->position.x - player->position.x);
    float dy = fabsf(enemy->position.y - player->position.y);
    
    return (dx < ENEMY_SIMPLE_CAN_SEE_RANGE_X && dy < ENEMY_SIMPLE_CAN_SEE_RANGE_Y);
}

uint8_t Enemies_CanSeePlayerHard(EnemyHard* enemy, Player* player) {
    float dx = fabsf(enemy->position.x - player->position.x);
    float dy = fabsf(enemy->position.y - player->position.y);
    
    return (dx < ENEMY_HARD_CAN_SEE_RANGE_X && dy < ENEMY_HARD_CAN_SEE_RANGE_Y);
}

void Enemies_ShootAtPlayer(GameState* state, EnemySimple* enemy) {
    enemy->shoot_cooldown = enemy->shoot_delay;
    
    if (state->projectile_count < MAX_PROJECTILES) {
        float dx = state->player.position.x - enemy->position.x;
        float dy = state->player.position.y - enemy->position.y;
        float angle = atan2f(dy, dx);
        
        Projectile* proj = &state->projectiles[state->projectile_count];
        proj->position.x = enemy->position.x;
        proj->position.y = enemy->position.y;
        proj->angle = angle;
        proj->speed = ENEMY_SIMPLE_PROJECTILE_SPEED;
        proj->lifetime = PROJECTILE_LIFETIME;
        proj->radius = PROJECTILE_RADIUS;
        proj->is_player_shot = 0;
        proj->active = 1;
        
        state->projectile_count++;
    }
}

void Enemies_ShootHardAtPlayer(GameState* state, EnemyHard* enemy) {
    enemy->shoot_cooldown = enemy->shoot_delay;
    
    float base_angle = atan2f(state->player.position.y - enemy->position.y, 
                             state->player.position.x - enemy->position.x);
    
     
    for (int i = -1; i <= 1; i++) {
        if (state->projectile_count >= MAX_PROJECTILES) break;
        
        float angle = base_angle + i * ENEMY_HARD_PROJECTILE_SPREAD;
        
        Projectile* proj = &state->projectiles[state->projectile_count];
        proj->position.x = enemy->position.x;
        proj->position.y = enemy->position.y;
        proj->angle = angle;
        proj->speed = ENEMY_HARD_PROJECTILE_SPEED;
        proj->lifetime = PROJECTILE_LIFETIME;
        proj->radius = PROJECTILE_RADIUS;
        proj->is_player_shot = 0;
        proj->active = 1;
        
        state->projectile_count++;
    }
}

uint8_t Enemies_CheckCollision(GameState* state, float x, float y, float radius) {
    for (uint8_t i = 0; i < state->obstacle_count; i++) {
        if (!state->obstacles[i].active) continue;
        
        float dx = x - state->obstacles[i].position.x;
        float dy = y - state->obstacles[i].position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < radius + state->obstacles[i].radius) {
            return 1;
        }
    }
    return 0;
}

void Enemies_RemoveSimple(GameState* state, uint8_t index) {
    if (index < state->enemy_simple_count - 1) {
        state->enemies_simple[index] = state->enemies_simple[state->enemy_simple_count - 1];
    }
    state->enemy_simple_count--;
}

void Enemies_RemoveHard(GameState* state, uint8_t index) {
    if (index < state->enemy_hard_count - 1) {
        state->enemies_hard[index] = state->enemies_hard[state->enemy_hard_count - 1];
    }
    state->enemy_hard_count--;
}