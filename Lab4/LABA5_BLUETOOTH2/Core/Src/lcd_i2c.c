#include "lcd_i2c.h"
#include <string.h>
#include <stdio.h>

static I2C_HandleTypeDef *lcd_i2c;

static void LCD_WriteNibble(uint8_t nibble, uint8_t rs) {
    uint8_t data = 0;
    
    data = (nibble & 0xF0);
    data |= LCD_BIT_BL;
    
    if (rs) {
        data |= LCD_BIT_RS;
    }
    
    data |= LCD_BIT_EN;
    HAL_I2C_Master_Transmit(lcd_i2c, LCD_I2C_ADDR, &data, 1, 100);
    HAL_Delay(1);
    
    data &= ~LCD_BIT_EN;
    HAL_I2C_Master_Transmit(lcd_i2c, LCD_I2C_ADDR, &data, 1, 100);
    HAL_Delay(1);
}

static void LCD_SendCommand(uint8_t cmd) {
    LCD_WriteNibble(cmd & 0xF0, 0);
    
    LCD_WriteNibble((cmd << 4) & 0xF0, 0);
    
    if (cmd == LCD_CMD_CLEAR || cmd == LCD_CMD_HOME) {
        HAL_Delay(2);
    }
}

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
    
    // Function Set: 4-bit mode, 2 lines, 5x8 dots
    LCD_SendCommand(LCD_CMD_FUNCTION_SET);
    
    // Display OFF
    LCD_SendCommand(LCD_CMD_DISPLAY_OFF);
    
    // Clear Display
    LCD_SendCommand(LCD_CMD_CLEAR);
    HAL_Delay(2);
    
    // Entry Mode Set: increment cursor, no shift
    LCD_SendCommand(LCD_CMD_ENTRY_MODE);
    
    // Display ON: display on, cursor off, blink off
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
    sprintf(buffer, "%ld", value);
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
    LCD_SendCommand(0x40 | (location << 3));
    
    for (uint8_t i = 0; i < 8; i++) {
        LCD_SendData(charmap[i]);
    }
    
    LCD_SendCommand(LCD_CMD_SET_DDRAM);
}

void LCD_PrintCustomChar(uint8_t location) {
    LCD_SendData(location & 0x07);
}
