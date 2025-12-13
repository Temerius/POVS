let txPort = null;
let rxPort = null;
let reader = null;
let writer = null;
let isRecording = false;
let currentFrequency = 0;
let startTime = 0;

const selectTxPortBtn = document.getElementById('selectTxPortBtn');
const selectRxPortBtn = document.getElementById('selectRxPortBtn');
const txPortInfo = document.getElementById('txPortInfo');
const rxPortInfo = document.getElementById('rxPortInfo');
const connectBtn = document.getElementById('connectBtn');
const disconnectBtn = document.getElementById('disconnectBtn');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const connectionStatus = document.getElementById('connectionStatus');
const recordingStatus = document.getElementById('recordingStatus');
const frequencyValueEl = document.getElementById('frequencyValue');
const frequencyChart = document.getElementById('frequencyChart');
const maxFreqEl = document.getElementById('maxFreq');
const minFreqEl = document.getElementById('minFreq');
const avgFreqEl = document.getElementById('avgFreq');
let ctx = null;
if (frequencyChart) {
    ctx = frequencyChart.getContext('2d');
    const rect = frequencyChart.getBoundingClientRect();
    frequencyChart.width = rect.width || 800;
    frequencyChart.height = rect.height || 300;
}

if (!('serial' in navigator)) {
    alert('Ваш браузер не поддерживает Web Serial API. Используйте Chrome, Edge или Opera.');
}

function getPortInfo(port) {
    const info = port.getInfo();
    if (info.usbVendorId && info.usbProductId) {
        return `USB Serial (VID:${info.usbVendorId.toString(16)}, PID:${info.usbProductId.toString(16)})`;
    } else if (port.getInfo().path) {
        return port.getInfo().path;
    } else {
        return 'Serial Port';
    }
}

async function selectTxPort() {
    try {
        const port = await navigator.serial.requestPort();
        
        if (txPort && txPort.readable) {
            try {
                await txPort.close();
            } catch (e) {
            }
        }
        
        txPort = port;
        txPortInfo.textContent = getPortInfo(port);
        txPortInfo.className = 'port-info selected';
        
        checkCanConnect();
        
    } catch (error) {
        if (error.name !== 'NotFoundError') {
            console.error('Ошибка выбора порта отправки:', error);
            alert('Ошибка выбора порта: ' + error.message);
        }
    }
}

async function selectRxPort() {
    try {
        const port = await navigator.serial.requestPort();
        
        if (rxPort && rxPort.readable) {
            try {
                await rxPort.close();
            } catch (e) {
            }
        }
        
        rxPort = port;
        rxPortInfo.textContent = getPortInfo(port);
        rxPortInfo.className = 'port-info selected';
        
        checkCanConnect();
        
    } catch (error) {
        if (error.name !== 'NotFoundError') {
            console.error('Ошибка выбора порта приема:', error);
            alert('Ошибка выбора порта: ' + error.message);
        }
    }
}

function checkCanConnect() {
    if (txPort && rxPort) {
        connectBtn.disabled = false;
    } else {
        connectBtn.disabled = true;
    }
}

async function connect() {
    try {
        if (!txPort || !rxPort) {
            alert('Выберите оба порта!');
            return;
        }

        if (txPort === rxPort) {
            console.log('Используется один порт для TX и RX');
            await txPort.open({ baudRate: 115200 });
            console.log('Порт открыт');
            writer = txPort.writable.getWriter();
            reader = txPort.readable.getReader();
            console.log('Writer и Reader созданы');
        } else {
            console.log('Открываю порт отправки...');
            await txPort.open({ baudRate: 115200 });
            console.log('Порт отправки открыт');
            writer = txPort.writable.getWriter();
            console.log('Writer создан');

            console.log('Открываю порт приема...');
            await rxPort.open({ baudRate: 115200 });
            console.log('Порт приема открыт');
            reader = rxPort.readable.getReader();
            console.log('Reader создан');
        }

        connectBtn.disabled = true;
        disconnectBtn.disabled = false;
        startBtn.disabled = false;
        selectTxPortBtn.disabled = true;
        selectRxPortBtn.disabled = true;
        connectionStatus.textContent = 'Статус: Подключено';
        connectionStatus.className = 'status connected';

        readData();

    } catch (error) {
        console.error('Ошибка подключения:', error);
        alert('Ошибка подключения: ' + error.message);
    }
}

async function disconnect() {
    try {
        isRecording = false;
        
        if (reader) {
            await reader.cancel();
            await reader.releaseLock();
            reader = null;
        }

        if (writer) {
            await writer.releaseLock();
            writer = null;
        }

        if (txPort) {
            await txPort.close();
            txPort = null;
        }

        if (rxPort) {
            await rxPort.close();
            rxPort = null;
        }

        connectBtn.disabled = true;
        disconnectBtn.disabled = true;
        startBtn.disabled = true;
        stopBtn.disabled = true;
        selectTxPortBtn.disabled = false;
        selectRxPortBtn.disabled = false;
        connectionStatus.textContent = 'Статус: Не подключено';
        connectionStatus.className = 'status disconnected';
        recordingStatus.textContent = 'Запись не активна';
        recordingStatus.className = 'status disconnected';
        
        txPort = null;
        rxPort = null;
        txPortInfo.textContent = 'Не выбран';
        txPortInfo.className = 'port-info';
        rxPortInfo.textContent = 'Не выбран';
        rxPortInfo.className = 'port-info';
        
        frequencyValueEl.textContent = '-- Hz';
        currentFrequency = 0;
        if (frequencyChart && ctx) {
            updateChart();
        }
        if (maxFreqEl) maxFreqEl.textContent = '-- Hz';
        if (minFreqEl) minFreqEl.textContent = '-- Hz';
        if (avgFreqEl) avgFreqEl.textContent = '-- Hz';
        
        checkCanConnect();

    } catch (error) {
        console.error('Ошибка отключения:', error);
    }
}

async function readData() {
    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { value, done } = await reader.read();
            
            if (done) {
                break;
            }

            buffer += decoder.decode(value, { stream: true });

            let newlineIndex;
            while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
                const line = buffer.substring(0, newlineIndex).trim();
                buffer = buffer.substring(newlineIndex + 1);

                if (line.startsWith('FREQ:')) {
                    processFrequencyData(line);
                } else if (line === 'START_OK') {
                    console.log('Мониторинг начат');
                    recordingStatus.textContent = 'Мониторинг активен';
                    recordingStatus.className = 'status recording';
                } else if (line === 'STOP_OK') {
                    console.log('Мониторинг остановлен - получено подтверждение');
                    recordingStatus.textContent = 'Мониторинг остановлен';
                    recordingStatus.className = 'status disconnected';
                    isRecording = false;
                    stopBtn.disabled = true;
                    startBtn.disabled = false;
                }
            }
        }
    } catch (error) {
        console.error('Ошибка чтения:', error);
        if (error.name !== 'NetworkError') {
            await disconnect();
        }
    }
}

function processFrequencyData(line) {
    if (!isRecording) return;
    
    try {
        const freqStr = line.substring(5);
        const frequency = parseFloat(freqStr.trim());
        
        if (frequency > 0.1) {
            currentFrequency = frequency;
            
            if (frequency >= 1000) {
                frequencyValueEl.textContent = (frequency / 1000).toFixed(2) + ' kHz';
            } else {
                frequencyValueEl.textContent = frequency.toFixed(2) + ' Hz';
            }
        } else {
            currentFrequency = 0;
            frequencyValueEl.textContent = '-- Hz';
        }
        
        updateFrequencyStats();
    } catch (error) {
        console.error('Ошибка обработки данных о частоте:', error);
        currentFrequency = 0;
        frequencyValueEl.textContent = '-- Hz';
    }
}

function updateChart() {
    if (!frequencyChart || !ctx) {
        return;
    }
    
    const rect = frequencyChart.getBoundingClientRect();
    if (frequencyChart.width !== rect.width || frequencyChart.height !== rect.height) {
        frequencyChart.width = rect.width || 800;
        frequencyChart.height = rect.height || 300;
    }
    
    const width = frequencyChart.width;
    const height = frequencyChart.height;
    const centerY = height / 2;
    
    
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, width, height);
    
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    
    ctx.strokeStyle = '#222';
    ctx.beginPath();
    ctx.moveTo(0, centerY - height * 0.4);
    ctx.lineTo(width, centerY - height * 0.4);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(0, centerY + height * 0.4);
    ctx.lineTo(width, centerY + height * 0.4);
    ctx.stroke();
    
    ctx.strokeStyle = '#333';
    for (let i = 0; i <= 10; i++) {
        const x = (width / 10) * i;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }
    
    ctx.strokeStyle = '#555';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(width, centerY);
    ctx.stroke();
    
    if (currentFrequency > 0.1) {
        const amplitude = height * 0.35;
        const sampleRate = 44100;
        const timeWindow = 0.01;
        const samples = Math.floor(sampleRate * timeWindow);
        
        
        ctx.strokeStyle = '#667eea';
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        let firstPoint = true;
        for (let i = 0; i < samples; i++) {
            const t = (i / samples) * timeWindow;
            const x = (i / samples) * width;
            
            const y = centerY - amplitude * Math.sin(2 * Math.PI * currentFrequency * t);
            
            if (firstPoint) {
                ctx.moveTo(x, y);
                firstPoint = false;
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.stroke();
        
        ctx.fillStyle = '#fff';
        ctx.font = '14px Arial';
        ctx.fillText(`${formatFrequency(currentFrequency)}`, 10, 20);
        ctx.fillText('0 V', 10, centerY + 5);
        ctx.fillText(`${timeWindow * 1000} ms`, width - 80, height - 10);
    } else {
        const timeWindow = 0.01;
        ctx.fillStyle = '#888';
        ctx.font = '14px Arial';
        ctx.fillText('-- Hz', 10, 20);
        ctx.fillText('0 V', 10, centerY + 5);
        ctx.fillText(`${timeWindow * 1000} ms`, width - 80, height - 10);
    }
}

function updateFrequencyStats() {
    if (currentFrequency > 0.1) {
        if (maxFreqEl) maxFreqEl.textContent = formatFrequency(currentFrequency);
    } else {
        if (maxFreqEl) maxFreqEl.textContent = '-- Hz';
    }
}

function formatFrequency(freq) {
    if (freq >= 1000) {
        return (freq / 1000).toFixed(2) + ' kHz';
    } else {
        return freq.toFixed(2) + ' Hz';
    }
}

async function sendCommand(cmd) {
    console.log('=== sendCommand вызвана ===');
    console.log('writer существует:', !!writer);
    console.log('txPort существует:', !!txPort);
    
    if (!writer) {
        console.error('Writer не существует!');
        alert('Не подключено к порту отправки!');
        return;
    }

    if (!txPort) {
        console.error('txPort не существует!');
        alert('Порт отправки не выбран!');
        return;
    }

    try {
        if (!txPort.readable && !txPort.writable) {
            console.error('Порт не открыт!');
            alert('Порт отправки не открыт! Попробуйте переподключиться.');
            return;
        }

        const encoder = new TextEncoder();
        const data = encoder.encode(cmd + '\r\n');
        console.log('Отправляю данные:', cmd, 'Байты:', Array.from(data).map(b => '0x' + b.toString(16)).join(' '));
        
        await writer.write(data);
        console.log('✅ Команда успешно отправлена:', cmd);
        
        await writer.ready;
        console.log('✅ Writer готов, данные отправлены');
        
    } catch (error) {
        console.error('❌ Ошибка отправки команды:', error);
        console.error('Детали ошибки:', error.name, error.message, error.stack);
        alert('Ошибка отправки команды: ' + error.message);
    }
}

async function startRecording() {
    currentFrequency = 0;
    startTime = Date.now();
    isRecording = true;
    
    startBtn.disabled = true;
    stopBtn.disabled = false;
    
    if (frequencyChart) {
        if (!ctx) {
            ctx = frequencyChart.getContext('2d');
        }
        const rect = frequencyChart.getBoundingClientRect();
        frequencyChart.width = rect.width || 800;
        frequencyChart.height = rect.height || 300;
    }
    
    animateChart();
    
    await sendCommand('S');
}

let animationId = null;
function animateChart() {
    if (!isRecording) {
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
        updateChart();
        return;
    }
    
    updateChart();
    updateFrequencyStats();
    
    animationId = requestAnimationFrame(() => animateChart());
}

async function stopRecording() {
    console.log('Остановка мониторинга...');
    isRecording = false;
    
    if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
    }
    
    await sendCommand('T');
    setTimeout(() => {
        if (!isRecording) {
            stopBtn.disabled = true;
            startBtn.disabled = false;
            updateChart();
        }
    }, 500);
}

selectTxPortBtn.addEventListener('click', selectTxPort);
selectRxPortBtn.addEventListener('click', selectRxPort);
connectBtn.addEventListener('click', connect);
disconnectBtn.addEventListener('click', disconnect);
startBtn.addEventListener('click', startRecording);
stopBtn.addEventListener('click', stopRecording);

window.addEventListener('load', () => {
    if (frequencyChart) {
        ctx = frequencyChart.getContext('2d');
        if (ctx) {
            updateChart();
        }
    }
});

