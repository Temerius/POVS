
#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include "main.h"
#include "game_types.h"

 
#define START_BYTE 0xAA
#define END_BYTE 0x55

 
#define PKT_GAME_STATE     0x01   
#define PKT_ADD_ENEMY      0x02   
#define PKT_ADD_OBSTACLE   0x03   
#define PKT_CLEANUP        0x04   
#define PKT_INIT_GAME      0x05   
#define PKT_ADD_WHIRLPOOL  0x06   
#define PKT_DEBUG          0x07   

 
#pragma pack(push, 1)
typedef struct {
    uint8_t header;               
    uint8_t received_packet_type;  
    uint8_t packet_size;           
    uint8_t parse_state;           
    uint8_t crc_received;          
    uint8_t crc_calculated;        
    uint8_t success;               
    char message[32];              
    uint8_t crc;                   
    uint8_t end_byte;              
} DebugPacket;
#pragma pack(pop)

 
void Protocol_SendDebug(uint8_t packet_type, uint8_t packet_size, uint8_t parse_state,
                       uint8_t crc_received, uint8_t crc_calculated, 
                       uint8_t success, const char* message);

 
#define MAX_ENEMIES_IN_PACKET 6       
#define MAX_PROJECTILES_IN_PACKET 20  
#define MAX_WHIRLPOOLS_IN_PACKET 3    

 
#pragma pack(push, 1)
typedef struct {
    uint8_t header;               
    
     
    float player_x;
    float player_y;
    float player_angle;
    int16_t player_health;
    uint16_t player_score;
    uint16_t player_shoot_cooldown;
    
     
    uint8_t enemy_count;
    struct {
        uint8_t type;
        float x;
        float y;
        int8_t health;
    } enemies[MAX_ENEMIES_IN_PACKET];
    
     
    uint8_t projectile_count;
    struct {
        float x;
        float y;
        uint8_t is_player_shot;
    } projectiles[MAX_PROJECTILES_IN_PACKET];
    
     
    uint8_t whirlpool_count;
    struct {
        float x;
        float y;
        uint8_t used;
    } whirlpools[MAX_WHIRLPOOLS_IN_PACKET];
    
    float camera_y;
    uint32_t frame_counter;
    uint8_t crc;                  
    uint8_t end_byte;             
} GameStatePacket;
#pragma pack(pop)

 
typedef struct __attribute__((packed)) {
    uint8_t header;               
    uint8_t type;                 
    float x;
    float y;
    uint8_t crc;
    uint8_t end_byte;
} AddEnemyPacket;

 
typedef struct __attribute__((packed)) {
    uint8_t header;               
    uint8_t type;                 
    float x;
    float y;
    float radius;
    uint8_t crc;
    uint8_t end_byte;
} AddObstaclePacket;

 
typedef struct __attribute__((packed)) {
    uint8_t header;               
    float x;
    float y;
    uint8_t crc;
    uint8_t end_byte;
} AddWhirlpoolPacket;

 
typedef struct __attribute__((packed)) {
    uint8_t header;               
    float threshold_y;
    uint8_t crc;
    uint8_t end_byte;
} CleanupPacket;

 
extern uint8_t rx_buffer[RX_BUFFER_SIZE];
extern volatile uint16_t rx_write_pos;   
extern volatile uint8_t uart_tx_busy;

 
void Protocol_Init(UART_HandleTypeDef* huart);
void Protocol_SendGameState(GameState* state);
void Protocol_ProcessIncoming(GameState* state);
void Protocol_CleanupRxBuffer(void);
uint8_t Protocol_CalculateCRC(uint8_t* data, uint16_t len);

#endif  