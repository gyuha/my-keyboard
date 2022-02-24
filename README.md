# 

내가 원하는 키보드 만들기

# 원하는 기능

- 분할 키보드
- 2개의 Function 키 사용 가능
- 가운데 추가 키 배치

## 

# 키보드 전체 레이아웃

![layout](https://github.com/gyuha/my-keyboard/blob/main/v2/keyboard-layout.png?raw=true)

제작 : http://www.keyboard-layout-editor.com/

## 

# 데이터

키보드 [www.keyboard-layout-editor.com](http://www.keyboard-layout-editor.com) 에서 아래 데이터를 `</> Raw Data` 탭을 선택해서 넣어 주면 키보드의 구성을 편집 할 수 있습니다.

### 좌측

```json
[{c:"#ea4221"},"ESC",{c:"#cccccc"},"`~","!\n1\n\nF1","@\n2\n\nF2","#\n3\n\nF3","$\n4\n\nF4","%\n5\n\nF5"],
[{c:"#63696a"},"PrtSc",{c:"#c8c3b8",w:1.5},"Tab",{c:"#cccccc"},"Q","W","E","R","T"],
[{c:"#63696a"},"F5",{c:"#c8c3b8",w:1.75},"Function.1",{c:"#cccccc"},"A","S","D","F","G"],
[{c:"#63696a"},"Insert",{c:"#c8c3b8",w:2.25},"Shift",{c:"#cccccc"},"Z","X","C","V","B"],
[{c:"#63696a"},"Del",{c:"#c8c3b8",w:1.25},"Ctrl",{w:1.25},"Win",{w:1.25},"Alt",{w:1.25},"Fn.2",{w:2.25},"Space"]
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

![요약](https://github.com/gyuha/my-keyboard/blob/main/v1/keylayout-summary.png?raw=true)



# 부품

| 부품명                                    | 수량  | 설명                        | 링크                                                                                                                   |
| -------------------------------------- | --- | ------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 아두이노 프로 마이크로<br/>Arduino ATmega32U4    | 2   | PC연결 용                    | [연결](https://ko.aliexpress.com/item/1348800135.html?gatewayAdapt=glo2kor&spm=a2g0o.9042311.0.0.7f234c4dRKXC3b)       |
| 스테레오 커넥터 / 3.5mm / FEMALE              | 2   | 보드 연결 용                   | [연결](https://www.devicemart.co.kr/goods/view?no=2679)                                                                |
| 3.5mm aux 케이블                          | 1   | 보드 연결 용                   | [연결](https://www.devicemart.co.kr/goods/view?no=1223097)                                                             |
| USB3.1 C 타입 FEMALE 26P <br/>변환보드 ANGLE | 2   | 보드 연결 용<br/>3.5 aux 대체용   | [연결](https://www.devicemart.co.kr/goods/view?no=13003211)                                                            |
| 전선                                     | 1   | 랩핑와이어 추천(인두기로 녹여서 사용가능)   | [연결](https://www.devicemart.co.kr/goods/view?no=1274107)                                                             |
| 스위치                                    | 77  |                           |                                                                                                                      |
| 키캡                                     |     | 되도록이면 XDA 또는 DSA를 선택 합니다. | [연결](https://ko.aliexpress.com/item/1005003510911114.html?gatewayAdapt=glo2kor&spm=a2g0o.9042311.0.0.bb0d4c4d3XOUd6) |
| 납땜 재료                                  |     | 인두기, 납, 인두기 스탠드 등등        |                                                                                                                      |
| 미끄럼 방지 패드 or 범퍼                        |     |                           | [연결](https://smartstore.naver.com/mg9000/products/3289975643)                                                        |



# 참고 사이트

## 참고 github

## 키보드 레이아웃

* [Keyboard Layout Info](http://kbdlayout.info/) : 키보드의 규격과 레이아웃이 정리 되어 있습니다.

* [Keyboard-Layout-Editor.com](http://www.keyboard-layout-editor.com/) : 키보드의 레이아웃을 구성해 볼 수 있고 사용되는 키의 갯수를 정리해 줍니다.

## 키보드 CAD

- [Keyboard CAD Assistant](http://www.keyboardcad.com/) : 여기서는 바로 STL 도면을 얻을 수 있습니다.

- [Plate Case Builder - swillkb](http://builder.swillkb.com/) : keyboard-layout-editor의 데이터를 이용해서 키보드 하판을 그려 줍니다.
  
  - [svg to stl](http://builder-docs.swillkb.com/pro-tips/#svg-to-stl-conversion) : 사이트에서 받은 svg 파일을 도면 파일로 변경 하는 동영상 설명이 되어 있습니다.# Keyboard CAD Assistant
