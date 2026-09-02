# 2026-09-02 — aux 보드 폐기 + RP2040-Zero·USB-C 바닥 크래들 고정 회고

## 계획 대비 실제

- **계획대로 된 것:** 슬라이스 S1~S3, S5~S7 전부 (이전 세션 산출물 포함). 최종 DoD 13항목 전부 통과, verified: yes.
- **어긋남:**
  - **이전 세션이 계획을 이미 실행하고 `run.md`를 남기지 않았다.** fg-run의 재실행 가드는 `run.md` 부재를 "정상 시작"으로 읽으므로 이 상태를 못 잡는다. 승격 직후 찍은 DoD 기준선이 전진 검사 7~13번의 "이미 통과"를 드러내 재실행 사고를 막았다. 계획에 적힌 DoD 6 사전 상태(bridged 84.4/56.3)가 실측(37.6/46.9)과 달랐던 것도 같은 원인.
  - **이전 세션이 S4를 헤드리스로 실행해 FCStd의 GUI 데이터(GuiDocument.xml·썸네일·ShapeAppearance)가 전부 소실돼 있었다.** 지오메트리만 질의하는 `verify_port_mounts.py`(DoD 7)는 이를 볼 수 없어 실패가 가려졌다. 이번 실행에서 GUI 재생성으로 복구(zip 엔트리 920개, ShapeAppearance 128개).
  - **"GUI 재생성 약 10분"은 틀린 수치였다 — 실측 40초.** 이전 회고(tilt-wedge) 교훈 6의 근거 수치를 정정한다. 검증 스크립트를 재생성과 분리한 판단 자체는 여전히 유효.
  - **MCP `execute_code`로는 재생성을 직접 못 돌린다** (동기 실행 타임아웃, async는 문서 트리·GUI 접근 금지). `QtCore.QTimer.singleShot`으로 GUI 스레드에 예약만 걸고 즉시 반환 후, 파일 플래그(`/tmp/fg_regen_status.txt`)로 완료를 관찰하는 우회가 통했다.
  - run.md가 처분을 회고로 미룬 `freecad/verify_port_mounts_selftest.py`는 이후 작업(a03d0d4)에서 커밋되어 유지가 확정됐다 — 종결.

## 배운 것

- **다음에 다르게 할 것:**
  - 승격 직후 DoD 기준선 측정은 재실행 가드보다 강한 안전장치다 — 전진 검사가 기준선에서 통과하면 "이미 실행된 작업"을 의심하라.
  - FCStd 산출물 검증에 지오메트리 검사만으로는 부족하다 — GUI 데이터 소실은 못 본다. 후속 후보: FCStd zip에 `GuiDocument.xml`·`ShapeAppearance*` 존재 검사 추가.
  - 장시간 GUI 작업을 MCP로 돌릴 때는 `QTimer.singleShot` 예약 + 파일 플래그 관찰 패턴을 쓴다.

## 문서 반영

- CONTEXT.md 승급: 없음
- ADR 추가: 없음 (되돌리기 어려운 트레이드오프 결정 없음 — 전부 프로세스·도구 교훈)
