import 'dart:math';
import 'dart:ui' as ui;
import '../game_config.dart';
import 'player.dart';
import 'island.dart';
import 'projectile.dart';

abstract class Enemy {
  double x;
  double y;
  late double baseSpeed;
  late double speedX;
  late double speedY;
  late double targetAngle;
  late double health;
  late double maxHealth;
  late int shootCooldown;
  late int shootDelay;
  late double size;
  late double radius;
  late int points;
  late bool active;
  late String currentDirection;  // 'up', 'down', 'left', 'right'
  
  Enemy(this.x, this.y) {
    speedX = 0;
    speedY = 0;
    targetAngle = pi / 2;  // 90 градусов вниз
    active = false;
    currentDirection = 'down';
  }
  
  List<Projectile>? update(List<Island> islands, List<Shore> shores, Player player, double worldTop);
  List<Projectile>? shoot(Player player);
  bool takeDamage(double amount);
  double getTorpedoDamage();
  bool collidesWith(double checkX, double checkY, double checkRadius);
}

class SimpleEnemy extends Enemy {
  late double wanderTimer;
  late double wanderAngle;
  String? currentStrategy;  // 'attack' or 'patrol'
  
  SimpleEnemy(double x, double y) : super(x, y) {
    baseSpeed = GameConfig.enemySimpleBaseSpeed;
    health = GameConfig.enemySimpleHealth;
    maxHealth = GameConfig.enemySimpleHealth;
    shootDelay = GameConfig.enemySimpleShootDelay;
    shootCooldown = 0;
    size = GameConfig.enemySimpleSize;
    radius = GameConfig.collisionRadiusEnemySimple;
    points = GameConfig.enemySimplePoints;
    wanderTimer = 0;
    wanderAngle = Random().nextDouble() * 2 * pi;
  }
  
  @override
  List<Projectile>? update(List<Island> islands, List<Shore> shores, Player player, double worldTop) {
    // Активация
    if (!active && y > player.y + GameConfig.enemyActivationDistance * GameConfig.screenHeight) {
      active = true;
      currentStrategy = Random().nextDouble() < GameConfig.enemySimpleAttackChance ? 'attack' : 'patrol';
    }
    
    if (!active) return [];
    
    // Удаление если далеко позади
    if (y > player.y + GameConfig.enemyDeleteDistance) {
      return null;  // Удалить врага
    }
    
    // Проверка видимости игрока
    bool canSeePlayer = (x - player.x).abs() < GameConfig.enemySimpleCanSeeRangeX && 
                        y > player.y - GameConfig.enemySimpleCanSeeRangeY;
    
    // Определение целевого направления
    double targetAngle;
    if (currentStrategy == 'attack') {
      double dx = player.x - x;
      double dy = player.y - y;
      targetAngle = atan2(dy, dx);
    } else {
      wanderTimer--;
      if (wanderTimer <= 0) {
        wanderTimer = Random().nextInt(91) + 90;  // 90-180
        wanderAngle = Random().nextDouble() * pi / 3 - pi / 6;  // -30 to 30 градусов
      }
      targetAngle = pi / 2 + wanderAngle;
    }
    
    // Плавный поворот
    double angleDiff = targetAngle - this.targetAngle;
    while (angleDiff > pi) angleDiff -= 2 * pi;
    while (angleDiff < -pi) angleDiff += 2 * pi;
    this.targetAngle += angleDiff * GameConfig.enemySimpleTurnSmoothness;
    
    // Применение движения
    speedX = cos(this.targetAngle) * baseSpeed;
    speedY = sin(this.targetAngle) * baseSpeed;
    
    double prevX = x;
    double prevY = y;
    x += speedX;
    y += speedY;
    
    // Проверка коллизий
    if (_checkCollision(islands, shores)) {
      x = prevX;
      y = prevY;
      this.targetAngle += [pi / 2, -pi / 2, pi][Random().nextInt(3)];
    }
    
    // Ограничение по краям
    if (x < GameConfig.shoreEdgeMargin - 80) {
      x = GameConfig.shoreEdgeMargin - 80;
      this.targetAngle = Random().nextInt(121) * pi / 180 + pi / 6;  // 30-150 градусов
    } else if (x > GameConfig.screenWidth - GameConfig.shoreEdgeMargin + 80) {
      x = GameConfig.screenWidth - GameConfig.shoreEdgeMargin + 80;
      this.targetAngle = Random().nextInt(121) * pi / 180 + 7 * pi / 6;  // 210-330 градусов
    }
    
    _updateAnimation();
    
    if (shootCooldown > 0) {
      shootCooldown--;
    }
    
    if (shootCooldown == 0 && canSeePlayer) {
      return shoot(player);
    }
    
    return [];
  }
  
  bool _checkCollision(List<Island> islands, List<Shore> shores) {
    for (var island in islands) {
      if (island.collidesWith(x, y, radius)) return true;
    }
    for (var shore in shores) {
      if (shore.collidesWith(x, y, radius)) return true;
    }
    return false;
  }
  
  void _updateAnimation() {
    if (speedX.abs() > speedY.abs()) {
      currentDirection = speedX > 0 ? 'right' : 'left';
    } else {
      currentDirection = speedY > 0 ? 'down' : 'up';
    }
  }
  
  @override
  List<Projectile>? shoot(Player player) {
    shootCooldown = shootDelay;
    double dx = player.x - x;
    double dy = player.y - y;
    double angle = atan2(dy, dx);
    
    return [Projectile(x, y, angle, false, 
                      speed: GameConfig.enemySimpleProjectileSpeed)];
  }
  
  @override
  bool takeDamage(double amount) {
    health -= amount;
    return health <= 0;
  }
  
  @override
  double getTorpedoDamage() => GameConfig.enemySimpleTorpedoDamage;
  
  @override
  bool collidesWith(double checkX, double checkY, double checkRadius) {
    double dx = x - checkX;
    double dy = y - checkY;
    return sqrt(dx * dx + dy * dy) < radius + checkRadius;
  }
}

class HardEnemy extends Enemy {
  late double wanderTimer;
  late double wanderAngle;
  late List<ui.Offset> patrolPoints;
  late int pursuitTimer;
  late double pursuitDirection;
  String? currentStrategy;
  late int armorTimer;
  
  HardEnemy(double x, double y) : super(x, y) {
    baseSpeed = GameConfig.enemyHardBaseSpeed;
    health = GameConfig.enemyHardHealth;
    maxHealth = GameConfig.enemyHardHealth;
    shootDelay = GameConfig.enemyHardShootDelay;
    shootCooldown = 0;
    size = GameConfig.enemyHardSize;
    radius = GameConfig.collisionRadiusEnemyHard;
    points = GameConfig.enemyHardPoints;
    wanderTimer = 0;
    wanderAngle = Random().nextDouble() * pi / 3 - pi / 6;
    patrolPoints = [];
    pursuitTimer = 0;
    pursuitDirection = 0;
    armorTimer = 0;
  }
  
  @override
  List<Projectile>? update(List<Island> islands, List<Shore> shores, Player player, double worldTop) {
    // Активация
    if (!active && y > player.y + GameConfig.enemyActivationDistance * GameConfig.screenHeight) {
      active = true;
      if (Random().nextDouble() < GameConfig.enemyHardAggressiveChance) {
        currentStrategy = 'aggressive';
        pursuitTimer = 0;
      } else {
        currentStrategy = 'patrol';
        _generatePatrolPoints(player);
      }
    }
    
    if (!active) return [];
    
    if (y > player.y + GameConfig.enemyDeleteDistance) {
      return null;
    }
    
    bool canSeePlayer = (x - player.x).abs() < GameConfig.enemyHardCanSeeRangeX && 
                        (y - player.y).abs() < GameConfig.enemyHardCanSeeRangeY;
    
    double targetAngle = _calculateTargetAngle(canSeePlayer, player);
    
    // Плавный поворот
    double angleDiff = targetAngle - this.targetAngle;
    while (angleDiff > pi) angleDiff -= 2 * pi;
    while (angleDiff < -pi) angleDiff += 2 * pi;
    this.targetAngle += angleDiff * GameConfig.enemyHardTurnSmoothness;
    
    // Применение движения
    speedX = cos(this.targetAngle) * baseSpeed;
    speedY = sin(this.targetAngle) * baseSpeed;
    
    double prevX = x;
    double prevY = y;
    x += speedX;
    y += speedY;
    
    // Проверка коллизий
    if (_checkCollision(islands, shores)) {
      x = prevX;
      y = prevY;
      double turnAngle = [pi / 2, -pi / 2][Random().nextInt(2)];
      this.targetAngle += turnAngle;
      wanderAngle = this.targetAngle - pi / 2;
    }
    
    // Ограничение по краям
    if (x < GameConfig.shoreWidth) {
      x = GameConfig.shoreWidth;
      this.targetAngle = Random().nextInt(121) * pi / 180 + pi / 6;
      wanderAngle = this.targetAngle - pi / 2;
    } else if (x > GameConfig.screenWidth - GameConfig.shoreWidth) {
      x = GameConfig.screenWidth - GameConfig.shoreWidth;
      this.targetAngle = Random().nextInt(121) * pi / 180 + 7 * pi / 6;
      wanderAngle = this.targetAngle - pi / 2;
    }
    
    _updateAnimation();
    _updateTimers();
    
    if (shootCooldown == 0 && canSeePlayer) {
      return shoot(player);
    }
    
    return [];
  }
  
  double _calculateTargetAngle(bool canSeePlayer, Player player) {
    if (currentStrategy == 'aggressive') {
      if (canSeePlayer) {
        double predictX = player.x + (player.hullAngle / 45) * 50;
        double predictY = player.y - 50;
        double dx = predictX - x;
        double dy = predictY - y;
        double angle = atan2(dy, dx);
        pursuitTimer = GameConfig.enemyHardPursuitTimer;
        pursuitDirection = angle;
        return angle;
      } else if (pursuitTimer > 0) {
        pursuitTimer--;
        return pursuitDirection;
      } else {
        double angle = pi / 2 + wanderAngle;
        wanderTimer--;
        if (wanderTimer <= 0) {
          wanderTimer = Random().nextInt(121) + 180;  // 180-300
          wanderAngle += (Random().nextDouble() * 0.1 - 0.05);
          wanderAngle = wanderAngle.clamp(-pi / 6, pi / 6);
        }
        return angle;
      }
    } else {  // patrol
      if (patrolPoints.isEmpty) {
        _generatePatrolPoints(player);
      }
      
      double targetX = patrolPoints[0].dx;
      double targetY = patrolPoints[0].dy;
      double dx = targetX - x;
      double dy = targetY - y;
      double distance = sqrt(dx * dx + dy * dy);
      
      if (distance < GameConfig.enemyHardMinPatrolDistance) {
        patrolPoints.removeAt(0);
        if (patrolPoints.isEmpty) {
          _generatePatrolPoints(player);
        }
        if (patrolPoints.isNotEmpty) {
          targetX = patrolPoints[0].dx;
          targetY = patrolPoints[0].dy;
          dx = targetX - x;
          dy = targetY - y;
        }
      }
      
      return atan2(dy, dx);
    }
  }
  
  void _generatePatrolPoints(Player player) {
    patrolPoints.clear();
    double startX = x;
    double startY = y + 200;
    
    int numPoints = Random().nextInt(GameConfig.enemyHardPatrolPointsMax - 
                                    GameConfig.enemyHardPatrolPointsMin + 1) + 
                   GameConfig.enemyHardPatrolPointsMin;
    
    for (int i = 0; i < numPoints; i++) {
      double yOffset = Random().nextDouble() * 400 + 400;  // 400-800
      double xOffset = Random().nextDouble() * 600 - 300;  // -300 to 300
      
      double px = (startX + xOffset).clamp(300.0, GameConfig.screenWidth - 300);
      double py = startY + yOffset;
      
      // Избегаем близости к игроку
      double distToPlayer = sqrt((px - player.x) * (px - player.x) + (py - player.y) * (py - player.y));
      if (distToPlayer < 300) {
        double dx = px - player.x;
        double dy = py - player.y;
        double dist = sqrt(dx * dx + dy * dy);
        if (dist > 0) {
          px += (dx / dist) * 300;
          py += (dy / dist) * 300;
        }
      }
      
      patrolPoints.add(ui.Offset(px, py));
      startX = px;
      startY = py;
    }
  }
  
  bool _checkCollision(List<Island> islands, List<Shore> shores) {
    for (var island in islands) {
      if (island.collidesWith(x, y, radius)) return true;
    }
    for (var shore in shores) {
      if (shore.collidesWith(x, y, radius)) return true;
    }
    return false;
  }
  
  void _updateAnimation() {
    if (speedX.abs() > speedY.abs() * 0.7) {
      currentDirection = speedX > 0 ? 'right' : 'left';
    } else {
      currentDirection = speedY > 0 ? 'down' : 'up';
    }
  }
  
  void _updateTimers() {
    if (armorTimer > 0) armorTimer--;
    if (shootCooldown > 0) shootCooldown--;
  }
  
  @override
  List<Projectile>? shoot(Player player) {
    shootCooldown = shootDelay;
    
    List<Projectile> projectiles = [];
    double baseAngle = atan2(player.y - y, player.x - x);
    
    for (int i = -1; i <= 1; i++) {
      double angle = baseAngle + i * GameConfig.enemyHardProjectileSpread;
      projectiles.add(Projectile(x, y, angle, false,
                                speed: GameConfig.enemyHardProjectileSpeed));
    }
    
    return projectiles;
  }
  
  @override
  bool takeDamage(double amount) {
    health -= amount;
    armorTimer = GameConfig.enemyHardArmorFlashDuration;
    return health <= 0;
  }
  
  @override
  double getTorpedoDamage() => GameConfig.enemyHardTorpedoDamage;
  
  @override
  bool collidesWith(double checkX, double checkY, double checkRadius) {
    double dx = x - checkX;
    double dy = y - checkY;
    return sqrt(dx * dx + dy * dy) < radius + checkRadius;
  }
}

