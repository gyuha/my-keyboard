#pragma once

//#include "config_common.h"

#define VENDOR_ID       0xFEED
#define PRODUCT_ID      0x4445
#define DEVICE_VER      0x0001
#define PRODUCT         "Split-keyboard"
#define MANUFACTURER    "MyHome"

/* key matrix size */
// Rows are doubled-up
#define MATRIX_ROWS 10
#define MATRIX_COLS 9

// #define ENCODERS_PAD_A { F4 }
// #define ENCODERS_PAD_B { F5 }

// wiring of each half
#define MATRIX_ROW_PINS { F7, B1, B3, B2, B6}
#define MATRIX_COL_PINS { D4, C6, D7, E6, B4, B5, F4, F5, F6}

#define DIODE_DIRECTION COL2ROW
#define SOFT_SERIAL_PIN D0

// WS2812 RGB LED strip input and number of LEDs
// #define RGB_DI_PIN D3
// #define RGBLED_NUM 12
