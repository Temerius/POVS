/* protocol.c*/

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
    pkt.header = START_BYTE;
    pkt.type = PKT_BUTTONS;
    pkt.left_pressed = left;
    pkt.right_pressed = right;
    pkt.fire_pressed = fire;
    

    uint8_t* data_start = &pkt.type;
    uint16_t data_len = 4;
    pkt.crc = Protocol_CalculateCRC(data_start, data_len);
    pkt.end_byte = END_BYTE;
    

    memcpy(tx_buffer, &pkt, sizeof(ButtonPacket));
    
    if (HAL_UART_Transmit_DMA(huart_handle, tx_buffer, sizeof(ButtonPacket)) == HAL_OK) {
        uart_tx_busy = 1;
    }
}


void Protocol_ProcessIncoming(uint16_t* miles_out) {
    if (huart_handle == NULL || miles_out == NULL) return;
    

    uint16_t dma_pos = 64 - __HAL_DMA_GET_COUNTER(huart_handle->hdmarx);
    

    for (uint16_t i = 0; i < dma_pos; i++) {

        if (rx_buffer[i] == START_BYTE && (i + 5) < 64) {

            if (rx_buffer[i+1] == PKT_MILES && rx_buffer[i+5] == END_BYTE) {
                uint8_t data_for_crc[3] = {rx_buffer[i+1], rx_buffer[i+2], rx_buffer[i+3]};
                uint8_t crc_calc = Protocol_CalculateCRC(data_for_crc, 3);
                
                if (crc_calc == rx_buffer[i+4]) {
                    uint16_t new_miles = rx_buffer[i+2] | (rx_buffer[i+3] << 8);
                    *miles_out = new_miles;
                    return;
                }
            }
        }
    }
}