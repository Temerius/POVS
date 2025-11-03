/* protocol.c - Реализация протокола */

#include "protocol.h"
#include <string.h>

// Буферы DMA
uint8_t rx_buffer[RX_BUFFER_SIZE];
uint8_t tx_buffer[TX_BUFFER_SIZE];
volatile uint8_t uart_tx_busy = 0;

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
    
    packet.camera_y = state->camera_y;
    
    // Контрольная сумма
    packet.checksum = Protocol_CalculateChecksum((uint8_t*)&packet, sizeof(packet) - 2);
    
    // Отправка через DMA
    uart_tx_busy = 1;
    HAL_UART_Transmit_DMA(huart_handle, (uint8_t*)&packet, sizeof(packet));
}

void Protocol_ProcessIncoming(GameState* state) {
    // TODO: реализуем позже (парсинг входящих пакетов)
    // Пока заглушка
}