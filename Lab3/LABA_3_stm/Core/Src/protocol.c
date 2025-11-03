/* protocol.c - Реализация протокола (окончательная версия) */

#include "protocol.h"
#include "cleanup.h"
#include "whirlpool.h"
#include <string.h>

static UART_HandleTypeDef* huart_handle = NULL;

void Protocol_Init(UART_HandleTypeDef* huart) {
    huart_handle = huart;
    
    // Запускаем приём DMA в циклическом режиме
    HAL_UART_Receive_DMA(huart, rx_buffer, RX_BUFFER_SIZE);
}

uint16_t Protocol_CalculateChecksum(uint8_t* data, uint16_t len) {
    uint16_t sum = 0;
    for (uint16_t i = 0; i < len; i++) {
        sum += data[i];
    }
    return sum;
}

void Protocol_SendGameState(GameState* state) {
    if (uart_tx_busy || huart_handle == NULL) {
        return;
    }
    
    GameStatePacket packet;
    memset(&packet, 0, sizeof(packet));
    
    packet.header = PKT_GAME_STATE;
    
    // Данные игрока
    packet.player_x = state->player.position.x;
    packet.player_y = state->player.position.y;
    packet.player_angle = state->player.hull_angle;
    packet.player_health = state->player.health;
    packet.player_score = (uint16_t)(state->player.score & 0xFFFF);
    
    // Враги (собираем простых и сложных)
    packet.enemy_count = 0;
    
    for (uint8_t i = 0; i < MAX_ENEMIES_SIMPLE && packet.enemy_count < 15; i++) {
        if (state->enemies_simple[i].alive && state->enemies_simple[i].active) {
            packet.enemies[packet.enemy_count].type = 0;
            packet.enemies[packet.enemy_count].x = state->enemies_simple[i].position.x;
            packet.enemies[packet.enemy_count].y = state->enemies_simple[i].position.y;
            packet.enemies[packet.enemy_count].health = state->enemies_simple[i].health;
            packet.enemy_count++;
        }
    }
    
    for (uint8_t i = 0; i < MAX_ENEMIES_HARD && packet.enemy_count < 15; i++) {
        if (state->enemies_hard[i].alive && state->enemies_hard[i].active) {
            packet.enemies[packet.enemy_count].type = 1;
            packet.enemies[packet.enemy_count].x = state->enemies_hard[i].position.x;
            packet.enemies[packet.enemy_count].y = state->enemies_hard[i].position.y;
            packet.enemies[packet.enemy_count].health = state->enemies_hard[i].health;
            packet.enemy_count++;
        }
    }
    
    // Снаряды (максимум 30)
    packet.projectile_count = 0;
    for (uint8_t i = 0; i < MAX_PROJECTILES && packet.projectile_count < 30; i++) {
        if (state->projectiles[i].active) {
            packet.projectiles[packet.projectile_count].x = state->projectiles[i].position.x;
            packet.projectiles[packet.projectile_count].y = state->projectiles[i].position.y;
            packet.projectiles[packet.projectile_count].is_player_shot = state->projectiles[i].is_player_shot;
            packet.projectile_count++;
        }
    }
    
    // Водовороты
    if (state->whirlpool_manager) {
        packet.whirlpool_count = state->whirlpool_manager->whirlpool_count;
        for (uint8_t i = 0; i < packet.whirlpool_count; i++) {
            Whirlpool* whirlpool = &state->whirlpool_manager->whirlpools[i];
            packet.whirlpools[i].x = whirlpool->position.x;
            packet.whirlpools[i].y = whirlpool->position.y;
            packet.whirlpools[i].used = whirlpool->used_recently;
        }
    } else {
        packet.whirlpool_count = 0;
    }
    
    packet.camera_y = state->camera_y;
    
    // Контрольная сумма
    packet.checksum = Protocol_CalculateChecksum((uint8_t*)&packet, sizeof(packet) - 2);
    
    // Отправка через DMA
    uart_tx_busy = 1;
    HAL_UART_Transmit_DMA(huart_handle, (uint8_t*)&packet, sizeof(packet));
}

void Protocol_ProcessIncoming(GameState* state) {
    // Простой парсер - ищем пакеты в буфере
    for (uint16_t i = 0; i < RX_BUFFER_SIZE - 1; i++) {
        uint8_t header = rx_buffer[i];
        
        switch (header) {
            case PKT_ADD_ENEMY: {
                if (i + sizeof(AddEnemyPacket) <= RX_BUFFER_SIZE) {
                    AddEnemyPacket* packet = (AddEnemyPacket*)&rx_buffer[i];
                    
                    // Проверка контрольной суммы
                    uint16_t checksum = Protocol_CalculateChecksum(rx_buffer + i, sizeof(AddEnemyPacket) - 2);
                    if (checksum == packet->checksum) {
                        // Добавление врага
                        if (packet->type == 0 && state->enemy_simple_count < MAX_ENEMIES_SIMPLE) {
                            EnemySimple* enemy = &state->enemies_simple[state->enemy_simple_count];
                            
                            enemy->position.x = packet->x;
                            enemy->position.y = packet->y;
                            enemy->initial_y = packet->y;
                            enemy->health = ENEMY_SIMPLE_HEALTH;
                            enemy->max_health = ENEMY_SIMPLE_HEALTH;
                            enemy->shoot_cooldown = 0;
                            enemy->shoot_delay = ENEMY_SIMPLE_SHOOT_DELAY;
                            enemy->radius = COLLISION_RADIUS_ENEMY_SIMPLE;
                            enemy->points = ENEMY_SIMPLE_POINTS;
                            enemy->active = 0; // Активируется при приближении к игроку
                            enemy->alive = 1;
                            enemy->wander_angle = 0;
                            enemy->wander_timer = 0;
                            enemy->strategy = STRATEGY_ATTACK;
                            
                            state->enemy_simple_count++;
                        }
                        else if (packet->type == 1 && state->enemy_hard_count < MAX_ENEMIES_HARD) {
                            EnemyHard* enemy = &state->enemies_hard[state->enemy_hard_count];
                            
                            enemy->position.x = packet->x;
                            enemy->position.y = packet->y;
                            enemy->initial_y = packet->y;
                            enemy->health = ENEMY_HARD_HEALTH;
                            enemy->max_health = ENEMY_HARD_HEALTH;
                            enemy->shoot_cooldown = 0;
                            enemy->shoot_delay = ENEMY_HARD_SHOOT_DELAY;
                            enemy->radius = COLLISION_RADIUS_ENEMY_HARD;
                            enemy->points = ENEMY_HARD_POINTS;
                            enemy->armor_timer = 0;
                            enemy->active = 0;
                            enemy->alive = 1;
                            enemy->wander_angle = 0;
                            enemy->wander_timer = 0;
                            enemy->pursuit_timer = 0;
                            enemy->pursuit_direction = 0;
                            enemy->patrol_point_index = 0;
                            enemy->patrol_points_count = 0;
                            enemy->strategy = STRATEGY_AGGRESSIVE;
                            
                            state->enemy_hard_count++;
                        }
                        
                        // Сдвигаем указатель за обработанный пакет
                        i += sizeof(AddEnemyPacket) - 1;
                    }
                }
                break;
            }
            
            case PKT_ADD_OBSTACLE: {
                if (i + sizeof(AddObstaclePacket) <= RX_BUFFER_SIZE) {
                    AddObstaclePacket* packet = (AddObstaclePacket*)&rx_buffer[i];
                    
                    // Проверка контрольной суммы
                    uint16_t checksum = Protocol_CalculateChecksum(rx_buffer + i, sizeof(AddObstaclePacket) - 2);
                    if (checksum == packet->checksum) {
                        // Добавление препятствия
                        if (state->obstacle_count < MAX_OBSTACLES) {
                            Obstacle* obstacle = &state->obstacles[state->obstacle_count];
                            
                            obstacle->position.x = packet->x;
                            obstacle->position.y = packet->y;
                            obstacle->radius = packet->radius;
                            obstacle->type = (ObstacleType)packet->type;
                            obstacle->active = 1;
                            
                            state->obstacle_count++;
                        }
                        
                        // Сдвигаем указатель за обработанный пакет
                        i += sizeof(AddObstaclePacket) - 1;
                    }
                }
                break;
            }
            
            case PKT_ADD_WHIRLPOOL: {
                if (i + sizeof(AddWhirlpoolPacket) <= RX_BUFFER_SIZE) {
                    AddWhirlpoolPacket* packet = (AddWhirlpoolPacket*)&rx_buffer[i];
                    
                    // Проверка контрольной суммы
                    uint16_t checksum = Protocol_CalculateChecksum(rx_buffer + i, sizeof(AddWhirlpoolPacket) - 2);
                    if (checksum == packet->checksum) {
                        // Добавление водоворота
                        if (state->whirlpool_manager) {
                            WhirlpoolManager_Add(state->whirlpool_manager, packet->x, packet->y);
                        }
                    }
                    
                    // Сдвигаем указатель за обработанный пакет
                    i += sizeof(AddWhirlpoolPacket) - 1;
                }
                break;
            }
            
            case PKT_CLEANUP: {
                if (i + sizeof(CleanupPacket) <= RX_BUFFER_SIZE) {
                    CleanupPacket* packet = (CleanupPacket*)&rx_buffer[i];
                    
                    // Проверка контрольной суммы
                    uint16_t checksum = Protocol_CalculateChecksum(rx_buffer + i, sizeof(CleanupPacket) - 2);
                    if (checksum == packet->checksum) {
                        // Очистка старых объектов
                        Enemies_CleanupOld(state, packet->threshold_y);
                        Obstacles_CleanupOld(state, packet->threshold_y);
                        if (state->whirlpool_manager) {
                            WhirlpoolManager_Cleanup(state->whirlpool_manager, packet->threshold_y);
                        }
                    }
                    
                    // Сдвигаем указатель за обработанный пакет
                    i += sizeof(CleanupPacket) - 1;
                }
                break;
            }
            
            case PKT_INIT_GAME: {
                // Сброс игрового состояния
                GameState_Cleanup(state);
                GameState_Init(state);
                
                // Сдвигаем указатель
                i += 1;
                break;
            }
        }
    }
}