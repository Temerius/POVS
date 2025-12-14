import 'dart:math';
import '../game_config.dart';
import 'projectile.dart';
import 'island.dart';

class Player {
  double x;
  double y;
  late double hullAngle;  // угол поворота корпуса в градусах
  late double size;
  late double baseSpeed;
  late double health;
  late double maxHealth;
  late int shootCooldown;
  late int score;
  late double radius;
  late double totalDistance;  // Общее пройденное расстояние в пикселях

  Player(this.x, this.y) {
    hullAngle = 0;
    size = GameConfig.playerSize;
    baseSpeed = GameConfig.playerBaseSpeed;
    health = GameConfig.playerMaxHealth;
    maxHealth = GameConfig.playerMaxHealth;
    shootCooldown = 0;
    score = 0;
    radius = GameConfig.collisionRadiusPlayer;
    totalDistance = 0.0;
  }

  void update(double joystickX, double joystickY, List<dynamic> obstacles) {
    // Управление через джойстик
    // joystickX и joystickY от -100 до 100
    // joystickX управляет поворотом и боковым движением (чем больше отклонение, тем быстрее поворот)
    // joystickY управляет скоростью вперёд (чем больше отклонение, тем быстрее)
    
    _handleRotation(joystickX);
    _handleMovement(joystickX, joystickY, obstacles);
    _updateCooldown();
  }

  void _handleRotation(double joystickX) {
    // Джойстик X управляет углом поворота
    // Чем больше отклонение, тем быстрее поворот
    double rotationSpeed = GameConfig.playerRotationSpeed * (joystickX.abs() / 100.0).clamp(0.1, 1.0);
    double targetAngle = (joystickX / 100.0) * GameConfig.playerMaxAngle;
    
    // Плавный поворот
    double angleDiff = targetAngle - hullAngle;
    if (angleDiff.abs() > rotationSpeed) {
      hullAngle += angleDiff.sign * rotationSpeed;
    } else {
      hullAngle = targetAngle;
    }
    
    // Автовозврат к прямому курсу если джойстик в центре
    if (joystickX.abs() < 5) {
      if (hullAngle.abs() < GameConfig.playerAutoReturnSpeed) {
        hullAngle = 0;
      } else {
        hullAngle -= hullAngle.sign * GameConfig.playerAutoReturnSpeed;
      }
    }
    
    hullAngle = hullAngle.clamp(-GameConfig.playerMaxAngle, GameConfig.playerMaxAngle);
  }

  void _handleMovement(double joystickX, double joystickY, List<dynamic> obstacles) {
    double oldX = x;
    double oldY = y;
    
    // Скорость зависит от отклонения джойстика Y (чем больше отклонение, тем быстрее)
    // joystickY: положительное = вперёд (вверх), отрицательное = назад (вниз)
    // Но в игре всегда движемся вперёд, просто меняется скорость
    double forwardSpeedMultiplier = 1.0 + (joystickY.abs() / 100.0) * 0.5;
    double forwardSpeed = baseSpeed * forwardSpeedMultiplier;
    
    // Движение вперёд (вверх по экрану в игре) - всегда
    y -= forwardSpeed;
    
    // Накапливаем пройденное расстояние с учетом реальной скорости
    totalDistance += forwardSpeed;
    
    // Боковое смещение от угла поворота И от джойстика X
    // Чем больше отклонение X, тем больше боковое смещение
    double sideSpeedFromAngle = (hullAngle / GameConfig.playerMaxAngle) * GameConfig.playerSideSpeedMultiplier;
    double sideSpeedFromJoystick = (joystickX / 100.0) * 2.0;  // Прямое управление боковым движением
    x += sideSpeedFromAngle + sideSpeedFromJoystick;
    
    // Ограничение краёв экрана
    x = x.clamp(GameConfig.playerEdgeMargin, GameConfig.screenWidth - GameConfig.playerEdgeMargin);
    
    // Проверка коллизий
    if (_checkCollisions(obstacles)) {
      _handleCollision(oldX, oldY);
    }
  }

  bool _checkCollisions(List<dynamic> obstacles) {
    for (var obstacle in obstacles) {
      if (obstacle is Island) {
        if (obstacle.collidesWith(x, y, radius)) {
          return true;
        }
      } else if (obstacle is Shore) {
        if (obstacle.collidesWith(x, y, radius)) {
          return true;
        }
      }
    }
    return false;
  }

  void _handleCollision(double oldX, double oldY) {
    health -= GameConfig.playerCollisionDamage;
    x = oldX;
    y = oldY;
    y += GameConfig.playerCollisionPushback;
  }

  void _updateCooldown() {
    if (shootCooldown > 0) {
      shootCooldown--;
    }
  }

  bool collidesWith(double checkX, double checkY, double checkRadius) {
    double dx = x - checkX;
    double dy = y - checkY;
    double distance = sqrt(dx * dx + dy * dy);
    return distance < radius + checkRadius;
  }

  List<Projectile>? shoot() {
    if (shootCooldown > 0) {
      return null;
    }
    
    shootCooldown = GameConfig.playerShootCooldown;
    
    double angle = -pi / 2;  // Вверх
    
    if (hullAngle > GameConfig.playerMinAngleForSideShot) {
      angle += GameConfig.playerShootAngleOffset * pi / 180;
    } else if (hullAngle < -GameConfig.playerMinAngleForSideShot) {
      angle -= GameConfig.playerShootAngleOffset * pi / 180;
    }
    
    return [Projectile(x, y, angle, true)];
  }

  bool takeDamage(double amount) {
    health -= amount;
    return health <= 0;
  }
}

