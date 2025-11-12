/* benchmark.h - Бенчмаркинг и диагностика производительности */

#ifndef BENCHMARK_H
#define BENCHMARK_H

#include "game_types.h"
#include "main.h"

// Структура статистики производительности
typedef struct {
    uint32_t frame_time_us;           // Время кадра в микросекундах
    uint32_t update_time_us;          // Время обновления логики
    uint32_t collision_time_us;       // Время проверки коллизий
    uint32_t protocol_time_us;        // Время обработки протокола
    uint32_t send_time_us;            // Время отправки пакета
    
    uint16_t enemy_count;
    uint16_t projectile_count;
    uint16_t obstacle_count;
    uint16_t whirlpool_count;
    
    uint32_t max_frame_time_us;       // Максимальное время кадра
    uint32_t total_frames;
    uint32_t slow_frames;             // Кадры > 20ms
    
    float avg_frame_time_ms;
} BenchmarkStats;

extern BenchmarkStats g_benchmark;

// Инициализация бенчмарка
void Benchmark_Init(void);

// Начало измерения
void Benchmark_StartFrame(void);

// Отметки времени
void Benchmark_MarkUpdateStart(void);
void Benchmark_MarkUpdateEnd(void);
void Benchmark_MarkCollisionStart(void);
void Benchmark_MarkCollisionEnd(void);
void Benchmark_MarkProtocolStart(void);
void Benchmark_MarkProtocolEnd(void);
void Benchmark_MarkSendStart(void);
void Benchmark_MarkSendEnd(void);

// Конец измерения и обновление статистики
void Benchmark_EndFrame(GameState* state);

// Отправка статистики на PC (каждые N кадров)
void Benchmark_SendStats(void);

// Вывод статистики в debug
void Benchmark_PrintStats(void);

#endif // BENCHMARK_H