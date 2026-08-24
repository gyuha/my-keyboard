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

// wiring of each half -- read off the PCB schematic (pcb/split-keyboard.epro),
// which is the source of truth for the pin map. tools/verify_pcb_matrix.py
// re-derives it from that file and fails the build if these drift.
// GP0/GP1 are taken by the split link, so no GPIO is spare below GP16.
#define MATRIX_ROW_PINS { GP2, GP3, GP4, GP5, GP6 }
#define MATRIX_COL_PINS { GP7, GP8, GP9, GP10, GP11, GP12, GP13, GP14, GP15 }

#define DIODE_DIRECTION COL2ROW

// One-wire half-duplex on GP0. Both halves wire the connector identically
// (V/G/D+ -> 3V3/GND/GP0), so a straight cable ties TX to TX -- full duplex
// cannot work on this hardware however the firmware is configured. The PIO
// driver (SERIAL_DRIVER = vendor in rules.mk) needs only this one pin: no RX
// pin, no external pull-up.
#define SERIAL_USART_TX_PIN GP0

// Bootmagic runs before the split link is up, so each half can only read its
// own rows. USB is on the left now (see keymaps/default/config.h), whose rows
// are 0-4, so the unsuffixed pair below is what the master polls: (0,0) = left
// Esc. The _RIGHT pair is what the right half polls when it is the one being
// reset -- (5,0) is its top-row 6, the key this PCB added.
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
