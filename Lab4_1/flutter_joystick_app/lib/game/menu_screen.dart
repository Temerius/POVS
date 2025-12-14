import 'package:flutter/material.dart';
import 'dart:ui' as ui;
import '../joystick_data.dart';
import 'game_config.dart';

enum MenuType { main, pause, gameOver }

class MenuScreen extends StatefulWidget {
  final MenuType menuType;
  final ValueNotifier<JoystickData> joystickNotifier;
  final int? finalScore;
  final int? finalMiles;
  final VoidCallback? onStartGame;
  final VoidCallback? onResumeGame;
  final VoidCallback? onRestartGame;
  final VoidCallback? onExitGame;

  const MenuScreen({
    super.key,
    required this.menuType,
    required this.joystickNotifier,
    this.finalScore,
    this.finalMiles,
    this.onStartGame,
    this.onResumeGame,
    this.onRestartGame,
    this.onExitGame,
  });

  @override
  State<MenuScreen> createState() => _MenuScreenState();
}

class _MenuScreenState extends State<MenuScreen> {
  int selectedIndex = 0;
  bool buttonPressed = false;

  @override
  void initState() {
    super.initState();
    widget.joystickNotifier.addListener(_handleJoystickInput);
  }

  @override
  void dispose() {
    widget.joystickNotifier.removeListener(_handleJoystickInput);
    super.dispose();
  }

  void _handleJoystickInput() {
    if (!mounted) return;
    
    JoystickData data = widget.joystickNotifier.value;
    
    // Навигация влево/вправо
    if (data.left && !buttonPressed) {
      setState(() {
        selectedIndex = (selectedIndex - 1).clamp(0, _getMenuItems().length - 1);
        buttonPressed = true;
      });
    } else if (data.right && !buttonPressed) {
      setState(() {
        selectedIndex = (selectedIndex + 1).clamp(0, _getMenuItems().length - 1);
        buttonPressed = true;
      });
    } else if (!data.left && !data.right) {
      buttonPressed = false;
    }
    
    // Выбор кнопкой (UP или E)
    if (data.up || data.e) {
      _selectMenuItem(selectedIndex);
    }
  }

  List<String> _getMenuItems() {
    switch (widget.menuType) {
      case MenuType.main:
        return ['Начать игру', 'Выйти'];
      case MenuType.pause:
        return ['Продолжить', 'Начать заново', 'Выйти'];
      case MenuType.gameOver:
        return ['Начать заново', 'Выйти'];
    }
  }

  void _selectMenuItem(int index) {
    List<String> items = _getMenuItems();
    String item = items[index];
    
    switch (widget.menuType) {
      case MenuType.main:
        if (item == 'Начать игру' && widget.onStartGame != null) {
          widget.onStartGame!();
        } else if (item == 'Выйти' && widget.onExitGame != null) {
          widget.onExitGame!();
        }
        break;
      case MenuType.pause:
        if (item == 'Продолжить' && widget.onResumeGame != null) {
          widget.onResumeGame!();
        } else if (item == 'Начать заново' && widget.onRestartGame != null) {
          widget.onRestartGame!();
        } else if (item == 'Выйти' && widget.onExitGame != null) {
          widget.onExitGame!();
        }
        break;
      case MenuType.gameOver:
        if (item == 'Начать заново' && widget.onRestartGame != null) {
          widget.onRestartGame!();
        } else if (item == 'Выйти' && widget.onExitGame != null) {
          widget.onExitGame!();
        }
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;
    final screenWidth = screenSize.width;
    final screenHeight = screenSize.height;
    final uiScale = (screenWidth / 1200.0).clamp(0.5, 2.0);

    List<String> menuItems = _getMenuItems();

    return Container(
      width: screenWidth,
      height: screenHeight,
      color: Colors.black.withOpacity(0.85),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Заголовок
            Text(
              _getTitle(),
              style: TextStyle(
                color: Color(GameConfig.cyan),
                fontSize: 64 * uiScale,
                fontWeight: FontWeight.bold,
                shadows: [
                  Shadow(color: Colors.black, blurRadius: 8),
                ],
              ),
            ),
            SizedBox(height: 40 * uiScale),
            
            // Итоговый счёт (только для gameOver)
            if (widget.menuType == MenuType.gameOver) ...[
              if (widget.finalScore != null && widget.finalMiles != null)
                Text(
                  'Счёт: ${widget.finalScore} | Мили: ${widget.finalMiles}',
                  style: TextStyle(
                    color: Color(GameConfig.gold),
                    fontSize: 20 * uiScale,
                    shadows: [
                      Shadow(color: Colors.black, blurRadius: 4),
                    ],
                  ),
                ),
              SizedBox(height: 40 * uiScale),
            ],
            
            // Пункты меню
            ...menuItems.asMap().entries.map((entry) {
              int index = entry.key;
              String item = entry.value;
              bool isSelected = index == selectedIndex;
              
              return Padding(
                padding: EdgeInsets.symmetric(vertical: 8 * uiScale),
                child: GestureDetector(
                  onTap: () => _selectMenuItem(index),
                  child: Container(
                    padding: EdgeInsets.symmetric(
                      horizontal: 40 * uiScale,
                      vertical: 16 * uiScale,
                    ),
                    decoration: BoxDecoration(
                      color: isSelected 
                          ? Color(GameConfig.cyan).withOpacity(0.3)
                          : Colors.transparent,
                      border: Border.all(
                        color: isSelected 
                            ? Color(GameConfig.cyan)
                            : Colors.transparent,
                        width: 2,
                      ),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      item,
                      style: TextStyle(
                        color: isSelected 
                            ? Color(GameConfig.cyan)
                            : Colors.white,
                        fontSize: 32 * uiScale,
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        shadows: [
                          Shadow(color: Colors.black, blurRadius: 4),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
            
            SizedBox(height: 40 * uiScale),
            
            // Подсказка
            Text(
              'Используйте LEFT/RIGHT для навигации, кнопка UP/E для выбора',
              style: TextStyle(
                color: Colors.white70,
                fontSize: 16 * uiScale,
                shadows: [
                  Shadow(color: Colors.black, blurRadius: 2),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getTitle() {
    switch (widget.menuType) {
      case MenuType.main:
        return 'МОРСКОЙ БОЙ';
      case MenuType.pause:
        return 'ПАУЗА';
      case MenuType.gameOver:
        return 'ИГРА ОКОНЧЕНА';
    }
  }
}

