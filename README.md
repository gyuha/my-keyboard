내가 원하는 키보드 만들기

# 원하는 기능

- 분할 키보드
- 2개의 Function 키 사용 가능
- 가운데 추가 키 배치

## 

# 키보드 전체 레이아웃

![layout](image/keyboard-layout.png?raw=true)

제작 : http://www.keyboard-layout-editor.com/

## 

#### 제작 화면

![keyboard](https://github.com/gyuha/my-keyboard/blob/main/image/keyboard.jpg?raw=true)

# 데이터

키보드 [www.keyboard-layout-editor.com](http://www.keyboard-layout-editor.com) 에서 아래 데이터를 `</> Raw Data` 탭을 선택해서 넣어 주면 키보드의 구성을 편집 할 수 있습니다.

### 좌측

```json
[{c:"#ea4221"},"ESC",{c:"#cccccc"},"!\n1\n\nF1","@\n2\n\nF2","#\n3\n\nF3","$\n4\n\nF4","%\n5\n\nF5","^\n6\n\nF6"],
[{c:"#c8c3b8",w:1.5},"Tab",{c:"#cccccc"},"Q","W","E","R","T"],
[{c:"#c8c3b8",w:1.75},"Function.1",{c:"#cccccc"},"A","S","D","F","G"],
[{c:"#c8c3b8",w:2.25},"Shift",{c:"#cccccc"},"Z","X","C","V","B"],
[{c:"#c8c3b8",w:1.25},"Ctrl",{w:1.25},"Win",{w:1.25},"Alt",{w:1.25},"Fn.2",{w:2.25},"Space"]
```

### 우측

```json
["^\n6\n\nF6","&\n7\n\nF7","*\n8\n\nF8","(\n9\n\nF9",")\n0\n\nF10","_\n-\n\nF11","+\n=\n\nF12",{c:"#c8c3b8",w:2},"Backspace",{c:"#63696a"},"Home"],
[{x:0.5,c:"#cccccc"},"Y","U","I","O","P","{\n[","}\n]",{c:"#c8c3b8",w:1.5},"|\n\\",{c:"#63696a"},"End"],
[{x:0.75,c:"#cccccc"},"H","J","K","L",":\n;","\"\n'",{c:"#c8c3b8",w:2.25},"Enter",{c:"#63696a"},"PgUp"],
[{x:0.25,c:"#ffe08d"},"B",{c:"#cccccc"},"N","M","<\n,",">\n.","?\n/",{c:"#c8c3b8",w:1.75},"Shift",{c:"#ea4221",a:7},"↑",{c:"#63696a",a:4},"PgDn"],
[{x:0.25,c:"#ffe08d"},"한/영",{c:"#c8c3b8",w:2.75},"Space","Alt","Fn.1","Del",{c:"#ea4221",a:7},"←","↓","→"]
```

# 써머리

![요약](image/keylayout-summary.png?raw=true)

# 준비물

| 부품명                                    | 수량  | 설명                        | 링크                                                                                                                   |
| -------------------------------------- | --- | ------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| RP2040-Zero RP2040 | 2 | 보드용 | [연결](https://ko.aliexpress.com/item/1005003823256706.html) |
| 스테레오 커넥터 / 3.5mm / FEMALE              | 2   | 보드 연결 용                   | [연결](https://www.devicemart.co.kr/goods/view?no=1067728)                                                             |
| 3.5mm aux 케이블                          | 1   | 보드 연결 용, 다이소에서 구매         |                                                                                                                      |
| USB3.1 C 타입 FEMALE 26P <br/>변환보드 ANGLE | 2   | 보드 연결 용<br/>3.5 aux 대체용   | [연결](https://www.devicemart.co.kr/goods/view?no=13003211)                                                            |
| 체리 스테빌 라이저                             | 2   |                           | [연결](https://smartstore.naver.com/whatkey/products/5153072093)                                                       |
| 전선                                     | 1   | 랩핑와이어 추천(인두기로 녹여서 사용가능)   | [연결](https://www.devicemart.co.kr/goods/view?no=1274107)                                                             |
| 스위치                                    | 77  | 개인 취향으로 게이트론 백축을 선택 했습니다. | [연결](https://smartstore.naver.com/happysaturday/products/5541876955)                                                 |
| 키캡                                     | -   | 되도록이면 XDA 또는 DSA를 선택 합니다. | [연결](https://ko.aliexpress.com/item/1005003510911114.html?gatewayAdapt=glo2kor&spm=a2g0o.9042311.0.0.bb0d4c4d3XOUd6) |
| Gateron Hot-swappable PCB Socket       | 77  | 스위치 핫 스왓 용                | [연결](https://ko.aliexpress.com/item/1005002637150446.html)                                                           |
| 납땜 재료                                  | -   | 인두기, 납, 인두기 스탠드 등등        |                                                                                                                      |
| 미끄럼 방지 패드 or 범퍼                        |     |                           | [연결](https://www.coupang.com/vp/products/6265639245)                                                                 |
| 다이오드(1N4148)                           | 77  |                           | [연결](https://www.devicemart.co.kr/goods/view?no=25)                                                                  |
| 접시머리 십자볼트 (니켈) 머신스크류 M3*10             | 32  |                           | [연결](https://www.devicemart.co.kr/goods/view?no=34782)                                                               |
| 스위치                                    | 2   | 펌웨어 업데이트용 리세 스위치          | [연결](https://www.devicemart.co.kr/goods/view?no=34555)                                                               |



### 프로마이크로 핀

![PIN](https://github.com/gyuha/my-keyboard/raw/main/kbfirmware/pin.png?raw=true)

### 좌측

![left](https://github.com/gyuha/my-keyboard/raw/main/kbfirmware/left.png?raw=true)

### 우측

![우측](https://github.com/gyuha/my-keyboard/raw/main/kbfirmware/right.png?raw=true)

핀 배선은 [kbfirmware.com](https://kbfirmware.com/) 에서 만들었습니다.

# 스트레오 컨넥트 연결 핀

![핀](https://github.com/gyuha/my-keyboard/blob/main/image/stero%20connect%20ping.png?raw=true)

# QMK

## 소스 연결 하기

qmk를 설치하고 나면 qmk_firmware라는 폴더가 생기고, 그 안에 있는 `keyboards` 폴더에 소스 파일을 넣어 주고 컴파일을 해야 합니다.
저 같은 경우에는 폴더를 symbolic link를 걸어서 넣어 줬습니다.

```bash
ln -snf $HOME/qmk_firmware/keyboards/gkey `pwd`/gkey
```

## 컴파일 하기

```bash
qmk compile -kb gkey -km default
```

컴파일 한 output 파일은 `$HOME/qmk_firmware/.build` 폴더에 복사 됩니다.

`gkey_default.hex` 파일을 QMK Toolbox를 이용해서  아두이노에 넣어 주시면 됩니다.

아두이도 프로 마이크로의 펌웨어를 업데이트 하기 전에는 보드의 `리셋(13)`과 `그라운드(GND)`를 같이 눌러주고 펌웨어를 올리시면 됩니다.

여기까지 했으면 조립해서 사용하시면 됩니다.

# 참고 사이트

## 종합
* **[Mechanical Keyboard and where to find them](https://github.com/help-14/mechanical-keyboard)** : 다양한 DIY 키보드 링크

## 참고 github

* [GitHub - mastery6/wingB_Korean-Split-keyboard](https://github.com/mastery6/wingB_Korean-Split-keyboard) : 참고를 가장 많이한 저장소 입니다. 감사합니다.

## 키보드 레이아웃

* [Keyboard Layout Info](http://kbdlayout.info/) : 키보드의 규격과 레이아웃이 정리 되어 있습니다.

* [Keyboard-Layout-Editor.com](http://www.keyboard-layout-editor.com/) : 키보드의 레이아웃을 구성해 볼 수 있고 사용되는 키의 갯수를 정리해 줍니다.

## 키보드 CAD

- [Keyboard CAD Assistant](http://www.keyboardcad.com/) : 여기서는 바로 STL 도면을 얻을 수 있습니다.

- [Plate Case Builder - swillkb](http://builder.swillkb.com/) : keyboard-layout-editor의 데이터를 이용해서 키보드 하판을 그려 줍니다.
  
  - [svg to stl](http://builder-docs.swillkb.com/pro-tips/#svg-to-stl-conversion) : 사이트에서 받은 svg 파일을 도면 파일로 변경 하는 동영상 설명이 되어 있습니다.# Keyboard CAD Assistant

- [ai03 Plate Generator](https://kbplate.ai03.com/) : 단순하지만 실시간 반영이 됨
- [Keyboard Plate Generator by Keebio](https://plate.keeb.io/)

## QMK

* [QMK Logo QMK Firmware](https://qmk.fm/)

* [QMK  키코드](https://docs.qmk.fm/#/keycodes)

* [QMK Toolbox download](https://github.com/qmk/qmk_toolbox/releases)

* [세상에서 제일 쉬운 QMK 사용법 - YouTube](https://www.youtube.com/c/TeleV2/search?query=qmk)

* [Keyboard Firmware Builder](https://kbfirmware.com/)

## 온라인 강좌

### PCB
* [자작 키보드 PCB 기판 설계 시 참고하면 좋은 자료들](https://gura7060.tistory.com/2) : PCB 관련 링크가 잘 정리 되어 있음.
* PCB 기판 제작
  * [PCB 기판 제작(1)](https://ola-page.tistory.com/13?category=888576) PCB란? PCB 관련 용어, 개념 소개. Easy EDA 툴 소개
  * [PCB 기판 제작(2)](https://ola-page.tistory.com/14?category=888576) 회로도 기호. 칩 타입 부품의 사이즈, 용량 표기법
  * [PCB 기판 제작(3)](https://ola-page.tistory.com/15?category=888576) 회로도 그리기. 부품 검색 및 불러오기
  * [PCB 기판 제작(4)](https://ola-page.tistory.com/16?category=888576) 회로도를 아트웍으로 변환하기. 부품 배치 및 오토라우팅
  * [PCB 기판 제작(5)](https://ola-page.tistory.com/17?category=888576) PCB 아트웍에서 주의할 점. 아트웍 수정하기.
  * [PCB 기판 제작(6)](https://ola-page.tistory.com/27) 거버파일 추출하기. PCB 주문하기.
* [ai03's Keyboard PCB Design Guide](https://wiki.ai03.com/books/pcb-design/page/pcb-guide-part-1---preparations#bkmrk-ai03%27s-keyboard-pcb-) : PCB 키보드 기판 제작에서 유명한 사이트, 그대로 만드는건 추천하지 않음
* [Noah Kiser](https://www.youtube.com/channel/UC45VUrCGJStbkWobT0FMTVA) : PCB 키보드 제작 유투브
* olothy 40 플랭크배열 키보드 :  [#1 기판 설계](https://kbddiary.tistory.com/64), [#2 하우징](https://kbddiary.tistory.com/65), [#3 출력물](https://kbddiary.tistory.com/67), [#4 RP2040](https://kbddiary.tistory.com/68)

### EasyEDA
* [EasyEDA Tutorial](https://docs.easyeda.com/en/PCB/Board-Outline/index.html) : 공식 튜토리얼
* Seoul Workshop EasyEDA study 모임: [D1](https://youtu.be/iccL90Sumq0?si=wwP8hzIaCHO0lw5Z), [D2](https://www.youtube.com/watch?v=-fAiftZiQZ0), [D3](https://www.youtube.com/watch?v=gJiEe28L_og), [D4](https://www.youtube.com/watch?v=qRYwaHenh9w), [D5](https://www.youtube.com/watch?v=dFWP4ezcN6w)


### 제작

* [기계식키보드 마이너 갤러리 도움말 - Google Sheets](https://docs.google.com/spreadsheets/d/1DJDHeYMjaFfE15rE-lezlNs-_lD4InzRbwcVyTJKrkc/edit#gid=986385303)

* [스압) 맨땅에서 키보드 만드는 제작기 - 기계식키보드 갤러리](https://gall.dcinside.com/mgallery/board/view?id=mechanicalkeyboard&no=830197)

* 풀와이어링 키보드 제작 가이드 - 기계식키보드 갤러리
  
  * [4. 다이오드 및 행 연결](https://gall.dcinside.com/mgallery/board/view?id=mechanicalkeyboard&no=395243)
  
  * [6. 각 행과 열을 컨트롤러 핀에 연결하기](https://gall.dcinside.com/mgallery/board/view?id=mechanicalkeyboard&no=395287)

* Teensy 2.0에 qmk 올리기 : 
  * [1부](https://gall.dcinside.com/mechanicalkeyboard/395303)
  * [2부](https://gall.dcinside.com/mechanicalkeyboard/395319)

### QMK
* QMK 노브,, OLED 생초보자 가이드: 기계식키보드 갤러리
  
  * [4. QMK 파일설명](https://gall.dcinside.com/mgallery/board/view/?id=mechanicalkeyboard&no=622220)
  
  * [5. QMK 새프로젝트](https://gall.dcinside.com/mgallery/board/view/?id=mechanicalkeyboard&no=624502)
  
  * [6. QMK rules.mk](https://gall.dcinside.com/mgallery/board/view/?id=mechanicalkeyboard&no=624556)
  
  * [7. QMK c와 h](https://gall.dcinside.com/mgallery/board/view/?id=mechanicalkeyboard&no=624636)
  
  * [8. QMK config.h](https://gall.dcinside.com/mgallery/board/view/?id=mechanicalkeyboard&no=624668)
  
  * [9. QMK keymap.c](https://gall.dcinside.com/mgallery/board/view/?id=mechanicalkeyboard&no=625890)
  
  * [10. QMK 컴파일](https://gall.dcinside.com/mgallery/board/view/?id=mechanicalkeyboard&no=625963)

* 아두이노로 키보드 만들기 
  * [1부](http://www.kbdmania.net/xe/best_article/8635141)
  * [2부](http://www.kbdmania.net/xe/best_article/8639304)
  * [3부](http://www.kbdmania.net/xe/best_article/8640469)

### 3D Printer
* [3D프린터만으로 풀와이어링 기계식키보드 직접 만들기](https://www.youtube.com/watch?v=bxcL0NbGioA)
  * https://www.thingiverse.com/thing:4929989

### 기타
* [자작 키보드 디스코드 채널](https://discord.com/invite/8sUwcKzFa5)
* [마우저(부품 사양, 가격 확인)](https://www.mouser.kr/)
* [CNC 비용 줄이기 TIP](https://www.hubs.com/knowledge-base/reducing-cnc-machining-costs-design-tips/)

<br/>

# 참고 자료
* [RP2040 datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
