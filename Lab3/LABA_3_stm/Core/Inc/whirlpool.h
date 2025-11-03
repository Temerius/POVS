/* whirlpool.h - Водовороты с полной логикой на STM32 */

#ifndef WHIRLPOOL_H
#define WHIRLPOOL_H

#include "game_config.h"
#include "game_types.h"
#include "utils.h"

// Водоворот
typedef struct {
    Vector2 position;
    float radius;
    float rotation;
    uint8_t used_recently;
    uint16_t cooldown_timer;
    float animation_phase;
} Whirlpool;

// Полное определение менеджера водоворотов
struct WhirlpoolManager {
    Whirlpool whirlpools[WHIRLPOOL_MAX_COUNT];
    uint8_t whirlpool_count;
};

// Инициализация менеджера водоворотов
void WhirlpoolManager_Init(struct WhirlpoolManager* manager);

// Обновление всех водоворотов и обработка коллизий
void WhirlpoolManager_Update(struct WhirlpoolManager* manager, GameState* state);

// Добавление нового водоворота
uint8_t WhirlpoolManager_Add(struct WhirlpoolManager* manager, float x, float y);

// Очистка старых водоворотов
void WhirlpoolManager_Cleanup(struct WhirlpoolManager* manager, float threshold_y);

// Проверка коллизии водоворота с точкой
uint8_t Whirlpool_CollidesWith(Whirlpool* whirlpool, float x, float y, float radius);

// Поиск подходящего водоворота для телепортации
Whirlpool* WhirlpoolManager_FindTarget(struct WhirlpoolManager* manager, Whirlpool* current, float world_top);

// Создание нового водоворота для телепортации
Whirlpool* WhirlpoolManager_CreateForTeleport(struct WhirlpoolManager* manager, 
                                             Whirlpool* current, 
                                             float world_top,
                                             Obstacle* obstacles,
                                             uint8_t obstacle_count);

// Телепортация игрока
void WhirlpoolManager_TeleportPlayer(struct WhirlpoolManager* manager, 
                                    Whirlpool* source, 
                                    Whirlpool* target, 
                                    Player* player);

#endif // WHIRLPOOL_H