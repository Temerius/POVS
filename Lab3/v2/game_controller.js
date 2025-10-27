/**
 * Game Controller - управление клавиатурой
 * A - поворот влево (стрельба вправо)
 * W - поворот вправо (стрельба влево) 
 * SPACE - стрельба
 */

class GameController {
    constructor() {
        this.keys = {
            left: false,    // A
            right: false,   // W
            fire: false     // SPACE
        };
        
        this.lastMove = 'none'; // 'left', 'right', 'none'
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Обработка нажатий клавиш
        document.addEventListener('keydown', (e) => {
            switch(e.code) {
                case 'KeyA':
                    e.preventDefault();
                    this.keys.left = true;
                    this.lastMove = 'left';
                    break;
                case 'KeyD':
                    e.preventDefault();
                    this.keys.right = true;
                    this.lastMove = 'right';
                    break;
                case 'Space':
                    e.preventDefault();
                    this.keys.fire = true;
                    break;
            }
        });
        
        // Обработка отпускания клавиш
        document.addEventListener('keyup', (e) => {
            switch(e.code) {
                case 'KeyA':
                    e.preventDefault();
                    this.keys.left = false;
                    break;
                case 'KeyD':
                    e.preventDefault();
                    this.keys.right = false;
                    break;
                case 'Space':
                    e.preventDefault();
                    this.keys.fire = false;
                    break;
            }
        });
    }
    
    // Получить текущее состояние управления
    getInput() {
        return {
            left: this.keys.left,
            right: this.keys.right,
            fire: this.keys.fire,
            lastMove: this.lastMove
        };
    }
    
    // Проверить, была ли нажата кнопка стрельбы (для одиночных выстрелов)
    isFirePressed() {
        return this.keys.fire;
    }
    
    // Сбросить состояние стрельбы
    resetFire() {
        this.keys.fire = false;
    }
}
