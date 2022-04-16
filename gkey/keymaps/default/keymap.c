#include QMK_KEYBOARD_H
#include "gkey.h"

enum layer_names {
   _QWERTY,
   _FN1,
   _FN2
};

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
   [_QWERTY] = LAYOUT(
      KC_ESC,   KC_1,    KC_2,    KC_3,    KC_4,    KC_5,    KC_6,     KC_6,    KC_7,    KC_8,    KC_9,    KC_0,     KC_MINS, KC_EQL,  KC_BSPC, KC_HOME,
      KC_TAB,   KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,              KC_Y,    KC_U,    KC_I,    KC_O,    KC_P,     KC_LBRC, KC_RBRC, KC_BSLS, KC_END,
      MO(_FN1), KC_A,    KC_S,    KC_D,    KC_F,    KC_G,              KC_H,    KC_J,    KC_K,    KC_L,    KC_SCLN,  KC_QUOT, KC_ENT,           KC_PGUP,
      KC_LSFT,  KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,              KC_B,    KC_N,    KC_M,    KC_COMM, KC_DOT,   KC_SLSH, KC_RSFT, KC_UP,   KC_PGDN,
      KC_LCTL,  KC_LWIN, KC_LALT, MO(_FN2),KC_SPC,                     KC_RALT, KC_SPC,           KC_RALT, MO(_FN1), KC_DEL,  KC_LEFT, KC_DOWN, KC_RGHT),
   [_FN1] = LAYOUT(
      KC_GRV ,  KC_F1,   KC_F2,   KC_F3,   KC_F4,   KC_F5,   KC_F6,    KC_F6,   KC_F7,   KC_F8,   KC_F9,    KC_F10,   KC_F11,  KC_F12,  _______, KC_MUTE,
      KC_CAPS,  KC_HOME, KC_UP,   KC_END,  KC_PGUP, _______,           _______, KC_GRV , _______, _______,  KC_PGUP,  _______, _______, _______, KC_MPLY,
      _______,  KC_LEFT, KC_DOWN, KC_RGHT, KC_PGDN, _______,           KC_LEFT, KC_DOWN, KC_UP,   KC_RGHT,  _______,  _______, _______,          KC_VOLU,
      _______,  KC_INS,  KC_DEL,  KC_PSCR, _______, _______,           KC_PGDN, KC_PGDN, _______, _______,  KC_INS ,  KC_DEL , _______, _______, KC_VOLD,
      _______,  _______, _______, _______, _______,                    KC_CAPS, _______,          _______,  _______,  _______, _______, _______, _______),
   [_FN2] = LAYOUT(
      RESET  ,  KC_KP_1, KC_KP_2, KC_KP_3, KC_KP_4, KC_KP_5, KC_KP_6,  KC_KP_6, KC_KP_7, KC_KP_8, KC_KP_9,  KC_KP_0,  KC_PMNS, KC_PEQL, _______, KC_MUTE,
      _______,  KC_HOME, KC_UP,   KC_END,  KC_PGUP, _______,           KC_KP_7, KC_KP_8, KC_KP_9, _______,  _______,  _______, _______, _______, KC_SLEP,
      _______,  KC_LEFT, KC_DOWN, KC_RGHT, KC_PGDN, _______,           KC_KP_4, KC_KP_5, KC_KP_6, _______,  _______,  _______, KC_PENT,          KC_MPRV,
      _______,  KC_INS,  KC_DEL,  KC_PSCR, _______, _______,           KC_KP_0, KC_KP_1, KC_KP_2, KC_KP_3,  KC_INS,   KC_DEL,  _______, _______, KC_MNXT,
      _______,  _______, _______, _______, _______,                    KC_NUM , _______,          _______,  _______,  _______, _______, _______, _______)
};

bool process_record_user(uint16_t keycode, keyrecord_t *record)
{
   return true;
}
