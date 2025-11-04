/* whirlpool.c - Реализация водоворотов с полной логикой на STM32 (ИСПРАВЛЕНО) */

#include "whirlpool.h"
#include <string.h>
#include <math.h>

void WhirlpoolManager_Init(struct WhirlpoolManager* manager) {
    memset(manager->whirlpools, 0, sizeof(manager->whirlpools));
    manager->whirlpool_count = 0;
}

void WhirlpoolManager_Update(struct WhirlpoolManager* manager, GameState* state) {
    // 1. Обновление анимации и cooldown для всех водоворотов
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        Whirlpool* whirlpool = &manager->whirlpools[i];
        
        // Обновление анимации
        whirlpool->rotation = fmodf(whirlpool->rotation + WHIRLPOOL_ROTATION_SPEED, 360.0f);
        whirlpool->animation_phase = fmodf(whirlpool->animation_phase + WHIRLPOOL_ANIMATION_SPEED, 2.0f * PI);
        
        // Обновление cooldown
        if (whirlpool->cooldown_timer > 0) {
            whirlpool->cooldown_timer--;
            if (whirlpool->cooldown_timer == 0) {
                whirlpool->used_recently = 0;
            }
        }
    }
    
    // 2. ИСПРАВЛЕНО: Проверка коллизии с игроком и телепортация
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        Whirlpool* whirlpool = &manager->whirlpools[i];
        
        // Проверка коллизии с игроком (только если не использован недавно)
        if (!whirlpool->used_recently && 
            Whirlpool_CollidesWith(whirlpool, 
                                  state->player.position.x, 
                                  state->player.position.y, 
                                  COLLISION_RADIUS_PLAYER)) {
            
            // Поиск подходящего водоворота для телепортации
            Whirlpool* target = WhirlpoolManager_FindTarget(manager, whirlpool, state->world_top);
            
            // Если не найден подходящий, создаем новый
            if (!target) {
                target = WhirlpoolManager_CreateForTeleport(manager, 
                                                          whirlpool, 
                                                          state->world_top,
                                                          state->obstacles,
                                                          state->obstacle_count);
            }
            
            // Если удалось найти или создать целевой водоворот
            if (target) {
                // Выполняем телепортацию
                WhirlpoolManager_TeleportPlayer(manager, whirlpool, target, &state->player);
                
                // ВАЖНО: После телепортации выходим, чтобы не проверять другие водовороты в этом кадре
                return;
            }
        }
    }
}

uint8_t WhirlpoolManager_Add(struct WhirlpoolManager* manager, float x, float y) {
    if (manager->whirlpool_count >= WHIRLPOOL_MAX_COUNT) {
        return 0;
    }
    
    // Добавляем водоворот
    Whirlpool* whirlpool = &manager->whirlpools[manager->whirlpool_count];
    whirlpool->position.x = x;
    whirlpool->position.y = y;
    whirlpool->radius = WHIRLPOOL_RADIUS;
    whirlpool->rotation = 0.0f;
    whirlpool->used_recently = 0;
    whirlpool->cooldown_timer = 0;
    whirlpool->animation_phase = 0.0f;
    
    manager->whirlpool_count++;
    return 1;
}

void WhirlpoolManager_Cleanup(struct WhirlpoolManager* manager, float threshold_y) {
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        // КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Добавляем проверку на валидность водоворота
        if (manager->whirlpools[i].position.y > threshold_y && 
            manager->whirlpools[i].position.y > 0) { // Защита от невалидных координат
            
            // Удаляем водоворот (перемещаем последний на место удаляемого)
            if (i < manager->whirlpool_count - 1) {
                manager->whirlpools[i] = manager->whirlpools[manager->whirlpool_count - 1];
            }
            manager->whirlpool_count--;
            i--; // Проверяем этот индекс снова
        }
    }
}

uint8_t Whirlpool_CollidesWith(Whirlpool* whirlpool, float x, float y, float radius) {
    // ИСПРАВЛЕНО: Не проверяем used_recently здесь, это делается выше
    float dx = x - whirlpool->position.x;
    float dy = y - whirlpool->position.y;
    float dist = Utils_Distance(0, 0, dx, dy);
    
    return (dist < whirlpool->radius + radius);
}

Whirlpool* WhirlpoolManager_FindTarget(struct WhirlpoolManager* manager, Whirlpool* current, float world_top) {
    Whirlpool* best_candidate = NULL;
    float best_distance = 0;
    
    for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
        Whirlpool* candidate = &manager->whirlpools[i];
        
        // Пропускаем текущий водоворот и уже использованные
        if (candidate == current || candidate->used_recently) {
            continue;
        }
        
        // Проверяем, что водоворот находится достаточно далеко позади (вверху по экрану)
        // current->position.y > candidate->position.y означает что candidate выше (меньше Y)
        float distance = current->position.y - candidate->position.y;
        
        // Водоворот должен быть:
        // 1. Достаточно далеко позади (distance >= WHIRLPOOL_TELEPORT_DISTANCE)
        // 2. Не слишком далеко (distance < WHIRLPOOL_TELEPORT_DISTANCE * 1.5)
        // 3. Выше world_top (candidate->position.y > world_top)
        if (distance >= WHIRLPOOL_TELEPORT_DISTANCE && 
            distance < WHIRLPOOL_TELEPORT_DISTANCE * 1.5f &&
            candidate->position.y > world_top) {
            
            // Выбираем водоворот, который ближе всего к идеальному расстоянию
            float score = fabsf(distance - WHIRLPOOL_TELEPORT_DISTANCE);
            if (!best_candidate || score < best_distance) {
                best_candidate = candidate;
                best_distance = score;
            }
        }
    }
    
    return best_candidate;
}

Whirlpool* WhirlpoolManager_CreateForTeleport(struct WhirlpoolManager* manager, 
                                            Whirlpool* current, 
                                            float world_top,
                                            Obstacle* obstacles,
                                            uint8_t obstacle_count) {
    // Проверяем, есть ли место для нового водоворота
    if (manager->whirlpool_count >= WHIRLPOOL_MAX_COUNT) {
        return NULL;
    }
    
    // Попытка найти подходящее место для нового водоворота
    for (uint8_t attempt = 0; attempt < WHIRLPOOL_PLACEMENT_ATTEMPTS; attempt++) {
        // Генерируем координаты для нового водоворота
        float new_y = current->position.y - WHIRLPOOL_TELEPORT_DISTANCE - 
                     Utils_RandomRangeFloat(0, 500);
        float new_x = Utils_RandomRangeFloat(WHIRLPOOL_EDGE_MARGIN, 
                                            SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN);
        
        // Проверяем безопасность размещения
        uint8_t safe = 1;
        
        // Проверка расстояния до препятствий
        for (uint8_t i = 0; i < obstacle_count; i++) {
            if (!obstacles[i].active) continue;
            
            float dx = new_x - obstacles[i].position.x;
            float dy = new_y - obstacles[i].position.y;
            float dist = Utils_Distance(0, 0, dx, dy);
            
            if (dist < obstacles[i].radius + WHIRLPOOL_ISLAND_SAFE_DISTANCE) {
                safe = 0;
                break;
            }
        }
        
        // Проверка нахождения в пределах мира
        if (new_y <= world_top) {
            safe = 0;
        }
        
        // Проверка расстояния до других водоворотов
        if (safe) {
            for (uint8_t i = 0; i < manager->whirlpool_count; i++) {
                float dx = new_x - manager->whirlpools[i].position.x;
                float dy = new_y - manager->whirlpools[i].position.y;
                float dist = Utils_Distance(0, 0, dx, dy);
                
                if (dist < WHIRLPOOL_MIN_DISTANCE * 2.5f) {
                    safe = 0;
                    break;
                }
            }
        }
        
        // Если место безопасно, создаем водоворот
        if (safe) {
            Whirlpool* new_whirlpool = &manager->whirlpools[manager->whirlpool_count];
            new_whirlpool->position.x = new_x;
            new_whirlpool->position.y = new_y;
            new_whirlpool->radius = WHIRLPOOL_RADIUS;
            new_whirlpool->rotation = 0.0f;
            new_whirlpool->used_recently = 0;
            new_whirlpool->cooldown_timer = 0;
            new_whirlpool->animation_phase = 0.0f;
            
            manager->whirlpool_count++;
            return new_whirlpool;
        }
    }
    
    // Если не удалось найти безопасное место, возвращаем NULL
    return NULL;
}

void WhirlpoolManager_TeleportPlayer(struct WhirlpoolManager* manager, 
                                   Whirlpool* source, 
                                   Whirlpool* target, 
                                   Player* player) {
    // Телепортация игрока
    player->position.x = target->position.x;
    player->position.y = target->position.y + WHIRLPOOL_PLAYER_OFFSET;
    
    // Помечаем оба водоворота как использованные
    source->used_recently = 1;
    source->cooldown_timer = WHIRLPOOL_COOLDOWN;
    
    target->used_recently = 1;
    target->cooldown_timer = WHIRLPOOL_COOLDOWN;
}