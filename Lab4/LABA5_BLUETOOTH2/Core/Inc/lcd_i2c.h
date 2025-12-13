#ifndef LCD_I2C_H
#define LCD_I2C_H

#include "stm32f1xx_hal.h"
#include <stdint.h>

#define LCD_I2C_ADDR (0x27 << 1)
#define LCD_CMD_CLEAR         0x01  
#define LCD_CMD_HOME          0x02  
#define LCD_CMD_ENTRY_MODE    0x06  
#define LCD_CMD_DISPLAY_ON    0x0C  
#define LCD_CMD_DISPLAY_OFF   0x08  
#define LCD_CMD_CURSOR_ON     0x0E  
#define LCD_CMD_BLINK_ON      0x0F  
#define LCD_CMD_FUNCTION_SET  0x28  
#define LCD_CMD_SET_CGRAM     0x40  
#define LCD_CMD_SET_DDRAM     0x80

#define LCD_BIT_RS    (1 << 0)  
#define LCD_BIT_RW    (1 << 1)  
#define LCD_BIT_EN    (1 << 2)  
#define LCD_BIT_BL    (1 << 3)

void LCD_Init(I2C_HandleTypeDef *hi2c);
void LCD_Clear(void);
void LCD_Home(void);
void LCD_SetCursor(uint8_t row, uint8_t col);
void LCD_Print(const char *str);
void LCD_PrintChar(char ch);
void LCD_PrintInt(int32_t value);
void LCD_PrintFloat(float value, uint8_t decimals);
void LCD_Backlight(uint8_t state);

void LCD_CreateChar(uint8_t location, uint8_t charmap[]);
void LCD_PrintCustomChar(uint8_t location);

#endif /* LCD_I2C_H */
