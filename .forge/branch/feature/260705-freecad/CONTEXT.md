# keyboard-plate (분할 키보드 케이스)

3D 프린팅용 분할 키보드 케이스. 현재 활성 모델은 FreeCAD 파라메트릭 스크립트(`freecad/create_keyboard_plates.py`)가 생성한다. Fusion 360 모델(keyboard-plate v9)은 이전 세대 작업물이다.

## Language

**keyboard-plate**:
Fusion 문서의 최상위 컴포넌트 이름. 이름은 "plate"지만 실제로는 좌우 케이스 전체 조립을 담는 컨테이너다.
_Avoid_: 상판(상판은 Plate)

**Body (바디)**:
좌우 케이스 하부 tub — 바닥판 + 벽체 + 내부 부품 마운트가 일체인 부분. `LeftBody` / `RightBody`.
_Avoid_: 케이스, 하판

**Plate (상판)**:
스위치가 안착하는 윗판. `LeftPlate` / `RightPlate`.
_Avoid_: 커버, 뚜껑

**부품 받침 (Part mount)**:
Body 바닥에서 RP2040 보드·TRRS 소켓 등 부품이 안착·정렬되는 자리. 형태는 모델 세대에 따라 다르다 — Fusion 모델에서는 돌출 패드+정렬 리브, 현행 FreeCAD 모델에서는 바닥을 파낸 리세스 시트. [[뒷변 받침]]과 구분된다.
_Avoid_: 포스트, 스탠드오프

**뒷변 받침 (Rear-edge mount)**:
Body 뒷벽에 인접해 부품 뒷단(USB-C 커넥터 쪽)을 받치는 돌기.
_Avoid_: 뒷벽 돌기

**부품 노출 홀 (Port cutout)**:
뒷벽을 관통해 USB-C·TRRS 커넥터가 외부로 드러나는 개구부.
_Avoid_: 포트 홀
