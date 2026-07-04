# 웹툴 STL·대화형 조작 대신 파라메트릭 FreeCAD Python 스크립트로 케이스를 생성한다

`draw-dxf/`에 이미 keyboardcad.com에서 뽑은 v3 STL(switch·body·palm-rest)이 있고 FreeCAD MCP로 대화형 조작도 가능하지만, `add-function` 레이아웃을 반복 수정·재출력할 수 있어야 하므로 DXF를 입력으로 받아 상판·바디·하판을 생성하고 STL까지 내보내는 **커밋된 FreeCAD Python 스크립트**를 원천으로 삼는다. 두께·오프셋·틸트 등을 변수로 노출해 값만 바꿔 재생성하며, 결과 지오메트리는 스크립트로 검증한다. MCP는 실행 결과를 GUI로 시각화하는 보조 수단으로만 쓴다(웹툴 STL은 편집 불가, 대화형 조작은 .FCStd에만 상태가 남아 재현이 어렵다는 트레이드오프를 택하지 않는다).

## Consequences

- 실행에는 FreeCAD가 필요하다. MCP RPC가 켜져 있으면 `execute_code`로 GUI에 실시간 반영, 꺼져 있으면 `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD`로 헤드리스 실행한다. (현재 freecad-mcp RPC는 미연결 상태 — FreeCAD 실행 + RPC 애드온 시작이 시각화 전제조건.)
