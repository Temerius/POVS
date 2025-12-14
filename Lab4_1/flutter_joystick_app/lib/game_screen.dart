import 'package:flutter/material.dart';
import 'dart:async';
import 'joystick_data.dart';

class GameScreen extends StatefulWidget {
  final JoystickData joystickData;
  final ValueNotifier<JoystickData>? joystickNotifier;

  const GameScreen({super.key, required this.joystickData, this.joystickNotifier});

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  late JoystickData _joystickData;
  double _playerX = 0.5;
  double _playerY = 0.5;
  double _playerSpeed = 0.005;
  Timer? _gameTimer;

  @override
  void initState() {
    super.initState();
    _joystickData = widget.joystickData;
    _startGameLoop();
    
    // Слушаем обновления джойстика, если есть notifier
    widget.joystickNotifier?.addListener(_onJoystickUpdate);
  }

  void _onJoystickUpdate() {
    if (widget.joystickNotifier != null) {
      setState(() {
        _joystickData = widget.joystickNotifier!.value;
      });
    }
  }

  @override
  void dispose() {
    widget.joystickNotifier?.removeListener(_onJoystickUpdate);
    _gameTimer?.cancel();
    super.dispose();
  }

  void _startGameLoop() {
    _gameTimer = Timer.periodic(const Duration(milliseconds: 16), (timer) {
      if (mounted) {
        setState(() {
          _updatePlayerPosition();
        });
      }
    });
  }

  void _updatePlayerPosition() {
    // Обновляем позицию игрока на основе данных джойстика
    double deltaX = _joystickData.x / 100.0 * _playerSpeed * 100;
    double deltaY = -_joystickData.y / 100.0 * _playerSpeed * 100; // Инвертируем Y

    _playerX += deltaX;
    _playerY += deltaY;

    // Ограничиваем границами экрана
    _playerX = _playerX.clamp(0.1, 0.9);
    _playerY = _playerY.clamp(0.1, 0.9);
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Игра - Управление джойстиком'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Stack(
        children: [
          // Фон игры
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Colors.blue[200]!, Colors.blue[400]!],
              ),
            ),
          ),

          // Сетка
          CustomPaint(
            size: Size.infinite,
            painter: GridPainter(),
          ),

          // Игрок
          Positioned(
            left: MediaQuery.of(context).size.width * _playerX - 25,
            top: MediaQuery.of(context).size.height * _playerY - 25,
            child: Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                color: Colors.red,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.3),
                    blurRadius: 10,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: const Icon(Icons.gamepad, color: Colors.white),
            ),
          ),

          // Информация о джойстике
          Positioned(
            top: 16,
            left: 16,
            right: 16,
            child: Card(
              color: Colors.black.withOpacity(0.7),
              child: Padding(
                padding: const EdgeInsets.all(8.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'X: ${_joystickData.x}% | Y: ${_joystickData.y}%',
                      style: const TextStyle(color: Colors.white, fontSize: 12),
                    ),
                    if (_joystickData.up || _joystickData.down || _joystickData.left || _joystickData.right)
                      Text(
                        'Кнопки: ${_joystickData.up ? "UP " : ""}${_joystickData.down ? "DOWN " : ""}${_joystickData.left ? "LEFT " : ""}${_joystickData.right ? "RIGHT " : ""}',
                        style: const TextStyle(color: Colors.yellow, fontSize: 12),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    Paint paint = Paint()
      ..color = Colors.white.withOpacity(0.1)
      ..strokeWidth = 1;

    const double spacing = 50;

    // Вертикальные линии
    for (double x = 0; x < size.width; x += spacing) {
      canvas.drawLine(
        Offset(x, 0),
        Offset(x, size.height),
        paint,
      );
    }

    // Горизонтальные линии
    for (double y = 0; y < size.height; y += spacing) {
      canvas.drawLine(
        Offset(0, y),
        Offset(size.width, y),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}

