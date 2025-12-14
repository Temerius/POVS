import 'package:flutter/material.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:async';
import 'joystick_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Bluetooth Joystick',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const BluetoothConnectionScreen(),
    );
  }
}

class BluetoothConnectionScreen extends StatefulWidget {
  const BluetoothConnectionScreen({super.key});

  @override
  State<BluetoothConnectionScreen> createState() => _BluetoothConnectionScreenState();
}

class _BluetoothConnectionScreenState extends State<BluetoothConnectionScreen> {
  // ========== ВАШ MAC-АДРЕС HC-05 ==========
  static const String HC05_MAC_ADDRESS = "98:D3:71:F7:25:09";
  // =========================================

  BluetoothState _bluetoothState = BluetoothState.UNKNOWN;
  List<BluetoothDevice> _devices = [];
  BluetoothConnection? _connection;
  bool _isConnecting = false;
  String _statusMessage = "Готов к подключению";
  List<String> _logs = [];

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    await _requestPermissions();
    await _getBluetoothState();
    await _getDevices();
  }

  void _log(String message) {
    setState(() {
      _logs.insert(0, "${DateTime.now().toString().substring(11, 19)}: $message");
      if (_logs.length > 20) _logs.removeLast();
    });
    print("BT_LOG: $message");
  }

  Future<void> _requestPermissions() async {
    _log("Запрос разрешений...");
    
    Map<Permission, PermissionStatus> statuses = await [
      Permission.bluetooth,
      Permission.bluetoothConnect,
      Permission.bluetoothScan,
      Permission.location,
    ].request();

    statuses.forEach((permission, status) {
      _log("$permission: $status");
    });
  }

  Future<void> _getBluetoothState() async {
    BluetoothState state = await FlutterBluetoothSerial.instance.state;
    setState(() {
      _bluetoothState = state;
    });
    _log("Bluetooth состояние: $state");

    FlutterBluetoothSerial.instance.onStateChanged().listen((state) {
      setState(() {
        _bluetoothState = state;
      });
      _log("Bluetooth изменён: $state");
    });
  }

  Future<void> _getDevices() async {
    _log("Получение списка устройств...");
    try {
      List<BluetoothDevice> devices = await FlutterBluetoothSerial.instance.getBondedDevices();
      setState(() {
        _devices = devices;
      });
      _log("Найдено ${devices.length} устройств:");
      for (var d in devices) {
        _log("  - ${d.name} [${d.address}]");
      }
    } catch (e) {
      _log("Ошибка получения устройств: $e");
    }
  }

  // ========== ПРЯМОЕ ПОДКЛЮЧЕНИЕ К HC-05 ==========
  Future<void> _connectToHC05() async {
    await _connectToAddress(HC05_MAC_ADDRESS);
  }

  Future<void> _connectToAddress(String address) async {
    if (_isConnecting) {
      _log("Уже идёт подключение!");
      return;
    }

    setState(() {
      _isConnecting = true;
      _statusMessage = "Подключение к $address...";
    });

    _log("=== НАЧАЛО ПОДКЛЮЧЕНИЯ ===");
    _log("MAC: $address");

    try {
      // Закрываем старое соединение если есть
      if (_connection != null) {
        _log("Закрытие старого соединения...");
        try {
          await _connection!.close();
        } catch (e) {
          _log("Ошибка закрытия старого соединения: $e");
        }
        _connection = null;
        await Future.delayed(const Duration(milliseconds: 500));
      }

      _log("Попытка подключения...");
      
      // Проверяем, что устройство спарено
      if (!_devices.any((d) => d.address == address)) {
        throw Exception("Устройство не найдено в спаренных. Сначала сопрягите HC-05 в настройках Bluetooth.");
      }
      
      BluetoothDevice device = _devices.firstWhere((d) => d.address == address);
      _log("Найдено устройство: ${device.name}");
      
      // Попытка отключиться от других устройств (если подключено)
      try {
        _log("Проверка текущих подключений...");
      } catch (e) {
        _log("Не удалось проверить подключения: $e");
      }
      
      // Подключение с таймаутом
      // flutter_bluetooth_serial использует стандартный UUID для SPP автоматически
      _log("Подключение к устройству...");
      BluetoothConnection connection = await BluetoothConnection.toAddress(address)
          .timeout(
            const Duration(seconds: 20),
            onTimeout: () {
              throw TimeoutException("Таймаут подключения (20 сек). Убедитесь, что HC-05 не подключен к другому устройству.");
            },
          );

      _log("✓ ПОДКЛЮЧЕНО!");
      _log("isConnected: ${connection.isConnected}");

      setState(() {
        _connection = connection;
        _isConnecting = false;
        _statusMessage = "Подключено!";
      });

      // Переход на экран джойстика
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => JoystickControlScreen(connection: connection),
          ),
        );
      }

    } on TimeoutException catch (e) {
      _log("✗ ТАЙМАУТ: $e");
      setState(() {
        _isConnecting = false;
        _statusMessage = "Таймаут подключения";
      });
      _showError("Таймаут подключения. HC-05 включен?");
      
    } catch (e) {
      _log("✗ ОШИБКА: $e");
      _log("Тип ошибки: ${e.runtimeType}");
      setState(() {
        _isConnecting = false;
        _statusMessage = "Ошибка: $e";
      });
      _showError("Ошибка: $e\n\nПроверьте:\n1. HC-05 включен\n2. LED мигает\n3. Устройство спарено");
    }
  }

  void _showError(String message) {
    if (mounted) {
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text("Ошибка подключения"),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("OK"),
            ),
          ],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('HC-05 Подключение'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _getDevices,
          ),
        ],
      ),
      body: _bluetoothState.isEnabled
          ? _buildConnectedUI()
          : _buildBluetoothOffUI(),
    );
  }

  Widget _buildConnectedUI() {
    return SingleChildScrollView(
      child: Column(
        children: [
        // Статус
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          color: _isConnecting ? Colors.orange : Colors.blue,
          child: Column(
            children: [
              Text(
                _statusMessage,
                style: const TextStyle(color: Colors.white, fontSize: 16),
                textAlign: TextAlign.center,
              ),
              if (_isConnecting)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: LinearProgressIndicator(color: Colors.white),
                ),
            ],
          ),
        ),

        // ========== ГЛАВНАЯ КНОПКА ПОДКЛЮЧЕНИЯ ==========
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: ElevatedButton.icon(
            onPressed: _isConnecting ? null : _connectToHC05,
            icon: _isConnecting 
                ? const SizedBox(
                    width: 20, 
                    height: 20, 
                    child: CircularProgressIndicator(strokeWidth: 2)
                  )
                : const Icon(Icons.bluetooth_connected, size: 32),
            label: Column(
              children: [
                const Text(
                  'ПОДКЛЮЧИТЬСЯ К HC-05',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                Text(
                  HC05_MAC_ADDRESS,
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
              minimumSize: const Size(double.infinity, 80),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),

        const Divider(),

        // Список устройств
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              Text(
                'Спаренные устройства (${_devices.length}):',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ],
          ),
        ),

        // Список устройств в скроллируемом списке
        SizedBox(
          height: 200,
          child: ListView(
            children: [
              // Список устройств
              ..._devices.map((device) => ListTile(
                    leading: Icon(
                      Icons.bluetooth,
                      color: device.address == HC05_MAC_ADDRESS 
                          ? Colors.green 
                          : Colors.grey,
                    ),
                    title: Text(device.name ?? "Unknown"),
                    subtitle: Text(
                      device.address +
                      (device.address == HC05_MAC_ADDRESS ? " ← ВАШ HC-05" : ""),
                    ),
                    trailing: device.address == HC05_MAC_ADDRESS
                        ? const Icon(Icons.star, color: Colors.amber)
                        : null,
                    onTap: _isConnecting
                        ? null
                        : () => _connectToAddress(device.address),
                  )),

              // Проверка наличия HC-05 в списке
              if (!_devices.any((d) => d.address == HC05_MAC_ADDRESS))
                const Card(
                  margin: EdgeInsets.all(16),
                  color: Colors.orange,
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      children: [
                        Icon(Icons.warning, color: Colors.white, size: 32),
                        SizedBox(height: 8),
                        Text(
                          "HC-05 НЕ НАЙДЕН В СПАРЕННЫХ!",
                          style: TextStyle(
                            color: Colors.white, 
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(height: 8),
                        Text(
                          "1. Откройте Настройки → Bluetooth\n"
                          "2. Найдите HC-05\n"
                          "3. Нажмите 'Сопряжение'\n"
                          "4. Введите PIN: 1234\n"
                          "5. Вернитесь в приложение",
                          style: TextStyle(color: Colors.white),
                        ),
                      ],
                    ),
                  ),
                ),

              const Divider(),

              // Логи
              Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  'Логи:',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              ..._logs.map((log) => Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                    child: Text(
                      log,
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 11,
                      ),
                    ),
                  )),
            ],
          ),
        ),
      ],
      ),
    );
  }

  Widget _buildBluetoothOffUI() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.bluetooth_disabled, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          const Text('Bluetooth выключен'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () async {
              await FlutterBluetoothSerial.instance.requestEnable();
            },
            child: const Text('Включить Bluetooth'),
          ),
        ],
      ),
    );
  }
}