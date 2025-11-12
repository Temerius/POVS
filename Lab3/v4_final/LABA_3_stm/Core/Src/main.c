/* main.c - Управление кнопками и семисегментным индикатором */

#include "main.h"
#include "protocol.h"
#include <string.h>

/* Private variables */
UART_HandleTypeDef huart2;
DMA_HandleTypeDef hdma_usart2_rx;
DMA_HandleTypeDef hdma_usart2_tx;

// Текущий счёт миль
static uint16_t current_miles = 0;

// Display
volatile uint8_t disp_buf[4] = {0, 0, 0, 0};
static uint32_t last_refresh_tick = 0;
static uint8_t current_digit = 0;
#define DIGIT_ON_MS 2

static const uint8_t seg_digits[10] = {
    0b00111111, // 0
    0b00000110, // 1
    0b01011011, // 2
    0b01001111, // 3
    0b01100110, // 4
    0b01101101, // 5
    0b01111101, // 6
    0b00000111, // 7
    0b01111111, // 8
    0b01101111  // 9
};

// Состояние кнопок
static uint8_t button_left_prev = 0;
static uint8_t button_right_prev = 0;
static uint8_t button_fire_prev = 0;

/* Private function prototypes */
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_USART2_UART_Init(void);

// Display functions
static void shift_out_byte(uint8_t b);
static void latch_pulse(void);
static void prepare_display_buffer(uint16_t miles);
static void display_refresh_cycle(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    /* Initialize peripherals */
    MX_GPIO_Init();
    MX_DMA_Init();
    MX_USART2_UART_Init();

    /* Initialize protocol */
    Protocol_Init(&huart2);
    
    uint32_t last_send_tick = HAL_GetTick();
    
    while (1)
    {
        uint32_t current_tick = HAL_GetTick();
        
        // Обновление индикатора (каждые 2 мс)
        display_refresh_cycle();
        
        // Чтение кнопок (инвертированная логика: 0 = нажата)
        uint8_t left = !HAL_GPIO_ReadPin(CANON_LEFT_GPIO_Port, CANON_LEFT_Pin);
        uint8_t right = !HAL_GPIO_ReadPin(CANON_RIGHT_GPIO_Port, CANON_RIGHT_Pin);
        uint8_t fire = !HAL_GPIO_ReadPin(CANON_FIRE_GPIO_Port, CANON_FIRE_Pin);
        
        // Отправка состояния кнопок каждые 50 мс
        if (current_tick - last_send_tick >= 50) {
            Protocol_SendButtons(left, right, fire);
            last_send_tick = current_tick;
        }
        
        // Приём миль от PC
        uint16_t received_miles = current_miles;
        Protocol_ProcessIncoming(&received_miles);
        
        if (received_miles != current_miles) {
            current_miles = received_miles;
            prepare_display_buffer(current_miles);
        }
        
        button_left_prev = left;
        button_right_prev = right;
        button_fire_prev = fire;
    }
}

/* UART Callbacks */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2) {
        uart_tx_busy = 0;
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2) {
        uart_tx_busy = 0;
        HAL_UART_Receive_DMA(&huart2, rx_buffer, 64);
    }
}

/* Display Functions */
static void shift_out_byte(uint8_t b)
{
    for(int i = 7; i >= 0; --i) {
        uint8_t bit = (b >> i) & 0x1;
        HAL_GPIO_WritePin(DATA_DISP_GPIO_Port, DATA_DISP_Pin, 
                         bit ? GPIO_PIN_SET : GPIO_PIN_RESET);
        HAL_GPIO_WritePin(CLK_DISP_GPIO_Port, CLK_DISP_Pin, GPIO_PIN_SET);
        HAL_GPIO_WritePin(CLK_DISP_GPIO_Port, CLK_DISP_Pin, GPIO_PIN_RESET);
    }
}

static void latch_pulse(void)
{
    HAL_GPIO_WritePin(LATCH_DISP_GPIO_Port, LATCH_DISP_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(LATCH_DISP_GPIO_Port, LATCH_DISP_Pin, GPIO_PIN_RESET);
}

static void prepare_display_buffer(uint16_t miles)
{
    if (miles > 9999) miles = 9999;
    
    uint8_t d3 = (miles / 1000) % 10;
    uint8_t d2 = (miles / 100) % 10;
    uint8_t d1 = (miles / 10) % 10;
    uint8_t d0 = miles % 10;
    
    disp_buf[0] = seg_digits[d3];
    disp_buf[1] = seg_digits[d2];
    disp_buf[2] = seg_digits[d1];
    disp_buf[3] = seg_digits[d0];
}

static void display_refresh_cycle(void)
{
    uint32_t now = HAL_GetTick();
    
    if((now - last_refresh_tick) >= DIGIT_ON_MS) {
        uint8_t segments = disp_buf[current_digit];
        uint8_t digit_mask = (1 << current_digit);
        
        shift_out_byte(~segments);
        shift_out_byte(digit_mask);
        latch_pulse();
        
        current_digit++;
        if(current_digit >= 4) current_digit = 0;
        
        last_refresh_tick = now;
    }
}

/* System Clock Configuration */
void SystemClock_Config(void)
{
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    RCC_OscInitStruct.HSIState = RCC_HSI_ON;
    RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
    RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI_DIV2;
    RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL16;
    HAL_RCC_OscConfig(&RCC_OscInitStruct);

    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                                |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
    HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2);
}

/* USART2 Initialization */
static void MX_USART2_UART_Init(void)
{
    huart2.Instance = USART2;
    huart2.Init.BaudRate = 115200;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart2);
}

/* DMA Initialization */
static void MX_DMA_Init(void)
{
    __HAL_RCC_DMA1_CLK_ENABLE();

    HAL_NVIC_SetPriority(DMA1_Channel6_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel6_IRQn);
    
    HAL_NVIC_SetPriority(DMA1_Channel7_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel7_IRQn);
}

/* GPIO Initialization */
static void MX_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* Кнопки с подтяжкой вверх */
    GPIO_InitStruct.Pin = CANON_LEFT_Pin|CANON_RIGHT_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = CANON_FIRE_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT; 
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(CANON_FIRE_GPIO_Port, &GPIO_InitStruct);

    /* Пины дисплея */
    HAL_GPIO_WritePin(GPIOA, CLK_DISP_Pin|DATA_DISP_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOB, LATCH_DISP_Pin, GPIO_PIN_RESET);

    GPIO_InitStruct.Pin = CLK_DISP_Pin|DATA_DISP_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_PULLDOWN;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = LATCH_DISP_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_PULLDOWN;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LATCH_DISP_GPIO_Port, &GPIO_InitStruct);
}

void Error_Handler(void)
{
    __disable_irq();
    while (1) {}
}