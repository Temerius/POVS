/* enemies.c - Логика врагов */

#include "game_config.h"
#include "enemies.h"
#include "utils.h"
#include <math.h>

void Enemies_Update(GameState* state) {
    // Обновление простых врагов
    for (uint8_t i = 0; i < state->enemy_simple_count; i++) {
        EnemySimple* enemy = &state->enemies_simple[i];
        
        if (!enemy->alive || !enemy->active) continue;
        
        // Активация врага при приближении к игроку
        if (!enemy->active && enemy->position.y > state->player.position.y + ENEMY_ACTIVATION_DISTANCE * SCREEN_HEIGHT) {
            enemy->active = 1;
            enemy->strategy = (Utils_RandomFloat() < ENEMY_SIMPLE_ATTACK_CHANCE) ? STRATEGY_ATTACK : STRATEGY_PATROL;
        }
        
        // Удаление врага, если он слишком далеко позади игрока
        if (enemy->position.y > state->player.position.y + ENEMY_DELETE_DISTANCE) {
            Enemies_RemoveSimple(state, i);
            i--;
            continue;
        }
        
        // Обновление AI
        EnemySimple_UpdateAI(enemy, &state->player);
        
        // Применение движения
        float angle_diff = enemy->target_angle - atan2f(enemy->velocity.y, enemy->velocity.x);
        angle_diff = Utils_NormalizeAngle(angle_diff);
        float turn_amount = angle_diff * ENEMY_SIMPLE_TURN_SMOOTHNESS;
        
        enemy->velocity.x = cosf(enemy->target_angle + turn_amount) * ENEMY_SIMPLE_BASE_SPEED;
        enemy->velocity.y = sinf(enemy->target_angle + turn_amount) * ENEMY_SIMPLE_BASE_SPEED;
        
        float prev_x = enemy->position.x;
        float prev_y = enemy->position.y;
        
        enemy->position.x += enemy->velocity.x;
        enemy->position.y += enemy->velocity.y;
        
        // Проверка коллизий с препятствиями
        if (Enemies_CheckCollision(state, enemy->position.x, enemy->position.y, enemy->radius)) {
            enemy->position.x = prev_x;
            enemy->position.y = prev_y;
            enemy->target_angle += Utils_DegToRad(Utils_RandomRange(90, 270));
        }
        
        // Ограничение по краям
        if (enemy->position.x < SHORE_EDGE_MARGIN - 80) {
            enemy->position.x = SHORE_EDGE_MARGIN - 80;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(30, 150));
        }
        else if (enemy->position.x > SCREEN_WIDTH - SHORE_EDGE_MARGIN + 80) {
            enemy->position.x = SCREEN_WIDTH - SHORE_EDGE_MARGIN + 80;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(210, 330));
        }
        
        // Обновление таймеров
        if (enemy->wander_timer > 0) {
            enemy->wander_timer--;
        }
        
        if (enemy->shoot_cooldown > 0) {
            enemy->shoot_cooldown--;
        }
        
        // Стрельба
        if (enemy->shoot_cooldown == 0 && Enemies_CanSeePlayer(enemy, &state->player)) {
            Enemies_ShootAtPlayer(state, enemy);
        }
    }
    
    // Обновление сложных врагов (аналогично, но с более сложной логикой)
    for (uint8_t i = 0; i < state->enemy_hard_count; i++) {
        EnemyHard* enemy = &state->enemies_hard[i];
        
        if (!enemy->alive || !enemy->active) continue;
        
        // Активация врага
        if (!enemy->active && enemy->position.y > state->player.position.y + ENEMY_ACTIVATION_DISTANCE * SCREEN_HEIGHT) {
            enemy->active = 1;
            enemy->strategy = (Utils_RandomFloat() < ENEMY_HARD_AGGRESSIVE_CHANCE) ? STRATEGY_AGGRESSIVE : STRATEGY_PATROL;
            
            if (enemy->strategy == STRATEGY_PATROL) {
                Enemies_GeneratePatrolPoints(enemy, &state->player);
            }
        }
        
        // Удаление врага
        if (enemy->position.y > state->player.position.y + ENEMY_DELETE_DISTANCE) {
            Enemies_RemoveHard(state, i);
            i--;
            continue;
        }
        
        // Обновление AI
        EnemyHard_UpdateAI(enemy, &state->player, state->obstacles, state->obstacle_count);
        
        // Применение движения
        float prev_x = enemy->position.x;
        float prev_y = enemy->position.y;
        
        enemy->position.x += cosf(enemy->target_angle) * ENEMY_HARD_BASE_SPEED;
        enemy->position.y += sinf(enemy->target_angle) * ENEMY_HARD_BASE_SPEED;
        
        // Проверка коллизий
        if (Enemies_CheckCollision(state, enemy->position.x, enemy->position.y, enemy->radius)) {
            enemy->position.x = prev_x;
            enemy->position.y = prev_y;
            enemy->target_angle += Utils_DegToRad(Utils_RandomRange(90, 270));
        }
        
        // Ограничение по краям
        if (enemy->position.x < SHORE_WIDTH) {
            enemy->position.x = SHORE_WIDTH;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(30, 150));
        }
        else if (enemy->position.x > SCREEN_WIDTH - SHORE_WIDTH) {
            enemy->position.x = SCREEN_WIDTH - SHORE_WIDTH;
            enemy->target_angle = Utils_DegToRad(Utils_RandomRange(210, 330));
        }
        
        // Обновление таймеров
        if (enemy->armor_timer > 0) {
            enemy->armor_timer--;
        }
        
        if (enemy->shoot_cooldown > 0) {
            enemy->shoot_cooldown--;
        }
        
        // Стрельба
        if (enemy->shoot_cooldown == 0 && Enemies_CanSeePlayerHard(enemy, &state->player)) {
            Enemies_ShootHardAtPlayer(state, enemy);
        }
    }
}

void EnemySimple_UpdateAI(EnemySimple* enemy, Player* player) {
    // Проверка видимости игрока
    uint8_t can_see_player = Enemies_CanSeePlayer(enemy, player);
    
    if (enemy->strategy == STRATEGY_ATTACK && can_see_player) {
        // Целевой угол - направление к игроку
        enemy->target_angle = atan2f(player->position.y - enemy->position.y, 
                                   player->position.x - enemy->position.x);
    }
    else {
        // Патрулирование
        enemy->wander_timer--;
        if (enemy->wander_timer == 0) {
            enemy->wander_timer = Utils_RandomRange(90, 180);
            enemy->wander_angle = Utils_RandomRangeFloat(-PI/6, PI/6);
        }
        
        enemy->target_angle = Utils_DegToRad(90) + enemy->wander_angle;
    }
}

void EnemyHard_UpdateAI(EnemyHard* enemy, Player* player, Obstacle* obstacles, uint8_t obstacle_count) {
    // Проверка видимости игрока
    uint8_t can_see_player = Enemies_CanSeePlayerHard(enemy, player);
    
    if (enemy->strategy == STRATEGY_AGGRESSIVE) {
        if (can_see_player) {
            // Предсказание движения игрока
            float predict_x = player->position.x + (player->hull_angle / 45) * 50;
            float predict_y = player->position.y - 50;
            
            enemy->target_angle = atan2f(predict_y - enemy->position.y, 
                                       predict_x - enemy->position.x);
            enemy->pursuit_timer = ENEMY_HARD_PURSUIT_TIMER;
            enemy->pursuit_direction = enemy->target_angle;
        }
        else if (enemy->pursuit_timer > 0) {
            enemy->pursuit_timer--;
            enemy->target_angle = enemy->pursuit_direction;
        }
        else {
            // Блуждание
            enemy->wander_timer--;
            if (enemy->wander_timer <= 0) {
                enemy->wander_timer = Utils_RandomRange(180, 300);
                enemy->wander_angle += Utils_RandomRangeFloat(-0.05f, 0.05f);
                enemy->wander_angle = Utils_Clamp(enemy->wander_angle, -PI/6, PI/6);
            }
            enemy->target_angle = Utils_DegToRad(90) + enemy->wander_angle;
        }
    }
    else { // STRATEGY_PATROL
        if (enemy->patrol_point_index >= enemy->patrol_points_count) {
            Enemies_GeneratePatrolPoints(enemy, player);
        }
        
        if (enemy->patrol_points_count > 0) {
            Vector2* target = &enemy->patrol_points[enemy->patrol_point_index];
            float dx = target->x - enemy->position.x;
            float dy = target->y - enemy->position.y;
            float distance = Utils_Distance(0, 0, dx, dy);
            
            if (distance < ENEMY_HARD_MIN_PATROL_DISTANCE) {
                enemy->patrol_point_index++;
                if (enemy->patrol_point_index >= enemy->patrol_points_count) {
                    Enemies_GeneratePatrolPoints(enemy, player);
                }
            }
            
            if (enemy->patrol_point_index < enemy->patrol_points_count) {
                target = &enemy->patrol_points[enemy->patrol_point_index];
                dx = target->x - enemy->position.x;
                dy = target->y - enemy->position.y;
                enemy->target_angle = atan2f(dy, dx);
            }
        }
    }
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
        
        // Избегаем близости к игроку
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
    
    // Добавляем финальную точку
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
    
    // Создание снаряда
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
    
    // Создание трех снарядов (веер)
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