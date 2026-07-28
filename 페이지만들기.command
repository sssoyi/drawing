#!/bin/bash
# 더블클릭하면 공유페이지.html 을 새로 만듭니다.
cd "$(dirname "$0")" || exit 1
echo "도안 페이지를 만드는 중…"
echo
python3 만들기.py || { echo; echo "오류가 났어요. 위 메시지를 확인해주세요."; read -n 1 -s; exit 1; }
echo
open index.html
echo "브라우저에서 열었습니다. 이 창은 닫으셔도 됩니다."
