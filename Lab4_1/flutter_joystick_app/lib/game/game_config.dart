// Конфигурация игры - все константы из Python версии

class GameConfig {
  // Размеры экрана
  static const double screenWidth = 1200.0;
  static const double screenHeight = 800.0;
  static const int fps = 60;
  
  // Цвета
  static const int waterBlue = 0xFF1469B4;  // (20, 105, 180)
  static const int islandGreen = 0xFF228B22;  // (34, 139, 34)
  static const int darkGreen = 0xFF196419;  // (25, 100, 25)
  static const int brown = 0xFF8B4513;  // (139, 69, 19)
  static const int white = 0xFFFFFFFF;
  static const int black = 0xFF000000;
  static const int red = 0xFFDC1414;  // (220, 20, 20)
  static const int gold = 0xFFFFD700;  // (255, 215, 0)
  static const int cyan = 0xFF00FFFF;  // (0, 255, 255)
  
  // Игрок
  static const double playerSize = 50.0;
  static const double playerBaseSpeed = 3.0;
  static const double playerMaxHealth = 100.0;
  static const double playerMaxAngle = 45.0;
  static const double playerRotationSpeed = 1.0;
  static const double playerAutoReturnSpeed = 1.5;
  static const double playerSideSpeedMultiplier = 3.0;
  static const int playerShootCooldown = 30;  // frames
  static const double playerShootAngleOffset = 20.0;  // градусы
  static const double playerMinAngleForSideShot = 5.0;  // градусы
  static const double playerCollisionDamage = 2.0;
  static const double playerCollisionPushback = 15.0;
  static const double playerEdgeMargin = 100.0;
  
  // Снаряды
  static const double projectileSpeed = 4.0;
  static const int projectileLifetime = 270;  // frames
  static const double projectileRadius = 5.0;
  static const int projectileColorPlayer = 0xFFFFFF00;  // желтый
  static const int projectileColorEnemy = 0xFFFF3232;  // красный
  static const double projectileDamageToPlayer = 20.0;
  
  // Острова
  static const double islandMinRadius = 50.0;
  static const double islandMaxRadius = 120.0;
  static const int islandShapePoints = 20;
  static const double islandShapeNoiseMin = 0.85;
  static const double islandShapeNoiseMax = 1.15;
  static const double islandCollisionMultiplier = 0.8;
  static const int islandStructuresMin = 0;
  static const int islandStructuresMax = 2;
  static const int islandDecorationsMin = 3;
  static const int islandDecorationsMax = 8;
  
  // Берега
  static const double shoreWidth = 150.0;
  static const double shoreIndentMin = 40.0;
  static const double shoreIndentMax = 100.0;
  static const double shoreSegmentHeightMin = 80.0;
  static const double shoreSegmentHeightMax = 150.0;
  static const double shoreEdgeMargin = 200.0;
  
  // Враги - простые
  static const double enemySimpleSize = 40.0;
  static const double enemySimpleBaseSpeed = 2.2;
  static const double enemySimpleHealth = 1.0;
  static const int enemySimpleShootDelay = 150;  // frames
  static const int enemySimplePoints = 100;
  static const double enemySimpleDetectionRange = 250.0;
  static const double enemySimpleAvoidanceForce = 0.15;
  static const double enemySimpleTurnSmoothness = 0.05;
  static const double enemySimpleAttackChance = 0.8;  // 80% агрессивных
  static const double enemySimpleProjectileSpeed = 3.5;
  static const double enemySimpleTorpedoDamage = 30.0;
  static const double enemySimpleSpawnChance = 0.25;
  static const double enemySimpleCanSeeRangeX = 400.0;
  static const double enemySimpleCanSeeRangeY = 300.0;
  
  // Враги - сложные
  static const double enemyHardSize = 60.0;
  static const double enemyHardBaseSpeed = 1.6;
  static const double enemyHardHealth = 3.0;
  static const int enemyHardShootDelay = 240;  // frames
  static const int enemyHardPoints = 300;
  static const double enemyHardDetectionRange = 300.0;
  static const double enemyHardAvoidanceForce = 0.2;
  static const double enemyHardTurnSmoothness = 0.03;
  static const double enemyHardAggressiveChance = 0.7;  // 70% агрессивных
  static const int enemyHardPursuitTimer = 120;  // frames памяти о игроке
  static const int enemyHardProjectilesCount = 3;
  static const double enemyHardProjectileSpeed = 2.8;
  static const double enemyHardProjectileSpread = 0.15;  // радианы
  static const double enemyHardTorpedoDamage = 1000.0;
  static const double enemyHardSpawnChance = 0.10;
  static const double enemyHardCanSeeRangeX = 500.0;
  static const double enemyHardCanSeeRangeY = 400.0;
  static const int enemyHardArmorFlashDuration = 20;  // frames
  static const double enemyHardMinPatrolDistance = 300.0;
  static const int enemyHardPatrolPointsMin = 2;
  static const int enemyHardPatrolPointsMax = 2;
  
  // Водовороты
  static const double whirlpoolRadius = 45.0;
  static const double whirlpoolRotationSpeed = 8.0;
  static const double whirlpoolAnimationSpeed = 0.1;
  static const double whirlpoolPulseAmount = 5.0;
  static const int whirlpoolCooldown = 180;  // frames
  static const double whirlpoolMinDistance = 300.0;
  static const double whirlpoolTeleportDistance = 1200.0;
  static const double whirlpoolSpawnChance = 0.1;
  static const int whirlpoolMaxCount = 6;
  static const int whirlpoolPlacementAttempts = 20;
  static const double whirlpoolPlayerOffset = -150.0;
  static const double whirlpoolEdgeMargin = 300.0;
  static const double whirlpoolIslandSafeDistance = 50.0;
  
  // Генерация мира
  static const double worldSegmentHeight = 2000.0;
  static const double worldGenerationAhead = 1500.0;
  static const double worldIslandSpawnChance = 0.85;
  static const double worldIslandMinSpacing = 120.0;
  static const int worldIslandRecentCheck = 30;
  static const double worldIslandStepMin = 60.0;
  static const double worldIslandStepMax = 120.0;
  static const double worldEnemySpawnDistance = -1500.0;
  static const double worldEnemyStepMin = 100.0;
  static const double worldEnemyStepMax = 200.0;
  static const double worldCleanupDistance = 2000.0;
  static const int worldInitialSegments = 3;
  
  // Камера
  static const double cameraOffset = 200.0;
  
  // UI
  static const double uiHealthBarWidth = 250.0;
  static const double uiHealthBarHeight = 30.0;
  static const double uiPadding = 20.0;
  static const double uiFontSize = 36.0;
  static const double uiSmallFontSize = 24.0;
  static const double uiBigFontSize = 48.0;
  static const double uiControlsWidth = 440.0;
  static const double uiControlsHeight = 150.0;
  static const int uiGameOverWait = 4000;  // milliseconds
  
  // Анимация
  static const double waveSpeed = 2.0;
  static const double waveHeight = 40.0;
  static const int teleportEffectDuration = 30;  // frames
  
  // Активация и очистка
  static const double enemyActivationDistance = -2.0;  // экранов от игрока
  static const double enemyDeleteDistance = 3000.0;
  static const double whirlpoolDeleteDistance = 2000.0;
  
  // Физика
  static const double collisionRadiusPlayer = playerSize / 2;
  static const double collisionRadiusEnemySimple = enemySimpleSize / 2;
  static const double collisionRadiusEnemyHard = enemyHardSize / 2;
  static const double spawnClearanceRadius = 50.0;
  static const double enemyClearanceExtra = 50.0;
  
  // Конверсия
  static const double pixelsPerMile = 10.0;
}

