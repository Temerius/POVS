/* lcd_i2c.c - Полная реализация драйвера LCD1602 через I2C (PCF8574) */
#include "lcd_i2c.h"
#include <string.h>
#include <stdio.h>

// Глобальная переменная для хранения указателя на I2C
static I2C_HandleTypeDef *lcd_i2c;

/**
 * @brief Отправка половины байта (nibble) в LCD
 */
static void LCD_WriteNibble(uint8_t nibble, uint8_t rs) {
    uint8_t data = 0;
    
    // Формируем байт для PCF8574
    // Биты: D7 D6 D5 D4 BL EN RW RS
    data = (nibble & 0xF0);      // Старшие 4 бита данных
    data |= LCD_BIT_BL;          // Включаем подсветку
    
    if (rs) {
        data |= LCD_BIT_RS;      // Режим данных
    }
    
    // Генерируем импульс Enable (HIGH)
    data |= LCD_BIT_EN;
    HAL_I2C_Master_Transmit(lcd_i2c, LCD_I2C_ADDR, &data, 1, 100);
    // Небольшая задержка, можно уменьшить для скорости отрисовки волны
    // Но совсем убирать нельзя, LCD медленный
    for(int k=0; k<500; k++) { __NOP(); } 
    
    // Генерируем импульс Enable (LOW)
    data &= ~LCD_BIT_EN;
    HAL_I2C_Master_Transmit(lcd_i2c, LCD_I2C_ADDR, &data, 1, 100);
    for(int k=0; k<500; k++) { __NOP(); }
}

/**
 * @brief Отправка команды в LCD
 */
static void LCD_SendCommand(uint8_t cmd) {
    LCD_WriteNibble(cmd & 0xF0, 0);
    LCD_WriteNibble((cmd << 4) & 0xF0, 0);
    
    if (cmd == LCD_CMD_CLEAR || cmd == LCD_CMD_HOME) {
        HAL_Delay(2);
    }
}

/**
 * @brief Отправка данных (символа) в LCD
 */
static void LCD_SendData(uint8_t data) {
    LCD_WriteNibble(data & 0xF0, 1);
    LCD_WriteNibble((data << 4) & 0xF0, 1);
}

void LCD_Init(I2C_HandleTypeDef *hi2c) {
    lcd_i2c = hi2c;
    
    HAL_Delay(50);
    
    LCD_WriteNibble(0x30, 0);
    HAL_Delay(5);
    LCD_WriteNibble(0x30, 0);
    HAL_Delay(1);
    LCD_WriteNibble(0x30, 0);
    HAL_Delay(1);
    LCD_WriteNibble(0x20, 0);
    HAL_Delay(1);
    
    LCD_SendCommand(LCD_CMD_FUNCTION_SET);
    LCD_SendCommand(LCD_CMD_DISPLAY_OFF);
    LCD_SendCommand(LCD_CMD_CLEAR);
    HAL_Delay(2);
    LCD_SendCommand(LCD_CMD_ENTRY_MODE);
    LCD_SendCommand(LCD_CMD_DISPLAY_ON);
}

void LCD_Clear(void) {
    LCD_SendCommand(LCD_CMD_CLEAR);
    HAL_Delay(2);
}

void LCD_Home(void) {
    LCD_SendCommand(LCD_CMD_HOME);
    HAL_Delay(2);
}

void LCD_SetCursor(uint8_t row, uint8_t col) {
    uint8_t address;
    if (row == 0) {
        address = 0x00 + col;
    } else {
        address = 0x40 + col;
    }
    LCD_SendCommand(LCD_CMD_SET_DDRAM | address);
}

void LCD_Print(const char *str) {
    while (*str) {
        LCD_SendData((uint8_t)(*str));
        str++;
    }
}

void LCD_PrintChar(char ch) {
    LCD_SendData((uint8_t)ch);
}

void LCD_PrintInt(int32_t value) {
    char buffer[12];
    sprintf(buffer, "%ld", (long)value);
    LCD_Print(buffer);
}

void LCD_PrintFloat(float value, uint8_t decimals) {
    char buffer[16];
    char format[8];
    sprintf(format, "%%.%df", decimals);
    sprintf(buffer, format, value);
    LCD_Print(buffer);
}

void LCD_Backlight(uint8_t state) {
    uint8_t data = 0;
    if (state) {
        data = LCD_BIT_BL;
    }
    HAL_I2C_Master_Transmit(lcd_i2c, LCD_I2C_ADDR, &data, 1, 100);
}

void LCD_CreateChar(uint8_t location, uint8_t charmap[]) {
    location &= 0x7;
    LCD_SendCommand(LCD_CMD_SET_CGRAM | (location << 3));
    
    for (uint8_t i = 0; i < 8; i++) {
        LCD_SendData(charmap[i]);
    }
    LCD_SendCommand(LCD_CMD_SET_DDRAM);
}

void LCD_PrintCustomChar(uint8_t location) {
    LCD_SendData(location & 0x07);
}