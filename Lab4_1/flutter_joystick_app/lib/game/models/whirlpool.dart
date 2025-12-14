import 'dart:math';
import 'dart:ui' as ui;
import '../game_config.dart';
import 'island.dart';

class Whirlpool {
  double x;
  double y;
  late double radius;
  late double rotation;
  late bool usedRecently;
  late int cooldownTimer;
  late double animationPhase;

  Whirlpool(this.x, this.y) {
    radius = GameConfig.whirlpoolRadius;
    rotation = 0;
    usedRecently = false;
    cooldownTimer = 0;
    animationPhase = 0;
  }

  void update() {
    rotation = (rotation + GameConfig.whirlpoolRotationSpeed) % 360;
    animationPhase = (animationPhase + GameConfig.whirlpoolAnimationSpeed) % (2 * pi);

    if (cooldownTimer > 0) {
      cooldownTimer--;
      if (cooldownTimer == 0) {
        usedRecently = false;
      }
    }
  }

  bool collidesWith(double checkX, double checkY, double checkRadius) {
    if (usedRecently) return false;

    double dx = checkX - x;
    double dy = checkY - y;
    double dist = sqrt(dx * dx + dy * dy);
    return dist < radius + checkRadius;
  }

  static bool canPlaceWhirlpool(double x, double y, List<Island> islands, 
                                List<Shore> shores, List<Whirlpool> existingWhirlpools,
                                {double minDistance = GameConfig.whirlpoolMinDistance}) {
    // Проверка расстояния до островов
    for (var island in islands) {
      double safeDistance = island.radius + GameConfig.whirlpoolIslandSafeDistance;
      double dist = sqrt((island.x - x) * (island.x - x) + (island.y - y) * (island.y - y));
      if (dist < safeDistance) return false;
    }

    // Проверка что не внутри острова
    for (var island in islands) {
      if (island.collidesWith(x, y, 0)) return false;
    }

    // Проверка расстояния до берегов
    if (x < GameConfig.whirlpoolEdgeMargin || 
        x > GameConfig.screenWidth - GameConfig.whirlpoolEdgeMargin) {
      return false;
    }

    // Проверка расстояния до других водоворотов
    for (var whirlpool in existingWhirlpools) {
      double dist = sqrt((whirlpool.x - x) * (whirlpool.x - x) + 
                        (whirlpool.y - y) * (whirlpool.y - y));
      if (dist < minDistance * 2.5) return false;
    }

    return true;
  }

  static Whirlpool? findTeleportTarget(Whirlpool currentWhirlpool, 
                                       List<Whirlpool> allWhirlpools,
                                       double worldTop,
                                       List<Island> islands,
                                       List<Shore> shores,
                                       {double minDistance = GameConfig.whirlpoolTeleportDistance}) {
    List<Whirlpool> candidates = [];

    for (var whirlpool in allWhirlpools) {
      if (whirlpool != currentWhirlpool &&
          !whirlpool.usedRecently &&
          whirlpool.y < currentWhirlpool.y - minDistance &&
          whirlpool.y > worldTop) {
        candidates.add(whirlpool);
      }
    }

    if (candidates.isNotEmpty) {
      return candidates[Random().nextInt(candidates.length)];
    }

    // Попытка создать новый водоворот
    double newY = currentWhirlpool.y - minDistance - Random().nextDouble() * 500;
    Random rng = Random();

    for (int attempts = 0; attempts < GameConfig.whirlpoolPlacementAttempts; attempts++) {
      double newX = rng.nextDouble() * (GameConfig.screenWidth - GameConfig.whirlpoolEdgeMargin * 2) +
                    GameConfig.whirlpoolEdgeMargin;

      if (canPlaceWhirlpool(newX, newY, islands, shores, allWhirlpools)) {
        return Whirlpool(newX, newY);
      }

      newY -= 100;
    }

    // Если не получилось, создаём без проверки
    double newX = rng.nextDouble() * (GameConfig.screenWidth - GameConfig.whirlpoolEdgeMargin * 2) +
                  GameConfig.whirlpoolEdgeMargin;
    return Whirlpool(newX, newY);
  }

  ui.Offset? teleportPlayer(Whirlpool? target) {
    if (target == null) return null;

    double newX = target.x;
    double newY = target.y + GameConfig.whirlpoolPlayerOffset;

    usedRecently = true;
    cooldownTimer = GameConfig.whirlpoolCooldown;

    target.usedRecently = true;
    target.cooldownTimer = GameConfig.whirlpoolCooldown;

    return ui.Offset(newX, newY);
  }
}

class WhirlpoolManager {
  late List<Whirlpool> whirlpools;
  late int maxWhirlpools;

  WhirlpoolManager({int maxWhirlpools = GameConfig.whirlpoolMaxCount}) {
    this.maxWhirlpools = maxWhirlpools;
    whirlpools = [];
  }

  void update(List<Whirlpool> allWhirlpools) {
    for (var whirlpool in whirlpools) {
      whirlpool.update();
    }
  }

  ui.Offset? checkTeleport(double playerX, double playerY, double worldTop,
                       List<Island> islands, List<Shore> shores) {
    for (var whirlpool in whirlpools) {
      if (whirlpool.collidesWith(playerX, playerY, 25)) {
        Whirlpool? target = Whirlpool.findTeleportTarget(
          whirlpool,
          whirlpools,
          worldTop,
          islands,
          shores,
        );

        if (target != null && !whirlpools.contains(target)) {
          whirlpools.add(target);
        }

        return whirlpool.teleportPlayer(target);
      }
    }
    return null;
  }

  bool addWhirlpool(double x, double y, List<Island> islands, List<Shore> shores) {
    if (whirlpools.length >= maxWhirlpools) return false;

    if (!Whirlpool.canPlaceWhirlpool(x, y, islands, shores, whirlpools)) {
      return false;
    }

    whirlpools.add(Whirlpool(x, y));
    return true;
  }

  void cleanup(double cleanupThreshold) {
    whirlpools.removeWhere((w) => w.y > cleanupThreshold);
  }
}

