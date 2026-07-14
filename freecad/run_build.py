"""freecadcmd 헤드리스 러너: 좌·우 전체 빌드 + export."""
import sys
sys.path.insert(0, '/Users/gyuha/workspace/my-keyboard/freecad')
import create_switch_plate as csp
csp.build_all(export=True)
