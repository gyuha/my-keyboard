#pragma once

//#include "config_common.h"

// 0xFEED is QMK's placeholder VID and VIA rejects it outright; 0x1209/0x0001 is
// the pid.codes test PID, free for prototypes. Must stay in sync with via.json.
#define VENDOR_ID       0x1209
#define PRODUCT_ID      0x0001
#define DEVICE_VER      0x0001
#define PRODUCT         "Split-keyboard"
#define MANUFACTURER    "Gyuha"

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

// Bootmagic runs before the split link is up, so the master can only read its
// own rows. USB is on the right (MASTER_RIGHT), whose rows are 6-11, so without
// the _RIGHT pair below it would poll (0,0) on the left half and never trigger.
// (6,0) = right F7; (0,0) = left ESC, used when a half boots as the slave.
#define BOOTMAGIC_ROW           0
#define BOOTMAGIC_COLUMN        0
#define BOOTMAGIC_ROW_RIGHT     6
#define BOOTMAGIC_COLUMN_RIGHT  0

// WS2812 RGB LED strip input and number of LEDs
// #define RGB_DI_PIN D3
// #define RGBLED_NUM 12
