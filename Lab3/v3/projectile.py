# projectile.py
import pygame
import math
from config import BLACK

class Projectile:
    def __init__(self, x, y, angle, speed=12):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.radius = 5
        self.lifetime = 150
        
    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
        
    def draw(self, screen, camera_y):
        screen_y = int(self.y - camera_y)
        if -50 < screen_y < 850:
            pygame.draw.circle(screen, BLACK, (int(self.x), screen_y), self.radius)
            pygame.draw.circle(screen, (255, 150, 0), (int(self.x), screen_y), self.radius - 2)