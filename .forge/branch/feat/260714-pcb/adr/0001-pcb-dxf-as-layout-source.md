# 상판 배열의 원천을 switch.dxf에서 PCB DXF export로 전환한다

손배선 시절에는 `left-switch.dxf`/`right-switch.dxf`가 스위치 배열의 원천이었으나 이 파일들은 삭제되었고, 이제 전용 PCB를 사용하므로 `left-pcb.dxf`/`right-pcb.dxf`(전체 레이어 export)가 유일한 배열 원천이다. 상판의 키 위치는 PCB의 스위치 중심홀(Multi-Layer, Ø4mm)에서 추출하고, 나사 위치는 PCB의 기존 마운팅 홀(Ø5 코너·Ø3 중앙)에서 가져온다.

## Consequences

- 배열·홀 좌표를 깔끔한 switch.dxf 대신 평탄화된 PCB export에서 역추출하므로 추출이 취약하다 — 스위치 수·홀 수·피치(19.05mm)를 매번 수치로 검증해야 한다.
- PCB가 배열을 바꾸면 상판도 자동으로 따라간다(원천이 하나로 통일됨).
- 좌우 배열이 비대칭이므로(좌/우 키 수가 다름) 미러링이 아니라 각 PCB에서 독립 생성한다.
