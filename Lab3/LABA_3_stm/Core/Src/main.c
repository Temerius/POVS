/* USER CODE BEGIN Header */
/**
  * @file           : main.c
  * @brief          : Space Defender - FULL VERSION with Menus
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart2;
DMA_HandleTypeDef hdma_usart2_rx;
DMA_HandleTypeDef hdma_usart2_tx;

/* USER CODE BEGIN PV */

static char debug_buffer[128];

#define START_BYTE 0xAA
#define END_BYTE 0x55
#define PACKET_GAME_STATE 0x01
#define PACKET_MENU_STATE 0x02
#define PACKET_DEBUG 0x03
#define PACKET_EXPLOSION 0x04
#define PACKET_SPAWN_ENEMY 0x10
#define PACKET_START_GAME 0x11

#define MAX_ENEMIES 10
#define MAX_BULLETS 10
#define MAX_EXPLOSIONS 5
#define SCREEN_WIDTH 800
#define SCREEN_HEIGHT 600

typedef struct {
    int16_t x;
    int16_t y;
} Vector2;

typedef struct {
    Vector2 pos;
    uint8_t hp;
    uint8_t shoot_cooldown;
} Player;

typedef struct {
    Vector2 pos;
    Vector2 vel;
    uint8_t active;
} Bullet;

typedef struct {
    Vector2 pos;
    int8_t vel_x;
    int8_t vel_y;
    uint8_t hp;
    uint8_t max_hp;
    uint8_t type;
    uint8_t active;
    uint8_t shoot_cooldown;
} Enemy;

typedef struct {
    Vector2 pos;
    uint8_t frame;
    uint8_t active;
} Explosion;

typedef enum {
    GAME_MENU = 0,      // ??????? ????
    GAME_PLAYING,       // ???? ????
    GAME_PAUSED,        // ?????
    GAME_OVER          // Game Over
} GameState;

typedef enum {
    MENU_ITEM_START = 0,
    MENU_ITEM_CONTINUE,
    MENU_ITEM_RESTART,
    MENU_ITEM_EXIT,
    MENU_ITEM_COUNT
} MenuItem;

static Player player;
static Enemy enemies[MAX_ENEMIES];
static Bullet bullets[MAX_BULLETS];
static Bullet enemy_bullets[MAX_BULLETS];
static Explosion explosions[MAX_EXPLOSIONS];

static GameState game_state = GAME_MENU;
static uint16_t score = 0;
static uint8_t level = 1;
static MenuItem selected_menu_item = MENU_ITEM_START;

volatile uint8_t uart_tx_busy = 0;
static uint8_t tx_buffer[256];

#define RX_BUFFER_SIZE 512
static uint8_t rx_buffer[RX_BUFFER_SIZE];
static volatile uint16_t rx_write_pos = 0;

static uint32_t last_update_time = 0;
static uint32_t last_tx_time = 0;
static uint32_t last_debug_time = 0;
#define UPDATE_INTERVAL_MS 16
#define TX_INTERVAL_MS 33
#define DEBUG_INTERVAL_MS 2000

volatile uint8_t disp_buf[4] = {0, 0, 0, 0};
static uint32_t last_refresh_tick = 0;
static uint8_t current_digit = 0;
#define DIGIT_ON_MS 2

static const uint8_t seg_digits[10] = {
    0b00111111, 0b00000110, 0b01011011, 0b01001111,
    0b01100110, 0b01101101, 0b01111101, 0b00000111,
    0b01111111, 0b01101111
};

// ?????? ? ??????????? ?????????
static uint8_t button_left_held = 0;
static uint8_t button_right_held = 0;
static uint8_t button_fire_held = 0;
static uint32_t button_fire_press_start = 0;
static uint32_t last_button_action = 0;
#define BUTTON_REPEAT_DELAY_MS 150
#define PAUSE_HOLD_TIME_MS 500

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_USART2_UART_Init(void);
/* USER CODE BEGIN PFP */
static void send_debug(const char *msg);
static uint8_t crc8(uint8_t *data, uint16_t len);
static void send_game_state(void);
static void send_menu_state(void);
static void send_explosion(int16_t x, int16_t y);
static void process_rx_data(void);
static void game_init(void);
static void game_start(void);
static void game_update(float dt);
static void menu_update(void);
static void player_update(float dt);
static void bullets_update(float dt);
static void enemies_update(float dt);
static void explosions_update(float dt);
static void check_collisions(void);
static void player_shoot(void);
static void enemy_shoot(Enemy *enemy);
static void spawn_enemy(int16_t x, uint8_t type, int8_t vx, int8_t vy);
static void create_explosion(int16_t x, int16_t y);
static void shift_out_byte(uint8_t b);
static void latch_pulse(void);
static void prepare_display_buffer(uint16_t score);
static void display_refresh_cycle(void);
static void handle_button_events(void);
static void cleanup_rx_buffer(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

static uint8_t crc8(uint8_t *data, uint16_t len)
{
    uint8_t crc = 0;
    for(uint16_t i = 0; i < len; i++) {
        crc ^= data[i];
        for(uint8_t j = 0; j < 8; j++) {
            if(crc & 0x80)
                crc = (crc << 1) ^ 0x07;
            else
                crc <<= 1;
        }
    }
    return crc;
}

static void send_debug(const char *msg)
{
    if(uart_tx_busy) return;
    
    uint16_t idx = 0;
    uint16_t msg_len = strlen(msg);
    if(msg_len > 100) msg_len = 100;
    
    tx_buffer[idx++] = START_BYTE;
    tx_buffer[idx++] = PACKET_DEBUG;
    
    for(uint16_t i = 0; i < msg_len; i++) {
        tx_buffer[idx++] = msg[i];
    }
    
    uint8_t crc_val = crc8(&tx_buffer[1], idx - 1);
    tx_buffer[idx++] = crc_val;
    tx_buffer[idx++] = END_BYTE;
    
    if(HAL_UART_Transmit_DMA(&huart2, tx_buffer, idx) == HAL_OK) {
        uart_tx_busy = 1;
    }
}

static void send_menu_state(void)
{
    if(uart_tx_busy) return;
    
    uint16_t idx = 0;
    tx_buffer[idx++] = START_BYTE;
    tx_buffer[idx++] = PACKET_MENU_STATE;
    tx_buffer[idx++] = game_state;
    tx_buffer[idx++] = selected_menu_item;
    tx_buffer[idx++] = (score >> 8) & 0xFF;
    tx_buffer[idx++] = score & 0xFF;
    
    uint8_t crc_val = crc8(&tx_buffer[1], idx - 1);
    tx_buffer[idx++] = crc_val;
    tx_buffer[idx++] = END_BYTE;
    
    if(HAL_UART_Transmit_DMA(&huart2, tx_buffer, idx) == HAL_OK) {
        uart_tx_busy = 1;
    }
}

static void send_explosion(int16_t x, int16_t y)
{
    if(uart_tx_busy) return;
    
    uint16_t idx = 0;
    tx_buffer[idx++] = START_BYTE;
    tx_buffer[idx++] = PACKET_EXPLOSION;
    tx_buffer[idx++] = (x >> 8) & 0xFF;
    tx_buffer[idx++] = x & 0xFF;
    tx_buffer[idx++] = (y >> 8) & 0xFF;
    tx_buffer[idx++] = y & 0xFF;
    
    uint8_t crc_val = crc8(&tx_buffer[1], idx - 1);
    tx_buffer[idx++] = crc_val;
    tx_buffer[idx++] = END_BYTE;
    
    if(HAL_UART_Transmit_DMA(&huart2, tx_buffer, idx) == HAL_OK) {
        uart_tx_busy = 1;
    }
}

static void send_game_state(void)
{
    if(uart_tx_busy) return;
		uint16_t idx = 0;
    if(idx + 50 > sizeof(tx_buffer)) return;
    
    
    tx_buffer[idx++] = START_BYTE;
    tx_buffer[idx++] = PACKET_GAME_STATE;
    
    tx_buffer[idx++] = (player.pos.x >> 8) & 0xFF;
    tx_buffer[idx++] = player.pos.x & 0xFF;
    tx_buffer[idx++] = (player.pos.y >> 8) & 0xFF;
    tx_buffer[idx++] = player.pos.y & 0xFF;
    tx_buffer[idx++] = player.hp;
    tx_buffer[idx++] = (score >> 8) & 0xFF;
    tx_buffer[idx++] = score & 0xFF;
    tx_buffer[idx++] = level;
    
    uint8_t enemy_count = 0;
    for(uint8_t i = 0; i < MAX_ENEMIES; i++) {
        if(enemies[i].active) enemy_count++;
    }
    tx_buffer[idx++] = enemy_count;
    
    for(uint8_t i = 0; i < MAX_ENEMIES && idx + 6 < sizeof(tx_buffer) - 10; i++) {
        if(enemies[i].active) {
            tx_buffer[idx++] = (enemies[i].pos.x >> 8) & 0xFF;
            tx_buffer[idx++] = enemies[i].pos.x & 0xFF;
            tx_buffer[idx++] = (enemies[i].pos.y >> 8) & 0xFF;
            tx_buffer[idx++] = enemies[i].pos.y & 0xFF;
            tx_buffer[idx++] = enemies[i].type;
            tx_buffer[idx++] = enemies[i].hp;
        }
    }
    
    uint8_t bullet_count = 0;
    for(uint8_t i = 0; i < MAX_BULLETS; i++) {
        if(bullets[i].active) bullet_count++;
    }
    tx_buffer[idx++] = bullet_count;
    
    for(uint8_t i = 0; i < MAX_BULLETS && idx + 4 < sizeof(tx_buffer) - 10; i++) {
        if(bullets[i].active) {
            tx_buffer[idx++] = (bullets[i].pos.x >> 8) & 0xFF;
            tx_buffer[idx++] = bullets[i].pos.x & 0xFF;
            tx_buffer[idx++] = (bullets[i].pos.y >> 8) & 0xFF;
            tx_buffer[idx++] = bullets[i].pos.y & 0xFF;
        }
    }
    
    uint8_t ebullet_count = 0;
    for(uint8_t i = 0; i < MAX_BULLETS; i++) {
        if(enemy_bullets[i].active) ebullet_count++;
    }
    tx_buffer[idx++] = ebullet_count;
    
    for(uint8_t i = 0; i < MAX_BULLETS && idx + 4 < sizeof(tx_buffer) - 10; i++) {
        if(enemy_bullets[i].active) {
            tx_buffer[idx++] = (enemy_bullets[i].pos.x >> 8) & 0xFF;
            tx_buffer[idx++] = enemy_bullets[i].pos.x & 0xFF;
            tx_buffer[idx++] = (enemy_bullets[i].pos.y >> 8) & 0xFF;
            tx_buffer[idx++] = enemy_bullets[i].pos.y & 0xFF;
        }
    }
    
    uint8_t crc_val = crc8(&tx_buffer[1], idx - 1);
    tx_buffer[idx++] = crc_val;
    tx_buffer[idx++] = END_BYTE;
    
    if(HAL_UART_Transmit_DMA(&huart2, tx_buffer, idx) == HAL_OK) {
        uart_tx_busy = 1;
    }
}

static void cleanup_rx_buffer(void)
{
    uint16_t dma_pos = RX_BUFFER_SIZE - __HAL_DMA_GET_COUNTER(&hdma_usart2_rx);
    
    // ???? ????? ???????? ????? ??? ?? 90%, ?????????? ?????? ??????
    uint16_t used = (dma_pos >= rx_write_pos) ? 
                    (dma_pos - rx_write_pos) : 
                    (RX_BUFFER_SIZE - rx_write_pos + dma_pos);
    
    if(used > (RX_BUFFER_SIZE * 9 / 10)) {
        rx_write_pos = dma_pos;
        send_debug("RX overflow");
    }
}

static void process_rx_data(void)
{
    uint16_t dma_pos = RX_BUFFER_SIZE - __HAL_DMA_GET_COUNTER(&hdma_usart2_rx);
    
    while(rx_write_pos != dma_pos) {
        uint8_t byte = rx_buffer[rx_write_pos];
        
        static uint8_t packet_state = 0;
        static uint8_t packet_type = 0;
        static uint8_t packet_data[10];
        static uint8_t packet_idx = 0;
        
        if(packet_state == 0 && byte == START_BYTE) {
            packet_state = 1;
            packet_idx = 0;
        }
        else if(packet_state == 1) {
            packet_type = byte;
            packet_state = 2;
        }
        else if(packet_state == 2) {
            packet_data[packet_idx++] = byte;
            
            if(packet_type == PACKET_START_GAME) {
                if(packet_idx >= 2 && packet_data[1] == END_BYTE) {
                    // ?????????? ???? ??? ??????
                    packet_state = 0;
                }
                else if(packet_idx > 2) packet_state = 0;
            }
            else if(packet_type == PACKET_SPAWN_ENEMY) {
                if(packet_idx >= 7 && packet_data[6] == END_BYTE) {
                    int16_t x = (packet_data[0] << 8) | packet_data[1];
                    uint8_t type = packet_data[2];
                    int8_t vx = (int8_t)packet_data[3];
                    int8_t vy = (int8_t)packet_data[4];
                    spawn_enemy(x, type, vx, vy);
                    packet_state = 0;
                }
                else if(packet_idx > 7) packet_state = 0;
            }
            else {
                packet_state = 0;
            }
        }
        
        rx_write_pos++;
        if(rx_write_pos >= RX_BUFFER_SIZE) rx_write_pos = 0;
    }
}

static void game_init(void)
{
    player.pos.x = SCREEN_WIDTH / 2;
    player.pos.y = SCREEN_HEIGHT - 80;
    player.hp = 100;
    player.shoot_cooldown = 0;
    
    memset(enemies, 0, sizeof(enemies));
    memset(bullets, 0, sizeof(bullets));
    memset(enemy_bullets, 0, sizeof(enemy_bullets));
    memset(explosions, 0, sizeof(explosions));
    
    score = 0;
    level = 1;
}

static void game_start(void)
{
    game_init();
    game_state = GAME_PLAYING;
    HAL_GPIO_WritePin(LED_D12_GPIO_Port, LED_D12_Pin, GPIO_PIN_SET);
    send_debug("Game Start");
}

static void menu_update(void)
{
    // ???? ??????????? ????? handle_button_events
    // ????? ?????? ?????????? ?????????
}

static void game_update(float dt)
{
    if(game_state != GAME_PLAYING) return;
    
    player_update(dt);
    bullets_update(dt);
    enemies_update(dt);
    explosions_update(dt);
    check_collisions();
    
    if(player.hp == 0) {
        game_state = GAME_OVER;
        HAL_GPIO_WritePin(LED_D12_GPIO_Port, LED_D12_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(LED_D11_GPIO_Port, LED_D11_Pin, GPIO_PIN_SET);
        selected_menu_item = MENU_ITEM_RESTART;
        send_debug("GAME OVER");
    }
}

static void player_update(float dt)
{
    if(player.shoot_cooldown > 0) player.shoot_cooldown--;
}

static void bullets_update(float dt)
{
    for(uint8_t i = 0; i < MAX_BULLETS; i++) {
        if(bullets[i].active) {
            bullets[i].pos.y += bullets[i].vel.y;
            if(bullets[i].pos.y < -20) bullets[i].active = 0;
        }
    }
    
    for(uint8_t i = 0; i < MAX_BULLETS; i++) {
        if(enemy_bullets[i].active) {
            enemy_bullets[i].pos.y += enemy_bullets[i].vel.y;
            if(enemy_bullets[i].pos.y > SCREEN_HEIGHT + 20) enemy_bullets[i].active = 0;
        }
    }
}

static void enemies_update(float dt)
{
    for(uint8_t i = 0; i < MAX_ENEMIES; i++) {
        if(enemies[i].active) {
            enemies[i].pos.x += enemies[i].vel_x / 5;
            enemies[i].pos.y += enemies[i].vel_y / 8;
            
            if(enemies[i].pos.y > SCREEN_HEIGHT + 50) {
                enemies[i].active = 0;
            }
            
            if(enemies[i].type == 1) {
                if(enemies[i].shoot_cooldown > 0) {
                    enemies[i].shoot_cooldown--;
                } else {
                    enemy_shoot(&enemies[i]);
                    enemies[i].shoot_cooldown = 120;
                }
            }
        }
    }
}

static void explosions_update(float dt)
{
    for(uint8_t i = 0; i < MAX_EXPLOSIONS; i++) {
        if(explosions[i].active) {
            explosions[i].frame++;
            if(explosions[i].frame >= 10) {
                explosions[i].active = 0;
            }
        }
    }
}

static void check_collisions(void)
{
    for(uint8_t b = 0; b < MAX_BULLETS; b++) {
        if(!bullets[b].active) continue;
        
        for(uint8_t e = 0; e < MAX_ENEMIES; e++) {
            if(!enemies[e].active) continue;
            
            int16_t dx = bullets[b].pos.x - enemies[e].pos.x;
            int16_t dy = bullets[b].pos.y - enemies[e].pos.y;
            
            if(dx > -20 && dx < 20 && dy > -20 && dy < 20) {
                bullets[b].active = 0;
                
                if(enemies[e].hp > 10) {
                    enemies[e].hp -= 10;
                } else {
                    create_explosion(enemies[e].pos.x, enemies[e].pos.y);
                    enemies[e].active = 0;
                    score += (enemies[e].type == 0) ? 10 : 25;
                }
                break;
            }
        }
    }
    
    for(uint8_t b = 0; b < MAX_BULLETS; b++) {
        if(!enemy_bullets[b].active) continue;
        
        int16_t dx = enemy_bullets[b].pos.x - player.pos.x;
        int16_t dy = enemy_bullets[b].pos.y - player.pos.y;
        
        if(dx > -30 && dx < 30 && dy > -20 && dy < 20) {
            enemy_bullets[b].active = 0;
            if(player.hp > 10) player.hp -= 10;
            else player.hp = 0;
        }
    }
    
    for(uint8_t e = 0; e < MAX_ENEMIES; e++) {
        if(!enemies[e].active) continue;
        
        int16_t dx = enemies[e].pos.x - player.pos.x;
        int16_t dy = enemies[e].pos.y - player.pos.y;
        
        if(dx > -40 && dx < 40 && dy > -30 && dy < 30) {
            create_explosion(enemies[e].pos.x, enemies[e].pos.y);
            enemies[e].active = 0;
            if(player.hp > 20) player.hp -= 20;
            else player.hp = 0;
        }
    }
}

static void player_shoot(void)
{
    if(player.shoot_cooldown > 0) return;
    
    for(uint8_t i = 0; i < MAX_BULLETS; i++) {
        if(!bullets[i].active) {
            bullets[i].active = 1;
            bullets[i].pos.x = player.pos.x;
            bullets[i].pos.y = player.pos.y - 20;
            bullets[i].vel.x = 0;
            bullets[i].vel.y = -8;
            player.shoot_cooldown = 18;
            break;
        }
    }
}

static void enemy_shoot(Enemy *enemy)
{
    for(uint8_t i = 0; i < MAX_BULLETS; i++) {
        if(!enemy_bullets[i].active) {
            enemy_bullets[i].active = 1;
            enemy_bullets[i].pos.x = enemy->pos.x;
            enemy_bullets[i].pos.y = enemy->pos.y + 20;
            enemy_bullets[i].vel.x = 0;
            enemy_bullets[i].vel.y = 4;
            break;
        }
    }
}

static void spawn_enemy(int16_t x, uint8_t type, int8_t vx, int8_t vy)
{
    for(uint8_t i = 0; i < MAX_ENEMIES; i++) {
        if(!enemies[i].active) {
            enemies[i].active = 1;
            enemies[i].pos.x = x;
            enemies[i].pos.y = -50;
            enemies[i].vel_x = vx;
            enemies[i].vel_y = vy;
            enemies[i].type = type;
            enemies[i].hp = (type == 0) ? 20 : 40;
            enemies[i].max_hp = enemies[i].hp;
            enemies[i].shoot_cooldown = 60;
            HAL_GPIO_TogglePin(LED_D10_GPIO_Port, LED_D10_Pin);
            break;
        }
    }
}

static void create_explosion(int16_t x, int16_t y)
{
    for(uint8_t i = 0; i < MAX_EXPLOSIONS; i++) {
        if(!explosions[i].active) {
            explosions[i].active = 1;
            explosions[i].pos.x = x;
            explosions[i].pos.y = y;
            explosions[i].frame = 0;
            send_explosion(x, y);
            break;
        }
    }
}

/* ??????????? main.c - ?????? ????? create_explosion */

static void shift_out_byte(uint8_t b)
{
    for(int i = 7; i >= 0; --i) {
        uint8_t bit = (b >> i) & 0x1;
        HAL_GPIO_WritePin(DATA_DISP_GPIO_Port, DATA_DISP_Pin, 
                         bit ? GPIO_PIN_SET : GPIO_PIN_RESET);
        HAL_GPIO_WritePin(CLK_DISP_GPIO_Port, CLK_DISP_Pin, GPIO_PIN_SET);
        HAL_GPIO_WritePin(CLK_DISP_GPIO_Port, CLK_DISP_Pin, GPIO_PIN_RESET);
    }
}

static void latch_pulse(void)
{
    HAL_GPIO_WritePin(LATCH_DISP_GPIO_Port, LATCH_DISP_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(LATCH_DISP_GPIO_Port, LATCH_DISP_Pin, GPIO_PIN_RESET);
}

static void prepare_display_buffer(uint16_t score_val)
{
    uint8_t d3 = (score_val / 1000) % 10;
    uint8_t d2 = (score_val / 100) % 10;
    uint8_t d1 = (score_val / 10) % 10;
    uint8_t d0 = score_val % 10;
    
    disp_buf[0] = seg_digits[d3];
    disp_buf[1] = seg_digits[d2];
    disp_buf[2] = seg_digits[d1];
    disp_buf[3] = seg_digits[d0];
}

static void display_refresh_cycle(void)
{
    uint32_t now = HAL_GetTick();
    
    if((now - last_refresh_tick) >= DIGIT_ON_MS) {
        uint8_t segments = disp_buf[current_digit];
        uint8_t digit_mask = (1 << current_digit);
        
        shift_out_byte(~segments);
        shift_out_byte(digit_mask);
        latch_pulse();
        
        current_digit++;
        if(current_digit >= 4) current_digit = 0;
        
        last_refresh_tick = now;
    }
}

static void handle_button_events(void)
{
    uint32_t now = HAL_GetTick();

    // ??? ????
    if(game_state == GAME_MENU || game_state == GAME_PAUSED || game_state == GAME_OVER) {

        // LEFT - ?????????? ????? ????
        if(button_left_held && (now - last_button_action) > BUTTON_REPEAT_DELAY_MS) {
            if(selected_menu_item > 0) {
                selected_menu_item--;
            } else {
                selected_menu_item = MENU_ITEM_COUNT - 1;
            }
            last_button_action = now;
        }

        // RIGHT - ????????? ????? ????
        if(button_right_held && (now - last_button_action) > BUTTON_REPEAT_DELAY_MS) {
            selected_menu_item++;
            if(selected_menu_item >= MENU_ITEM_COUNT) {
                selected_menu_item = 0;
            }
            last_button_action = now;
        }

        // FIRE - ????? ?????? ???? (?????? ??? ??????????)
        if(!button_fire_held && button_fire_press_start > 0) {
            uint32_t press_duration = now - button_fire_press_start;
            button_fire_press_start = 0;

            // ???????? ??????? - ?????
            if(press_duration < PAUSE_HOLD_TIME_MS) {
                switch(selected_menu_item) {
                    case MENU_ITEM_START:
                        if(game_state == GAME_MENU) {
                            game_start();
                        }
                        break;
                    case MENU_ITEM_CONTINUE:
                        if(game_state == GAME_PAUSED) {
                            game_state = GAME_PLAYING;
                            send_debug("Resume");
                        }
                        break;
                    case MENU_ITEM_RESTART:
                        game_start();
                        break;
                    case MENU_ITEM_EXIT:
                        game_state = GAME_MENU;
                        selected_menu_item = MENU_ITEM_START;
                        break;
                }
            }
        }
				
				}
    
    
    
    // ??? ????
    if(game_state == GAME_PLAYING) {
        
        // LEFT - ???????? ?????
        if(button_left_held) {
            player.pos.x -= 5;
            if(player.pos.x < 30) player.pos.x = 30;
        }
        
        // RIGHT - ???????? ??????
        if(button_right_held) {
            player.pos.x += 5;
            if(player.pos.x > SCREEN_WIDTH - 30) player.pos.x = SCREEN_WIDTH - 30;
        }
        
        // FIRE - ???????? (????????? ???? ??????)
        if(button_fire_held) {
            player_shoot();
        }
        
        // ?????????? ????????? FIRE ??? ?????
        if(button_fire_held && (now - button_fire_press_start) > PAUSE_HOLD_TIME_MS) {
            game_state = GAME_PAUSED;
            selected_menu_item = MENU_ITEM_CONTINUE;
            button_fire_press_start = 0;
            send_debug("Paused");
        }
    }
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_USART2_UART_Init();
  /* USER CODE BEGIN 2 */
    HAL_Delay(100);
    
    // ?????? DMA ??? ??????
    HAL_UART_Receive_DMA(&huart2, rx_buffer, RX_BUFFER_SIZE);
    
    game_init();
    
    HAL_GPIO_WritePin(LED_D10_GPIO_Port, LED_D10_Pin, GPIO_PIN_SET);
    
    send_debug("System Ready");
    
    last_update_time = HAL_GetTick();
    last_tx_time = HAL_GetTick();
    last_debug_time = HAL_GetTick();
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
    while (1)
    {
        uint32_t now = HAL_GetTick();
        
        // ????????? ???????? ??????
        process_rx_data();
        cleanup_rx_buffer();
        
        // ?????????? ??????? (?????????)
        prepare_display_buffer(score);
        display_refresh_cycle();
        
        // ????????? ??????
        handle_button_events();
        
        // ?????????? ??????? ??????
        if((now - last_update_time) >= UPDATE_INTERVAL_MS) {
            float dt = (now - last_update_time) / 1000.0f;
            
            if(game_state == GAME_PLAYING) {
                game_update(dt);
            } else {
                menu_update();
            }
            
            last_update_time = now;
        }
        
        // ???????? ?????????
        if((now - last_tx_time) >= TX_INTERVAL_MS && !uart_tx_busy) {
            if(game_state == GAME_PLAYING) {
                send_game_state();
            } else {
                send_menu_state();
            }
            last_tx_time = now;
        }
        
        // ????????????? ?????????? ??????????
        if((now - last_debug_time) >= DEBUG_INTERVAL_MS) {
            if(game_state == GAME_PLAYING) {
                // snprintf(debug_buffer, sizeof(debug_buffer), 
                //       "HP:%d S:%d E:%d", player.hp, score, level);
                //send_debug(debug_buffer);
            }
            last_debug_time = now;
        }
        
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI_DIV2;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL16;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{

  /* DMA controller clock enable */
  __HAL_RCC_DMA1_CLK_ENABLE();

  /* DMA interrupt init */
  /* DMA1_Channel6_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel6_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel6_IRQn);
  /* DMA1_Channel7_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel7_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel7_IRQn);

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
/* USER CODE BEGIN MX_GPIO_Init_1 */
/* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, LED_D12_Pin|LED_D11_Pin|CLK_DISP_Pin|DATA_DISP_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(USER_BUZZER_GPIO_Port, USER_BUZZER_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, LATCH_DISP_Pin|LED_D10_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : CANON_LEFT_Pin CANON_RIGHT_Pin */
  GPIO_InitStruct.Pin = CANON_LEFT_Pin|CANON_RIGHT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING_FALLING;
  GPIO_InitStruct.Pull = GPIO_PULLDOWN;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : LED_D12_Pin LED_D11_Pin */
  GPIO_InitStruct.Pin = LED_D12_Pin|LED_D11_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pin : CANON_FIRE_Pin */
  GPIO_InitStruct.Pin = CANON_FIRE_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING_FALLING;
  GPIO_InitStruct.Pull = GPIO_PULLDOWN;
  HAL_GPIO_Init(CANON_FIRE_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : CLK_DISP_Pin DATA_DISP_Pin */
  GPIO_InitStruct.Pin = CLK_DISP_Pin|DATA_DISP_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_PULLDOWN;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pin : USER_BUZZER_Pin */
  GPIO_InitStruct.Pin = USER_BUZZER_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_OD;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(USER_BUZZER_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : LATCH_DISP_Pin */
  GPIO_InitStruct.Pin = LATCH_DISP_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_PULLDOWN;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LATCH_DISP_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : LED_D10_Pin */
  GPIO_InitStruct.Pin = LED_D10_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LED_D10_GPIO_Port, &GPIO_InitStruct);

  /* EXTI interrupt init*/
  HAL_NVIC_SetPriority(EXTI0_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI0_IRQn);

  HAL_NVIC_SetPriority(EXTI1_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI1_IRQn);

  HAL_NVIC_SetPriority(EXTI4_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI4_IRQn);

/* USER CODE BEGIN MX_GPIO_Init_2 */
/* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/**
  * @brief  EXTI line detection callbacks
  */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    uint32_t now = HAL_GetTick();
    
    if(GPIO_Pin == CANON_LEFT_Pin) {
        GPIO_PinState state = HAL_GPIO_ReadPin(CANON_LEFT_GPIO_Port, CANON_LEFT_Pin);
        if(state == GPIO_PIN_RESET) {  // ?????? ?????? (???????? LOW)
            button_left_held = 1;
            last_button_action = now;
        } else {  // ?????? ????????
            button_left_held = 0;
        }
    }
    
    if(GPIO_Pin == CANON_RIGHT_Pin) {
        GPIO_PinState state = HAL_GPIO_ReadPin(CANON_RIGHT_GPIO_Port, CANON_RIGHT_Pin);
        if(state == GPIO_PIN_RESET) {
            button_right_held = 1;
            last_button_action = now;
        } else {
            button_right_held = 0;
        }
    }
    
    if(GPIO_Pin == CANON_FIRE_Pin) {
        GPIO_PinState state = HAL_GPIO_ReadPin(CANON_FIRE_GPIO_Port, CANON_FIRE_Pin);
        if(state == GPIO_PIN_RESET) {
            button_fire_held = 1;
            button_fire_press_start = now;
        } else {
            button_fire_held = 0;
            // ????????? ?????????? ????? ? handle_button_events
        }
    }
}

/**
  * @brief  Tx Transfer completed callback
  */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if(huart->Instance == USART2) {
        uart_tx_busy = 0;
    }
}

/**
  * @brief  UART error callbacks
  */
void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if(huart->Instance == USART2) {
        uart_tx_busy = 0;
        // ?????????? ?????? ??? ??????
        HAL_UART_Receive_DMA(&huart2, rx_buffer, RX_BUFFER_SIZE);
    }
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
