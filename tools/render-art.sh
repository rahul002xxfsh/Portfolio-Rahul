#!/bin/zsh
# Re-renders assets/art/* from tools/art.html using headless Chrome.
cd "$(dirname "$0")/.."
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TMP=$(mktemp -d)
render(){ # scene width height
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --default-background-color=00000000 \
    --user-data-dir="$TMP/profile" --window-size=$2,$3 --virtual-time-budget=4000 \
    --screenshot="$TMP/$1.png" "file://$PWD/tools/art.html#$1" >/dev/null 2>&1
  if [[ $1 == portrait ]]; then cp "$TMP/$1.png" "assets/art/$1.png"
  else sips -s format jpeg -s formatOptions 84 "$TMP/$1.png" --out "assets/art/$1.jpg" >/dev/null; fi
}
render city 1800 1100; render clay 1800 1100; render office 1200 640
render trailer 1200 640; render reel 1200 760; render portrait 1200 1400
rm -rf "$TMP"; ls -la assets/art
