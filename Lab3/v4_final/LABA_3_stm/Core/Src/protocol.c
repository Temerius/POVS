/* protocol.c - Реализация упрощённого протокола */

#include "protocol.h"
#include <string.h>

static UART_HandleTypeDef* huart_handle = NULL;

volatile uint8_t uart_tx_busy = 0;
uint8_t tx_buffer[64];
uint8_t rx_buffer[64];
volatile uint16_t rx_write_pos = 0;

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
    HAL_UART_Receive_DMA(huart, rx_buffer, 64);
}

void Protocol_SendButtons(uint8_t left, uint8_t right, uint8_t fire) {
    if (uart_tx_busy || huart_handle == NULL) {
        return;
    }
    
    ButtonPacket pkt;
    pkt.start_byte = START_BYTE;
		pkt.type = PKT_BUTTONS;
    pkt.left_pressed = left;
    pkt.right_pressed = right;
    pkt.fire_pressed = fire;
    
    // CRC считаем от типа пакета до данных включительно
    uint8_t* data_start = (uint8_t*)&pkt + 1; // пропускаем START_BYTE
    uint16_t data_len = 4; // PKT_BUTTONS + 3 кнопки
    pkt.crc = Protocol_CalculateCRC(data_start, data_len);
    pkt.end_byte = END_BYTE;
    
    // Копируем в tx_buffer
    memcpy(tx_buffer, &pkt, sizeof(ButtonPacket));
    
    if (HAL_UART_Transmit_DMA(huart_handle, tx_buffer, sizeof(ButtonPacket)) == HAL_OK) {
        uart_tx_busy = 1;
    }
}

void Protocol_ProcessIncoming(uint16_t* miles_out) {
    if (huart_handle == NULL || miles_out == NULL) return;
    
    uint16_t dma_pos = 64 - __HAL_DMA_GET_COUNTER(huart_handle->hdmarx);
    
    while (rx_write_pos != dma_pos) {
        // Ищем стартовый байт
        if (rx_buffer[rx_write_pos] != START_BYTE) {
            rx_write_pos++;
            if (rx_write_pos >= 64) rx_write_pos = 0;
            continue;
        }
        
        uint16_t packet_start = rx_write_pos;
        
        // Проверяем наличие минимум 5 байт (START + TYPE + DATA + CRC + END)
        uint16_t available = (dma_pos >= packet_start) ? 
                            (dma_pos - packet_start) : 
                            (64 - packet_start + dma_pos);
        
        if (available < sizeof(MilesPacket)) {
            return; // Недостаточно данных
        }
        
        // Копируем пакет
        MilesPacket pkt;
        for (uint8_t i = 0; i < sizeof(MilesPacket); i++) {
            ((uint8_t*)&pkt)[i] = rx_buffer[(packet_start + i) % 64];
        }
        
        // Проверка END_BYTE
        if (pkt.end_byte != END_BYTE) {
            rx_write_pos++;
            if (rx_write_pos >= 64) rx_write_pos = 0;
            continue;
        }
        
        // Проверка CRC
        uint8_t* data_start = (uint8_t*)&pkt + 1; // пропускаем START_BYTE
        uint16_t data_len = 3; // PKT_MILES + 2 байта miles
        uint8_t crc_calc = Protocol_CalculateCRC(data_start, data_len);
        
        if (crc_calc != pkt.crc) {
            rx_write_pos++;
            if (rx_write_pos >= 64) rx_write_pos = 0;
            continue;
        }
        
        // Пакет валиден - обрабатываем
        *miles_out = pkt.miles;
        
        // Пропускаем обработанный пакет
        rx_write_pos = (packet_start + sizeof(MilesPacket)) % 64;
    }
}