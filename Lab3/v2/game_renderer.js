/**
 * Game Renderer - отображение игры
 * Рисует море, корабль, врагов, пули, меню
 */

class GameRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.images = {};
        
        this.setupCanvas();
        this.loadImages();
    }
    
    setupCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        window.addEventListener('resize', () => {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
        });
    }
    
    async loadImages() {
        // Загружаем изображения корабля
        const shipImages = ['player_up', 'player_down', 'player_left', 'player_right'];
        for (const name of shipImages) {
            this.images[name] = new Image();
            this.images[name].src = `${name}.png`;
        }
        
        // Загружаем изображения врагов
        this.images['enemy_simple'] = new Image();
        this.images['enemy_simple'].src = 'img/enemy_simple.png';
        
        this.images['enemy_hard'] = new Image();
        this.images['enemy_hard'].src = 'img/enemy_hard.png';
        
        // Загружаем водоворот
        this.images['whirlpool'] = new Image();
        this.images['whirlpool'].src = 'img/Whirlpool.gif';
    }
    
    render(gameState) {
        if (gameState.gameState.state === 'MENU' || 
            gameState.gameState.state === 'PAUSED' || 
            gameState.gameState.state === 'GAME_OVER') {
            // Очистка экрана
            this.drawSea();
            this.drawMenu(gameState);
        } else {
            this.drawGame(gameState);
        }
    }
    
    drawSea(scrollY = 0) {
        // Градиент моря
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        gradient.addColorStop(0, '#87CEEB');
        gradient.addColorStop(0.5, '#4682B4');
        gradient.addColorStop(1, '#191970');
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Волны с прокруткой
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        this.ctx.lineWidth = 2;
        for (let i = 0; i < 8; i++) {
            this.ctx.beginPath();
            const y = (100 + i * 100 - scrollY) % (this.canvas.height + 200);
            for (let x = 0; x < this.canvas.width; x += 20) {
                const waveY = y + Math.sin((x + Date.now() * 0.001) * 0.01) * 10;
                if (x === 0) {
                    this.ctx.moveTo(x, waveY);
                } else {
                    this.ctx.lineTo(x, waveY);
                }
            }
            this.ctx.stroke();
        }
    }
    
    drawMenu(gameState) {
        // Полупрозрачный фон
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Заголовок
        this.ctx.fillStyle = '#FFD700';
        this.ctx.font = 'bold 48px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('SEA DEFENDERS', this.canvas.width / 2, 150);
        
        // Подзаголовок
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '24px Arial';
        this.ctx.fillText('Зеркальная морская битва', this.canvas.width / 2, 200);
        
        // Пункты меню
        const menuItems = this.getMenuItems(gameState.gameState.state);
        const startY = 300;
        const itemHeight = 60;
        
        for (let i = 0; i < menuItems.length; i++) {
            const y = startY + i * itemHeight;
            const isSelected = i === gameState.gameState.selectedItem;
            
            // Фон для выбранного пункта
            if (isSelected) {
                this.ctx.fillStyle = 'rgba(255, 215, 0, 0.3)';
                this.ctx.fillRect(this.canvas.width / 2 - 200, y - 30, 400, 50);
            }
            
            // Текст пункта меню
            this.ctx.fillStyle = isSelected ? '#FFD700' : '#FFFFFF';
            this.ctx.font = isSelected ? 'bold 28px Arial' : '24px Arial';
            this.ctx.fillText(menuItems[i], this.canvas.width / 2, y);
        }
        
        // Инструкции
        this.ctx.fillStyle = '#CCCCCC';
        this.ctx.font = '18px Arial';
        this.ctx.fillText('A/W - навигация, SPACE - выбор', this.canvas.width / 2, this.canvas.height - 100);
        
        // Счет (для Game Over)
        if (gameState.gameState.state === 'GAME_OVER') {
            this.ctx.fillStyle = '#FF6B6B';
            this.ctx.font = 'bold 32px Arial';
            this.ctx.fillText(`Счет: ${gameState.gameState.score}`, this.canvas.width / 2, 250);
        }
    }
    
    drawGame(gameState) {
        // Рисуем море с прокруткой
        this.drawSea(gameState.scrollY);
        
        // Рисуем острова
        this.drawIslands(gameState.islands);
        
        // Рисуем водовороты
        this.drawWhirlpools(gameState.whirlpools);
        
        // Рисуем игрока
        this.drawPlayer(gameState.player);
        
        // Рисуем врагов
        this.drawEnemies(gameState.enemies);
        
        // Рисуем пули
        this.drawBullets(gameState.bullets, gameState.enemyBullets);
        
        // Рисуем взрывы
        this.drawExplosions(gameState.explosions);
        
        // Рисуем UI
        this.drawUI(gameState);
    }
    
    drawPlayer(player) {
        this.ctx.save();
        this.ctx.translate(player.x, player.y);
        
        // Поворачиваем корабль по углу
        this.ctx.rotate(player.angle * Math.PI / 180);
        
        // Выбираем изображение в зависимости от угла
        let shipImage = this.images['player_up']; // по умолчанию
        
        if (player.angle > 45) {
            shipImage = this.images['player_right'];
        } else if (player.angle < -45) {
            shipImage = this.images['player_left'];
        } else if (Math.abs(player.angle) < 15) {
            shipImage = this.images['player_up'];
        }
        
        // Рисуем изображение корабля
        if (shipImage && shipImage.complete) {
            this.ctx.drawImage(shipImage, -32, -32, 64, 64);
        } else {
            // Fallback - рисуем простой корабль
            this.drawSimpleShip();
        }
        
        // Показываем направление стрельбы
        this.ctx.strokeStyle = '#FFD700';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        if (player.angle < -15) { // Поворот влево = стрельба вправо
            this.ctx.moveTo(15, 0);
            this.ctx.lineTo(25, 0);
        } else if (player.angle > 15) { // Поворот вправо = стрельба влево
            this.ctx.moveTo(-15, 0);
            this.ctx.lineTo(-25, 0);
        } else { // Прямо = стрельба вперед
            this.ctx.moveTo(0, -10);
            this.ctx.lineTo(0, -20);
        }
        this.ctx.stroke();
        
        this.ctx.restore();
    }
    
    drawSimpleShip() {
        // Корпус корабля
        this.ctx.fillStyle = '#8B4513';
        this.ctx.fillRect(-20, -10, 40, 20);
        
        // Паруса
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.fillRect(-15, -25, 30, 15);
        
        // Мачта
        this.ctx.strokeStyle = '#654321';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(0, -10);
        this.ctx.lineTo(0, -25);
        this.ctx.stroke();
        
        // Флаг
        this.ctx.fillStyle = '#FF0000';
        this.ctx.fillRect(-2, -25, 4, 8);
        
        // Нос корабля
        this.ctx.fillStyle = '#8B4513';
        this.ctx.beginPath();
        this.ctx.moveTo(20, 0);
        this.ctx.lineTo(25, -5);
        this.ctx.lineTo(25, 5);
        this.ctx.closePath();
        this.ctx.fill();
    }
    
    drawEnemies(enemies) {
        for (let enemy of enemies) {
            this.ctx.save();
            this.ctx.translate(enemy.x, enemy.y);
            
            // Рисуем изображение врага
            let enemyImage = null;
            if (enemy.type === 0) { // Шлюпка
                enemyImage = this.images['enemy_simple'];
            } else { // Галеон
                enemyImage = this.images['enemy_hard'];
            }
            
            if (enemyImage && enemyImage.complete) {
                this.ctx.drawImage(enemyImage, -32, -32, 64, 64);
            } else {
                // Fallback - рисуем простого врага
                if (enemy.type === 0) { // Шлюпка
                    this.ctx.fillStyle = '#4169E1';
                    this.ctx.fillRect(-15, -8, 30, 16);
                    
                    // Парус шлюпки
                    this.ctx.fillStyle = '#F0F8FF';
                    this.ctx.fillRect(-10, -15, 20, 10);
                } else { // Галеон
                    this.ctx.fillStyle = '#8B0000';
                    this.ctx.fillRect(-25, -12, 50, 24);
                    
                    // Паруса галеона
                    this.ctx.fillStyle = '#FFFFFF';
                    this.ctx.fillRect(-20, -20, 15, 15);
                    this.ctx.fillRect(5, -20, 15, 15);
                }
            }
            
            // Полоска здоровья
            if (enemy.hp < enemy.maxHp) {
                this.ctx.fillStyle = '#FF0000';
                this.ctx.fillRect(-20, -25, 40, 4);
                this.ctx.fillStyle = '#00FF00';
                this.ctx.fillRect(-20, -25, (enemy.hp / enemy.maxHp) * 40, 4);
            }
            
            this.ctx.restore();
        }
    }
    
    drawBullets(bullets, enemyBullets) {
        // Пули игрока
        this.ctx.fillStyle = '#FFD700';
        this.ctx.shadowColor = '#FFD700';
        this.ctx.shadowBlur = 10;
        for (let bullet of bullets) {
            this.ctx.beginPath();
            this.ctx.arc(bullet.x, bullet.y, 5, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        // Пули врагов
        this.ctx.fillStyle = '#FF4500';
        this.ctx.shadowColor = '#FF4500';
        this.ctx.shadowBlur = 10;
        for (let bullet of enemyBullets) {
            this.ctx.beginPath();
            this.ctx.arc(bullet.x, bullet.y, 5, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        // Сбрасываем тень
        this.ctx.shadowBlur = 0;
    }
    
    drawExplosions(explosions) {
        for (let explosion of explosions) {
            this.ctx.save();
            this.ctx.translate(explosion.x, explosion.y);
            
            const alpha = 1 - (explosion.frame / 10);
            this.ctx.fillStyle = `rgba(255, 100, 0, ${alpha})`;
            
            const size = explosion.frame * 3;
            this.ctx.beginPath();
            this.ctx.arc(0, 0, size, 0, Math.PI * 2);
            this.ctx.fill();
            
            this.ctx.restore();
        }
    }
    
    drawIslands(islands) {
        for (let island of islands) {
            // Тень острова
            this.ctx.fillStyle = '#654321';
            this.ctx.beginPath();
            if (island.points && island.points.length > 0) {
                this.ctx.moveTo(island.points[0].x + 3, island.points[0].y + 3);
                for (let i = 1; i < island.points.length; i++) {
                    this.ctx.lineTo(island.points[i].x + 3, island.points[i].y + 3);
                }
                this.ctx.closePath();
            } else {
                this.ctx.arc(island.x + 3, island.y + 3, Math.max(island.width, island.height) / 2, 0, Math.PI * 2);
            }
            this.ctx.fill();
            
            // Основа острова
            this.ctx.fillStyle = '#8B4513';
            this.ctx.beginPath();
            if (island.points && island.points.length > 0) {
                this.ctx.moveTo(island.points[0].x, island.points[0].y);
                for (let i = 1; i < island.points.length; i++) {
                    this.ctx.lineTo(island.points[i].x, island.points[i].y);
                }
                this.ctx.closePath();
            } else {
                this.ctx.arc(island.x, island.y, Math.max(island.width, island.height) / 2, 0, Math.PI * 2);
            }
            this.ctx.fill();
            
            // Трава на острове
            this.ctx.fillStyle = '#228B22';
            this.ctx.beginPath();
            if (island.points && island.points.length > 0) {
                this.ctx.moveTo(island.points[0].x, island.points[0].y);
                for (let i = 1; i < island.points.length; i++) {
                    this.ctx.lineTo(island.points[i].x, island.points[i].y);
                }
                this.ctx.closePath();
            } else {
                this.ctx.arc(island.x, island.y, Math.max(island.width, island.height) / 2 - 8, 0, Math.PI * 2);
            }
            this.ctx.fill();
            
            // Рисуем деревья
            if (island.trees) {
                for (let tree of island.trees) {
                    this.drawTree(tree.x, tree.y, tree.type, tree.size);
                }
            }
        }
    }
    
    drawTree(x, y, type, size) {
        this.ctx.save();
        this.ctx.translate(x, y);
        
        if (type === 'palm') {
            // Ствол пальмы
            this.ctx.strokeStyle = '#8B4513';
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.moveTo(0, 0);
            this.ctx.lineTo(0, -size);
            this.ctx.stroke();
            
            // Листья пальмы
            this.ctx.fillStyle = '#228B22';
            for (let i = 0; i < 6; i++) {
                const angle = (i * Math.PI * 2) / 6;
                const leafX = Math.cos(angle) * size * 0.8;
                const leafY = Math.sin(angle) * size * 0.8;
                
                this.ctx.beginPath();
                this.ctx.arc(leafX, leafY, size * 0.3, 0, Math.PI * 2);
                this.ctx.fill();
            }
        } else { // bush
            // Куст
            this.ctx.fillStyle = '#228B22';
            this.ctx.beginPath();
            this.ctx.arc(0, 0, size, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Детали куста
            this.ctx.fillStyle = '#32CD32';
            this.ctx.beginPath();
            this.ctx.arc(0, 0, size * 0.7, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        this.ctx.restore();
    }
    
    drawWhirlpools(whirlpools) {
        for (let whirlpool of whirlpools) {
            this.ctx.save();
            this.ctx.translate(whirlpool.x, whirlpool.y);
            
            // Рисуем GIF водоворота
            if (this.images['whirlpool'] && this.images['whirlpool'].complete) {
                this.ctx.drawImage(this.images['whirlpool'], -40, -40, 80, 80);
            } else {
                // Fallback - рисуем простой водоворот
                const time = Date.now() * 0.01;
                this.ctx.strokeStyle = 'rgba(0, 100, 255, 0.8)';
                this.ctx.lineWidth = 3;
                
                for (let i = 0; i < 3; i++) {
                    this.ctx.beginPath();
                    const radius = 15 + i * 5;
                    const startAngle = time + i * Math.PI / 3;
                    const endAngle = startAngle + Math.PI * 1.5;
                    this.ctx.arc(0, 0, radius, startAngle, endAngle);
                    this.ctx.stroke();
                }
            }
            
            this.ctx.restore();
        }
    }
    
    drawUI(gameState) {
        // Счет
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 24px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`Счет: ${gameState.gameState.score}`, 20, 40);
        
        // Здоровье
        this.ctx.fillText(`Здоровье: ${gameState.player.hp}`, 20, 70);
        
        // Угол
        this.ctx.fillText(`Угол: ${gameState.player.angle}°`, 20, 100);
        
        // Полоска здоровья
        const healthBarWidth = 200;
        const healthBarHeight = 20;
        const healthPercent = gameState.player.hp / 100;
        
        this.ctx.fillStyle = '#FF0000';
        this.ctx.fillRect(20, 120, healthBarWidth, healthBarHeight);
        this.ctx.fillStyle = '#00FF00';
        this.ctx.fillRect(20, 120, healthBarWidth * healthPercent, healthBarHeight);
        
        // Рамка полоски здоровья
        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(20, 120, healthBarWidth, healthBarHeight);
    }
    
    getMenuItems(state) {
        if (state === 'MENU') {
            return ['НАЧАТЬ ИГРУ', 'ВЫХОД'];
        } else if (state === 'PAUSED') {
            return ['ПРОДОЛЖИТЬ', 'ЗАНОВО', 'ВЫХОД'];
        } else if (state === 'GAME_OVER') {
            return ['ЗАНОВО', 'ВЫХОД'];
        }
        return [];
    }
}
