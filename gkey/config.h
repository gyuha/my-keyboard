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
#define MATRIX_ROWS 10
#define MATRIX_COLS 9

// #define ENCODERS_PAD_A { F4 }
// #define ENCODERS_PAD_B { F5 }

// wiring of each half
// The function row is gone (5 rows per half), so GP5 is free.
#define MATRIX_ROW_PINS { GP0, GP1, GP2, GP3, GP4 }
#define MATRIX_COL_PINS { GP6, GP7, GP8, GP9, GP10, GP11, GP12, GP13, GP14 }

#define DIODE_DIRECTION COL2ROW
#define SERIAL_USART_TX_PIN GP15

// Bootmagic runs before the split link is up, so the master can only read its
// own rows. USB is on the right (MASTER_RIGHT), whose rows are 5-9, so without
// the _RIGHT pair below it would poll (0,0) on the left half and never trigger.
// (5,0) = right 7; (0,0) = left Esc, used when a half boots as the slave.
#define BOOTMAGIC_ROW           0
#define BOOTMAGIC_COLUMN        0
#define BOOTMAGIC_ROW_RIGHT     5
#define BOOTMAGIC_COLUMN_RIGHT  0

// Grave Escape sits where the function row used to push ` down to: tap = Esc,
// Shift = ~. ALT/CTRL are overridden so Windows keeps Alt+Esc (window cycle)
// and Ctrl+Esc (start menu). GUI is deliberately NOT overridden, so Cmd+Esc
// still sends Cmd+` for macOS same-app window switching; SHIFT must not be
// overridden either or ~ becomes unreachable. A bare ` comes from Fn1.
#define GRAVE_ESC_ALT_OVERRIDE
#define GRAVE_ESC_CTRL_OVERRIDE

// WS2812 RGB LED strip input and number of LEDs
// #define RGB_DI_PIN D3
// #define RGBLED_NUM 12
