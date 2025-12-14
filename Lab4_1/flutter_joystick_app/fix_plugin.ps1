# Скрипт для автоматического исправления namespace в flutter_bluetooth_serial

$pluginPath = "$env:USERPROFILE\.pub-cache\hosted\pub.dev\flutter_bluetooth_serial-0.4.0\android\build.gradle"

if (Test-Path $pluginPath) {
    Write-Host "Найден файл плагина: $pluginPath"
    
    $content = Get-Content $pluginPath -Raw
    
    if ($content -notmatch "namespace") {
        Write-Host "Добавляю namespace в build.gradle..."
        
        # Заменяем android { на android { namespace = "..."
        $newContent = $content -replace '(?s)(android\s*\{)', "`$1`n        namespace = `"it.matteocrippa.flutterbluetoothserial`""
        
        Set-Content -Path $pluginPath -Value $newContent -NoNewline
        
        Write-Host "Namespace добавлен успешно!"
    } else {
        Write-Host "Namespace уже присутствует в файле"
    }
} else {
    Write-Host "Файл плагина не найден. Выполните сначала: flutter pub get"
    Write-Host "Путь: $pluginPath"
}

