	/* USER CODE BEGIN Header */
	/**
		* @file           : main.c
		* @brief          : Sea Defenders - FINAL VERSION with Mirror Logic
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

	static uint8_t last_game_state = 255;
	static uint8_t last_selected_item = 255;

	static char debug_buffer[128];

	#define START_BYTE 0xAA
	#define END_BYTE 0x55
	#define PACKET_GAME_STATE 0x01
	#define PACKET_MENU_STATE 0x02
	#define PACKET_DEBUG 0x03
	#define PACKET_EXPLOSION 0x04
	#define PACKET_SPAWN_ENEMY 0x10
	#define PACKET_START_GAME 0x11
	#define PACKET_SPAWN_ISLAND 0x13
	#define PACKET_SPAWN_WHIRLPOOL 0x14

	#define MAX_ENEMIES 10
	#define MAX_BULLETS 10
	#define MAX_EXPLOSIONS 5
	#define MAX_ISLANDS 20
	#define MAX_WHIRLPOOLS 5
	#define SCREEN_WIDTH 800
	#define SCREEN_HEIGHT 600
	
	// Константы для Sea Defenders
	#define MAX_SHIP_ANGLE 45        // Максимальный угол поворота корабля
	#define ANGLE_STEP 15           // Шаг поворота за нажатие
	#define ANGLE_RETURN_SPEED 2    // Скорость возврата к прямому курсу
	#define SHIP_SPEED 3            // Скорость движения корабля вперед

	typedef struct {
			int16_t x;
			int16_t y;
	} Vector2;

	typedef struct {
			Vector2 pos;
			uint8_t hp;
			uint8_t shoot_cooldown;
			int8_t angle;        // Угол поворота корабля (-45° до +45°)
			uint8_t last_move;  // Последнее движение: 0=влево, 1=вправо, 2=прямо
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
			uint8_t type;        // 0=шлюпка, 1=галеон
			uint8_t active;
			uint8_t shoot_cooldown;
			uint8_t shoot_pattern; // Паттерн стрельбы для галеонов
	} Enemy;

	typedef struct {
			Vector2 pos;
			uint8_t frame;
			uint8_t active;
	} Explosion;

	typedef struct {
			Vector2 pos;
			uint8_t size;
			uint8_t active;
	} Island;

	typedef struct {
			Vector2 pos;
			Vector2 target_pos;  // Куда телепортирует
			uint8_t active;
	} Whirlpool;

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
	static Island islands[MAX_ISLANDS];
	static Whirlpool whirlpools[MAX_WHIRLPOOLS];

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
	static uint32_t last_move_time = 0;        // ????????: ??? ???????? ????????
	static uint8_t pause_triggered = 0;  
	#define BUTTON_REPEAT_DELAY_MS 150
	#define PAUSE_HOLD_TIME_MS 500
	#define MOVE_DELAY_MS 30          // ???????? ????? ??????????
	#define FIRE_COOLDOWN_FRAMES 18


	static uint8_t button_left_pressed = 0;  
	static uint8_t button_right_pressed = 0;
	static uint8_t button_fire_released = 0; 


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
	static void islands_update(float dt);
	static void whirlpools_update(float dt);
	static void check_collisions(void);
	static void player_shoot(void);
	static void enemy_shoot(Enemy *enemy);
	static void spawn_enemy(int16_t x, uint8_t type, int8_t vx, int8_t vy);
	static void create_explosion(int16_t x, int16_t y);
	static void create_island(int16_t x, int16_t y, uint8_t size);
	static void create_whirlpool(int16_t x, int16_t y, int16_t target_x, int16_t target_y);
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
			tx_buffer[idx++] = (int8_t)player.angle;  // Угол корабля
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
							else if(packet_type == PACKET_SPAWN_ISLAND) {
									if(packet_idx >= 6 && packet_data[5] == END_BYTE) {
											int16_t x = (packet_data[0] << 8) | packet_data[1];
											int16_t y = (packet_data[2] << 8) | packet_data[3];
											uint8_t size = packet_data[4];
											create_island(x, y, size);
											packet_state = 0;
									}
									else if(packet_idx > 6) packet_state = 0;
							}
							else if(packet_type == PACKET_SPAWN_WHIRLPOOL) {
									if(packet_idx >= 9 && packet_data[8] == END_BYTE) {
											int16_t x = (packet_data[0] << 8) | packet_data[1];
											int16_t y = (packet_data[2] << 8) | packet_data[3];
											int16_t target_x = (packet_data[4] << 8) | packet_data[5];
											int16_t target_y = (packet_data[6] << 8) | packet_data[7];
											create_whirlpool(x, y, target_x, target_y);
											packet_state = 0;
									}
									else if(packet_idx > 9) packet_state = 0;
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
			player.angle = 0;           // Корабль смотрит прямо
			player.last_move = 2;        // Прямо
			
			memset(enemies, 0, sizeof(enemies));
			memset(bullets, 0, sizeof(bullets));
			memset(enemy_bullets, 0, sizeof(enemy_bullets));
			memset(explosions, 0, sizeof(explosions));
			memset(islands, 0, sizeof(islands));
			memset(whirlpools, 0, sizeof(whirlpools));
			
			score = 0;
			level = 1;
	}

	static void game_start(void)
{
    game_init();
    game_state = GAME_PLAYING;
    
    // ????? ???? ????????? ??????
    pause_triggered = 0;
    button_fire_press_start = 0;
    button_fire_held = 0;       // ????????: ????? held
    button_fire_released = 0;   // ????????: ????? released
    last_move_time = 0;
    
    HAL_GPIO_WritePin(LED_D12_GPIO_Port, LED_D12_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(LED_D11_GPIO_Port, LED_D11_Pin, GPIO_PIN_RESET);
    
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
			islands_update(dt);
			whirlpools_update(dt);
			check_collisions();
			
			if(player.hp == 0) {
					game_state = GAME_OVER;
					selected_menu_item = 0; // Restart
					
					// ????? ????????? ??????
					pause_triggered = 0;
					button_fire_press_start = 0;
					button_fire_held = 0;
					
					// LED ?????????
					HAL_GPIO_WritePin(LED_D12_GPIO_Port, LED_D12_Pin, GPIO_PIN_RESET);
					HAL_GPIO_WritePin(LED_D11_GPIO_Port, LED_D11_Pin, GPIO_PIN_SET);
					
					send_debug("GAME OVER");
			}
	}

	static void player_update(float dt)
	{
			if(player.shoot_cooldown > 0) player.shoot_cooldown--;
			
			// Автоматическое движение вперед
			player.pos.y -= SHIP_SPEED;
			
			// Постепенный возврат к прямому курсу
			if(player.angle > 0) {
					player.angle -= ANGLE_RETURN_SPEED;
					if(player.angle < 0) player.angle = 0;
			} else if(player.angle < 0) {
					player.angle += ANGLE_RETURN_SPEED;
					if(player.angle > 0) player.angle = 0;
			}
			
			// Ограничение по Y (если корабль вышел за экран)
			if(player.pos.y < -50) {
					player.pos.y = SCREEN_HEIGHT + 50;
			}
	}

	static void bullets_update(float dt)
	{
			for(uint8_t i = 0; i < MAX_BULLETS; i++) {
					if(bullets[i].active) {
							bullets[i].pos.x += bullets[i].vel.x;
							bullets[i].pos.y += bullets[i].vel.y;
							
							// Удаление пуль за границами экрана
							if(bullets[i].pos.y < -20 || bullets[i].pos.x < -20 || bullets[i].pos.x > SCREEN_WIDTH + 20) {
									bullets[i].active = 0;
							}
					}
			}
			
			for(uint8_t i = 0; i < MAX_BULLETS; i++) {
					if(enemy_bullets[i].active) {
							enemy_bullets[i].pos.x += enemy_bullets[i].vel.x;
							enemy_bullets[i].pos.y += enemy_bullets[i].vel.y;
							
							if(enemy_bullets[i].pos.y > SCREEN_HEIGHT + 20 || enemy_bullets[i].pos.x < -20 || enemy_bullets[i].pos.x > SCREEN_WIDTH + 20) {
									enemy_bullets[i].active = 0;
							}
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
							
							// Галеоны стреляют
							if(enemies[i].type == 1) {
									if(enemies[i].shoot_cooldown > 0) {
											enemies[i].shoot_cooldown--;
									} else {
											enemy_shoot(&enemies[i]);
											enemies[i].shoot_cooldown = 120;
									}
							}
							
							// Шлюпки быстрее и маневреннее
							if(enemies[i].type == 0) {
									enemies[i].pos.x += enemies[i].vel_x / 3; // Быстрее по X
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

	static void islands_update(float dt)
	{
			// Острова статичны, но можно добавить анимацию
			for(uint8_t i = 0; i < MAX_ISLANDS; i++) {
					if(islands[i].active) {
							// Острова могут медленно дрейфовать
							islands[i].pos.y += 1;
							if(islands[i].pos.y > SCREEN_HEIGHT + 100) {
									islands[i].active = 0;
							}
					}
			}
	}

	static void whirlpools_update(float dt)
	{
			// Водовороты анимируются
			for(uint8_t i = 0; i < MAX_WHIRLPOOLS; i++) {
					if(whirlpools[i].active) {
							// Водовороты могут двигаться
							whirlpools[i].pos.y += 1;
							if(whirlpools[i].pos.y > SCREEN_HEIGHT + 100) {
									whirlpools[i].active = 0;
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
			
			// Проверка столкновений с островами
			for(uint8_t i = 0; i < MAX_ISLANDS; i++) {
					if(!islands[i].active) continue;
					
					int16_t dx = islands[i].pos.x - player.pos.x;
					int16_t dy = islands[i].pos.y - player.pos.y;
					uint8_t radius = islands[i].size / 2;
					
					if(dx > -radius && dx < radius && dy > -radius && dy < radius) {
							// Столкновение с островом - урон
							if(player.hp > 10) player.hp -= 10;
							else player.hp = 0;
					}
			}
			
			// Проверка телепортации через водовороты
			for(uint8_t w = 0; w < MAX_WHIRLPOOLS; w++) {
					if(!whirlpools[w].active) continue;
					
					int16_t dx = whirlpools[w].pos.x - player.pos.x;
					int16_t dy = whirlpools[w].pos.y - player.pos.y;
					
					if(dx > -20 && dx < 20 && dy > -20 && dy < 20) {
							// Телепортация
							player.pos.x = whirlpools[w].target_pos.x;
							player.pos.y = whirlpools[w].target_pos.y;
							send_debug("Teleport!");
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
							
							// Зеркальная логика: стрельба в противоположную сторону от поворота
							if(player.last_move == 0) { // Поворот влево = стрельба вправо
									bullets[i].vel.x = 4;
									bullets[i].vel.y = -6;
							} else if(player.last_move == 1) { // Поворот вправо = стрельба влево
									bullets[i].vel.x = -4;
									bullets[i].vel.y = -6;
							} else { // Прямо
									bullets[i].vel.x = 0;
									bullets[i].vel.y = -8;
							}
							
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
							
							// Разные характеристики для разных типов
							if(type == 0) { // Шлюпка
									enemies[i].hp = 20;
									enemies[i].max_hp = 20;
									enemies[i].shoot_cooldown = 0; // Не стреляет
							} else { // Галеон
									enemies[i].hp = 40;
									enemies[i].max_hp = 40;
									enemies[i].shoot_cooldown = 60;
							}
							
							enemies[i].shoot_pattern = 0;
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

	static void create_island(int16_t x, int16_t y, uint8_t size)
	{
			for(uint8_t i = 0; i < MAX_ISLANDS; i++) {
					if(!islands[i].active) {
							islands[i].active = 1;
							islands[i].pos.x = x;
							islands[i].pos.y = y;
							islands[i].size = size;
							break;
					}
			}
	}

	static void create_whirlpool(int16_t x, int16_t y, int16_t target_x, int16_t target_y)
	{
			for(uint8_t i = 0; i < MAX_WHIRLPOOLS; i++) {
					if(!whirlpools[i].active) {
							whirlpools[i].active = 1;
							whirlpools[i].pos.x = x;
							whirlpools[i].pos.y = y;
							whirlpools[i].target_pos.x = target_x;
							whirlpools[i].target_pos.y = target_y;
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

    // ??? ???? (MENU, PAUSED, GAME_OVER)
    if(game_state == GAME_MENU || game_state == GAME_PAUSED || game_state == GAME_OVER) {

        // ?????????? ?????????? ??????? ???? ? ??????????? ?? ?????????
        uint8_t menu_items_count = 0;
        if(game_state == GAME_MENU) {
            menu_items_count = 2; // Start, Exit
        } else if(game_state == GAME_PAUSED) {
            menu_items_count = 3; // Continue, Restart, Exit
        } else if(game_state == GAME_OVER) {
            menu_items_count = 2; // Restart, Exit
        }

        // LEFT - переключение пункта меню (циклично)
        if(button_left_pressed) {
            button_left_pressed = 0;
            if(selected_menu_item > 0) {
                selected_menu_item--;
            } else {
                selected_menu_item = menu_items_count - 1;
            }
            send_debug("Menu Left");
        }

        // RIGHT - переключение пункта меню (циклично)
        if(button_right_pressed) {
            button_right_pressed = 0;
            selected_menu_item++;
            if(selected_menu_item >= menu_items_count) {
                selected_menu_item = 0;
            }
            send_debug("Menu Right");
        }

        // FIRE - выбор пункта меню
        if(button_fire_released) {
            uint32_t press_duration = button_fire_released;
            button_fire_released = 0; // сбрасываем флаг!
            
            send_debug("Menu Fire");
            
            // Короткое нажатие - выбор пункта меню
            if(press_duration < PAUSE_HOLD_TIME_MS) {
                if(game_state == GAME_MENU) {
                    // ????: [Start=0, Exit=1]
                    if(selected_menu_item == 0) { // Start
                        game_start();
                    } else if(selected_menu_item == 1) { // Exit
                        // ???????? ? ????
                    }
                } 
                else if(game_state == GAME_PAUSED) {
                    // ?????: [Continue=0, Restart=1, Exit=2]
                    if(selected_menu_item == 0) { // Continue
                        game_state = GAME_PLAYING;
                        pause_triggered = 0;
                        send_debug("Resume");
                    } else if(selected_menu_item == 1) { // Restart
                        game_start();
                        pause_triggered = 0;
                    } else if(selected_menu_item == 2) { // Exit
                        game_state = GAME_MENU;
                        selected_menu_item = 0;
                        pause_triggered = 0;
                    }
                }
                else if(game_state == GAME_OVER) {
                    // Game Over: [Restart=0, Exit=1]
                    if(selected_menu_item == 0) { // Restart
                        game_start();
                    } else if(selected_menu_item == 1) { // Exit
                        game_state = GAME_MENU;
                        selected_menu_item = 0;
                    }
                }
            }
            // ???? ??????? ??????? - ?????? ?????????? (??? ???? ????????? ??? ?????)
        }
    }
    
    // ??? ???? (PLAYING)
    if(game_state == GAME_PLAYING) {
        
        // ?????: ?????????? button_fire_released ???? ?? ??????? ?? ??????????? ?????????
        if(button_fire_released) {
            button_fire_released = 0;
        }
        
        // LEFT - поворот влево (зеркальная логика)
        if(button_left_held && (now - last_move_time) > MOVE_DELAY_MS) {
            if(player.angle > -MAX_SHIP_ANGLE) {
                player.angle -= ANGLE_STEP;
                if(player.angle < -MAX_SHIP_ANGLE) player.angle = -MAX_SHIP_ANGLE;
            }
            player.last_move = 0; // Запомнили поворот влево
            last_move_time = now;
        }
        
        // RIGHT - поворот вправо (зеркальная логика)
        if(button_right_held && (now - last_move_time) > MOVE_DELAY_MS) {
            if(player.angle < MAX_SHIP_ANGLE) {
                player.angle += ANGLE_STEP;
                if(player.angle > MAX_SHIP_ANGLE) player.angle = MAX_SHIP_ANGLE;
            }
            player.last_move = 1; // Запомнили поворот вправо
            last_move_time = now;
        }
        
        // FIRE - ???????? ? ?????
        if(button_fire_held) {
            // ???????? ?? ?????????? ????????? ??? ?????
            if(!pause_triggered && button_fire_press_start > 0 && 
               (now - button_fire_press_start) > PAUSE_HOLD_TIME_MS) {
                // ????? ?????????!
                game_state = GAME_PAUSED;
                selected_menu_item = 0; // Continue
                pause_triggered = 1;
                send_debug("Paused");
            } else if(!pause_triggered) {
                // ??????? ???????? (?????? ???? ????? ??? ?? ?????????)
                player_shoot();
            }
        }
        
        // ????? ????? ????? ??? ?????????? ??????
        if(!button_fire_held && pause_triggered) {
            pause_triggered = 0;
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
			
			last_game_state = game_state;
			last_selected_item = selected_menu_item;
			pause_triggered = 0;
			last_move_time = 0;
			button_left_pressed = 0;   // ????????
			button_right_pressed = 0; 
			button_fire_released = 0;
			
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
					// ???????? ?????????
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
									// ? ???? ?????????? ?????? ???
									send_game_state();
							} else {
									// ? ???? ?????????? ?????? ??? ??????????
									if (last_game_state != game_state || last_selected_item != selected_menu_item) {
											send_menu_state();
											last_game_state = game_state;
											last_selected_item = selected_menu_item;
									}
							}
							last_tx_time = now;
					}
					
					// ????????????? ?????????? ??????????
					if((now - last_debug_time) >= DEBUG_INTERVAL_MS) {
							if(game_state == GAME_PLAYING) {
									snprintf(debug_buffer, sizeof(debug_buffer), 
													"HP:%d S:%d L:%d", player.hp, score, level);
									send_debug(debug_buffer);
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
    GPIO_PinState state;
    
    if(GPIO_Pin == CANON_LEFT_Pin) {
        state = HAL_GPIO_ReadPin(CANON_LEFT_GPIO_Port, CANON_LEFT_Pin);
        if(state == GPIO_PIN_SET) {  
            button_left_held = 1;
            button_left_pressed = 1;
            last_button_action = now;
            last_move_time = now - MOVE_DELAY_MS;
        } else {  
            button_left_held = 0;
        }
    }
    
    if(GPIO_Pin == CANON_RIGHT_Pin) {
        state = HAL_GPIO_ReadPin(CANON_RIGHT_GPIO_Port, CANON_RIGHT_Pin);
        if(state == GPIO_PIN_SET) {
            button_right_held = 1;
            button_right_pressed = 1;
            last_button_action = now;
            last_move_time = now - MOVE_DELAY_MS;
        } else {
            button_right_held = 0;
        }
    }
    
    if(GPIO_Pin == CANON_FIRE_Pin) {
        state = HAL_GPIO_ReadPin(CANON_FIRE_GPIO_Port, CANON_FIRE_Pin);
        if(state == GPIO_PIN_SET) {
            button_fire_held = 1;
            button_fire_press_start = now;
        } else {
            button_fire_held = 0;
            
            if(button_fire_press_start > 0) {
                uint32_t duration = now - button_fire_press_start;
                button_fire_released = duration;
                button_fire_press_start = 0;
            }
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
