"""KLE raw-data 파서.

keyboard-layout-editor.com 의 raw data 는 JSON5 방언이다 — 최상위 대괄호가 없고
객체 키에 따옴표가 없다. 레전드 문자열 안에 이스케이프된 따옴표(`"\"\n'"`)가
들어있어 정규식 치환은 안전하지 않으므로, 문자열 바깥에서만 키를 인용한다.
"""
import json


def _quote_keys(text):
    """문자열 리터럴 바깥의 무인용 객체 키에만 따옴표를 붙인다."""
    out = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < n:      # 이스케이프 시퀀스는 통째로 넘긴다
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch.isalpha():                       # 무인용 키 후보
            j = i
            while j < n and text[j].isalnum():
                j += 1
            if j < n and text[j] == ":":
                out.append('"' + text[i:j] + '"')
                i = j
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def parse(path):
    """KLE raw 파일을 행 리스트로 읽는다. 각 행은 dict(속성)와 str(키)의 리스트."""
    with open(path, encoding="utf-8") as f:
        raw = f.read().strip()
    return json.loads("[" + _quote_keys(raw) + "]")


def keys(row):
    """한 행의 키(문자열 레전드)만 뽑는다."""
    return [item for item in row if isinstance(item, str)]


def row_width(row):
    """한 행의 총 폭(u). 선행 x 오프셋과 각 키의 w 를 누적한다."""
    width = 0.0
    pending_w = 1.0
    for item in row:
        if isinstance(item, dict):
            width += item.get("x", 0)
            if "w" in item:
                pending_w = item["w"]
        else:
            width += pending_w
            pending_w = 1.0
    return width


def leading_x(row):
    """행 맨 앞 속성 객체의 x 오프셋 (없으면 0)."""
    if row and isinstance(row[0], dict):
        return row[0].get("x", 0)
    return 0.0
