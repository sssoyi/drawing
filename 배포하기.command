#!/bin/bash
# 더블클릭하면 페이지를 새로 만들고 인터넷에 올립니다. (1~2분 뒤 반영)
cd "$(dirname "$0")" || exit 1

echo "1) 페이지 만드는 중…"
python3 만들기.py || { echo "실패했어요."; read -n 1 -s; exit 1; }

echo
echo "2) 올리는 중…"
git add -A
if git diff --cached --quiet; then
  echo "   바뀐 게 없어요. 그대로 둡니다."
else
  git commit -q -m "도안 업데이트 $(date '+%Y-%m-%d %H:%M')"
  git push -q origin main || { echo "   업로드 실패. 인터넷 연결을 확인해주세요."; read -n 1 -s; exit 1; }
  echo "   올렸습니다."
fi

echo
echo "완료! 1~2분 뒤 아래 주소에 반영됩니다."
echo "https://sssoyi.github.io/luckymommy-doan/"
echo
echo "이 창은 닫으셔도 됩니다."
