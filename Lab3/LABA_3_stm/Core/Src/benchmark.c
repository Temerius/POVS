/* benchmark.c - Реализация бенчмаркинга */

#include "benchmark.h"
#include "protocol.h"
#include "whirlpool.h"
#include <string.h>

BenchmarkStats g_benchmark;

static uint32_t frame_start_tick;
static uint32_t update_start_tick;
static uint32_t collision_start_tick;
static uint32_t protocol_start_tick;
static uint32_t send_start_tick;

void Benchmark_Init(void) {
    memset(&g_benchmark, 0, sizeof(BenchmarkStats));
}

void Benchmark_StartFrame(void) {
    frame_start_tick = HAL_GetTick();
}

void Benchmark_MarkUpdateStart(void) {
    update_start_tick = HAL_GetTick();
}

void Benchmark_MarkUpdateEnd(void) {
    g_benchmark.update_time_us = (HAL_GetTick() - update_start_tick) * 1000;
}

void Benchmark_MarkCollisionStart(void) {
    collision_start_tick = HAL_GetTick();
}

void Benchmark_MarkCollisionEnd(void) {
    g_benchmark.collision_time_us = (HAL_GetTick() - collision_start_tick) * 1000;
}

void Benchmark_MarkProtocolStart(void) {
    protocol_start_tick = HAL_GetTick();
}

void Benchmark_MarkProtocolEnd(void) {
    g_benchmark.protocol_time_us = (HAL_GetTick() - protocol_start_tick) * 1000;
}

void Benchmark_MarkSendStart(void) {
    send_start_tick = HAL_GetTick();
}

void Benchmark_MarkSendEnd(void) {
    g_benchmark.send_time_us = (HAL_GetTick() - send_start_tick) * 1000;
}

void Benchmark_EndFrame(GameState* state) {
    uint32_t frame_end_tick = HAL_GetTick();
    g_benchmark.frame_time_us = (frame_end_tick - frame_start_tick) * 1000;
    
    // Обновление счётчиков объектов
    g_benchmark.enemy_count = state->enemy_simple_count + state->enemy_hard_count;
    g_benchmark.projectile_count = state->projectile_count;
    g_benchmark.obstacle_count = state->obstacle_count;
    g_benchmark.whirlpool_count = state->whirlpool_manager ? 
                                  state->whirlpool_manager->whirlpool_count : 0;
    
    // Статистика
    if (g_benchmark.frame_time_us > g_benchmark.max_frame_time_us) {
        g_benchmark.max_frame_time_us = g_benchmark.frame_time_us;
    }
    
    if (g_benchmark.frame_time_us > 20000) { // > 20ms
        g_benchmark.slow_frames++;
    }
    
    g_benchmark.total_frames++;
    
    // Средняя скорость (скользящее среднее)
    float current_ms = g_benchmark.frame_time_us / 1000.0f;
    g_benchmark.avg_frame_time_ms = (g_benchmark.avg_frame_time_ms * 0.95f) + (current_ms * 0.05f);
}

void Benchmark_SendStats(void) {
    // Формируем отчёт в виде строки
    char message[32];
    
    // Формат: "FPS:XX E:XX P:XX T:XXms"
    uint16_t fps = g_benchmark.avg_frame_time_ms > 0 ? 
                   (uint16_t)(1000.0f / g_benchmark.avg_frame_time_ms) : 0;
    
    // Упрощённое форматирование без sprintf
    message[0] = 'F'; message[1] = 'P'; message[2] = 'S'; message[3] = ':';
    
    // FPS (2 цифры)
    message[4] = '0' + (fps / 10);
    message[5] = '0' + (fps % 10);
    message[6] = ' ';
    
    // Enemies
    message[7] = 'E'; message[8] = ':';
    message[9] = '0' + (g_benchmark.enemy_count / 10);
    message[10] = '0' + (g_benchmark.enemy_count % 10);
    message[11] = ' ';
    
    // Projectiles
    message[12] = 'P'; message[13] = ':';
    message[14] = '0' + (g_benchmark.projectile_count / 10);
    message[15] = '0' + (g_benchmark.projectile_count % 10);
    message[16] = ' ';
    
    // Frame time
    message[17] = 'T'; message[18] = ':';
    uint16_t time_ms = (uint16_t)g_benchmark.avg_frame_time_ms;
    message[19] = '0' + (time_ms / 10);
    message[20] = '0' + (time_ms % 10);
    message[21] = 'm'; message[22] = 's';
    message[23] = '\0';
    
    Protocol_SendDebug(0xFF, 0, 0, 0, 0, 1, message);
}

void Benchmark_PrintStats(void) {
    // Для отладки через SWO/ITM (если доступно)
    // Здесь можно добавить вывод через ITM_SendChar
}