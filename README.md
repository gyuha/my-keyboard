# my-keyboard

내가 원하는 키보드 만들기

## 원하는 기능

- 분할 키보드
- 2개의 Function 키 사용 가능
- 가운데 추가 키 배치 (가운데 키는 분할이 가능 하면 좋을 것 같다)

## 키보드 레이아웃

![layout](https://github.com/gyuha/my-keyboard/blob/main/keylayout/keyboard-layout.png?raw=true)

참고 : http://www.keyboard-layout-editor.com/

## 데이터

```json
["Esc\n\n\n`~","!\n1\n\nF1","@\n2\n\nF2","#\n3\n\nF3","$\n4\n\nF4","%\n5\n\nF5",{x:3},"^\n6\n\nF6","&\n7\n\nF7","*\n8\n\nF8","(\n9\n\nF9",")\n0\n\nF10","_\n-\n\nF11","+\n=\n\nF12",{w:2},"Backspace","Home"],
[{w:1.5},"Tab","Q","W","E","R","T",{x:3},"Y","U","I","O","P","{\n[","}\n]",{w:1.5},"|\n\\","End"],
[{w:1.75},"Function.1","A","S","D","F","G",{x:3},"H","J","K","L",":\n;","\"\n'",{w:2.25},"Enter","PgUp"],
[{w:2.25},"Shift","Z","X","C","V","B",{x:2,c:"#ffe08d"},"B",{c:"#cccccc"},"N","M","<\n,",">\n.","?\n/",{w:1.75},"Shift",{a:7},"↑",{a:4},"PgDn"],
[{w:1.25},"Ctrl",{w:1.25},"Win",{w:1.25},"Alt",{w:1.25},"Fn.2",{w:2.25},"Space",{x:2,c:"#ffe08d"},"한/영",{c:"#cccccc",w:2.75},"Space","Alt","Fn.1","Del",{a:7},"←","↓","→"]
```

## 써머리

![요약](https://github.com/gyuha/my-keyboard/blob/main/keylayout/keylayout-summary.png?raw=true)



# 참고 사이트

* [Keyboard Layout Info](http://kbdlayout.info/) : 키보드의 규격과 레이아웃이 정리 되어 있다.

* [Keyboard-Layout-Editor.com](http://www.keyboard-layout-editor.com/) : 키보드의 레이아웃을 구성해 볼 수 있고 사용되는 키의 갯수를 정리해 준다.

* http://builder.swillkb.com/ : keyboard-layout-editor의 데이터를 이용해서 키보드 하판을 그려 준다.
