#pragma once

//#include "config_common.h"

#define VENDOR_ID       0xFEED
#define PRODUCT_ID      0x4445
#define DEVICE_VER      0x0001
#define PRODUCT         "Split-keyboard"
#define MANUFACTURER    "Gyuha"

/* key matrix size */
// Rows are doubled-up (5 physical rows per half x 2 = 10)
#define MATRIX_ROWS 10
#define MATRIX_COLS 9

// #define ENCODERS_PAD_A { F4 }
// #define ENCODERS_PAD_B { F5 }

// wiring of each half (from PCB schematic pcb/split-keyboard.epro)
// ROW0..ROW4 = GP2..GP6 (common to both halves)
// COL0..COL8 = GP7..GP15 (left uses COL0..6, right uses COL0..8)
#define MATRIX_ROW_PINS { GP2, GP3, GP4, GP5, GP6 }
#define MATRIX_COL_PINS { GP7, GP8, GP9, GP10, GP11, GP12, GP13, GP14, GP15 }

#define DIODE_DIRECTION COL2ROW

// TRRS split serial (full-duplex): schematic nets TX0=GP0, RX0=GP1, plus 3V3, GND
#define SERIAL_USART_FULL_DUPLEX
#define SERIAL_USART_TX_PIN GP0
#define SERIAL_USART_RX_PIN GP1

// WS2812 RGB LED strip input and number of LEDs
// #define RGB_DI_PIN D3
// #define RGBLED_NUM 12
