---
author: gyuha
decided: 2026-07-16
---
# 펌웨어 매트릭스 배선의 원천은 EasyEDA Pro 스키마(.epro)다

QMK 펌웨어의 키 매트릭스(어느 스위치가 어느 ROW/COL 넷 → 어느 RP2040 GP핀에 연결되는지)와 핀 배치의 **진실의 원천은 `pcb/split-keyboard.epro`의 스키마(`SHEET/*.esch`)**다. PCB DXF export(`left-pcb.dxf`/`right-pcb.dxf`)는 넷 연결 정보가 없고(Ratline 레이어 공백, 평탄화된 구리 트레이스뿐), README 핀 표는 손으로 관리돼 낡았으므로(6행으로 표기됐으나 실제 5행) 둘 다 배선 원천이 될 수 없다. 스키마에는 ROW0~ROW4·COL0~COL8 넷 라벨, 2× RP2040-Zero 모듈 핀↔넷, TRRS(TX0/RX0/3V3/GND) 연결이 완전히 들어 있다.

## Consequences

- 스키마는 EasyEDA Pro 독자 포맷(ZIP + JSON-lines `.esch`)이라, 매트릭스를 뽑으려면 넷 트레이싱 파서(부품 배치 변환 → 절대 핀 좌표 → 와이어/넷라벨 연결)가 필요하다. DXF보다 파싱 부담은 크지만 결과가 정확하다.
- README 핀 표는 스키마에 맞춰 정정한다(원천은 스키마, README는 파생 문서).
- PCB가 5행이므로(ADR-0001의 배열 추출과 정합), 현재 6행 펌웨어는 이전 세대 잔재다. 이 결정으로 `MATRIX_ROWS`는 10(5×2)이 된다.
- 상판/body 배열 원천이 PCB DXF인 것([[pcb-dxf-as-layout-source]] ADR-0001)과 원천이 갈린다: **기구(상판·body) = DXF, 펌웨어(배선) = 스키마.** 같은 `.epro`의 서로 다른 export라 모순 아님.
