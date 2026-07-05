#pragma once

//#include "config_common.h"

#define VENDOR_ID       0xFEED
#define PRODUCT_ID      0x4445
#define DEVICE_VER      0x0001
#define PRODUCT         "Split-keyboard"
#define MANUFACTURER    "MyHome"

/* key matrix size */
// Rows are doubled-up
#define MATRIX_ROWS 12
#define MATRIX_COLS 9

// #define ENCODERS_PAD_A { F4 }
// #define ENCODERS_PAD_B { F5 }

// wiring of each half
#define MATRIX_ROW_PINS { GP0, GP1, GP2, GP3, GP4, GP5 }
#define MATRIX_COL_PINS { GP6, GP7, GP8, GP9, GP10, GP11, GP12, GP13, GP14 }

#define DIODE_DIRECTION COL2ROW
#define SERIAL_USART_TX_PIN GP15

// WS2812 RGB LED strip input and number of LEDs
// #define RGB_DI_PIN D3
// #define RGBLED_NUM 12
