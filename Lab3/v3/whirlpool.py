# whirlpool.py - Водовороты с системой телепортации

import pygame
import math
import random
from config import *

class Whirlpool:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = WHIRLPOOL_RADIUS
        self.rotation = 0
        self.used_recently = False
        self.cooldown_timer = 0
        self.animation_phase = 0
    
    def update(self):
        """Обновление анимации и cooldown"""
        self.rotation = (self.rotation + WHIRLPOOL_ROTATION_SPEED) % 360
        self.animation_phase = (self.animation_phase + WHIRLPOOL_ANIMATION_SPEED) % (2 * math.pi)
        
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1
            if self.cooldown_timer == 0:
                self.used_recently = False
    
    def draw(self, screen, camera_y):
        """Отрисовка водоворота с анимацией"""
        y_screen = int(self.y - camera_y)
        
        if y_screen < -150 or y_screen > SCREEN_HEIGHT + 150:
            return
        
        pulse = math.sin(self.animation_phase) * WHIRLPOOL_PULSE_AMOUNT
        current_radius = self.radius + pulse
        
        # Рисуем спиральный водоворот
        for i in range(4):
            r = current_radius - i * 10
            angle_offset = self.rotation + i * 30
            color_val = 60 + i * 40
            
            for j in range(8):
                angle = math.radians(j * 45 + angle_offset)
                x1 = self.x + math.cos(angle) * r
                y1 = y_screen + math.sin(angle) * r
                x2 = self.x + math.cos(angle) * (r - 8)
                y2 = y_screen + math.sin(angle) * (r - 8)
                
                color = (color_val, color_val, 255)
                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 3)
        
        # Центр водоворота
        center_color = (30, 30, 150) if not self.used_recently else (100, 100, 100)
        pygame.draw.circle(screen, center_color, (int(self.x), y_screen), 12)
        
        # Индикатор cooldown
        if self.used_recently and self.cooldown_timer > 0:
            progress = self.cooldown_timer / WHIRLPOOL_COOLDOWN
            arc_angle = progress * 360
            
            points = [(int(self.x), y_screen)]
            for angle in range(0, int(arc_angle), 10):
                rad = math.radians(angle - 90)
                px = self.x + math.cos(rad) * (current_radius + 8)
                py = y_screen + math.sin(rad) * (current_radius + 8)
                points.append((int(px), int(py)))
            
            if len(points) > 2:
                pygame.draw.polygon(screen, (255, 100, 100, 100), points)
    
    def collides_with(self, x, y, radius=25):
        """Проверка столкновения с водоворотом"""
        if self.used_recently:
            return False
        
        dx = x - self.x
        dy = y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.radius + radius
    
    @staticmethod
    def can_place_whirlpool(x, y, islands, shores, existing_whirlpools, min_distance=WHIRLPOOL_MIN_DISTANCE):
        """Проверка возможности размещения водоворота"""
        # Проверка расстояния до островов
        for island in islands:
            safe_distance = island.radius + WHIRLPOOL_ISLAND_SAFE_DISTANCE
            dist = math.sqrt((island.x - x)**2 + (island.y - y)**2)
            if dist < safe_distance:
                return False
        
        # Проверка что не внутри острова
        for island in islands:
            if island.collides_with(x, y, 0):
                return False
        
        # Проверка расстояния до берегов
        if x < WHIRLPOOL_EDGE_MARGIN or x > SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN:
            return False
        
        # Проверка расстояния до других водоворотов
        for whirlpool in existing_whirlpools:
            dist = math.sqrt((whirlpool.x - x)**2 + (whirlpool.y - y)**2)
            if dist < min_distance * 2.5:
                return False
        
        return True
    
    @staticmethod
    def find_teleport_target(current_whirlpool, all_whirlpools, world_top, islands, shores, 
                           min_distance=WHIRLPOOL_TELEPORT_DISTANCE):
        """Найти подходящий водоворот для телепортации"""
        candidates = []
        
        for whirlpool in all_whirlpools:
            if (whirlpool != current_whirlpool and
                not whirlpool.used_recently and
                whirlpool.y < current_whirlpool.y - min_distance and
                whirlpool.y > world_top
                ):
                candidates.append(whirlpool)
        
        if not candidates:
            attempts = 0
            new_y = current_whirlpool.y - min_distance - random.randint(0, 500)
            
            while attempts < WHIRLPOOL_PLACEMENT_ATTEMPTS:
                new_x = random.randint(WHIRLPOOL_EDGE_MARGIN, SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN)
                
                if Whirlpool.can_place_whirlpool(new_x, new_y, islands, shores, all_whirlpools):
                    new_whirlpool = Whirlpool(new_x, new_y)
                    all_whirlpools.append(new_whirlpool)
                    print(f"✨ Создан новый водоворот для телепортации в ({new_x}, {new_y})")
                    return new_whirlpool
                
                attempts += 1
                new_y -= 100
            
            if attempts == WHIRLPOOL_PLACEMENT_ATTEMPTS:
                new_x = random.randint(WHIRLPOOL_EDGE_MARGIN, SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN)
                new_whirlpool = Whirlpool(new_x, new_y)
                all_whirlpools.append(new_whirlpool)
                print(f"⚠️ Создан водоворот без проверки в ({new_x}, {new_y})")
                return new_whirlpool
        
        return random.choice(candidates)
    
    def teleport_player(self, target_whirlpool):
        """Телепортация игрока"""
        if target_whirlpool is None:
            return None
        
        new_x = target_whirlpool.x
        new_y = target_whirlpool.y + WHIRLPOOL_PLAYER_OFFSET
        
        self.used_recently = True
        self.cooldown_timer = WHIRLPOOL_COOLDOWN
        
        target_whirlpool.used_recently = True
        target_whirlpool.cooldown_timer = WHIRLPOOL_COOLDOWN
        
        return (new_x, new_y)


class WhirlpoolManager:
    def __init__(self, max_whirlpools=WHIRLPOOL_MAX_COUNT):
        self.whirlpools = []
        self.max_whirlpools = max_whirlpools
    
    def update(self, player, world_top, islands, shores):
        """Обновление всех водоворотов"""
        for whirlpool in self.whirlpools:
            whirlpool.update()
        
        for whirlpool in self.whirlpools:
            if whirlpool.collides_with(player.x, player.y):
                target = Whirlpool.find_teleport_target(
                    whirlpool, 
                    self.whirlpools, 
                    world_top,
                    islands,
                    shores,
                    min_distance=WHIRLPOOL_TELEPORT_DISTANCE
                )
                
                teleport_pos = whirlpool.teleport_player(target)
                if teleport_pos:
                    print(f"🌀 ТЕЛЕПОРТАЦИЯ! {player.y:.0f} → {teleport_pos[1]:.0f} (прыжок: {player.y - teleport_pos[1]:.0f})")
                return teleport_pos
        
        return None
    
    def draw(self, screen, camera_y):
        """Отрисовка всех водоворотов"""
        for whirlpool in self.whirlpools:
            whirlpool.draw(screen, camera_y)
    
    def add_whirlpool(self, x, y, islands, shores):
        """Добавление нового водоворота"""
        if len(self.whirlpools) >= self.max_whirlpools:
            return False
        
        if not Whirlpool.can_place_whirlpool(x, y, islands, shores, self.whirlpools):
            return False
        
        whirlpool = Whirlpool(x, y)
        self.whirlpools.append(whirlpool)
        print(f"➕ Водоворот добавлен в ({x}, {y}), всего: {len(self.whirlpools)}")
        return True
    
    def cleanup(self, cleanup_threshold):
        """Удаление старых водоворотов"""
        before = len(self.whirlpools)
        self.whirlpools = [w for w in self.whirlpools if w.y < cleanup_threshold]
        
        if len(self.whirlpools) < before:
            print(f"🗑️ Удалено водоворотов: {before - len(self.whirlpools)}, осталось: {len(self.whirlpools)}")

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

// ИСПРАВЛЕНИЕ 4: Создаем водоворот даже при неудачных попытках (как в рабочей версии)
// Если не удалось найти безопасное место, создаем водоворот без строгих проверок
float new_y = current->position.y - WHIRLPOOL_TELEPORT_DISTANCE - 
             Utils_RandomRangeFloat(0, 500);
float new_x = Utils_RandomRangeFloat(WHIRLPOOL_EDGE_MARGIN, 
                                    SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN);

// Принудительно устанавливаем минимальное значение Y
if (new_y <= world_top) {
    new_y = world_top + 100;
}

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