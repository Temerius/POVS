/* player.c - Логика игрока (окончательная версия) */

#include "player.h"
#include "utils.h"
#include <math.h>

void Player_Update(Player* player, InputState* input, Obstacle* obstacles, uint8_t obstacle_count) {
    // Обработка поворота корпуса
    Player_HandleRotation(player, input);
    
    // Обработка движения и коллизий
    Player_HandleMovement(player, obstacles, obstacle_count);
    
    // Обновление таймера перезарядки
    Player_UpdateCooldown(player);
}

void Player_HandleRotation(Player* player, InputState* input) {
    if (Input_IsPressed(input, BTN_LEFT) && player->hull_angle > -PLAYER_MAX_ANGLE) {
        player->hull_angle -= PLAYER_ROTATION_SPEED;
    } 
    else if (Input_IsPressed(input, BTN_RIGHT) && player->hull_angle < PLAYER_MAX_ANGLE) {
        player->hull_angle += PLAYER_ROTATION_SPEED;
    }
    else {
        // Автовозврат к прямому курсу
        if (Utils_Abs(player->hull_angle) < PLAYER_AUTO_RETURN_SPEED) {
            player->hull_angle = 0.0f;
        }
        else if (player->hull_angle > 0) {
            player->hull_angle -= PLAYER_AUTO_RETURN_SPEED;
        }
        else {
            player->hull_angle += PLAYER_AUTO_RETURN_SPEED;
        }
    }
    
    // Ограничение угла
    player->hull_angle = Utils_Clamp(player->hull_angle, -PLAYER_MAX_ANGLE, PLAYER_MAX_ANGLE);
}

void Player_HandleMovement(Player* player, Obstacle* obstacles, uint8_t obstacle_count) {
    float old_x = player->position.x;
    float old_y = player->position.y;
    
    // Движение вперёд и боковое смещение
    player->position.y -= player->base_speed;
    float side_speed = (player->hull_angle / PLAYER_MAX_ANGLE) * PLAYER_SIDE_SPEED_MULTIPLIER;
    player->position.x += side_speed;
    
    // Ограничение краёв экрана
    player->position.x = Utils_Clamp(player->position.x, PLAYER_EDGE_MARGIN, SCREEN_WIDTH - PLAYER_EDGE_MARGIN);
    
    // Проверка коллизий
    if (Player_CheckCollisions(player, obstacles, obstacle_count)) {
        // Обработка столкновения
        player->health -= PLAYER_COLLISION_DAMAGE;
        player->position.x = old_x;
        player->position.y = old_y;
        player->position.y += PLAYER_COLLISION_PUSHBACK;
    }
}

uint8_t Player_CheckCollisions(Player* player, Obstacle* obstacles, uint8_t obstacle_count) {
    for (uint8_t i = 0; i < obstacle_count; i++) {
        if (!obstacles[i].active) continue;
        
        float dx = player->position.x - obstacles[i].position.x;
        float dy = player->position.y - obstacles[i].position.y;
        float dist = Utils_Distance(0, 0, dx, dy);
        
        if (dist < player->radius + obstacles[i].radius) {
            return 1;
        }
    }
    return 0;
}

void Player_UpdateCooldown(Player* player) {
    if (player->shoot_cooldown > 0) {
        player->shoot_cooldown--;
    }
}

void Player_Shoot(GameState* state) {
    if (state->player.shoot_cooldown > 0) {
        return;
    }
    
    state->player.shoot_cooldown = PLAYER_SHOOT_COOLDOWN;
    
    // Базовый угол - вверх
    float angle = Utils_DegToRad(-90.0f);
    
    // Корректировка угла в зависимости от поворота
    if (state->player.hull_angle > PLAYER_MIN_ANGLE_FOR_SIDE_SHOT) {
        angle += Utils_DegToRad(PLAYER_SHOOT_ANGLE_OFFSET);
    }
    else if (state->player.hull_angle < -PLAYER_MIN_ANGLE_FOR_SIDE_SHOT) {
        angle -= Utils_DegToRad(PLAYER_SHOOT_ANGLE_OFFSET);
    }
    
    // Добавление снаряда
    if (state->projectile_count < MAX_PROJECTILES) {
        Projectile* proj = &state->projectiles[state->projectile_count];
        proj->position.x = state->player.position.x;
        proj->position.y = state->player.position.y;
        proj->angle = angle;
        proj->speed = PROJECTILE_SPEED;
        proj->lifetime = PROJECTILE_LIFETIME;
        proj->radius = PROJECTILE_RADIUS;
        proj->is_player_shot = 1;
        proj->active = 1;
        
        state->projectile_count++;
    }
}