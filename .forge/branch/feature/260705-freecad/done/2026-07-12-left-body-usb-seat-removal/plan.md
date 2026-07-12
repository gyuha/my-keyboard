<!-- forge-slug: left-body-usb-seat-removal -->
<!-- task: 3 -->
<!-- tdd: off -->
<!-- retro-hint: optional -->
# 좌측 바디에서 컨트롤러 시트·USB 홀 제거

## Goal / Non-goals
- Goal: FreeCAD 파라메트릭 스크립트(`freecad/create_keyboard_plates.py`)가 생성하는 **Left 18 mm keyboard body**에서 컨트롤러 관련 형상 4종 — ①RP2040-Zero 시트(바닥 1mm 리세스) ②USB-C 관통홀(10×6) ③외벽 베젤 리세스(14×10×1) ④RP2040 참조 객체(`Left_RP2040_Zero_Reference`) — 을 제거하고 FCStd·STL을 재생성한다. 좌측 리어월은 PJ-322 잭 홀만 남는다.
- 배경 결정: 펌웨어가 `MASTER_RIGHT`(USB는 우측에만 연결)이고, RP2040-Zero 플래싱은 어차피 BOOT 버튼 물리 접근(케이스 개방)이 필요하므로 좌측 USB 홀은 실효성이 없다. 좌측 RP2040-Zero는 계속 탑재하되(TRRS 슬레이브, 펌웨어상 필수) 시트 없이 **자유 배치**(테이프/글루 고정)한다.
- Non-goals:
  - 우측 바디 변경(우측은 마스터 — 시트·USB 홀 유지, 형상 완전 무변화)
  - 좌측 PJ-322 잭 홀·뒷막이 블록·잭 참조 객체 변경(TRRS 연결에 필수, 유지)
  - 좌측 컨트롤러용 대체 고정 구조물 추가(자유 배치로 결정)
  - 플레이트·팜레스트·틸트 웨지·인서트 포켓 변경
  - 펌웨어(gkey/)·README 변경
  - Fusion 360 모델(keyboard-plate v9) — 이전 세대 작업물, 건드리지 않음

## Source of truth
- Glossary terms: Body(바디), 부품 받침(Part mount — 현행 FreeCAD 모델에서는 바닥 리세스 시트), 부품 노출 홀(Port cutout) — `.forge/CONTEXT.md` (이번 그릴링에서 FreeCAD 현행화 반영)
- Related ADRs: `.forge/adr/0002-split-serial-half-duplex.md` (TRRS 1선 half-duplex — 좌측 잭 유지 근거)
- 코드 사실: `build_body()`의 `include_controller` 플래그가 시트·USB홀·베젤·참조 객체를 일괄 제어 — 좌측 호출(create_keyboard_plates.py 하단)에서 `include_controller=False`, `usb_center_x=None`으로 바꾸면 잭 관련 형상은 그대로 유지된 채 4종만 빠진다
- 펌웨어 근거: `gkey/keymaps/default/config.h`의 `#define MASTER_RIGHT`
- Definition of Done:
  - 스크립트 무오류 재실행, FCStd 저장
  - 좌측 바디: 구 USB 홀 위치의 리어월이 완전 솔리드(프로브 부피 == 프로브 체적), 구 시트 영역(z −16~−15)이 솔리드, FCStd에 `Left_RP2040_Zero_Reference` 부재
  - 좌측 유지 확인: PJ-322 잭 홀(Ø6.5)·뒷막이 블록(72mm³ 프로브) 그대로
  - 우측 바디: 부피 변화 없음(변경 전후 동일)
  - `left_keyboard_body.stl` 재생성

## Work slices
- [ ] S1. `create_keyboard_plates.py` 좌측 `build_body` 호출을 `include_controller=False`(usb 인자 None)로 변경하고 FreeCAD에서 재실행 — 완료 기준: 스크립트 무오류 실행, FCStd에 `Left_RP2040_Zero_Reference` 없음, STL 재생성
- [ ] S2. 기하 검증 (depends: S1) — 완료 기준: 좌측 리어월 구 USB 영역 솔리드 프로브 통과, 구 시트 영역 솔리드 프로브 통과, 좌측 잭 홀·뒷막이 유지 프로브 통과, 우측 바디 부피 변경 전과 동일
