/*
Copyright 2018 Mattia Dal Ben <matthewdibi@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#pragma once

/* Use I2C or Serial, not both */
#define USE_SERIAL
// #define USE_I2C

/* Select hand configuration */
// USB goes to the RIGHT half. The aux board is gone -- the RP2040-Zero and the
// USB-C breakout are now cradled on the body floor and hand-wired to the main
// PCB's 16-pin header pads, so the right module is no longer stranded inside
// the wall and its host port reaches the rear opening. The left module sits
// beside its header with no wall opening at all. See
// adr/260824-224604-drop-aux-board-and-floor-mount-modules.md, which retires
// adr/260824-003937-usb-host-is-the-left-half.md.
// #define MASTER_LEFT
#define MASTER_RIGHT

// #define EE_HANDS
// #undef RGBLED_NUM
// #define RGBLIGHT_ANIMATIONS
// #define RGBLED_NUM 14
// #define RGBLIGHT_HUE_STEP 8
// #define RGBLIGHT_SAT_STEP 8
// #define RGBLIGHT_VAL_STEP 8
