import 'package:flutter/material.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import 'dart:async';
import 'dart:typed_data';
import 'joystick_data.dart';
import 'game_screen.dart';

class JoystickControlScreen extends StatefulWidget {
  final BluetoothConnection connection;

  const JoystickControlScreen({super.key, required this.connection});

  @override
  State<JoystickControlScreen> createState() => _JoystickControlScreenState();
}

class _JoystickControlScreenState extends State<JoystickControlScreen> {
  JoystickData _joystickData = JoystickData();
  ValueNotifier<JoystickData> _joystickNotifier = ValueNotifier(JoystickData());
  StreamSubscription<Uint8List>? _subscription;
  String _status = 'Подключено';
  bool _isConnected = true;

  @override
  void initState() {
    super.initState();
    _startListening();
  }

  void _startListening() {
    if (widget.connection.input != null) {
      _subscription = widget.connection.input!.listen(
        (data) {
          try {
            String received = String.fromCharCodes(data);
            List<String> lines = received.split('\n');
            
            for (String line in lines) {
              if (line.contains('X=') && line.contains('Y=')) {
                setState(() {
                  _joystickData = JoystickData.fromString(line);
                  _joystickNotifier.value = _joystickData;
                  _status = 'Данные получены';
                });
              }
            }
          } catch (e) {
            print('Error parsing data: $e');
          }
        },
        onError: (error) {
          setState(() {
            _status = 'Ошибка: $error';
            _isConnected = false;
          });
        },
        onDone: () {
          setState(() {
            _isConnected = false;
            _status = 'Соединение разорвано';
          });
        },
        cancelOnError: false,
      );
    }
  }

  void _disconnect() async {
    await _subscription?.cancel();
    await widget.connection.close();
    if (mounted) {
      Navigator.of(context).pop();
    }
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _joystickNotifier.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Управление джойстиком'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.videogame_asset),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (context) => GameScreen(
                    joystickData: _joystickData,
                    joystickNotifier: _joystickNotifier,
                  ),
                ),
              );
            },
            tooltip: 'Игра',
          ),
        ],
      ),
      body: Column(
        children: [
          // Статус подключения
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            color: _isConnected ? Colors.green : Colors.red,
            child: Text(
              _status,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontSize: 16),
            ),
          ),

          Expanded(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Визуализация джойстика
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          children: [
                            const Text(
                              'Джойстик',
                              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 16),
                            SizedBox(
                              width: 200,
                              height: 200,
                              child: Stack(
                                children: [
                                  // Фон
                                  Container(
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      border: Border.all(color: Colors.grey, width: 2),
                                    ),
                                  ),
                                  // Позиция джойстика
                                  Positioned(
                                    left: 100 + (_joystickData.x / 100 * 80),
                                    top: 100 - (_joystickData.y / 100 * 80),
                                    child: Container(
                                      width: 20,
                                      height: 20,
                                      decoration: const BoxDecoration(
                                        color: Colors.blue,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                            Text('X: ${_joystickData.x}%'),
                            Text('Y: ${_joystickData.y}%'),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // Кнопки
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Кнопки',
                              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 16),
                            Wrap(
                              spacing: 16,
                              runSpacing: 16,
                              children: [
                                _buildButtonIndicator('UP', _joystickData.up),
                                _buildButtonIndicator('DOWN', _joystickData.down),
                                _buildButtonIndicator('LEFT', _joystickData.left),
                                _buildButtonIndicator('RIGHT', _joystickData.right),
                                _buildButtonIndicator('E (LB)', _joystickData.e),
                                _buildButtonIndicator('F (RB)', _joystickData.f),
                                _buildButtonIndicator('Click', _joystickData.joystickClick),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // Сырые данные
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Сырые данные',
                              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 8),
                            SelectableText(
                              _joystickData.toString(),
                              style: const TextStyle(fontFamily: 'monospace'),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // Кнопка отключения
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ElevatedButton.icon(
              onPressed: _disconnect,
              icon: const Icon(Icons.bluetooth_disabled),
              label: const Text('Отключиться'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: Colors.white,
                minimumSize: const Size(double.infinity, 50),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildButtonIndicator(String label, bool pressed) {
    return Container(
      width: 100,
      height: 60,
      decoration: BoxDecoration(
        color: pressed ? Colors.green : Colors.grey[300],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: pressed ? Colors.green[700]! : Colors.grey,
          width: 2,
        ),
      ),
      child: Center(
        child: Text(
          label,
          style: TextStyle(
            color: pressed ? Colors.white : Colors.black,
            fontWeight: pressed ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}

