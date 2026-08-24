---
author: gyuha
decided: 2026-08-24 00:19
---
# 분할 링크는 USB-C 커넥터에 3선 half-duplex(GP0)로 구성한다

PCB 회로도는 반쪽마다 PJ-322A 4극 잭에 3V3·GND·TX0(GP0)·RX0(GP1)을 배선해 두었고 `feat/260714-pcb` 브랜치의 펌웨어는 그것을 `SERIAL_USART_FULL_DUPLEX`로 읽었다. **그 조합은 동작할 수 없다** — 좌우 aux 보드의 잭 배선이 완전히 동일하므로(TX0→pad3, RX0→pad4) 스트레이트 케이블은 TX0↔TX0, RX0↔RX0을 잇는다. 크로스오버 케이블이나 반쪽별로 다른 펌웨어 없이는 full-duplex가 성립하지 않는다.

3.5mm 잭을 **USB-C 브레이크아웃(12×15mm, V/D−/D+/G)** 으로 대체하고, **GP0 단선 half-duplex**를 쓴다. 실제 배선은 3가닥 — `V`→3V3, `G`→GND, `D+`→GP0. `D−`는 미사용. `rules.mk`의 `SERIAL_DRIVER = vendor`(RP2040 PIO)가 이미 켜져 있어 `config.h`의 `SERIAL_USART_TX_PIN GP0` 한 줄로 구성되며 RX 핀 정의나 외부 풀업이 필요 없다. 이는 ADR `0002-split-serial-half-duplex`(`.forge/branch/feature/260705-freecad/adr/`)의 half-duplex 결정을 유지하면서 핀만 GP15 → GP0으로 옮긴 것이다. 다만 그 ADR의 근거였던 "기존 3극 TRS 케이블 재사용"은 PCB가 4극 잭을 쓰면서 이미 무효가 됐고, 이제 커넥터 자체가 USB-C로 바뀌었다.

**위험을 알고 택했다.** 케이스 후면에 호스트용 USB-C(RP2040-Zero)와 분할 링크용 USB-C가 나란히 놓이며 육안으로 구별되지 않는다. 분할 포트에 PC 케이블을 꽂으면 VBUS 5V가 `V`(=3V3 레일)로 들어가 RP2040을 파괴할 수 있다. TRRS는 컴퓨터에 꽂을 수 있는 모양이 아니어서 이 사고가 구조적으로 불가능했다. 두 포트를 다른 벽에 분리하는 완화안을 제시했으나, 배선 길이와 좌우 케이블 경로를 이유로 **기존 aux 잭 위치(후면)** 를 유지하기로 결정했다.

## Consequences

- `V` 라인 직렬 쇼트키 다이오드는 선택 사항으로 남긴다 — 넣으면 5V 역주입을 막는다.
- `MASTER_RIGHT`이므로 좌측 반쪽의 호스트 USB-C는 플래싱 외에는 쓰이지 않는다. 좌측에는 기능하지 않는 USB-C가 하나 더 생기며 혼동 가능성이 그만큼 늘어난다.
