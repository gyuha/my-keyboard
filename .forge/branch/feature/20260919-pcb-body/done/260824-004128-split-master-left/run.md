# run — PC 연결 반쪽을 좌측으로 (MASTER_LEFT)

## 슬라이스별 결과

- S1 `MASTER_RIGHT` → `MASTER_LEFT` — ✅ 계획대로. 근거 ADR 을 가리키는 주석을 함께 남겼다.
- S2 `gkey/config.h` BOOTMAGIC 주석 정정 — ✅ 계획대로. 값(`0,0` / `5,0`)은 그대로 두고 근거만 뒤집었다. `_RIGHT` 쌍의 `(5,0)` 설명도 "우측 7"에서 "우측 최상단 6"으로 고쳤다 — 2of4 에서 그 자리에 새 키가 들어왔기 때문이다.
- S3 빌드 + `firmware/gkey_default.uf2` 갱신 — ✅ 계획대로. `645b3be2… → d14c6898…`.

## Plan vs actual

계획한 3개 슬라이스가 그대로 들어갔고 Non-goals(케이스·README·키맵·배열·핀 미변경)를 지켰다. 발산 없음.

이 작업 자체가 계획에 없던 작업이다 — 1of4 가 좌우 aux 비대칭을 찾아내면서 3of4 의 S8 이 우측에서 성립하지 않는다는 것이 드러났고, 그 해결이 펌웨어 한 줄이었기 때문이다. 2of4 가 이미 봉인돼 있어 펌웨어 변경을 거기에 얹을 수 없으므로 별도 작업으로 갈랐다.

## DoD baseline → after

1. `MASTER_LEFT`/`MASTER_RIGHT` 정의 수 — `0 / 1` → **`1 / 0`**
2. `qmk compile -kb gkey -km default` — exit 0 → **exit 0** (회귀 방지, 불변이 기대 결과)
3. `verify_pcb_matrix.py` · `verify_keylayout.py` — 둘 다 exit 0 → **둘 다 exit 0** (회귀 방지)
4. `firmware/gkey_default.uf2` — `645b3be2ae978878f1a9bd6b988a0e35` → **`d14c68988e484baf750e4e648f5aa970`**, 빌드 산출물과 바이트 일치
