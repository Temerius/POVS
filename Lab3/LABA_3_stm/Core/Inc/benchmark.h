

#ifndef BENCHMARK_H
#define BENCHMARK_H

#include "game_types.h"
#include "main.h"

typedef struct {
    uint32_t frame_time_us;            
    uint32_t update_time_us;           
    uint32_t collision_time_us;        
    uint32_t protocol_time_us;         
    uint32_t send_time_us;             
    
    uint16_t enemy_count;
    uint16_t projectile_count;
    uint16_t obstacle_count;
    uint16_t whirlpool_count;
    
    uint32_t max_frame_time_us;        
    uint32_t total_frames;
    uint32_t slow_frames;              
    
    float avg_frame_time_ms;
} BenchmarkStats;

extern BenchmarkStats g_benchmark;

 
void Benchmark_Init(void);

 
void Benchmark_StartFrame(void);

 
void Benchmark_MarkUpdateStart(void);
void Benchmark_MarkUpdateEnd(void);
void Benchmark_MarkCollisionStart(void);
void Benchmark_MarkCollisionEnd(void);
void Benchmark_MarkProtocolStart(void);
void Benchmark_MarkProtocolEnd(void);
void Benchmark_MarkSendStart(void);
void Benchmark_MarkSendEnd(void);

 
void Benchmark_EndFrame(GameState* state);

 
void Benchmark_SendStats(void);

 
void Benchmark_PrintStats(void);

#endif  