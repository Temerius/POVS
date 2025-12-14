import 'dart:math';
import '../game_config.dart';
import 'island.dart';
import 'player.dart';
import 'enemy.dart';

class Projectile {
  double x;
  double y;
  double angle;
  late double speed;
  late int color;
  late int lifetime;
  late double radius;
  bool isPlayerShot;

  Projectile(this.x, this.y, this.angle, this.isPlayerShot,
      {double? speed, int? color}) {
    this.speed = speed ?? GameConfig.projectileSpeed;
    this.color = color ?? (isPlayerShot 
        ? GameConfig.projectileColorPlayer 
        : GameConfig.projectileColorEnemy);
    lifetime = GameConfig.projectileLifetime;
    radius = GameConfig.projectileRadius;
  }

  void update() {
    x += cos(angle) * speed;
    y += sin(angle) * speed;
    lifetime--;
  }

  bool collidesWith(dynamic obstacle) {
    if (obstacle is Island) {
      return obstacle.collidesWith(x, y, radius);
    } else if (obstacle is Shore) {
      return obstacle.collidesWith(x, y, radius);
    } else if (obstacle is Enemy) {
      double dx = x - obstacle.x;
      double dy = y - obstacle.y;
      double distance = sqrt(dx * dx + dy * dy);
      return distance < radius + obstacle.radius;
    } else if (obstacle is Player) {
      double dx = x - obstacle.x;
      double dy = y - obstacle.y;
      double distance = sqrt(dx * dx + dy * dy);
      return distance < radius + obstacle.radius;
    }
    return false;
  }
}

