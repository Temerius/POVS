"""
main.py
Главный файл Space Defender
Связывает Model-View-Controller
"""

import pygame
from game_model import GameModel, GameState
from game_view import GameView
from game_controller import InputController

def main():
    # Параметры окна
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60
    
    # Инициализация MVC
    model = GameModel(SCREEN_WIDTH, SCREEN_HEIGHT)
    view = GameView(SCREEN_WIDTH, SCREEN_HEIGHT)
    controller = InputController()
    
    # Главный цикл
    running = True
    
    print("=" * 60)
    print("Space Defender - Game Started")
    print("=" * 60)
    print("Controls:")
    print("  Arrow Keys / A,D - Move")
    print("  SPACE - Shoot")
    print("  P - Pause/Resume")
    print("  R - Restart (Game Over)")
    print("  ESC - Quit")
    print("=" * 60)
    
    while running:
        dt = view.clock.tick(FPS) / 1000.0  # Секунды
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    
                elif event.key == pygame.K_p:
                    # Пауза
                    model.toggle_pause()
                    
                elif event.key == pygame.K_SPACE and model.state == GameState.MENU:
                    # Старт игры из меню
                    model.start_game()
                    
                elif event.key == pygame.K_r and model.state == GameState.GAME_OVER:
                    # Перезапуск после Game Over
                    model.start_game()
                    
        # Обновление ввода
        controller.update(model)
        
        # Обновление логики
        model.update(dt)
        
        # Отрисовка
        view.render(model)
        
    pygame.quit()
    print("\nGame closed. Final score:", model.score)

if __name__ == "__main__":
    main()