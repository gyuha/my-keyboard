<!-- forge-slug: drop-aux-board-floor-mount-modules -->
# RUN — aux 보드를 폐기하고 RP2040-Zero·USB-C 브레이크아웃을 바디 바닥 크래들에 고정한다

실행일: 2026-08-25

## 이 실행의 성격 — 워크플로우를 세우지 않았다

계획 승격 직후 DoD 기준선(baseline)을 찍었더니 **13개 항목이 전부 통과**했다. 실패해야
정상인 전진 검사 7~13번까지 포함해서다. 즉 **이 계획은 이전 세션이 이미 실행했고,
`run.md` 를 남기지 않은 채 끝났다.** fg-run 의 재실행 가드는 `run.md` 부재를 "정상 시작"
으로 읽으므로, 가드만 믿었으면 이미 끝난 작업을 통째로 다시 돌릴 뻔했다. 기준선이
이를 잡아냈다.

남은 실제 작업은 슬라이스 하나의 잔여분(S4)뿐이었다. fg-run 의 비용 제약("단일 에이전트
규모면 워크플로우를 건너뛰고 직접 처리하는 편이 싸고 빠르다")에 따라 **Dynamic Workflow
를 세우지 않고 이 세션에서 직접 처리**했다. 서브에이전트를 띄우지 않았다.

## 슬라이스별 결과

- S1 `freecad/verify_port_mounts.py` 작성 (8항목 검사) — ✅ 계획대로 (이전 세션 산출물)
- S2 `PARAMS`·`stack_z()` 바닥 기준 재정의 — ✅ 계획대로 (이전 세션 산출물)
- S3 `build_body()` 크래들·포트 자리·개구부 — ✅ 계획대로 (이전 세션 산출물)
- S4 GUI 재생성 + STL 8개 + 스크린샷 — ⚠ **이전 세션이 헤드리스로 실행해 FCStd 의 GUI
  데이터를 파괴했고 스크린샷을 재촬영하지 않았다. 이번 실행에서 고쳤다.**
- S5 `tools/pcb.py` 정리 — ✅ 계획대로 (이전 세션 산출물)
- S6 펌웨어 `MASTER_RIGHT` 복귀 — ✅ 계획대로 (이전 세션 산출물)
- S7 README 정합 (10개 지점) — ✅ 계획대로 (이전 세션 산출물)

## 계획과 실제의 어긋남

### 1. S4 가 헤드리스로 실행되어 FCStd 의 GUI 데이터가 전부 소실돼 있었다 (이번에 복구)

S4 는 "헤드리스 생성은 파트 색상을 잃으므로 권위 있는 재생성은 GUI 에서 한다"고 명시했다.
이전 세션은 그 반대로 했다. **DoD 7 이 통과하고 있었기 때문에 이 실패가 가려져 있었다** —
`verify_port_mounts.py` 는 지오메트리만 질의하므로 GUI 데이터 소실을 볼 수 없다.

zip 내용물 비교로 확정했다:

| | HEAD (커밋된 판) | 이전 세션 산출물 | 이번 실행 후 |
| --- | --- | --- | --- |
| zip 엔트리 총수 | — | — | 920 |
| `Document.xml` | 있음 | 있음 | 있음 |
| `GuiDocument.xml` | 있음 | **없음** | 있음 |
| `thumbnails/Thumbnail.png` | 있음 | **없음** | 있음 |
| `ShapeAppearance*` | 116개 | **0개** | 128개 |
| `LineColorArray*` | 101개 | **0개** | 있음 |
| `*Aux*` 엔트리 | `Left_Aux_Guides` 등 다수 | 0개 | 0개 |

**우회로는 없었다.** HEAD 의 `GuiDocument.xml` 을 이식하는 방법은 성립하지 않는다 — 그
파일은 `Left_Aux_Guides`·`Right_Aux_Board_Reference` 등 이제 존재하지 않는 오브젝트를
참조한다. 지오메트리가 바뀐 이상 매핑이 깨진다. GUI 재생성 외에 길이 없었다.

복구 방법: FreeCAD GUI 를 띄우고(`auto_start_rpc: true` 라 RPC 자동 연결)
`create_keyboard_parametric.py` 를 GUI 스레드에서 재실행했다.

### 2. 재생성이 10분이 아니라 40초에 끝났다

계획의 "실행 전 전제"는 "재생성은 약 10분"이라고 적었다. 실측 **40초**다. 15배 차이다.
이 오해가 S1 의 설계 근거(회고 교훈 6 — "10분짜리 GUI 재생성 밖에 두어 수 초에 끝나게
한다")에도 얹혀 있다. 검증 스크립트를 재생성과 분리한 판단 자체는 여전히 옳지만
(검증은 재생성 없이 반복 가능해야 한다), **근거로 든 시간 수치는 틀렸다.**

### 3. MCP `execute_code` 로는 재생성을 직접 못 돌린다

`execute_code` 는 GUI 스레드 동기 실행이라 장시간 작업에서 타임아웃이 나고,
`execute_code_async` 는 문서 트리·GUI 를 건드리는 코드를 금지한다 — 생성기는 둘 다 한다.
`QtCore.QTimer.singleShot` 으로 GUI 스레드에 예약만 걸고 MCP 호출은 즉시 반환시킨 뒤,
파일 플래그(`/tmp/fg_regen_status.txt`)로 완료를 관찰하는 우회를 썼다. 계획에 없던 수단이다.

### 4. 계획이 기록한 DoD 6 사전 상태가 실제와 달랐다

계획은 `bridged 좌 84.4 / 우 56.3` 이라 적었으나 기준선 실측은 `좌 37.6 / 우 46.9` 였다.
이전 세션이 이미 형상을 바꾼 뒤였기 때문이다. 계획 작성 시점의 값이 낡은 것이지
검사가 틀린 것이 아니다.

### 5. 계획에 없는 산출물이 하나 있다

`freecad/verify_port_mounts_selftest.py` (5.9KB, untracked). S1 은 `verify_port_mounts.py`
하나만 요구했다. 자체 검증용으로 보이나 계획의 산출물 목록에 없고, 어느 DoD 항목도
이 파일을 실행하지 않는다. 유지할지 버릴지는 회고에서 정할 문제로 남긴다.

### 6. 스크린샷 프레이밍은 원본 관례를 그대로 유지했다

`viewIsometric()` + `ViewFit` + `saveImage(1760×1000, White)` 로 재촬영했다. 원본과
콘텐츠 점유율을 비교해 어긋나지 않음을 확인했다 — iso 53%W/56%H (원본 53%W/58%H),
top 51%W/46%H (원본 50%W/46%H). 팜레스트가 검게 나오는 것은 이전부터의 관례이지
이번 회귀가 아니다(원본 스크린샷에서도 동일).

## DoD 결과 (기준선 → 실행 후)

**회귀 가드 — 기준선에서 이미 통과. 통과 유지가 정상이다:**

| # | 검사 | 기준선 | 실행 후 |
| --- | --- | --- | --- |
| 1 | `python3 tools/test_pcb.py` | 통과 (exit 0) | 통과 (exit 0) — 변화 없음 |
| 2 | `python3 tools/verify_keylayout.py` | 통과 (5행 73키) | 통과 — 변화 없음 |
| 3 | `python3 tools/verify_pcb_matrix.py` | 통과 | 통과 — 변화 없음 |
| 4 | `python3 tools/test_gen_dxf.py` | 통과 (편차 0.0006mm) | 통과 — 변화 없음 |
| 5 | `FreeCAD -c verify_magnet_pockets.py` | `All checks passed` | `All checks passed` — 변화 없음 |
| 6 | `python3 freecad/verify_no_support.py` | 4파트 PASS, support 0.0 (bridged 37.6/46.9, bed-tangent 29.0) | 4파트 PASS, support 0.0 (bridged 37.6/46.9, bed-tangent 29.0) — **GUI 재생성 후에도 수치 동일**, 즉 지오메트리는 그대로고 GUI 데이터만 복원됐다 |

**전진 검사 — 계획은 전부 실패를 예상했으나 기준선에서 이미 통과했다:**

| # | 검사 | 계획의 예상 | 기준선 | 실행 후 |
| --- | --- | --- | --- | --- |
| 7 | `FreeCAD -c verify_port_mounts.py` | 파일 없어 실패 | 8/8 PASS | 8/8 PASS (GUI 재생성본 기준 재검증) |
| 8 | `grep -c '^#define MASTER_RIGHT' config.h` | 0 → 1 | 1 | 1 |
| 9 | `grep -c '^#define MASTER_LEFT' config.h` | 1 → 0 | 0 | 0 |
| 10 | `grep -c 'aux_placement\|aux_connectors'` | pcb.py 4 / parametric 2 → 0 | 0 / 0 | 0 / 0 |
| 11 | `grep -c 'Aux_Guide\|AuxStackHeight'` | 6 → 0 | 0 | 0 |
| 12 | `grep -ci 'aux' README.md` | 7 → 0 | 0 | 0 |
| 13 | `grep -c 'MASTER_LEFT' README.md` | 1 → 0 | 0 | 0 |

## 이번 실행이 실제로 바꾼 파일

- `freecad/keyboard_parametric.FCStd` — GUI 재생성. GUI 데이터 복원(엔트리 920개,
  `GuiDocument.xml`·썸네일·`ShapeAppearance` 128개), Aux 오브젝트 0개
- `freecad/parametric_stl/*.stl` (8개) — 재내보내기
- `image/freecad-iso.png`, `image/freecad-top.png` — 재촬영 (1760×1000)

되돌림용 백업: `/tmp/fg-backup-headless-keyboard_parametric.FCStd`,
`/tmp/fg-backup-parametric_stl/`

## 코드 리뷰

수행하지 않았다. 이번 실행의 변경은 생성기 재실행 산출물(FCStd·STL·PNG)뿐이고
손으로 쓴 코드가 없다. 인증·데이터 변경·공개 API·마이그레이션 어디에도 닿지 않는다.

## 남은 것 (계획의 비목표 — 별도 작업)

- `OuterMargin 11.5`·`BodyHeight 14.0` 축소
- `split keyboard.3mf` 갱신 (사용자가 직접)
- `verify_no_support.py` 의 4/8 파트 커버리지 확대
- `fg-merge` 브랜치 forge 통합 + `fg-cleanup` 으로 ADR 260824-003937 은퇴
