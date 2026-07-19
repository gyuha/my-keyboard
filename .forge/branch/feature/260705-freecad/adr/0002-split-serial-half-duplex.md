# RP2040 분할 키보드 시리얼은 1선 half-duplex로 구성한다

QMK의 RP2040 플랫폼은 분할 키보드 시리얼로 2선 full-duplex(`SERIAL_USART_TX_PIN`+`RX_PIN`, SIO/PIO 드라이버 기본 예시)를 우선 권장하지만, 기존 하드웨어의 3.5mm TRS(스테레오, 3극) 커넥터와 케이블이 데이터선 1가닥만 배선되어 있어 그대로 재사용하기 위해 1선 half-duplex를 선택했다. AVR의 `SOFT_SERIAL_PIN`은 RP2040에서 인식되지 않으며(실제 컴파일로 확인), RP2040의 half-duplex는 `rules.mk`의 `SERIAL_DRIVER = vendor`(PIO 기반)와 `config.h`의 `SERIAL_USART_TX_PIN GP15` 한 줄로 구성한다 — RX 핀 정의나 외부 풀업 저항이 필요 없다.

케이블에 2번째 도선(TRS의 Ring)을 추가 배선하면 언제든 2선 full-duplex로 전환할 수 있다 — 안정성이 더 필요해지면 우선 고려할 옵션이다.
