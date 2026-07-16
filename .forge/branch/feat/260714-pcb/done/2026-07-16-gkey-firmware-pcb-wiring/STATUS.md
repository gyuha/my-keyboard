# STATUS — gkey 펌웨어를 v3 PCB 스키마 배선에 맞춰 업데이트
slug: gkey-firmware-pcb-wiring
status: done
executed: 2026-07-16
completed: 2026-07-16
verified: yes (qmk compile -kb gkey -km default → gkey_default.uf2 83968B; 정합성: keyboard.json·gkey.h·via.json·keymap.c 3레이어 전부 73셀·매트릭스 10×9 완전 일치·중복0. 단 실물 하드웨어 검증은 미실시 — run.md 발산 #3 시리얼 크로싱 확인 필요)
retro: skipped (fg-next all 자동 진행 — 학습은 run.md, 승급은 추후 fg-learn)
docs updated: ADR 260716-15a; CONTEXT.md 펌웨어 용어(배선 원천·키 매트릭스·ROW/COL 넷·시리얼 배선·가운데 B/한영키)
