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
["~\n`","!\n1","@\n2","#\n3","$\n4","%\n5",{x:3},"^\n6","&\n7","*\n8","(\n9",")\n0","_\n-","+\n=",{w:2},"Backspace","Home"],
[{w:1.5},"Tab","Q","W","E","R","T",{x:3},"Y","U","I","O","P","{\n[","}\n]",{w:1.5},"|\n\\","End"],
[{w:1.75},"Caps Lock","A","S","D","F","G",{x:3},"H","J","K","L",":\n;","\"\n'",{w:2.25},"Enter","PgUp"],
[{w:2.25},"Shift","Z","X","C","V","B",{x:2,c:"#ffe08d"},"B",{c:"#cccccc"},"N","M","<\n,",">\n.","?\n/",{w:1.75},"Shift",{a:7},"↑",{a:4},"PgDn"],
[{w:1.25},"Ctrl",{w:1.25},"Win",{w:1.25},"Alt",{w:1.25},"Fn1",{w:2.25},"Space",{x:2,c:"#ffe08d"},"한/영",{c:"#cccccc",w:2.75},"Space","Fn1","Fn2","Del",{a:7},"←","↓","→"]
```

## 써머리
![요약](https://github.com/gyuha/my-keyboard/blob/main/keylayout/keylayout-summary.png?raw=true)
