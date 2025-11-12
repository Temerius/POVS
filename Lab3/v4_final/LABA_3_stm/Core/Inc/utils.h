/* utils.h - Математические утилиты */

#ifndef UTILS_H
#define UTILS_H

#include <stdint.h>
#include <math.h>
#include "game_config.h"

// === МАТЕМАТИКА ===

// Ограничение значения
static inline float Utils_Clamp(float value, float min, float max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

// Линейная интерполяция
static inline float Utils_Lerp(float a, float b, float t) {
    return a + (b - a) * t;
}

// Преобразование радианы -> градусы
static inline float Utils_RadToDeg(float rad) {
    return RAD_TO_DEG(rad);
}

// Преобразование градусы -> радианы
static inline float Utils_DegToRad(float deg) {
    return DEG_TO_RAD(deg);
}

// Нормализация угла в диапазон [-PI, PI]
static inline float Utils_NormalizeAngle(float angle) {
    while (angle > PI) angle -= 2.0f * PI;
    while (angle < -PI) angle += 2.0f * PI;
    return angle;
}

// Расстояние между двумя точками
static inline float Utils_Distance(float x1, float y1, float x2, float y2) {
    float dx = x2 - x1;
    float dy = y2 - y1;
    return sqrtf(dx * dx + dy * dy);
}

// Псевдослучайное число (простой LCG)
extern uint32_t Utils_RandomSeed;

static inline void Utils_SeedRandom(uint32_t seed) {
    Utils_RandomSeed = seed;
}

static inline uint32_t Utils_Random(void) {
    Utils_RandomSeed = (Utils_RandomSeed * 1103515245 + 12345) & 0x7fffffff;
    return Utils_RandomSeed;
}

static inline int Utils_RandomRange(int min, int max) {
    return min + (Utils_Random() % (max - min + 1));
}

static inline float Utils_RandomFloat(void) {
    return (float)Utils_Random() / (float)0x7fffffff;
}

static inline float Utils_RandomRangeFloat(float min, float max) {
    return min + Utils_RandomFloat() * (max - min);
}

// Абсолютное значение
static inline float Utils_Abs(float value) {
    return (value < 0) ? -value : value;
}

// Минимум/максимум
static inline float Utils_Min(float a, float b) {
    return (a < b) ? a : b;
}

static inline float Utils_Max(float a, float b) {
    return (a > b) ? a : b;
}

#endif // UTILS_H