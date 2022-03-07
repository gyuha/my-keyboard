#include QMK_KEYBOARD_H
#include "gkey.h"

enum layer_names
{
  _QWERTY,
  _LAYER_1,
  _LAYER_2
}

#define _QWERTY 0
#define _LAYER_1 1

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
   [_QWERTY] = LAYOUT(
   KC_ESC,   KC_GRV,       KC_1,    KC_2,    KC_3,    KC_4,    KC_5,          KC_6,    KC_7,    KC_8,   KC_9,    KC_0,         KC_MINS, KC_EQL,  KC_BSPC, KC_HOME,
   KC_PSCR,  KC_TAB,       KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,          KC_Y,    KC_U,    KC_I,   KC_O,    KC_P,         KC_LBRC, KC_RBRC, KC_BSLS, KC_END,
   KC_F5,    MO(_LAYER_1), KC_A,    KC_S,    KC_D,    KC_F,    KC_G,          KC_H,    KC_J,    KC_K,   KC_L,    KC_SCLN,      KC_QUOT, KC_ENT,  KC_ENT,  KC_PGUP,
   KC_INS,   KC_LSFT,      KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,          KC_B,    KC_N,    KC_M,   KC_COMM, KC_DOT,       KC_SLSH, KC_RSFT, KC_UP,   KC_PGDN,
   KC_DEL,   KC_LCTL,      KC_LWIN, KC_LALT, KC_APP,  KC_SPC,  KC_SPC,        KC_RALT, KC_SPC,  KC_SPC, KC_RALT, MO(_LAYER_1), KC_DEL,  KC_LEFT, KC_DOWN, KC_RGHT)
   [_LAYER_1] = LAYOUT(
   _______, _______,       KC_F1,   KC_F2,   KC_F3,   KC_F4,   KC_F5,         KC_F6,   KC_F7,   KC_F8,  KC_F9,   KC_F10,       KC_F11,  KC_F12,  KC_F12,  KC_F12,
   _______, _______,       _______, _______, KC_UP,   _______, _______,       _______, _______, KC_7,   KC_8,    KC_9,         _______, _______, _______, _______,
   _______, _______,       _______, KC_LEFT, KC_DOWN, KC_RGHT, _______,       KC_LBRC, KC_RBRC, KC_4,   KC_5,    KC_6,         _______, _______, _______, _______,
   _______, _______,       _______, KC_HOME, KC_PGUP, KC_PGDN, _______,       KC_LPRN, KC_RPRN, KC_1,   KC_2,    KC_3,         _______, _______, _______, _______,
   _______, _______,       _______, _______, _______, _______, _______,       _______, _______, KC_0,   _______, _______,      _______, _______, _______, _______)
};
bool process_record_user(uint16_t keycode, keyrecord_t *record)
{
   return true;
}
