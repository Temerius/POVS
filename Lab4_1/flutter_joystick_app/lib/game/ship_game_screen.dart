import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:async';
import 'dart:math';
import 'dart:ui' as ui;
import '../joystick_data.dart';
import 'game_config.dart';
import 'models/player.dart';
import 'models/enemy.dart';
import 'models/projectile.dart';
import 'models/island.dart';
import 'models/whirlpool.dart';

class ShipGameScreen extends StatefulWidget {
  final ValueNotifier<JoystickData> joystickNotifier;

  const ShipGameScreen({super.key, required this.joystickNotifier});

  @override
  State<ShipGameScreen> createState() => _ShipGameScreenState();
}

class _ShipGameScreenState extends State<ShipGameScreen> {
  // Игровые объекты
  late Player player;
  List<Island> islands = [];
  List<Shore> leftShores = [];
  List<Shore> rightShores = [];
  List<Projectile> projectiles = [];
  List<Enemy> enemies = [];
  WhirlpoolManager whirlpoolManager = WhirlpoolManager();
  
  // Игровое состояние
  double cameraY = 0;
  double worldTop = 0;
  double waveOffset = 0;
  int teleportEffectTimer = 0;
  bool gameOver = false;
  
  // Таймер игры
  Timer? gameTimer;
  
  // Загруженные изображения
  Map<String, ui.Image> playerImages = {};
  Map<String, ui.Image> enemySimpleImages = {};
  Map<String, ui.Image> enemyHardImages = {};
  bool imagesLoaded = false;

  @override
  void initState() {
    super.initState();
    // Блокируем горизонтальную ориентацию
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    _initGame();
    _loadImages();
    _startGameLoop();
  }

  void _initGame() {
    player = Player(GameConfig.screenWidth / 2, GameConfig.screenHeight - 150);
    cameraY = player.y - GameConfig.screenHeight + GameConfig.cameraOffset;
    worldTop = player.y - GameConfig.screenHeight * 2;
    
    _generateInitialWorld();
  }

  Future<void> _loadImages() async {
    try {
      // Загружаем изображения игрока
      print('Загрузка изображений игрока...');
      playerImages['up'] = await _loadImage('assets/images/player/player_up.png');
      print('player_up.png загружено: ${playerImages['up']?.width}x${playerImages['up']?.height}');
      playerImages['down'] = await _loadImage('assets/images/player/player_down.png');
      playerImages['left'] = await _loadImage('assets/images/player/player_left.png');
      playerImages['right'] = await _loadImage('assets/images/player/player_right.png');
      print('Изображения игрока загружены: ${playerImages.length}');
      
      // Загружаем изображения простых врагов
      enemySimpleImages['up'] = await _loadImage('assets/images/enemy_simple/enemy_simple_up.png');
      enemySimpleImages['down'] = await _loadImage('assets/images/enemy_simple/enemy_simple_down.png');
      enemySimpleImages['left'] = await _loadImage('assets/images/enemy_simple/enemy_simple_left.png');
      enemySimpleImages['right'] = await _loadImage('assets/images/enemy_simple/enemy_simple_right.png');
      
      // Загружаем изображения сложных врагов
      enemyHardImages['up'] = await _loadImage('assets/images/enemy_hard/enemy_hard_up.png');
      enemyHardImages['down'] = await _loadImage('assets/images/enemy_hard/enemy_hard_down.png');
      enemyHardImages['left'] = await _loadImage('assets/images/enemy_hard/enemy_hard_left.png');
      enemyHardImages['right'] = await _loadImage('assets/images/enemy_hard/enemy_hard_right.png');
      
      setState(() {
        imagesLoaded = true;
      });
      print('Все изображения загружены успешно!');
    } catch (e, stackTrace) {
      print('Ошибка загрузки изображений: $e');
      print('Stack trace: $stackTrace');
    }
  }

  Future<ui.Image> _loadImage(String path) async {
    final ByteData data = await rootBundle.load(path);
    final Uint8List bytes = data.buffer.asUint8List();
    final ui.Codec codec = await ui.instantiateImageCodec(bytes);
    final ui.FrameInfo frameInfo = await codec.getNextFrame();
    return frameInfo.image;
  }

  void _startGameLoop() {
    gameTimer = Timer.periodic(Duration(milliseconds: 1000 ~/ GameConfig.fps), (timer) {
      if (!gameOver && mounted) {
        setState(() {
          _update();
        });
      }
    });
  }

  void _update() {
    if (gameOver) return;
    
    JoystickData joystickData = widget.joystickNotifier.value;
    
    // Обновление камеры
    cameraY = player.y - GameConfig.screenHeight + GameConfig.cameraOffset;
    
    // Генерация мира
    if (player.y < worldTop + GameConfig.worldGenerationAhead) {
      _generateWorldSegment();
    }
    
    // Обновление водоворотов
    whirlpoolManager.update(whirlpoolManager.whirlpools);
    ui.Offset? teleportPos = whirlpoolManager.checkTeleport(
      player.x, player.y, worldTop, islands, leftShores + rightShores
    );
    
    if (teleportPos != null) {
      player.x = teleportPos.dx;
      player.y = teleportPos.dy;
      teleportEffectTimer = GameConfig.teleportEffectDuration;
    }
    
    // Обновление врагов
    _updateEnemies();
    
    // Обновление игрока с управлением от джойстика
    double joystickX = joystickData.x.toDouble();
    double joystickY = joystickData.y.toDouble();
    List<dynamic> allObstacles = [...islands, ...leftShores, ...rightShores];
    player.update(joystickX, joystickY, allObstacles);
    
    // Стрельба на кнопку A (UP)
    if (joystickData.up) {
      List<Projectile>? newProjectiles = player.shoot();
      if (newProjectiles != null) {
        projectiles.addAll(newProjectiles);
      }
    }
    
    // Обновление волн
    waveOffset = (waveOffset + GameConfig.waveSpeed) % GameConfig.waveHeight;
    
    // Обновление снарядов
    _updateProjectiles(allObstacles);
    
    if (teleportEffectTimer > 0) {
      teleportEffectTimer--;
    }
    
    // Очистка старых объектов
    _cleanupOldObjects();
    
    // Проверка конца игры
    if (player.health <= 0) {
      gameOver = true;
      _showGameOver();
    }
  }

  void _updateEnemies() {
    List<Projectile> newEnemyProjectiles = [];
    List<Enemy> enemiesToRemove = [];
    
    for (var enemy in enemies) {
      List<Projectile>? enemyProjectiles = enemy.update(islands, leftShores + rightShores, 
                                                       player, worldTop);
      
      if (enemyProjectiles == null) {
        enemiesToRemove.add(enemy);
        continue;
      }
      
      newEnemyProjectiles.addAll(enemyProjectiles);
      
      // Таран
      if (player.collidesWith(enemy.x, enemy.y, enemy.radius)) {
        double damage = enemy.getTorpedoDamage();
        player.takeDamage(damage);
        if (enemy is SimpleEnemy) {
          enemiesToRemove.add(enemy);
        }
      }
    }
    
    for (var enemy in enemiesToRemove) {
      enemies.remove(enemy);
    }
    
    projectiles.addAll(newEnemyProjectiles);
  }

  void _updateProjectiles(List<dynamic> allObstacles) {
    List<Projectile> projectilesToRemove = [];
    
    for (var proj in projectiles) {
      proj.update();
      
      // Столкновение с врагами
      for (var enemy in enemies) {
        if (proj.collidesWith(enemy)) {
          if (proj.isPlayerShot) {
            if (enemy.takeDamage(1)) {
              player.score += enemy.points;
              enemies.remove(enemy);
            }
            projectilesToRemove.add(proj);
            break;
          }
        }
      }
      
      // Столкновение с препятствиями
      bool obstacleHit = false;
      for (var obstacle in allObstacles) {
        if (proj.collidesWith(obstacle)) {
          obstacleHit = true;
          break;
        }
      }
      
      // Столкновение с игроком
      bool playerHit = !proj.isPlayerShot && player.collidesWith(proj.x, proj.y, proj.radius);
      if (playerHit) {
        player.takeDamage(GameConfig.projectileDamageToPlayer);
      }
      
      if (proj.lifetime <= 0 ||
          proj.x < 0 ||
          proj.x > GameConfig.screenWidth ||
          obstacleHit ||
          playerHit) {
        projectilesToRemove.add(proj);
      }
    }
    
    for (var proj in projectilesToRemove) {
      projectiles.remove(proj);
    }
  }

  void _cleanupOldObjects() {
    double cleanupThreshold = player.y + GameConfig.worldCleanupDistance;
    
    islands.removeWhere((i) => i.y > cleanupThreshold);
    leftShores.removeWhere((s) => s.startY > cleanupThreshold);
    rightShores.removeWhere((s) => s.startY > cleanupThreshold);
    whirlpoolManager.cleanup(cleanupThreshold);
  }

  void _generateInitialWorld() {
    for (int i = 0; i < GameConfig.worldInitialSegments; i++) {
      _generateWorldSegment();
    }
  }

  void _generateWorldSegment() {
    double segmentStart = worldTop - GameConfig.worldSegmentHeight;
    double segmentEnd = worldTop;
    
    leftShores.add(Shore('left', segmentStart, segmentEnd));
    rightShores.add(Shore('right', segmentStart, segmentEnd));
    
    Random rng = Random();
    double currentY = segmentStart;
    
    // Генерация островов
    while (currentY < segmentEnd) {
      if (rng.nextDouble() < GameConfig.worldIslandSpawnChance) {
        double x = rng.nextDouble() * (GameConfig.screenWidth - GameConfig.shoreWidth * 2) + 
                   GameConfig.shoreWidth;
        
        bool tooClose = false;
        int checkCount = islands.length > GameConfig.worldIslandRecentCheck 
            ? GameConfig.worldIslandRecentCheck 
            : islands.length;
        for (int i = islands.length - checkCount; i < islands.length; i++) {
          if (i < 0) continue;
          double dist = sqrt((islands[i].x - x) * (islands[i].x - x) + 
                            (islands[i].y - currentY) * (islands[i].y - currentY));
          if (dist < GameConfig.worldIslandMinSpacing) {
            tooClose = true;
            break;
          }
        }
        
        if (!tooClose) {
          islands.add(Island(x, currentY, rng.nextInt(1000000)));
        }
      }
      
      // Генерация водоворотов
      if (rng.nextDouble() < GameConfig.whirlpoolSpawnChance) {
        double x = rng.nextDouble() * (GameConfig.screenWidth - GameConfig.whirlpoolEdgeMargin * 2) +
                   GameConfig.whirlpoolEdgeMargin;
        whirlpoolManager.addWhirlpool(x, currentY, islands, leftShores + rightShores);
      }
      
      currentY += rng.nextDouble() * (GameConfig.worldIslandStepMax - GameConfig.worldIslandStepMin) +
                  GameConfig.worldIslandStepMin;
    }
    
    // Генерация врагов
    currentY = segmentStart;
    while (currentY < segmentEnd) {
      if (currentY < player.y + GameConfig.worldEnemySpawnDistance) {
        // Простые враги
        if (rng.nextDouble() < GameConfig.enemySimpleSpawnChance) {
          for (int attempt = 0; attempt < 10; attempt++) {
            double x = rng.nextDouble() * (GameConfig.screenWidth - 500) + 250;
            if (_isPositionClear(x, currentY, GameConfig.collisionRadiusEnemySimple)) {
              enemies.add(SimpleEnemy(x, currentY));
              break;
            }
          }
        }
        
        // Сложные враги
        if (rng.nextDouble() < GameConfig.enemyHardSpawnChance) {
          for (int attempt = 0; attempt < 10; attempt++) {
            double x = rng.nextDouble() * (GameConfig.screenWidth - 600) + 300;
            if (_isPositionClear(x, currentY, GameConfig.collisionRadiusEnemyHard)) {
              enemies.add(HardEnemy(x, currentY));
              break;
            }
          }
        }
      }
      
      currentY += rng.nextDouble() * (GameConfig.worldEnemyStepMax - GameConfig.worldEnemyStepMin) +
                  GameConfig.worldEnemyStepMin;
    }
    
    worldTop = segmentStart;
  }

  bool _isPositionClear(double x, double y, double radius) {
    double clearance = GameConfig.spawnClearanceRadius + GameConfig.enemyClearanceExtra;
    
    for (var island in islands) {
      double dist = sqrt((island.x - x) * (island.x - x) + (island.y - y) * (island.y - y));
      if (dist < island.radius + clearance) return false;
    }
    
    for (var shore in leftShores + rightShores) {
      if (shore.collidesWith(x, y, clearance)) return false;
    }
    
    if (x < GameConfig.shoreEdgeMargin || x > GameConfig.screenWidth - GameConfig.shoreEdgeMargin) {
      return false;
    }
    
    return true;
  }

  void _showGameOver() {
    gameTimer?.cancel();
    Future.delayed(Duration(milliseconds: GameConfig.uiGameOverWait), () {
      if (mounted) {
        Navigator.of(context).pop();
      }
    });
  }

  @override
  void dispose() {
    gameTimer?.cancel();
    // Разблокируем ориентацию при выходе
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.portraitDown,
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: LayoutBuilder(
        builder: (context, constraints) {
          return Stack(
            children: [
              // Игровое поле с масштабированием - заполняет весь экран пропорционально
              Positioned.fill(
                child: FittedBox(
                  fit: BoxFit.cover,
                  child: SizedBox(
                    width: GameConfig.screenWidth,
                    height: GameConfig.screenHeight,
                    child: CustomPaint(
                      painter: GamePainter(
                        player: player,
                        islands: islands,
                        leftShores: leftShores,
                        rightShores: rightShores,
                        projectiles: projectiles,
                        enemies: enemies,
                        whirlpoolManager: whirlpoolManager,
                        cameraY: cameraY,
                        waveOffset: waveOffset,
                        teleportEffectTimer: teleportEffectTimer,
                        gameOver: gameOver,
                        playerImages: playerImages,
                        enemySimpleImages: enemySimpleImages,
                        enemyHardImages: enemyHardImages,
                        imagesLoaded: imagesLoaded,
                      ),
                      size: Size(GameConfig.screenWidth, GameConfig.screenHeight),
                    ),
                  ),
                ),
              ),
              // UI поверх игрового поля (без масштабирования)
              _buildUI(1.0),
            ],
          );
        },
      ),
    );
  }

  Widget _buildUI(double scale) {
    double healthRatio = (player.health / player.maxHealth).clamp(0.0, 1.0);
    int miles = player.y > 0 ? 0 : (player.y.abs() / GameConfig.pixelsPerMile).toInt();
    
    // Получаем размер экрана для адаптивного UI
    final screenSize = MediaQuery.of(context).size;
    final screenWidth = screenSize.width;
    final screenHeight = screenSize.height;
    
    // Масштаб для UI (чтобы UI был читаемым на любом экране)
    final uiScale = (screenWidth / 1200.0).clamp(0.5, 2.0);
    
    return Stack(
      children: [
        // HP
        Positioned(
          top: GameConfig.uiPadding * uiScale,
          left: GameConfig.uiPadding * uiScale,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'HP: ${player.health.toInt()}/${player.maxHealth.toInt()}',
                style: TextStyle(
                  color: Colors.white, 
                  fontSize: GameConfig.uiFontSize * uiScale,
                  shadows: [
                    Shadow(color: Colors.black, blurRadius: 4),
                  ],
                ),
              ),
              SizedBox(height: 10 * uiScale),
              Container(
                width: GameConfig.uiHealthBarWidth * uiScale,
                height: GameConfig.uiHealthBarHeight * uiScale,
                decoration: BoxDecoration(
                  color: Colors.red.shade700,
                  border: Border.all(color: Colors.white, width: 3 * uiScale),
                ),
                child: FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: healthRatio,
                  child: Container(color: Colors.green),
                ),
              ),
            ],
          ),
        ),
        
        // Счёт и мили
        Positioned(
          top: GameConfig.uiPadding * uiScale,
          right: 250 * uiScale,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Счёт: ${player.score}',
                style: TextStyle(
                  color: Color(GameConfig.gold), 
                  fontSize: GameConfig.uiFontSize * uiScale,
                  shadows: [
                    Shadow(color: Colors.black, blurRadius: 4),
                  ],
                ),
              ),
              SizedBox(height: 10 * uiScale),
              Text(
                'Мили: $miles',
                style: TextStyle(
                  color: Colors.white, 
                  fontSize: GameConfig.uiFontSize * uiScale,
                  shadows: [
                    Shadow(color: Colors.black, blurRadius: 4),
                  ],
                ),
              ),
            ],
          ),
        ),
        
        // Угол
        Positioned(
          top: GameConfig.uiPadding * uiScale,
          left: screenWidth / 2 - 100 * uiScale,
          child: Text(
            'Угол: ${player.hullAngle.toInt()}°',
            style: TextStyle(
              color: Color(GameConfig.cyan), 
              fontSize: GameConfig.uiBigFontSize * uiScale,
              shadows: [
                Shadow(color: Colors.black, blurRadius: 4),
              ],
            ),
          ),
        ),
        
        // Game Over overlay
        if (gameOver)
          Container(
            width: screenWidth,
            height: screenHeight,
            color: Colors.black.withOpacity(0.8),
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'ИГРА ОКОНЧЕНА',
                    style: TextStyle(
                      color: Color(GameConfig.red), 
                      fontSize: 84 * uiScale,
                      shadows: [
                        Shadow(color: Colors.black, blurRadius: 8),
                      ],
                    ),
                  ),
                  SizedBox(height: 40 * uiScale),
                  Text(
                    'Финальный счёт: ${player.score}',
                    style: TextStyle(
                      color: Color(GameConfig.gold), 
                      fontSize: GameConfig.uiBigFontSize * uiScale,
                      shadows: [
                        Shadow(color: Colors.black, blurRadius: 4),
                      ],
                    ),
                  ),
                  SizedBox(height: 20 * uiScale),
                  Text(
                    'Пройдено: $miles морских миль',
                    style: TextStyle(
                      color: Colors.white, 
                      fontSize: GameConfig.uiFontSize * uiScale,
                      shadows: [
                        Shadow(color: Colors.black, blurRadius: 4),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

// Кастомный Painter для отрисовки игры
class GamePainter extends CustomPainter {
  final Player player;
  final List<Island> islands;
  final List<Shore> leftShores;
  final List<Shore> rightShores;
  final List<Projectile> projectiles;
  final List<Enemy> enemies;
  final WhirlpoolManager whirlpoolManager;
  final double cameraY;
  final double waveOffset;
  final int teleportEffectTimer;
  final bool gameOver;
  final Map<String, ui.Image> playerImages;
  final Map<String, ui.Image> enemySimpleImages;
  final Map<String, ui.Image> enemyHardImages;
  final bool imagesLoaded;

  GamePainter({
    required this.player,
    required this.islands,
    required this.leftShores,
    required this.rightShores,
    required this.projectiles,
    required this.enemies,
    required this.whirlpoolManager,
    required this.cameraY,
    required this.waveOffset,
    required this.teleportEffectTimer,
    required this.gameOver,
    required this.playerImages,
    required this.enemySimpleImages,
    required this.enemyHardImages,
    required this.imagesLoaded,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Фон воды
    canvas.drawRect(
      Rect.fromLTWH(0, 0, size.width, size.height),
      Paint()..color = Color(GameConfig.waterBlue),
    );
    
    // Волны
    _drawWaves(canvas, size);
    
    // Берега
    for (var shore in leftShores) {
      _drawShore(canvas, shore);
    }
    for (var shore in rightShores) {
      _drawShore(canvas, shore);
    }
    
    // Водовороты
    for (var whirlpool in whirlpoolManager.whirlpools) {
      _drawWhirlpool(canvas, whirlpool);
    }
    
    // Острова
    for (var island in islands) {
      _drawIsland(canvas, island);
    }
    
    // Враги
    for (var enemy in enemies) {
      _drawEnemy(canvas, enemy);
    }
    
    // Снаряды
    for (var proj in projectiles) {
      _drawProjectile(canvas, proj);
    }
    
    // Игрок
    _drawPlayer(canvas);
    
    // Эффект телепортации
    if (teleportEffectTimer > 0) {
      double alpha = (teleportEffectTimer / GameConfig.teleportEffectDuration) * 200;
      canvas.drawRect(
        Rect.fromLTWH(0, 0, size.width, size.height),
        Paint()..color = Colors.white.withOpacity(alpha / 255),
      );
    }
  }

  void _drawWaves(Canvas canvas, Size size) {
    const double amplitude = 12;
    const double waveLength = 80;
    const double waveSpeed = 0.03;
    const double verticalSpacing = 35;
    
    double baseOffset = ((cameraY / 3) % verticalSpacing + (waveOffset % verticalSpacing));
    
    for (int layer = -2; layer < size.height / verticalSpacing + 3; layer++) {
      double baseY = layer * verticalSpacing + baseOffset;
      
      int depthFactor = (layer % 3) * 5;
      Color color = Color.fromRGBO(
        10 + depthFactor,
        95 + depthFactor,
        170 + (depthFactor < 10 ? depthFactor : 10),
        1.0,
      );
      
      double phaseShift = layer * 0.8;
      List<ui.Offset> points = [];
      
      for (double x = 0; x <= size.width + waveLength; x += 5) {
        double y = baseY + amplitude * sin(
          (2 * pi * x / waveLength) + (waveOffset * waveSpeed) + phaseShift
        );
        y += amplitude * 0.3 * sin(
          (4 * pi * x / waveLength) + (waveOffset * waveSpeed * 1.5) + phaseShift * 1.2
        );
        points.add(ui.Offset(x, y));
      }
      
      if (points.length > 1) {
        canvas.drawPoints(
          ui.PointMode.polygon,
          points,
          Paint()
            ..color = color
            ..strokeWidth = 2
            ..style = PaintingStyle.stroke,
        );
      }
    }
  }

  void _drawShore(Canvas canvas, Shore shore) {
    List<ui.Offset> adjustedPoints = shore.points.map((p) => 
      ui.Offset(p.dx, p.dy - cameraY)
    ).toList();
    
    if (adjustedPoints.isEmpty) return;
    
    List<ui.Offset> polygonPoints = [];
    if (shore.side == 'left') {
      polygonPoints = [ui.Offset(0, -200)] + adjustedPoints + [ui.Offset(0, GameConfig.screenHeight + 200)];
    } else {
      polygonPoints = [ui.Offset(GameConfig.screenWidth, -200)] + adjustedPoints + 
                     [ui.Offset(GameConfig.screenWidth, GameConfig.screenHeight + 200)];
    }
    
    canvas.drawPath(
      Path()..addPolygon(polygonPoints, true),
      Paint()..color = Color(GameConfig.islandGreen),
    );
    
    canvas.drawPoints(
      ui.PointMode.polygon,
      adjustedPoints,
      Paint()
        ..color = Color(GameConfig.darkGreen)
        ..strokeWidth = 4
        ..style = PaintingStyle.stroke,
    );
  }

  void _drawIsland(Canvas canvas, Island island) {
    List<ui.Offset> adjustedPoints = island.points.map((p) => 
      ui.Offset(p.dx, p.dy - cameraY)
    ).toList();
    
    if (adjustedPoints.isEmpty) return;
    
    canvas.drawPath(
      Path()..addPolygon(adjustedPoints, true),
      Paint()..color = island.color,
    );
    
    canvas.drawPath(
      Path()..addPolygon(adjustedPoints, true),
      Paint()
        ..color = Color(GameConfig.darkGreen)
        ..strokeWidth = 3
        ..style = PaintingStyle.stroke,
    );
    
    // Структуры и декорации (упрощённо - можно доработать)
    for (var structure in island.structures) {
      double x = structure['x'];
      double y = structure['y'] - cameraY;
      double structSize = structure['size'];
      
      if (y < -100 || y > GameConfig.screenHeight + 100) continue;
      
      // Простая отрисовка структур (можно улучшить)
      canvas.drawCircle(
        ui.Offset(x, y),
        8 * structSize,
        Paint()..color = Color(GameConfig.brown),
      );
    }
  }

  void _drawWhirlpool(Canvas canvas, Whirlpool whirlpool) {
    double yScreen = whirlpool.y - cameraY;
    
    if (yScreen < -150 || yScreen > GameConfig.screenHeight + 150) return;
    
    double pulse = sin(whirlpool.animationPhase) * GameConfig.whirlpoolPulseAmount;
    double currentRadius = whirlpool.radius + pulse;
    
    // Рисуем спиральный водоворот
    for (int i = 0; i < 4; i++) {
      double r = currentRadius - i * 10;
      double angleOffset = whirlpool.rotation + i * 30;
      int colorVal = (60 + i * 40).clamp(0, 255);
      
      for (int j = 0; j < 8; j++) {
        double angle = (j * 45 + angleOffset) * pi / 180;
        ui.Offset p1 = ui.Offset(
          whirlpool.x + cos(angle) * r,
          yScreen + sin(angle) * r,
        );
        ui.Offset p2 = ui.Offset(
          whirlpool.x + cos(angle) * (r - 8),
          yScreen + sin(angle) * (r - 8),
        );
        
        canvas.drawLine(
          p1,
          p2,
          Paint()
            ..color = Color.fromRGBO(colorVal, colorVal, 255, 1.0)
            ..strokeWidth = 3,
        );
      }
    }
    
    // Центр водоворота
    Color centerColor = whirlpool.usedRecently 
        ? Colors.grey 
        : Color.fromRGBO(30, 30, 150, 1.0);
    canvas.drawCircle(
      ui.Offset(whirlpool.x, yScreen),
      12,
      Paint()..color = centerColor,
    );
  }

  void _drawEnemy(Canvas canvas, Enemy enemy) {
    double xScreen = enemy.x;
    double yScreen = enemy.y - cameraY;
    
    if (yScreen < -1000 || yScreen > GameConfig.screenHeight + 1000) return;
    
    Map<String, ui.Image>? images;
    if (enemy is SimpleEnemy) {
      images = enemySimpleImages;
    } else if (enemy is HardEnemy) {
      images = enemyHardImages;
      // Эффект мигания при уроне
      if (enemy.armorTimer > 0 && enemy.armorTimer % 4 < 2) {
        canvas.drawCircle(
          Offset(xScreen, yScreen),
          enemy.size / 2,
          Paint()..color = Colors.red.withOpacity(0.5),
        );
      }
    }
    
    if (images != null && imagesLoaded && images.containsKey(enemy.currentDirection)) {
      ui.Image? img = images[enemy.currentDirection];
      if (img != null) {
        canvas.drawImageRect(
          img,
          Rect.fromLTWH(0, 0, img.width.toDouble(), img.height.toDouble()),
          Rect.fromCenter(center: ui.Offset(xScreen, yScreen), width: enemy.size, height: enemy.size),
          Paint(),
        );
        return;
      }
    }
    
    // Fallback - простое отрисовка
    canvas.drawCircle(
      ui.Offset(xScreen, yScreen),
      enemy.size / 2,
      Paint()..color = enemy is HardEnemy ? Colors.red.shade700 : Colors.red,
    );
  }

  void _drawProjectile(Canvas canvas, Projectile proj) {
    double yScreen = proj.y - cameraY;
    canvas.drawCircle(
      ui.Offset(proj.x, yScreen),
      proj.radius,
      Paint()..color = Color(proj.color),
    );
  }

  void _drawPlayer(Canvas canvas) {
    double yScreen = player.y - cameraY;
    
    // Проверяем видимость
    if (yScreen < -100 || yScreen > GameConfig.screenHeight + 100) return;
    
    // Всегда используем 'up' спрайт для игрока (как в Python версии)
    // Поворот будет через canvas.rotate
    String direction = 'up';
    
    // Пробуем использовать изображение
    if (imagesLoaded && playerImages.containsKey(direction)) {
      ui.Image? img = playerImages[direction];
      if (img != null) {
        canvas.save();
        canvas.translate(player.x, yScreen);
        canvas.rotate(-player.hullAngle * pi / 180);
        canvas.drawImageRect(
          img,
          Rect.fromLTWH(0, 0, img.width.toDouble(), img.height.toDouble()),
          Rect.fromCenter(center: ui.Offset.zero, width: player.size, height: player.size),
          Paint(),
        );
        canvas.restore();
        return;
      }
    }
    
    // Fallback - простая отрисовка (для отладки)
    canvas.save();
    canvas.translate(player.x, yScreen);
    canvas.rotate(-player.hullAngle * pi / 180);
    Path shipPath = Path();
    shipPath.moveTo(0, -player.size / 2);
    shipPath.lineTo(player.size / 2, player.size / 2);
    shipPath.lineTo(0, player.size * 0.7);
    shipPath.lineTo(-player.size / 2, player.size / 2);
    shipPath.close();
    canvas.drawPath(
      shipPath,
      Paint()..color = Colors.blue,
    );
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

