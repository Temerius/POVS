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
        // Если предыдущая передача не завершилась, увеличиваем счётчик пропущенных пакетов
        state->skipped_packets++;
        
        // Если пропущено много пакетов, отправляем debug-сообщение
        if (state->skipped_packets % 100 == 0 && state->frame_counter % 100 == 0) {
            // БЕЗОПАСНАЯ АЛЬТЕРНАТИВА ДЛЯ snprintf
            char message[32];
            memset(message, 0, sizeof(message));
            
            // Формируем строку вручную, чтобы избежать проблем с форматированием
            const char* prefix = "Skipped ";
            const char* suffix = " pkts";
            
            // Копируем префикс
            strncpy(message, prefix, sizeof(message)-1);
            
            // Конвертируем число в строку
            uint32_t num = state->skipped_packets;
            char num_str[10]; // Достаточно для 32-битного числа
            int pos = 0;
            
            // Специальный случай для нуля
            if (num == 0) {
                num_str[pos++] = '0';
            } else {
                // Обработка числа
                while (num > 0 && pos < (int)sizeof(num_str)-1) {
                    num_str[pos++] = '0' + (num % 10);
                    num /= 10;
                }
            }
            num_str[pos] = '\0';
            
            // Разворачиваем строку с числом (т.к. мы заполняли её с конца)
            for (int i = 0; i < pos/2; i++) {
                char temp = num_str[i];
                num_str[i] = num_str[pos-1-i];
                num_str[pos-1-i] = temp;
            }
            
            // Добавляем число к сообщению
            strncat(message, num_str, sizeof(message)-strlen(message)-1);
            
            // Добавляем суффикс
            strncat(message, suffix, sizeof(message)-strlen(message)-1);
            
            Protocol_SendDebug(0, 0, 0, 0, 0, 0, message);
        }
        
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
            tx_buffer[idx++] = state->enemies_simple[i].current_direction;
            
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
            tx_buffer[idx++] = state->enemies_simple[i].current_direction;
            
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
    } else {
        // Ошибка начала передачи
        uart_tx_busy = 0;
        state->skipped_packets++;
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


void Protocol_SendDebug(uint8_t packet_type, uint8_t packet_size, uint8_t parse_state,
                       uint8_t crc_received, uint8_t crc_calculated, 
                       uint8_t success, const char* message) {
    if (uart_tx_busy || huart_handle == NULL) {
        return;
    }
    
    // Формируем debug-пакет
    uint16_t idx = 0;
    tx_buffer[idx++] = START_BYTE;
    tx_buffer[idx++] = PKT_DEBUG;
    tx_buffer[idx++] = packet_type;
    tx_buffer[idx++] = packet_size;
    tx_buffer[idx++] = parse_state;
    tx_buffer[idx++] = crc_received;
    tx_buffer[idx++] = crc_calculated;
    tx_buffer[idx++] = success;
    
    // Копируем сообщение (максимум 32 байта)
    for (uint8_t i = 0; i < 32; i++) {
        if (message && message[i] != '\0') {
            tx_buffer[idx++] = message[i];
        } else {
            tx_buffer[idx++] = '\0';
        }
    }
    
    // Вычисляем CRC для debug-пакета
    uint8_t crc = Protocol_CalculateCRC(&tx_buffer[1], idx-1);
    tx_buffer[idx++] = crc;
    tx_buffer[idx++] = END_BYTE;
    
    // Отправка
    HAL_UART_Transmit_DMA(huart_handle, tx_buffer, idx);
    uart_tx_busy = 1;
}


void Protocol_ProcessIncoming(GameState* state) {
    if (huart_handle == NULL) return;
    
    uint16_t dma_pos = RX_BUFFER_SIZE - __HAL_DMA_GET_COUNTER(huart_handle->hdmarx);
    

    uint16_t processed_bytes = 0;
    const uint16_t MAX_BYTES_PER_CALL = 128;

    // Обрабатываем все доступные данные
    while (rx_write_pos != dma_pos && processed_bytes < MAX_BYTES_PER_CALL) {
        // Ищем стартовый байт
        if (rx_buffer[rx_write_pos] != START_BYTE) {
            rx_write_pos++;
            if (rx_write_pos >= RX_BUFFER_SIZE) rx_write_pos = 0;
            continue;
        }
        
        // Нашли START_BYTE
        uint16_t packet_start = rx_write_pos;
        uint16_t idx = rx_write_pos;
        
        // Проверяем, есть ли хотя бы 4 байта (минимальный пакет)
        uint16_t available = (dma_pos >= idx) ? (dma_pos - idx) : (RX_BUFFER_SIZE - idx + dma_pos);
        if (available < 4) {
            // Недостаточно данных, ждём
            return;
        }
        
        // Читаем тип пакета
        idx++;
        if (idx >= RX_BUFFER_SIZE) idx = 0;
        uint8_t packet_type = rx_buffer[idx];
        
        // Protocol_SendDebug(packet_type, 0, 0, 0, 0, 1, "Found packet type");
        
        // Определяем ожидаемый размер пакета по типу
        uint16_t expected_size = 0;
        switch (packet_type) {
            case PKT_ADD_ENEMY:
                expected_size = 13;  // START(1) + TYPE(1) + enemy_type(1) + x(4) + y(4) + CRC(1) + END(1)
                break;
            case PKT_ADD_OBSTACLE:
                expected_size = 17;  // START(1) + TYPE(1) + type(1) + x(4) + y(4) + radius(4) + CRC(1) + END(1)
                break;
            case PKT_ADD_WHIRLPOOL:
                expected_size = 12;  // START(1) + TYPE(1) + x(4) + y(4) + CRC(1) + END(1)
                break;
            case PKT_CLEANUP:
                expected_size = 8;   // START(1) + TYPE(1) + threshold_y(4) + CRC(1) + END(1)
                break;
            case PKT_INIT_GAME:
                expected_size = 4;   // START(1) + TYPE(1) + CRC(1) + END(1)
                break;
            default:
                // Неизвестный тип пакета, пропускаем START_BYTE и продолжаем поиск
                Protocol_SendDebug(packet_type, 0, 0, 0, 0, 0, "Unknown packet type");
                rx_write_pos++;
                if (rx_write_pos >= RX_BUFFER_SIZE) rx_write_pos = 0;
                continue;
        }
        
        // Проверяем, достаточно ли данных для полного пакета
        available = (dma_pos >= packet_start) ? (dma_pos - packet_start) : (RX_BUFFER_SIZE - packet_start + dma_pos);
        if (available < expected_size) {
            // Недостаточно данных, ждём
            Protocol_SendDebug(packet_type, expected_size, available, 0, 0, 0, "Waiting for data");
            return;
        }
        
        // Копируем пакет в линейный буфер для удобства обработки
        uint8_t packet_buffer[32];  // Максимальный размер пакета
        idx = packet_start;
        for (uint16_t i = 0; i < expected_size; i++) {
            packet_buffer[i] = rx_buffer[idx];
            idx++;
            if (idx >= RX_BUFFER_SIZE) idx = 0;
        }
        
        // Проверяем END_BYTE
        if (packet_buffer[expected_size - 1] != END_BYTE) {
            Protocol_SendDebug(packet_type, expected_size, 0, 0, 0, 0, "No END byte");
            // Пропускаем этот START_BYTE и ищем следующий
            rx_write_pos++;
            if (rx_write_pos >= RX_BUFFER_SIZE) rx_write_pos = 0;
            continue;
        }
        
        // Проверяем CRC (все байты кроме START, CRC и END)
        uint8_t crc_calculated = Protocol_CalculateCRC(&packet_buffer[1], expected_size - 3);
        uint8_t crc_received = packet_buffer[expected_size - 2];
        
        if (crc_calculated != crc_received) {
            Protocol_SendDebug(packet_type, expected_size, 0, crc_received, crc_calculated, 0, "CRC mismatch");
            // Пропускаем этот START_BYTE и ищем следующий
            rx_write_pos++;
            if (rx_write_pos >= RX_BUFFER_SIZE) rx_write_pos = 0;
            continue;
        }
        
        // CRC OK, обрабатываем пакет
        switch (packet_type) {
            case PKT_ADD_ENEMY: {
                uint8_t enemy_type = packet_buffer[2];
                float x = *(float*)&packet_buffer[3];
                float y = *(float*)&packet_buffer[7];
                
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
                    enemy->current_direction = 2;
                    
                    state->enemy_simple_count++;
                    Protocol_SendDebug(PKT_ADD_ENEMY, expected_size, state->enemy_simple_count, 
                                     crc_received, crc_calculated, 1, "Enemy simple OK");
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
                    enemy->current_direction = 2;
                    
                    state->enemy_hard_count++;
                    Protocol_SendDebug(PKT_ADD_ENEMY, expected_size, state->enemy_hard_count, 
                                     crc_received, crc_calculated, 1, "Enemy hard OK");
                }
                else {
                    Protocol_SendDebug(PKT_ADD_ENEMY, expected_size, 0, 
                                     crc_received, crc_calculated, 0, "Array full");
                }
                break;
            }
            
            case PKT_ADD_OBSTACLE: {
                uint8_t obstacle_type = packet_buffer[2];
                float x = *(float*)&packet_buffer[3];
                float y = *(float*)&packet_buffer[7];
                float radius = *(float*)&packet_buffer[11];
                
                if (state->obstacle_count < MAX_OBSTACLES) {
                    Obstacle* obstacle = &state->obstacles[state->obstacle_count];
                    
                    obstacle->position.x = x;
                    obstacle->position.y = y;
                    obstacle->radius = radius;
                    obstacle->type = (ObstacleType)obstacle_type;
                    obstacle->active = 1;
                    
                    state->obstacle_count++;
                    Protocol_SendDebug(PKT_ADD_OBSTACLE, expected_size, state->obstacle_count, 
                                     crc_received, crc_calculated, 1, "Obstacle OK");
                }
                else {
                    Protocol_SendDebug(PKT_ADD_OBSTACLE, expected_size, 0, 
                                     crc_received, crc_calculated, 0, "Array full");
                }
                break;
            }
            
            case PKT_ADD_WHIRLPOOL: {
                float x = *(float*)&packet_buffer[2];
                float y = *(float*)&packet_buffer[6];
                
                if (state->whirlpool_manager) {
                    uint8_t success = WhirlpoolManager_Add(state->whirlpool_manager, x, y);
                    if (success) {
                        Protocol_SendDebug(PKT_ADD_WHIRLPOOL, expected_size, 
                                         state->whirlpool_manager->whirlpool_count, 
                                         crc_received, crc_calculated, 1, "Whirlpool OK");
                    }
                    else {
                        Protocol_SendDebug(PKT_ADD_WHIRLPOOL, expected_size, 0, 
                                         crc_received, crc_calculated, 0, "Array full");
                    }
                }
                else {
                    Protocol_SendDebug(PKT_ADD_WHIRLPOOL, expected_size, 0, 
                                     crc_received, crc_calculated, 0, "Manager NULL");
                }
                break;
            }
            
            case PKT_CLEANUP: {
                float threshold_y = *(float*)&packet_buffer[2];
                
                uint8_t enemies_before = state->enemy_simple_count + state->enemy_hard_count;
                uint8_t obstacles_before = state->obstacle_count;
                
                Enemies_CleanupOld(state, threshold_y);
                Obstacles_CleanupOld(state, threshold_y);
                if (state->whirlpool_manager) {
                    WhirlpoolManager_Cleanup(state->whirlpool_manager, threshold_y);
                }
                
                uint8_t enemies_after = state->enemy_simple_count + state->enemy_hard_count;
                uint8_t cleaned = enemies_before - enemies_after;
                
                Protocol_SendDebug(PKT_CLEANUP, expected_size, cleaned, 
                                 crc_received, crc_calculated, 1, "Cleanup OK");
                break;
            }
            
            case PKT_INIT_GAME: {
                GameState_Cleanup(state);
                GameState_Init(state);
                Protocol_SendDebug(PKT_INIT_GAME, expected_size, 0, 
                                 crc_received, crc_calculated, 1, "Init OK");
                break;
            }
        }
        
        // Успешно обработали пакет, перемещаем указатель на конец пакета
        rx_write_pos = packet_start;
        for (uint16_t i = 0; i < expected_size; i++) {
            rx_write_pos++;
            if (rx_write_pos >= RX_BUFFER_SIZE) rx_write_pos = 0;
        }

        processed_bytes++;
    }

    uint16_t used = (dma_pos >= rx_write_pos) ? 
                    (dma_pos - rx_write_pos) : 
                    (RX_BUFFER_SIZE - rx_write_pos + dma_pos);
    
    if (used > (RX_BUFFER_SIZE * 9 / 10)) {
        rx_write_pos = dma_pos;
        Protocol_SendDebug(0, 0, 0, 0, 0, 0, "Forced buffer reset");
    }
}