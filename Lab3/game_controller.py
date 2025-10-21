"""
game_controller.py
CONTROLLER - Управление вводом (клавиатура / STM32)
"""

import pygame
from game_model import GameModel, GameState

class InputController:
    """Контроллер ввода - легко заменить на USART"""
    
    def __init__(self):
        self.left_pressed = False
        self.right_pressed = False
        self.shoot_pressed = False
        self.shoot_last_state = False
        
        # Для интеграции с STM32
        self.use_stm32 = False
        self.stm32_data = {
            'button_left': False,
            'button_right': False,
            'button_fire': False,
            'button_pause': False
        }
        
    def update(self, model: GameModel):
        """Обновление ввода"""
        if self.use_stm32:
            self._update_stm32(model)
        else:
            self._update_keyboard(model)
        
    def _update_keyboard(self, model: GameModel):
        """Обновление с клавиатуры (текущий метод)"""
        keys = pygame.key.get_pressed()
        
        # Движение
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if model.state == GameState.PLAYING:
                model.player_move_left()
            self.left_pressed = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if model.state == GameState.PLAYING:
                model.player_move_right()
            self.right_pressed = True
        else:
            if model.state == GameState.PLAYING:
                model.player_stop()
            self.left_pressed = False
            self.right_pressed = False
            
        # Выстрел (только при нажатии, не зажатии)
        self.shoot_pressed = keys[pygame.K_SPACE]
        if self.shoot_pressed and not self.shoot_last_state:
            if model.state == GameState.PLAYING:
                model.player_shoot()
        self.shoot_last_state = self.shoot_pressed
        
    def _update_stm32(self, model: GameModel):
        """
        Обновление с STM32 (для будущей интеграции)
        
        Данные должны приходить через update_stm32_state()
        """
        if model.state != GameState.PLAYING:
            return
            
        # Движение
        if self.stm32_data['button_left']:
            model.player_move_left()
        elif self.stm32_data['button_right']:
            model.player_move_right()
        else:
            model.player_stop()
            
        # Выстрел
        if self.stm32_data['button_fire'] and not self.shoot_last_state:
            model.player_shoot()
        self.shoot_last_state = self.stm32_data['button_fire']
        
    def update_stm32_state(self, button_left: bool, button_right: bool, 
                          button_fire: bool, button_pause: bool = False):
        """
        Обновить состояние кнопок от STM32
        
        Args:
            button_left: Кнопка влево нажата
            button_right: Кнопка вправо нажата
            button_fire: Кнопка огня нажата
            button_pause: Кнопка паузы нажата (зажатый огонь)
        """
        self.stm32_data['button_left'] = button_left
        self.stm32_data['button_right'] = button_right
        self.stm32_data['button_fire'] = button_fire
        self.stm32_data['button_pause'] = button_pause
        
    def enable_stm32_mode(self):
        """Включить режим управления от STM32"""
        self.use_stm32 = True
        print("✓ STM32 control mode enabled")
        
    def enable_keyboard_mode(self):
        """Включить режим управления с клавиатуры"""
        self.use_stm32 = False
        print("✓ Keyboard control mode enabled")