# 하단 body 외곽선은 plate가 아니라 PCB 외곽선을 기준으로 도출한다

하단 케이스(body)의 외벽 외곽선을 상판(plate) 외곽선이 아니라 **PCB 외곽선**에서 도출한다. 실측 결과 plate 외곽이 PCB 외곽보다 각 변 약 1.43mm 크지만, 벽 두께 3mm 기준으로 body 외벽을 plate 외곽선에 맞추면 내부 공동(plate−6mm)이 PCB보다 각 변 ~1.6mm 좁아 **PCB가 물리적으로 들어가지 않는다**(우: PCB 198.6 vs 내부 195.5, 좌: 146.2 vs 143.1). 따라서 외벽 = PCB 외곽 + (벽 3mm + 여유 0.4mm)을 각 변에 적용하고, 코너는 R5 둥근 사각으로 만든다.

## Considered Options

- **body 외곽 = plate 외곽, PCB 영역 벽만 국부 축소(<3mm)**: "벽 3mm" 요구와 상충하고 벽 강도가 약해짐. 기각.
- **벽 두께 자체를 축소(예: 1.5mm)해 body=plate 크기 유지**: "벽 3mm" 요구 위반. 기각.
- **body 외곽 = PCB 외곽 + 벽 + 여유 (채택)**: 벽 3mm를 유지하면서 PCB가 확실히 들어감. body가 plate보다 각 변 ~2mm 커지지만(작은 베젤) 감수.

## Consequences

- body가 plate보다 각 변 ~2mm 크다. 상판은 body 상단 안쪽 lip 단턱에 recess시켜 윗면을 벽 상단과 flush로 맞춘다(총 높이 17mm 유지).
- body 외곽 코너는 R5(plate와 동일 계열). PCB 외곽 코너(R3)와는 별개.
- 향후 벽 두께나 PCB 외곽이 바뀌면 body 외곽을 재도출해야 한다.
- 상판↔PCB↔body 코너 정렬은 [[코너 고정 홀]]을 공유해 한 축으로 유지된다(ADR-0001 원천 좌표계 기준).
