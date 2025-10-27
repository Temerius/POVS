/**
 * Game Logic - игровая логика Sea Defenders
 * Управление состоянием игры, врагами, пулями, коллизиями
 */

class GameLogic {
    constructor() {
        this.gameState = {
            state: 'MENU', // MENU, PLAYING, PAUSED, GAME_OVER
            selectedItem: 0,
            score: 0
        };
        
        this.player = {
            x: this.SCREEN_WIDTH / 2,
            y: this.SCREEN_HEIGHT - 100,
            hp: 100,
            angle: 0,
            shootCooldown: 0
        };
        
        // Прокрутка фона
        this.scrollY = 0;
        this.scrollSpeed = 2;
        
        this.enemies = new Array(20).fill(null).map(() => ({ active: false }));
        this.bullets = new Array(20).fill(null).map(() => ({ active: false }));
        this.enemyBullets = new Array(20).fill(null).map(() => ({ active: false }));
        this.explosions = new Array(10).fill(null).map(() => ({ active: false }));
        this.islands = [];
        this.whirlpools = [];
        
        // Константы
        this.SCREEN_WIDTH = window.innerWidth;
        this.SCREEN_HEIGHT = window.innerHeight;
        
        // Обновляем размеры при изменении окна
        window.addEventListener('resize', () => {
            this.SCREEN_WIDTH = window.innerWidth;
            this.SCREEN_HEIGHT = window.innerHeight;
        });
        this.MAX_SHIP_ANGLE = 45;
        this.ANGLE_STEP = 15;
        this.ANGLE_RETURN_SPEED = 2;
        this.SHIP_SPEED = 3;
        this.FIRE_COOLDOWN = 18;
        
        // Таймеры
        this.enemySpawnTimer = 0;
        this.enemySpawnInterval = 45;
        this.lastUpdateTime = 0;
        
        this.initLevel();
    }
    
    initLevel() {
        // Создаем острова с алгоритмом генерации
        this.islands = [];
        this.generateIslands();
        
        // Создаем водовороты
        this.whirlpools = [];
        for (let i = 0; i < 4; i++) {
            this.whirlpools.push({
                x: Math.random() * (this.SCREEN_WIDTH - 100) + 50,
                y: Math.random() * 200 + 200,
                targetX: Math.random() * (this.SCREEN_WIDTH - 100) + 50,
                targetY: Math.random() * 200 + 200,
                active: true
            });
        }
    }
    
    generateIslands() {
        const numIslands = 6;
        const minDistance = 200;
        
        for (let i = 0; i < numIslands; i++) {
            let attempts = 0;
            let x, y, width, height;
            
            do {
                x = Math.random() * (this.SCREEN_WIDTH - 300) + 150;
                y = Math.random() * 400 + 100;
                width = Math.random() * 120 + 80;
                height = Math.random() * 80 + 60;
                attempts++;
            } while (this.isTooCloseToOtherIslands(x, y, width, height, minDistance) && attempts < 50);
            
            if (attempts < 50) {
                this.islands.push({
                    x: x,
                    y: y,
                    width: width,
                    height: height,
                    active: true,
                    points: this.generateIslandShape(x, y, width, height),
                    trees: this.generateTrees(x, y, width, height)
                });
            }
        }
    }
    
    generateIslandShape(centerX, centerY, width, height) {
        const points = [];
        const numPoints = 8 + Math.floor(Math.random() * 8);
        const baseRadiusX = width / 2;
        const baseRadiusY = height / 2;
        
        for (let i = 0; i < numPoints; i++) {
            const angle = (i / numPoints) * Math.PI * 2;
            const radiusVariation = 0.7 + Math.random() * 0.6; // 0.7-1.3
            const radiusX = baseRadiusX * radiusVariation;
            const radiusY = baseRadiusY * radiusVariation;
            
            const x = centerX + Math.cos(angle) * radiusX;
            const y = centerY + Math.sin(angle) * radiusY;
            
            points.push({ x: x, y: y });
        }
        
        return points;
    }
    
    isTooCloseToOtherIslands(x, y, width, height, minDistance) {
        for (let island of this.islands) {
            const dx = x - island.x;
            const dy = y - island.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            const maxRadius = Math.max(width, height) / 2;
            const islandMaxRadius = Math.max(island.width, island.height) / 2;
            
            if (distance < minDistance + maxRadius + islandMaxRadius) {
                return true;
            }
        }
        return false;
    }
    
    generateTrees(islandX, islandY, islandWidth, islandHeight) {
        const trees = [];
        const numTrees = Math.floor((islandWidth + islandHeight) / 30);
        
        for (let i = 0; i < numTrees; i++) {
            // Генерируем позицию дерева на острове
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * Math.min(islandWidth, islandHeight) / 2 - 15;
            const treeX = islandX + Math.cos(angle) * distance;
            const treeY = islandY + Math.sin(angle) * distance;
            
            trees.push({
                x: treeX,
                y: treeY,
                type: Math.random() < 0.7 ? 'palm' : 'bush',
                size: Math.random() * 15 + 10
            });
        }
        
        return trees;
    }
    
    isPointInIsland(x, y, island) {
        if (!island.points || island.points.length < 3) {
            // Fallback для круглых островов
            const dx = x - island.x;
            const dy = y - island.y;
            const radius = Math.max(island.width, island.height) / 2;
            return Math.sqrt(dx * dx + dy * dy) < radius;
        }
        
        // Проверка точки в полигоне
        let inside = false;
        for (let i = 0, j = island.points.length - 1; i < island.points.length; j = i++) {
            if (((island.points[i].y > y) !== (island.points[j].y > y)) &&
                (x < (island.points[j].x - island.points[i].x) * (y - island.points[i].y) / (island.points[j].y - island.points[i].y) + island.points[i].x)) {
                inside = !inside;
            }
        }
        return inside;
    }
    
    update(input, deltaTime) {
        if (this.gameState.state === 'MENU') {
            this.updateMenu(input);
        } else if (this.gameState.state === 'PLAYING') {
            this.updateGame(input, deltaTime);
        } else if (this.gameState.state === 'PAUSED') {
            this.updateMenu(input);
        } else if (this.gameState.state === 'GAME_OVER') {
            this.updateMenu(input);
        }
    }
    
    updateMenu(input) {
        // Навигация по меню
        if (input.left && !this.lastInput?.left) {
            this.gameState.selectedItem = Math.max(0, this.gameState.selectedItem - 1);
        }
        if (input.right && !this.lastInput?.right) {
            const maxItems = this.getMenuItems().length;
            this.gameState.selectedItem = Math.min(maxItems - 1, this.gameState.selectedItem + 1);
        }
        
        // Выбор пункта меню
        if (input.fire && !this.lastInput?.fire) {
            this.selectMenuItem();
        }
        
        this.lastInput = { ...input };
    }
    
    updateGame(input, deltaTime) {
        // Прокрутка фона
        this.scrollY += this.scrollSpeed;
        
        // Обновление игрока
        this.updatePlayer(input, deltaTime);
        
        // Обновление пуль
        this.updateBullets(deltaTime);
        
        // Обновление врагов
        this.updateEnemies(deltaTime);
        
        // Обновление взрывов
        this.updateExplosions(deltaTime);
        
        // Обновление островов
        this.updateIslands(deltaTime);
        
        // Обновление водоворотов
        this.updateWhirlpools(deltaTime);
        
        // Спавн врагов
        this.updateEnemySpawning(deltaTime);
        
        // Проверка коллизий
        this.checkCollisions();
        
        // Проверка окончания игры
        if (this.player.hp <= 0) {
            this.gameState.state = 'GAME_OVER';
            this.gameState.selectedItem = 0;
        }
    }
    
    updatePlayer(input, deltaTime) {
        // Уменьшаем кулдаун стрельбы
        if (this.player.shootCooldown > 0) {
            this.player.shootCooldown--;
        }
        
        // Движение корабля
        const moveSpeed = 4;
        
        // Движение влево-вправо
        if (input.left) {
            this.player.x -= moveSpeed;
            this.player.angle = Math.max(-this.MAX_SHIP_ANGLE, this.player.angle - this.ANGLE_STEP);
        }
        if (input.right) {
            this.player.x += moveSpeed;
            this.player.angle = Math.min(this.MAX_SHIP_ANGLE, this.player.angle + this.ANGLE_STEP);
        }
        
        // Постепенный возврат к прямому курсу
        if (this.player.angle > 0) {
            this.player.angle = Math.max(0, this.player.angle - this.ANGLE_RETURN_SPEED);
        } else if (this.player.angle < 0) {
            this.player.angle = Math.min(0, this.player.angle + this.ANGLE_RETURN_SPEED);
        }
        
        // Ограничения по экрану
        this.player.x = Math.max(30, Math.min(this.SCREEN_WIDTH - 30, this.player.x));
        this.player.y = Math.max(50, Math.min(this.SCREEN_HEIGHT - 50, this.player.y));
        
        // Стрельба
        if (input.fire && this.player.shootCooldown === 0) {
            this.playerShoot();
        }
    }
    
    playerShoot() {
        this.player.shootCooldown = this.FIRE_COOLDOWN;
        
        // Находим свободную пулю
        for (let i = 0; i < this.bullets.length; i++) {
            if (!this.bullets[i].active) {
                this.bullets[i] = {
                    x: this.player.x,
                    y: this.player.y - 20,
                    velX: 0,
                    velY: -8,
                    active: true
                };
                
                // Зеркальная логика стрельбы
                if (this.player.angle < -15) { // Поворот влево = стрельба вправо
                    this.bullets[i].velX = 6;
                    this.bullets[i].velY = -6;
                } else if (this.player.angle > 15) { // Поворот вправо = стрельба влево
                    this.bullets[i].velX = -6;
                    this.bullets[i].velY = -6;
                } else { // Прямо = не стреляем
                    this.bullets[i].active = false;
                }
                
                break;
            }
        }
    }
    
    updateBullets(deltaTime) {
        for (let bullet of this.bullets) {
            if (bullet.active) {
                bullet.x += bullet.velX;
                bullet.y += bullet.velY;
                
                // Удаление за границами экрана
                if (bullet.y < -20 || bullet.x < -20 || bullet.x > this.SCREEN_WIDTH + 20) {
                    bullet.active = false;
                }
            }
        }
    }
    
    updateEnemies(deltaTime) {
        for (let enemy of this.enemies) {
            if (enemy.active) {
                enemy.x += enemy.velX;
                enemy.y += enemy.velY;
                
                // Удаление за экраном
                if (enemy.y > this.SCREEN_HEIGHT + 50) {
                    enemy.active = false;
                }
                
                // Стрельба галеонов
                if (enemy.type === 1 && enemy.shootCooldown > 0) {
                    enemy.shootCooldown--;
                } else if (enemy.type === 1) {
                    this.enemyShoot(enemy);
                    enemy.shootCooldown = 120;
                }
            }
        }
    }
    
    enemyShoot(enemy) {
        for (let i = 0; i < this.enemyBullets.length; i++) {
            if (!this.enemyBullets[i].active) {
                this.enemyBullets[i] = {
                    x: enemy.x,
                    y: enemy.y + 20,
                    velX: 0,
                    velY: 4,
                    active: true
                };
                break;
            }
        }
    }
    
    updateExplosions(deltaTime) {
        for (let explosion of this.explosions) {
            if (explosion.active) {
                explosion.frame++;
                if (explosion.frame >= 10) {
                    explosion.active = false;
                }
            }
        }
    }
    
    updateIslands(deltaTime) {
        for (let island of this.islands) {
            if (island.active) {
                // Движем острова вниз
                const deltaY = this.scrollSpeed;
                island.y += deltaY;
                
                // Обновляем позиции точек острова
                if (island.points) {
                    for (let point of island.points) {
                        point.y += deltaY;
                    }
                }
                
                // Обновляем позиции деревьев
                if (island.trees) {
                    for (let tree of island.trees) {
                        tree.y += deltaY;
                    }
                }
                
                // Если остров вышел за экран, перемещаем его вверх
                if (island.y > this.SCREEN_HEIGHT + 100) {
                    island.y = -100;
                    island.x = Math.random() * (this.SCREEN_WIDTH - 300) + 150;
                    island.width = Math.random() * 120 + 80;
                    island.height = Math.random() * 80 + 60;
                    island.points = this.generateIslandShape(island.x, island.y, island.width, island.height);
                    island.trees = this.generateTrees(island.x, island.y, island.width, island.height);
                }
            }
        }
    }
    
    updateWhirlpools(deltaTime) {
        for (let whirlpool of this.whirlpools) {
            if (whirlpool.active) {
                // Движем водовороты вниз
                whirlpool.y += this.scrollSpeed;
                
                // Если водоворот вышел за экран, перемещаем его вверх
                if (whirlpool.y > this.SCREEN_HEIGHT + 100) {
                    whirlpool.y = -100;
                    whirlpool.x = Math.random() * (this.SCREEN_WIDTH - 100) + 50;
                    whirlpool.targetX = Math.random() * (this.SCREEN_WIDTH - 100) + 50;
                    whirlpool.targetY = Math.random() * 200 + 200;
                }
            }
        }
    }
    
    updateEnemySpawning(deltaTime) {
        this.enemySpawnTimer++;
        if (this.enemySpawnTimer >= this.enemySpawnInterval) {
            this.spawnEnemy();
            this.enemySpawnTimer = 0;
            // Увеличиваем сложность со временем
            this.enemySpawnInterval = Math.max(20, 45 - Math.floor(this.gameState.score / 50) * 3);
        }
    }
    
    spawnEnemy() {
        // Спавним несколько врагов за раз
        const numEnemies = Math.random() < 0.3 ? 2 : 1;
        
        for (let j = 0; j < numEnemies; j++) {
            // Находим свободного врага
            for (let i = 0; i < this.enemies.length; i++) {
                if (!this.enemies[i].active) {
                    const type = Math.random() < 0.6 ? 0 : 1; // 60% шлюпки, 40% галеоны
                    
                    this.enemies[i] = {
                        x: Math.random() * (this.SCREEN_WIDTH - 100) + 50,
                        y: -50 - j * 30, // Размещаем врагов с интервалом
                        velX: (Math.random() - 0.5) * 6,
                        velY: Math.random() * 3 + 1,
                        type: type,
                        hp: type === 0 ? 20 : 40,
                        maxHp: type === 0 ? 20 : 40,
                        shootCooldown: type === 1 ? 60 : 0,
                        active: true
                    };
                    break;
                }
            }
        }
    }
    
    checkCollisions() {
        // Пули игрока vs враги
        for (let bullet of this.bullets) {
            if (!bullet.active) continue;
            
            for (let enemy of this.enemies) {
                if (!enemy.active) continue;
                
                const dx = bullet.x - enemy.x;
                const dy = bullet.y - enemy.y;
                
                if (Math.abs(dx) < 20 && Math.abs(dy) < 20) {
                    bullet.active = false;
                    enemy.hp -= 10;
                    
                    if (enemy.hp <= 0) {
                        this.createExplosion(enemy.x, enemy.y);
                        enemy.active = false;
                        this.gameState.score += enemy.type === 0 ? 10 : 25;
                    }
                }
            }
        }
        
        // Пули врагов vs игрок
        for (let bullet of this.enemyBullets) {
            if (!bullet.active) continue;
            
            const dx = bullet.x - this.player.x;
            const dy = bullet.y - this.player.y;
            
            if (Math.abs(dx) < 30 && Math.abs(dy) < 20) {
                bullet.active = false;
                this.player.hp = Math.max(0, this.player.hp - 10);
            }
        }
        
        // Враги vs игрок
        for (let enemy of this.enemies) {
            if (!enemy.active) continue;
            
            const dx = enemy.x - this.player.x;
            const dy = enemy.y - this.player.y;
            
            if (Math.abs(dx) < 40 && Math.abs(dy) < 30) {
                this.createExplosion(enemy.x, enemy.y);
                enemy.active = false;
                this.player.hp = Math.max(0, this.player.hp - 20);
            }
        }
        
        // Игрок vs острова
        for (let island of this.islands) {
            if (!island.active) continue;
            
            if (this.isPointInIsland(this.player.x, this.player.y, island)) {
                this.player.hp = Math.max(0, this.player.hp - 10);
            }
        }
        
        // Игрок vs водовороты
        for (let whirlpool of this.whirlpools) {
            if (!whirlpool.active) continue;
            
            const dx = whirlpool.x - this.player.x;
            const dy = whirlpool.y - this.player.y;
            
            if (Math.abs(dx) < 20 && Math.abs(dy) < 20) {
                this.player.x = whirlpool.targetX;
                this.player.y = whirlpool.targetY;
            }
        }
    }
    
    createExplosion(x, y) {
        for (let i = 0; i < this.explosions.length; i++) {
            if (!this.explosions[i].active) {
                this.explosions[i] = {
                    x: x,
                    y: y,
                    frame: 0,
                    active: true
                };
                break;
            }
        }
    }
    
    selectMenuItem() {
        if (this.gameState.state === 'MENU') {
            if (this.gameState.selectedItem === 0) { // Начать игру
                this.startGame();
            } else if (this.gameState.selectedItem === 1) { // Выход
                // Ничего не делаем
            }
        } else if (this.gameState.state === 'PAUSED') {
            if (this.gameState.selectedItem === 0) { // Продолжить
                this.gameState.state = 'PLAYING';
            } else if (this.gameState.selectedItem === 1) { // Заново
                this.startGame();
            } else if (this.gameState.selectedItem === 2) { // Выход
                this.gameState.state = 'MENU';
                this.gameState.selectedItem = 0;
            }
        } else if (this.gameState.state === 'GAME_OVER') {
            if (this.gameState.selectedItem === 0) { // Заново
                this.startGame();
            } else if (this.gameState.selectedItem === 1) { // Выход
                this.gameState.state = 'MENU';
                this.gameState.selectedItem = 0;
            }
        }
    }
    
    startGame() {
        this.gameState.state = 'PLAYING';
        this.player.x = this.SCREEN_WIDTH / 2;
        this.player.y = this.SCREEN_HEIGHT - 100;
        this.player.hp = 100;
        this.player.angle = 0;
        this.gameState.score = 0;
        this.scrollY = 0;
        
        // Очищаем массивы
        this.enemies.forEach(enemy => enemy.active = false);
        this.bullets.forEach(bullet => bullet.active = false);
        this.enemyBullets.forEach(bullet => bullet.active = false);
        this.explosions.forEach(explosion => explosion.active = false);
        
        this.initLevel();
    }
    
    getMenuItems() {
        if (this.gameState.state === 'MENU') {
            return ['НАЧАТЬ ИГРУ', 'ВЫХОД'];
        } else if (this.gameState.state === 'PAUSED') {
            return ['ПРОДОЛЖИТЬ', 'ЗАНОВО', 'ВЫХОД'];
        } else if (this.gameState.state === 'GAME_OVER') {
            return ['ЗАНОВО', 'ВЫХОД'];
        }
        return [];
    }
    
    getGameState() {
        return {
            gameState: this.gameState,
            player: this.player,
            enemies: this.enemies.filter(e => e.active),
            bullets: this.bullets.filter(b => b.active),
            enemyBullets: this.enemyBullets.filter(b => b.active),
            explosions: this.explosions.filter(e => e.active),
            islands: this.islands.filter(i => i.active),
            whirlpools: this.whirlpools.filter(w => w.active),
            scrollY: this.scrollY
        };
    }
}
