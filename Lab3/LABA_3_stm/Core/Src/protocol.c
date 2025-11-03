/* protocol.c - Надежная реализация протокола */

#include "protocol.h"
#include "cleanup.h"
#include "whirlpool.h"
#include <string.h>

static UART_HandleTypeDef* huart_handle = NULL;

// Глобальные переменные (уже объявлены в globals.h)
volatile uint8_t uart_tx_busy = 0;
uint8_t tx_buffer[TX_BUFFER_SIZE];
uint8_t rx_buffer[RX_BUFFER_SIZE];
volatile uint16_t rx_write_pos = 0;

// Состояние парсинга входящих данных
static uint8_t packet_state = 0;
static uint8_t packet_type = 0;
static uint8_t packet_data[512];
static uint16_t packet_idx = 0;

uint8_t Protocol_CalculateCRC(uint8_t* data, uint16_t len) {
    uint8_t crc = 0;
    for (uint16_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x80)
                crc = (crc << 1) ^ 0x07;
            else
                crc <<= 1;
        }
    }
    return crc;
}

void Protocol_Init(UART_HandleTypeDef* huart) {
    huart_handle = huart;
    
    // Инициализируем состояние парсинга
    packet_state = 0;
    packet_type = 0;
    packet_idx = 0;
    
    // Запускаем приём DMA в циклическом режиме
    HAL_UART_Receive_DMA(huart, rx_buffer, RX_BUFFER_SIZE);
}

void Protocol_SendGameState(GameState* state) {
    if (uart_tx_busy || huart_handle == NULL) {
        return;
    }
    
    // Формируем пакет
    uint16_t idx = 0;
    tx_buffer[idx++] = START_BYTE;
    tx_buffer[idx++] = PKT_GAME_STATE;
    
    // Данные игрока
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.x + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.x + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.x + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.x + 3);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.y + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.y + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.y + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->player.position.y + 3);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.hull_angle + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.hull_angle + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->player.hull_angle + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->player.hull_angle + 3);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.health + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.health + 1);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.score + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.score + 1);
    
    tx_buffer[idx++] = *((uint8_t*)&state->player.shoot_cooldown + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->player.shoot_cooldown + 1);
    
    // Сохраняем позицию для счетчика врагов
    uint16_t enemy_count_pos = idx++;
    
    // Враги
    uint8_t enemy_count = 0;
    for (uint8_t i = 0; i < state->enemy_simple_count && enemy_count < MAX_ENEMIES_IN_PACKET; i++) {
        if (state->enemies_simple[i].alive && state->enemies_simple[i].active) {
            tx_buffer[idx++] = 0;  // тип: простой враг
            
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.x + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.x + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.x + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.x + 3);
            
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.y + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.y + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.y + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_simple[i].position.y + 3);
            
            tx_buffer[idx++] = state->enemies_simple[i].health;
            
            enemy_count++;
        }
    }
    
    for (uint8_t i = 0; i < state->enemy_hard_count && enemy_count < MAX_ENEMIES_IN_PACKET; i++) {
        if (state->enemies_hard[i].alive && state->enemies_hard[i].active) {
            tx_buffer[idx++] = 1;  // тип: сложный враг
            
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.x + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.x + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.x + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.x + 3);
            
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.y + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.y + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.y + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->enemies_hard[i].position.y + 3);
            
            tx_buffer[idx++] = state->enemies_hard[i].health;
            
            enemy_count++;
        }
    }
    
    // Устанавливаем реальное количество врагов
    tx_buffer[enemy_count_pos] = enemy_count;
    
    // Сохраняем позицию для счетчика снарядов
    uint16_t projectile_count_pos = idx++;
    
    // Снаряды
    uint8_t projectile_count = 0;
    for (uint8_t i = 0; i < state->projectile_count && projectile_count < MAX_PROJECTILES_IN_PACKET; i++) {
        if (state->projectiles[i].active) {
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.x + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.x + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.x + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.x + 3);
            
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.y + 0);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.y + 1);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.y + 2);
            tx_buffer[idx++] = *((uint8_t*)&state->projectiles[i].position.y + 3);
            
            tx_buffer[idx++] = state->projectiles[i].is_player_shot;
            
            projectile_count++;
        }
    }
    
    // Устанавливаем реальное количество снарядов
    tx_buffer[projectile_count_pos] = projectile_count;
    
    // Сохраняем позицию для счетчика водоворотов
    uint16_t whirlpool_count_pos = idx++;
    
    // Водовороты
    uint8_t whirlpool_count = 0;
    if (state->whirlpool_manager) {
        whirlpool_count = state->whirlpool_manager->whirlpool_count;
        if (whirlpool_count > MAX_WHIRLPOOLS_IN_PACKET) {
            whirlpool_count = MAX_WHIRLPOOLS_IN_PACKET;
        }
        
        for (uint8_t i = 0; i < whirlpool_count; i++) {
            Whirlpool* whirlpool = &state->whirlpool_manager->whirlpools[i];
            
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.x + 0);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.x + 1);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.x + 2);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.x + 3);
            
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.y + 0);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.y + 1);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.y + 2);
            tx_buffer[idx++] = *((uint8_t*)&whirlpool->position.y + 3);
            
            tx_buffer[idx++] = whirlpool->used_recently;
        }
    }
    
    // Устанавливаем реальное количество водоворотов
    tx_buffer[whirlpool_count_pos] = whirlpool_count;
    
    // Camera и frame counter
    tx_buffer[idx++] = *((uint8_t*)&state->camera_y + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->camera_y + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->camera_y + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->camera_y + 3);
    
    tx_buffer[idx++] = *((uint8_t*)&state->frame_counter + 0);
    tx_buffer[idx++] = *((uint8_t*)&state->frame_counter + 1);
    tx_buffer[idx++] = *((uint8_t*)&state->frame_counter + 2);
    tx_buffer[idx++] = *((uint8_t*)&state->frame_counter + 3);
    
    // Вычисляем и добавляем CRC
    uint8_t crc = Protocol_CalculateCRC(&tx_buffer[1], idx - 1);
    tx_buffer[idx++] = crc;
    
    // Добавляем конечный байт
    tx_buffer[idx++] = END_BYTE;
    
    // Отправка через DMA
    if (HAL_UART_Transmit_DMA(huart_handle, tx_buffer, idx) == HAL_OK) {
        uart_tx_busy = 1;
    }
}

void Protocol_CleanupRxBuffer(void) {
    uint16_t dma_pos = RX_BUFFER_SIZE - __HAL_DMA_GET_COUNTER(huart_handle->hdmarx);
    
    // Если заполнено больше 90%, сбрасываем буфер
    uint16_t used = (dma_pos >= rx_write_pos) ? 
                    (dma_pos - rx_write_pos) : 
                    (RX_BUFFER_SIZE - rx_write_pos + dma_pos);
    
    if (used > (RX_BUFFER_SIZE * 9 / 10)) {
        rx_write_pos = dma_pos;
    }
}

void Protocol_ProcessIncoming(GameState* state) {
    if (huart_handle == NULL) return;
    
    //Protocol_CleanupRxBuffer();
    
    uint16_t dma_pos = RX_BUFFER_SIZE - __HAL_DMA_GET_COUNTER(huart_handle->hdmarx);
    
    // Обрабатываем все доступные данные
    while (rx_write_pos != dma_pos) {
        uint8_t byte = rx_buffer[rx_write_pos];
        
        switch (packet_state) {
            case 0: // Ожидание стартового байта
                if (byte == START_BYTE) {
                    packet_state = 1;
                    packet_idx = 0;
                    packet_data[packet_idx++] = byte;
                }
                break;
                
            case 1: // Получение типа пакета
                packet_type = byte;
                packet_data[packet_idx++] = byte;
                packet_state = 2;
                break;
                
            case 2: // Получение данных пакета
                packet_data[packet_idx++] = byte;
                
                // Проверка завершения пакета на основе типа
                switch (packet_type) {
                    case PKT_ADD_ENEMY: {
                        if (byte == END_BYTE) {
                            // Проверяем размер пакета: START(1) + TYPE(1) + DATA(9) + CRC(1) + END(1) = 13
                            if (packet_idx == 13) {
                                // Рассчитываем CRC только для данных (без START_BYTE и END_BYTE)
                                uint8_t crc_calculated = Protocol_CalculateCRC(&packet_data[1], 11);
                                if (crc_calculated == packet_data[11]) {
                                    uint8_t enemy_type = packet_data[2];
                                    float x = *(float*)&packet_data[3];
                                    float y = *(float*)&packet_data[7];
                                    
                                    if (enemy_type == 0 && state->enemy_simple_count < MAX_ENEMIES_SIMPLE) {
                                        EnemySimple* enemy = &state->enemies_simple[state->enemy_simple_count];
                                        
                                        enemy->position.x = x;
                                        enemy->position.y = y;
                                        enemy->initial_y = y;
                                        enemy->health = ENEMY_SIMPLE_HEALTH;
                                        enemy->max_health = ENEMY_SIMPLE_HEALTH;
                                        enemy->shoot_cooldown = 0;
                                        enemy->shoot_delay = ENEMY_SIMPLE_SHOOT_DELAY;
                                        enemy->radius = COLLISION_RADIUS_ENEMY_SIMPLE;
                                        enemy->points = ENEMY_SIMPLE_POINTS;
                                        enemy->active = 0;
                                        enemy->alive = 1;
                                        enemy->wander_angle = 0;
                                        enemy->wander_timer = 0;
                                        enemy->strategy = STRATEGY_ATTACK;
                                        
                                        state->enemy_simple_count++;
                                    }
                                    else if (enemy_type == 1 && state->enemy_hard_count < MAX_ENEMIES_HARD) {
                                        EnemyHard* enemy = &state->enemies_hard[state->enemy_hard_count];
                                        
                                        enemy->position.x = x;
                                        enemy->position.y = y;
                                        enemy->initial_y = y;
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
                                }
                            }
                        }
                        packet_state = 0;
                        break;
                    }
                    
                    case PKT_ADD_OBSTACLE: {
                        if (byte == END_BYTE) {
                            // Проверяем размер пакета: START(1) + TYPE(1) + DATA(13) + CRC(1) + END(1) = 17
                            if (packet_idx == 17) {
                                uint8_t crc_calculated = Protocol_CalculateCRC(&packet_data[1], 15);
                                if (crc_calculated == packet_data[15]) {
                                    uint8_t obstacle_type = packet_data[2];
                                    float x = *(float*)&packet_data[3];
                                    float y = *(float*)&packet_data[7];
                                    float value = *(float*)&packet_data[11];
                                    
                                    if (state->obstacle_count < MAX_OBSTACLES) {
                                        Obstacle* obstacle = &state->obstacles[state->obstacle_count];
                                        
                                        obstacle->position.x = x;
                                        obstacle->position.y = y;
                                        
                                        // Для берегов используем значение как радиус (ширина берега)
                                        if (obstacle_type == OBSTACLE_SHORE_LEFT || 
                                            obstacle_type == OBSTACLE_SHORE_RIGHT) {
                                            obstacle->radius = value;
                                        } 
                                        // Для островов используем значение как радиус острова
                                        else {
                                            obstacle->radius = value;
                                        }
                                        
                                        obstacle->type = (ObstacleType)obstacle_type;
                                        obstacle->active = 1;
                                        
                                        state->obstacle_count++;
                                    }
                                }
                            }
                        }
                        packet_state = 0;
                        break;
                    }
                    
                    case PKT_ADD_WHIRLPOOL: {
                        if (byte == END_BYTE) {
                            // Проверяем размер пакета: START(1) + TYPE(1) + DATA(8) + CRC(1) + END(1) = 12
                            if (packet_idx == 12) {
                                uint8_t crc_calculated = Protocol_CalculateCRC(&packet_data[1], 10);
                                if (crc_calculated == packet_data[10]) {
                                    float x = *(float*)&packet_data[2];
                                    float y = *(float*)&packet_data[6];
                                    
                                    if (state->whirlpool_manager) {
                                        WhirlpoolManager_Add(state->whirlpool_manager, x, y);
                                    }
                                }
                            }
                        }
                        packet_state = 0;
                        break;
                    }
                    
                    case PKT_CLEANUP: {
                        if (byte == END_BYTE) {
                            // Проверяем размер пакета: START(1) + TYPE(1) + DATA(4) + CRC(1) + END(1) = 8
                            if (packet_idx == 8) {
                                uint8_t crc_calculated = Protocol_CalculateCRC(&packet_data[1], 6);
                                if (crc_calculated == packet_data[6]) {
                                    float threshold_y = *(float*)&packet_data[2];
                                    
                                    Enemies_CleanupOld(state, threshold_y);
                                    Obstacles_CleanupOld(state, threshold_y);
                                    if (state->whirlpool_manager) {
                                        WhirlpoolManager_Cleanup(state->whirlpool_manager, threshold_y);
                                    }
                                }
                            }
                        }
                        packet_state = 0;
                        break;
                    }
                    
                    case PKT_INIT_GAME: {
                        if (byte == END_BYTE) {
                            // Проверяем размер пакета: START(1) + TYPE(1) + CRC(1) + END(1) = 4
                            if (packet_idx == 4) {
                                uint8_t crc_calculated = Protocol_CalculateCRC(&packet_data[1], 2);
                                if (crc_calculated == packet_data[2]) {
                                    GameState_Cleanup(state);
                                    GameState_Init(state);
                                }
                            }
                        }
                        packet_state = 0;
                        break;
                    }
                }
                break;
        }
        
        // Перемещаем позицию записи
        rx_write_pos++;
        if (rx_write_pos >= RX_BUFFER_SIZE) {
            rx_write_pos = 0;
        }
    }
}