/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : FFT Audio Spectrum Analyzer with 16 frequency bands (44.1 kHz DMA) + Bluetooth
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "lcd_i2c.h"
#include <string.h>
#include <stdio.h>
#include <math.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define FFT_SIZE 512
#define NUM_BANDS 16
#define PI 3.14159265358979323846f

#define TIM2_CLOCK_FREQ 72000000.0f
#define TIM2_PERIOD 1632
#define REAL_SAMPLE_RATE_VAL 44100.429f
float SAMPLE_RATE = REAL_SAMPLE_RATE_VAL;
float FREQ_RESOLUTION;
float CALIBRATION_FACTOR = 1.0f;

#define BT_CMD_START 'S'
#define BT_CMD_STOP  'T'
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;
DMA_HandleTypeDef hdma_adc1;

I2C_HandleTypeDef hi2c1;

TIM_HandleTypeDef htim2;

UART_HandleTypeDef huart2;
UART_HandleTypeDef huart3;
DMA_HandleTypeDef hdma_usart2_tx;
DMA_HandleTypeDef hdma_usart3_rx;
DMA_HandleTypeDef hdma_usart3_tx;

/* USER CODE BEGIN PV */
uint16_t adc_dma_buffer[FFT_SIZE * 2];
volatile uint32_t adc_buffer_index = 0;
volatile uint8_t adc_buffer_ready = 0;

char uart_buffer[64];
volatile uint8_t dma_complete = 1;

volatile uint8_t sensitivity_mode = 0;
volatile uint8_t mode_changed = 0;
volatile uint32_t last_button_time = 0;

float fft_input[FFT_SIZE];
float fft_real[FFT_SIZE];
float fft_imag[FFT_SIZE];
float fft_magnitude[FFT_SIZE/2];

uint8_t bar_peaks[NUM_BANDS] = {0};
float bar_peaks_smooth[NUM_BANDS] = {0};

float cos_table[FFT_SIZE];
float sin_table[FFT_SIZE];

#define FREQ_AVERAGE_SIZE 2
float freq_history[FREQ_AVERAGE_SIZE] = {0};
uint8_t freq_history_index = 0;
uint8_t freq_history_count = 0;

float dc_offset = 2048.0f;
float alpha_dc = 0.95f;

float noise_floor[NUM_BANDS] = {0};
float noise_gate_threshold = 0.2f;
uint8_t noise_calibrated = 0;

uint8_t bar_chars[8][8] = {
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F},
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F},
    {0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F},
    {0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F},
    {0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F},
    {0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F},
    {0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F},
    {0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F}
};

uint16_t band_limits[NUM_BANDS + 1] = {0};

volatile uint8_t bt_recording = 0;
volatile uint8_t bt_rx_byte = 0;
volatile uint8_t bt_rx_buffer[64];
volatile uint8_t bt_rx_index = 0;
volatile uint8_t bt_cmd_received = 0;

void Recalculate_Band_Limits(void) {
    float min_freq = 80.0f;    
    float max_freq = 8000.0f;  
    
    float calibrated_sample_rate = SAMPLE_RATE * CALIBRATION_FACTOR;
    float nyquist = calibrated_sample_rate / 2.0f;
    if(max_freq > nyquist) max_freq = nyquist;
    
    float log_min = logf(min_freq);
    float log_max = logf(max_freq);
    
    for(int i = 0; i <= NUM_BANDS; i++) {
        float t = (float)i / (float)NUM_BANDS;
        float freq = expf(log_min + t * (log_max - log_min));
        uint16_t bin = (uint16_t)roundf(freq / FREQ_RESOLUTION);
        
        if(bin >= FFT_SIZE/2) {
            bin = FFT_SIZE/2 - 1;
        }
        
        if(i > 0 && bin <= band_limits[i-1]) {
            bin = band_limits[i-1] + 1;
        }
        
        if(bin > 255) {
            band_limits[i] = 255;
        } else {
            band_limits[i] = (uint8_t)bin;
        }
    }
}
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_I2C1_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_ADC1_Init(void);
static void MX_TIM2_Init(void);
static void MX_USART3_UART_Init(void);
/* USER CODE BEGIN PFP */
void Setup_Custom_Chars(void);
void Init_FFT_Tables(void);
void Perform_FFT(void);
void Calculate_Frequency_Bands(float* bands);
void Recalculate_Band_Limits(void);
void Calibrate_Frequency(float known_freq, float measured_freq);
float Parabolic_Interpolation(int peak_bin, float* magnitude);
float Logarithmic_Interpolation(int peak_bin, float* magnitude);
float Enhanced_Peak_Frequency(int peak_bin, float* magnitude);
float Average_Frequency(float new_freq);
void Send_Frequency_Bluetooth(float frequency);
void Process_Bluetooth_Command(uint8_t cmd);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2) {
        dma_complete = 1;
    }
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if(GPIO_Pin == B1_Pin) {
        uint32_t current_time = HAL_GetTick();
        if ((current_time - last_button_time) > 250) {
            sensitivity_mode++;
            if (sensitivity_mode > 2) sensitivity_mode = 0;
            mode_changed = 1;
            last_button_time = current_time;
        }
    }
}

void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef* hadc)
{
    if(hadc->Instance == ADC1) {
        adc_buffer_index = 0;
        adc_buffer_ready = 1;
    }
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
    if(hadc->Instance == ADC1) {
        adc_buffer_index = FFT_SIZE;
        adc_buffer_ready = 1;
    }
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if(huart->Instance == USART3) {
        uint8_t received_byte = bt_rx_byte;
        
        sprintf(uart_buffer, "[BT RX] 0x%02X ('%c')\r\n", received_byte, 
                (received_byte >= 32 && received_byte < 127) ? received_byte : '?');
        HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 100);
        
        if(received_byte == '\n' || received_byte == '\r') {
        } else {
            if(received_byte == 'S' || received_byte == 'T') {
                Process_Bluetooth_Command(received_byte);
            } else {
                sprintf(uart_buffer, "[BT] Unknown byte: 0x%02X\r\n", received_byte);
                HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 100);
            }
        }
        
        HAL_UART_Receive_IT(&huart3, (uint8_t*)&bt_rx_byte, 1);
    }
}

void Setup_Custom_Chars(void)
{
    for (int i = 0; i < 8; i++) {
        LCD_CreateChar(i, bar_chars[i]);
    }
}

void Init_FFT_Tables(void)
{
    for (int i = 0; i < FFT_SIZE; i++) {
        float angle = 2.0f * PI * i / FFT_SIZE;
        cos_table[i] = cosf(angle);
        sin_table[i] = sinf(angle);
    }
}


void Perform_FFT(void)
{
    for (int i = 0; i < FFT_SIZE; i++) {
        fft_real[i] = fft_input[i];
        fft_imag[i] = 0.0f;
    }

    int j = 0;
    for (int i = 1; i < FFT_SIZE - 1; i++) {
        int k = FFT_SIZE >> 1;
        while (k <= j) {
            j -= k;
            k >>= 1;
        }
        j += k;
        
        if (i < j) {
            float temp_real = fft_real[i];
            float temp_imag = fft_imag[i];
            fft_real[i] = fft_real[j];
            fft_imag[i] = fft_imag[j];
            fft_real[j] = temp_real;
            fft_imag[j] = temp_imag;
        }
    }

    for (int stage = 1; stage <= 9; stage++) {
        int block_size = 1 << stage;
        int half_block = block_size >> 1;
        int step = FFT_SIZE / block_size;

        for (int block = 0; block < FFT_SIZE; block += block_size) {
            for (int i = 0; i < half_block; i++) {
                int idx1 = block + i;
                int idx2 = idx1 + half_block;
                int twiddle_idx = i * step;

                float cos_val = cos_table[twiddle_idx];
                float sin_val = -sin_table[twiddle_idx];

                float tr = fft_real[idx2] * cos_val - fft_imag[idx2] * sin_val;
                float ti = fft_real[idx2] * sin_val + fft_imag[idx2] * cos_val;

                fft_real[idx2] = fft_real[idx1] - tr;
                fft_imag[idx2] = fft_imag[idx1] - ti;
                fft_real[idx1] = fft_real[idx1] + tr;
                fft_imag[idx1] = fft_imag[idx1] + ti;
            }
        }
    }

    for (int i = 0; i < FFT_SIZE / 2; i++) {
        float real = fft_real[i];
        float imag = fft_imag[i];
        fft_magnitude[i] = sqrtf(real * real + imag * imag) / FFT_SIZE;
    }
    
    fft_magnitude[0] = 0.0f;
}

void Calculate_Frequency_Bands(float* bands)
{
    for (int band = 0; band < NUM_BANDS; band++) {
        uint8_t start = band_limits[band];
        uint8_t end = band_limits[band + 1];
        
        float max_val = 0.0f;
        
        for (int i = start; i < end && i < FFT_SIZE/2; i++) {
            if (fft_magnitude[i] > max_val) {
                max_val = fft_magnitude[i];
            }
        }
        
        bands[band] = max_val;
    }
}

float Parabolic_Interpolation(int peak_bin, float* magnitude)
{
    if (peak_bin <= 0 || peak_bin >= FFT_SIZE/2 - 1) {
        return 0.0f;
    }
    
    float y0 = magnitude[peak_bin - 1];
    float y1 = magnitude[peak_bin];
    float y2 = magnitude[peak_bin + 1];
    
    if (y1 <= y0 || y1 <= y2) {
        return 0.0f;
    }
    
    float denominator = y0 - 2.0f * y1 + y2;
    if (fabsf(denominator) < 0.0001f) {
        return 0.0f;
    }
    
    float offset = 0.5f * (y0 - y2) / denominator;
    
    if (offset > 0.5f) offset = 0.5f;
    if (offset < -0.5f) offset = -0.5f;
    
    return offset;
}

float Logarithmic_Interpolation(int peak_bin, float* magnitude)
{
    if (peak_bin <= 0 || peak_bin >= FFT_SIZE/2 - 1) {
        return 0.0f;
    }
    
    float y0 = magnitude[peak_bin - 1];
    float y1 = magnitude[peak_bin];
    float y2 = magnitude[peak_bin + 1];
    
    if (y1 <= 0.0f || y0 <= 0.0f || y2 <= 0.0f) {
        return Parabolic_Interpolation(peak_bin, magnitude);
    }
    
    if (y1 <= y0 || y1 <= y2) {
        return 0.0f;
    }
    
    float log_y0 = logf(y0);
    float log_y1 = logf(y1);
    float log_y2 = logf(y2);
    
    float denominator = log_y0 - 2.0f * log_y1 + log_y2;
    if (fabsf(denominator) < 0.001f) {
        return Parabolic_Interpolation(peak_bin, magnitude);
    }
    
    float offset = 0.5f * (log_y0 - log_y2) / denominator;
    
    if (offset > 0.5f) offset = 0.5f;
    if (offset < -0.5f) offset = -0.5f;
    
    return offset;
}

float Enhanced_Peak_Frequency(int peak_bin, float* magnitude)
{
    if (peak_bin <= 0 || peak_bin >= FFT_SIZE/2 - 1) {
        return (float)peak_bin;
    }
    
    float y0 = magnitude[peak_bin - 1];
    float y1 = magnitude[peak_bin];
    float y2 = magnitude[peak_bin + 1];
    
    float peak_ratio = (y0 + y2) / (2.0f * y1);
    if (peak_ratio > 0.9f) {
        return (float)peak_bin + Parabolic_Interpolation(peak_bin, magnitude);
    }
    
    float log_offset = Logarithmic_Interpolation(peak_bin, magnitude);
    float para_offset = Parabolic_Interpolation(peak_bin, magnitude);
    
    float weight = 1.0f - peak_ratio;
    float combined_offset = weight * log_offset + (1.0f - weight) * para_offset;
    
    return (float)peak_bin + combined_offset;
}

float Average_Frequency(float new_freq)
{
    freq_history[freq_history_index] = new_freq;
    freq_history_index = (freq_history_index + 1) % FREQ_AVERAGE_SIZE;
    
    if (freq_history_count < FREQ_AVERAGE_SIZE) {
        freq_history_count++;
    }
    
    float sum = 0.0f;
    for (uint8_t i = 0; i < freq_history_count; i++) {
        sum += freq_history[i];
    }
    
    return sum / (float)freq_history_count;
}

void Calibrate_Frequency(float known_freq, float measured_freq)
{
    if (measured_freq > 0.1f && known_freq > 0.1f) {
        CALIBRATION_FACTOR = known_freq / measured_freq;
        FREQ_RESOLUTION = (SAMPLE_RATE / FFT_SIZE) * CALIBRATION_FACTOR;
        
        sprintf(uart_buffer, "=== CALIBRATION UPDATE ===\r\n");
        HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 100);
        sprintf(uart_buffer, "Known: %.2f Hz, Measured: %.2f Hz\r\n", known_freq, measured_freq);
        HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 100);
        sprintf(uart_buffer, "Calibration Factor: %.4f\r\n", CALIBRATION_FACTOR);
        HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 100);
        sprintf(uart_buffer, "New Freq Resolution: %.2f Hz/bin\r\n", FREQ_RESOLUTION);
        HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 100);
        sprintf(uart_buffer, "==========================\r\n\r\n");
        HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 100);
    }
}

void Process_Bluetooth_Command(uint8_t cmd)
{
    if(cmd == BT_CMD_START || cmd == 'S') {
        bt_recording = 1;
        const char* ack = "START_OK\r\n";
        HAL_UART_Transmit(&huart3, (uint8_t*)ack, strlen(ack), 50);
        sprintf(uart_buffer, "[BT] START command received\r\n");
        HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 50);
    }
    else if(cmd == BT_CMD_STOP || cmd == 'T') {
        bt_recording = 0;
        
        const char* ack = "STOP_OK\r\n";
        HAL_UART_Transmit(&huart3, (uint8_t*)ack, strlen(ack), 50);
        sprintf(uart_buffer, "[BT] STOP command received, recording=%d\r\n", bt_recording);
        HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 50);
    } else {
        sprintf(uart_buffer, "[BT] Unknown command: 0x%02X ('%c')\r\n", cmd, (cmd >= 32 && cmd < 127) ? cmd : '?');
        HAL_UART_Transmit(&huart2, (uint8_t*)uart_buffer, strlen(uart_buffer), 100);
    }
}

void Send_Frequency_Bluetooth(float frequency)
{
    if(!bt_recording) return;
    
    char freq_buffer[32];
    int len = sprintf(freq_buffer, "FREQ:%.2f\r\n", frequency);
    HAL_UART_Transmit(&huart3, (uint8_t*)freq_buffer, len, 10);
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_I2C1_Init();
  MX_USART2_UART_Init();
  MX_ADC1_Init();
  MX_TIM2_Init();
  MX_USART3_UART_Init();
  /* USER CODE BEGIN 2 */
  HAL_Delay(100);
  LCD_Init(&hi2c1);
  LCD_Clear();
  Setup_Custom_Chars();
  Init_FFT_Tables();

  LCD_SetCursor(0, 0);
  LCD_Print("FFT Spectrum");
  LCD_SetCursor(1, 0);
  LCD_Print("44.1 kHz Ready");
  HAL_Delay(1500);
  LCD_Clear();

  FREQ_RESOLUTION = (SAMPLE_RATE / FFT_SIZE) * CALIBRATION_FACTOR;
  
  Recalculate_Band_Limits();
  
  LCD_SetCursor(0, 0);
  LCD_Print("Sample Rate:");
  LCD_SetCursor(1, 0);
  char rate_buf[17];
  sprintf(rate_buf, "%.1f kHz", (SAMPLE_RATE * CALIBRATION_FACTOR) / 1000.0f);
  LCD_Print(rate_buf);
  HAL_Delay(2000);
  
  HAL_UART_Receive_IT(&huart3, (uint8_t*)&bt_rx_byte, 1);
  
  if (HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_dma_buffer, FFT_SIZE * 2) != HAL_OK) {
    Error_Handler();
  }
  
  HAL_TIM_Base_Start(&htim2);
  HAL_TIM_OC_Start(&htim2, TIM_CHANNEL_2);
  
  LCD_SetCursor(0, 0);
  LCD_Print("Calibrating");
  LCD_SetCursor(1, 0);
  LCD_Print("Noise Floor...");
  
  HAL_Delay(500);
  
  for(int calib = 0; calib < 10; calib++) {
    while(!adc_buffer_ready) {
      HAL_Delay(10);
    }
    adc_buffer_ready = 0;
    
    uint16_t* current_buffer = &adc_dma_buffer[adc_buffer_index];
    for(int i = 0; i < FFT_SIZE; i++) {
      uint16_t raw = current_buffer[i];
      dc_offset = alpha_dc * dc_offset + (1.0f - alpha_dc) * raw;
      float centered = (float)raw - dc_offset;
      float window = 0.5f * (1.0f - cosf(2.0f * PI * i / FFT_SIZE));
      fft_input[i] = centered * window;
    }
    
    Perform_FFT();
    float frequency_bands[NUM_BANDS];
    Calculate_Frequency_Bands(frequency_bands);
    
    for(int i = 0; i < NUM_BANDS; i++) {
      noise_floor[i] += frequency_bands[i];
    }
  }
  
  for(int i = 0; i < NUM_BANDS; i++) {
    noise_floor[i] = (noise_floor[i] / 10.0f) * 1.5f;
  }
  noise_calibrated = 1;
  
  LCD_Clear();
  LCD_SetCursor(0, 0);
  LCD_Print("Calibration");
  LCD_SetCursor(1, 0);
  LCD_Print("Complete!");
  HAL_Delay(1000);
  LCD_Clear();

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  float frequency_bands[NUM_BANDS];
  
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    
    if (mode_changed) {
      LCD_Clear();
      LCD_SetCursor(0, 0);
      LCD_Print("Mode Changed:");
      LCD_SetCursor(1, 0);
      if (sensitivity_mode == 0)
        LCD_Print(">> AUTO SCALE");
      else if (sensitivity_mode == 1)
        LCD_Print(">> MANUAL LOW");
      else if (sensitivity_mode == 2)
        LCD_Print(">> MANUAL HIGH");

      HAL_Delay(1000);
      LCD_Clear();

      for(int i = 0; i < NUM_BANDS; i++) {
        bar_peaks[i] = 0;
        bar_peaks_smooth[i] = 0;
      }
      mode_changed = 0;
    }

    if (adc_buffer_ready) {
      adc_buffer_ready = 0;
      
      uint16_t* current_buffer = &adc_dma_buffer[adc_buffer_index];
      
      for(int i = 0; i < FFT_SIZE; i++) {
        uint16_t raw = current_buffer[i];
        
        dc_offset = alpha_dc * dc_offset + (1.0f - alpha_dc) * raw;
        
        float centered = (float)raw - dc_offset;
        
        float window = 0.5f * (1.0f - cosf(2.0f * PI * i / FFT_SIZE));
        fft_input[i] = centered * window;
      }

      Perform_FFT();

      Calculate_Frequency_Bands(frequency_bands);
      
      for(int i = 0; i < NUM_BANDS; i++) {
        frequency_bands[i] -= noise_floor[i];
        if(frequency_bands[i] < 0) {
          frequency_bands[i] = 0;
        }
      }

      float max_magnitude = 0.0f;
      for(int i = 0; i < NUM_BANDS; i++) {
        if (frequency_bands[i] > max_magnitude) {
          max_magnitude = frequency_bands[i];
        }
      }

      float scale_factor = 1.0f;
      
      if (sensitivity_mode == 0) {
        if (max_magnitude > 1.0f) {
          scale_factor = 16.0f / max_magnitude;
        } else if (max_magnitude > 0.1f) {
          scale_factor = 16.0f;
        } else {
          scale_factor = 160.0f;
        }
      } else if (sensitivity_mode == 1) {
        scale_factor = 2.0f;
      } else {
        scale_factor = 20.0f;
      }

      char row0[17];
      char row1[17];

      for(int x = 0; x < NUM_BANDS; x++) {
        float scaled_value = frequency_bands[x] * scale_factor;
        
        if(scaled_value < 0.5f) {
          scaled_value = 0;
        }
        
        if (scaled_value > bar_peaks_smooth[x]) {
          bar_peaks_smooth[x] = scaled_value;
        } else {
          bar_peaks_smooth[x] *= 0.80f;
        }
        
        uint16_t height_pixels = (uint16_t)(bar_peaks_smooth[x]);
        if (height_pixels > 16) height_pixels = 16;
        
        bar_peaks[x] = (uint8_t)height_pixels;
        uint8_t draw_height = bar_peaks[x];

        if (draw_height == 0) {
          row1[x] = ' ';
          row0[x] = ' ';
        } else if (draw_height <= 8) {
          row1[x] = (char)(draw_height - 1);
          row0[x] = ' ';
        } else {
          row1[x] = (char)7;
          uint8_t top_pixels = draw_height - 8;
          row0[x] = (char)(top_pixels - 1);
        }
      }

      row0[16] = 0;
      row1[16] = 0;

      LCD_SetCursor(0, 0);
      for(int i = 0; i < 16; i++) {
        LCD_PrintChar(row0[i]);
      }
      LCD_SetCursor(1, 0);
      for(int i = 0; i < 16; i++) {
        LCD_PrintChar(row1[i]);
      }
      
      if(bt_recording) {
        if(max_magnitude > 0.3f) {
          int max_band = 0;
          float max_band_val = 0;
          for(int i = 0; i < NUM_BANDS; i++) {
            if(frequency_bands[i] > max_band_val) {
              max_band_val = frequency_bands[i];
              max_band = i;
            }
          }
          
          int peak_bin = band_limits[max_band];
          float peak_val = 0;
          
          int search_start = (band_limits[max_band] > 2) ? band_limits[max_band] - 2 : 1;
          int search_end = (band_limits[max_band + 1] < FFT_SIZE/2 - 2) ? band_limits[max_band + 1] + 2 : FFT_SIZE/2 - 1;
          
          for(int b = search_start; b < search_end && b < FFT_SIZE/2 - 1; b++) {
            if(b > 0 && b < FFT_SIZE/2 - 1) {
              if(fft_magnitude[b] > fft_magnitude[b-1] && fft_magnitude[b] > fft_magnitude[b+1]) {
                if(fft_magnitude[b] > peak_val) {
                  peak_val = fft_magnitude[b];
                  peak_bin = b;
                }
              }
            }
          }
          
          if(peak_val == 0) {
            for(int b = band_limits[max_band]; b < band_limits[max_band + 1] && b < FFT_SIZE/2; b++) {
              if(fft_magnitude[b] > peak_val) {
                peak_val = fft_magnitude[b];
                peak_bin = b;
              }
            }
          }
          
          float exact_bin = Enhanced_Peak_Frequency(peak_bin, fft_magnitude);
          float exact_freq = exact_bin * FREQ_RESOLUTION;
          
          Send_Frequency_Bluetooth(exact_freq);
        } else {
          Send_Frequency_Bluetooth(0.0f);
        }
      }
    }
    
    HAL_Delay(10);
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC;
  PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV6;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC1_Init(void)
{

  /* USER CODE BEGIN ADC1_Init 0 */

  /* USER CODE END ADC1_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */

  /** Common config
  */
  hadc1.Instance = ADC1;
  hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
  hadc1.Init.ContinuousConvMode = DISABLE;
  hadc1.Init.DiscontinuousConvMode = DISABLE;
  hadc1.Init.ExternalTrigConv = ADC_EXTERNALTRIGCONV_T2_CC2;
  hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc1.Init.NbrOfConversion = 1;
  if (HAL_ADC_Init(&hadc1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Regular Channel
  */
  sConfig.Channel = ADC_CHANNEL_0;
  sConfig.Rank = ADC_REGULAR_RANK_1;
  sConfig.SamplingTime = ADC_SAMPLETIME_239CYCLES_5;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{

  /* USER CODE BEGIN I2C1_Init 0 */

  /* USER CODE END I2C1_Init 0 */

  /* USER CODE BEGIN I2C1_Init 1 */

  /* USER CODE END I2C1_Init 1 */
  hi2c1.Instance = I2C1;
  hi2c1.Init.ClockSpeed = 100000;
  hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c1.Init.OwnAddress1 = 0;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C1_Init 2 */

  /* USER CODE END I2C1_Init 2 */

}

/**
  * @brief TIM2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM2_Init(void)
{

  /* USER CODE BEGIN TIM2_Init 0 */

  /* USER CODE END TIM2_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM2_Init 1 */

  /* USER CODE END TIM2_Init 1 */
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 0;
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 1632;
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_OC_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_UPDATE;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 816;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_OC_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM2_Init 2 */

  /* USER CODE END TIM2_Init 2 */
  HAL_TIM_MspPostInit(&htim2);

}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * @brief USART3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART3_UART_Init(void)
{

  /* USER CODE BEGIN USART3_Init 0 */

  /* USER CODE END USART3_Init 0 */

  /* USER CODE BEGIN USART3_Init 1 */

  /* USER CODE END USART3_Init 1 */
  huart3.Instance = USART3;
  huart3.Init.BaudRate = 115200;
  huart3.Init.WordLength = UART_WORDLENGTH_8B;
  huart3.Init.StopBits = UART_STOPBITS_1;
  huart3.Init.Parity = UART_PARITY_NONE;
  huart3.Init.Mode = UART_MODE_TX_RX;
  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart3) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART3_Init 2 */

  /* USER CODE END USART3_Init 2 */

}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{

  /* DMA controller clock enable */
  __HAL_RCC_DMA1_CLK_ENABLE();

  /* DMA interrupt init */
  /* DMA1_Channel1_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel1_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel1_IRQn);
  /* DMA1_Channel2_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel2_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel2_IRQn);
  /* DMA1_Channel3_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel3_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel3_IRQn);
  /* DMA1_Channel7_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel7_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel7_IRQn);

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
/* USER CODE BEGIN MX_GPIO_Init_1 */
/* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin : B1_Pin */
  GPIO_InitStruct.Pin = B1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(B1_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : LD2_Pin */
  GPIO_InitStruct.Pin = LD2_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LD2_GPIO_Port, &GPIO_InitStruct);

  /* EXTI interrupt init*/
  HAL_NVIC_SetPriority(EXTI15_10_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);

/* USER CODE BEGIN MX_GPIO_Init_2 */
/* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
