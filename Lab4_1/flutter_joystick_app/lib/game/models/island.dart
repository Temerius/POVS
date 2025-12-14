import 'dart:math';
import 'dart:ui' as ui;
import '../game_config.dart';

class Island {
  double x;
  double y;
  late double radius;
  int seed;
  late List<ui.Offset> points;
  late List<Map<String, dynamic>> structures;
  late List<Map<String, dynamic>> decorations;
  late ui.Color color;

  Island(this.x, this.y, this.seed) {
    Random rng = Random(seed);
    radius = (rng.nextDouble() * (GameConfig.islandMaxRadius - GameConfig.islandMinRadius) + 
              GameConfig.islandMinRadius);
    
    color = ui.Color.fromRGBO(
      (20 + rng.nextInt(61)).clamp(20, 80),
      (80 + rng.nextInt(81)).clamp(80, 160),
      (10 + rng.nextInt(51)).clamp(10, 60),
      1.0,
    );
    
    points = _generateShape(rng);
    structures = _generateStructures(rng);
    decorations = _generateDecorations(rng);
  }

  List<ui.Offset> _generateShape(Random rng) {
    List<ui.Offset> shapePoints = [];
    for (int i = 0; i < GameConfig.islandShapePoints; i++) {
      double angle = (i / GameConfig.islandShapePoints) * 2 * pi;
      double noise = rng.nextDouble() * 
          (GameConfig.islandShapeNoiseMax - GameConfig.islandShapeNoiseMin) + 
          GameConfig.islandShapeNoiseMin;
      double r = radius * noise;
      shapePoints.add(ui.Offset(
        x + cos(angle) * r,
        y + sin(angle) * r,
      ));
    }
    return shapePoints;
  }

  List<Map<String, dynamic>> _generateStructures(Random rng) {
    List<Map<String, dynamic>> structs = [];
    int numStructures = rng.nextInt(GameConfig.islandStructuresMax - 
                                   GameConfig.islandStructuresMin + 1) + 
                       GameConfig.islandStructuresMin;
    
    // Веса для типов структур (как в Python версии)
    List<String> structureTypes = ['lighthouse', 'hut', 'palm', 'rock', 'shipwreck', 'chest'];
    List<double> weights = [0.1, 0.2, 0.3, 0.2, 0.1, 0.1];
    
    for (int i = 0; i < numStructures; i++) {
      double angle = rng.nextDouble() * 2 * pi;
      double distance = rng.nextDouble() * 0.4 + 0.3;
      
      // Выбор типа структуры с учетом весов
      double randomValue = rng.nextDouble();
      double cumulativeWeight = 0.0;
      String selectedType = structureTypes[0];
      for (int j = 0; j < structureTypes.length; j++) {
        cumulativeWeight += weights[j];
        if (randomValue <= cumulativeWeight) {
          selectedType = structureTypes[j];
          break;
        }
      }
      
      structs.add({
        'type': selectedType,
        'x': x + cos(angle) * distance * radius,
        'y': y + sin(angle) * distance * radius,
        'size': rng.nextDouble() * 0.4 + 0.8,
        'angle': rng.nextDouble() * 360,
      });
    }
    return structs;
  }

  List<Map<String, dynamic>> _generateDecorations(Random rng) {
    List<Map<String, dynamic>> decors = [];
    int numDecorations = rng.nextInt(GameConfig.islandDecorationsMax - 
                                    GameConfig.islandDecorationsMin + 1) + 
                        GameConfig.islandDecorationsMin;
    
    // Веса для типов декораций (как в Python версии)
    List<String> decorTypes = ['bush', 'flower', 'stone', 'coconut'];
    List<double> weights = [0.3, 0.3, 0.2, 0.2];
    
    for (int i = 0; i < numDecorations; i++) {
      double angle = rng.nextDouble() * 2 * pi;
      double distance = rng.nextDouble() * 0.6 + 0.2;
      
      // Выбор типа декорации с учетом весов
      double randomValue = rng.nextDouble();
      double cumulativeWeight = 0.0;
      String selectedType = decorTypes[0];
      for (int j = 0; j < decorTypes.length; j++) {
        cumulativeWeight += weights[j];
        if (randomValue <= cumulativeWeight) {
          selectedType = decorTypes[j];
          break;
        }
      }
      
      decors.add({
        'type': selectedType,
        'x': x + cos(angle) * distance * radius,
        'y': y + sin(angle) * distance * radius,
        'size': rng.nextDouble() * 0.5 + 0.5,
      });
    }
    return decors;
  }

  bool collidesWith(double checkX, double checkY, double checkRadius) {
    double dx = checkX - x;
    double dy = checkY - y;
    double dist = sqrt(dx * dx + dy * dy);
    return dist < radius * GameConfig.islandCollisionMultiplier + checkRadius;
  }
}

class Shore {
  String side;  // 'left' or 'right'
  double startY;
  double endY;
  late List<ui.Offset> points;
  late double xLeft;
  late double xRight;

  Shore(this.side, this.startY, this.endY) {
    Random rng = Random();
    points = _generateShore(rng);
    
    if (side == 'left') {
      xLeft = 0;
      xRight = GameConfig.shoreWidth;
    } else {
      xLeft = GameConfig.screenWidth - GameConfig.shoreWidth;
      xRight = GameConfig.screenWidth;
    }
  }

  List<ui.Offset> _generateShore(Random rng) {
    List<ui.Offset> shorePoints = [];
    double currentY = startY;
    
    if (side == 'left') {
      shorePoints.add(ui.Offset(0, currentY));
      
      while (currentY < endY) {
        double indent = rng.nextDouble() * (GameConfig.shoreIndentMax - GameConfig.shoreIndentMin) + 
                       GameConfig.shoreIndentMin;
        double segmentHeight = rng.nextDouble() * 
            (GameConfig.shoreSegmentHeightMax - GameConfig.shoreSegmentHeightMin) + 
            GameConfig.shoreSegmentHeightMin;
        
        shorePoints.add(ui.Offset(indent, currentY));
        currentY += segmentHeight / 2;
        shorePoints.add(ui.Offset(indent + (rng.nextDouble() * 40 - 20), currentY));
        currentY += segmentHeight / 2;
      }
      
      shorePoints.add(ui.Offset(0, endY));
    } else {
      shorePoints.add(ui.Offset(GameConfig.screenWidth, currentY));
      
      while (currentY < endY) {
        double indent = rng.nextDouble() * (GameConfig.shoreIndentMax - GameConfig.shoreIndentMin) + 
                       GameConfig.shoreIndentMin;
        double segmentHeight = rng.nextDouble() * 
            (GameConfig.shoreSegmentHeightMax - GameConfig.shoreSegmentHeightMin) + 
            GameConfig.shoreSegmentHeightMin;
        
        shorePoints.add(ui.Offset(GameConfig.screenWidth - indent, currentY));
        currentY += segmentHeight / 2;
        shorePoints.add(ui.Offset(GameConfig.screenWidth - indent + (rng.nextDouble() * 40 - 20), currentY));
        currentY += segmentHeight / 2;
      }
      
      shorePoints.add(ui.Offset(GameConfig.screenWidth, endY));
    }
    
    return shorePoints;
  }

  bool collidesWith(double checkX, double checkY, double checkRadius) {
    for (int i = 0; i < points.length - 1; i++) {
      double dist = _pointToSegmentDistance(
        checkX, checkY, 
        points[i].dx, points[i].dy,
        points[i + 1].dx, points[i + 1].dy
      );
      if (dist < checkRadius + 10) {
        return true;
      }
    }
    return false;
  }

  double _pointToSegmentDistance(double px, double py, double x1, double y1, double x2, double y2) {
    double lineVecX = x2 - x1;
    double lineVecY = y2 - y1;
    double pointVecX = px - x1;
    double pointVecY = py - y1;
    
    double lineLenSq = lineVecX * lineVecX + lineVecY * lineVecY;
    
    if (lineLenSq == 0) {
      double dx = px - x1;
      double dy = py - y1;
      return sqrt(dx * dx + dy * dy);
    }
    
    double t = ((pointVecX * lineVecX + pointVecY * lineVecY) / lineLenSq).clamp(0.0, 1.0);
    
    double nearestX = x1 + t * lineVecX;
    double nearestY = y1 + t * lineVecY;
    
    double dx = px - nearestX;
    double dy = py - nearestY;
    return sqrt(dx * dx + dy * dy);
  }
}

