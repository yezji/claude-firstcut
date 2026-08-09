#!/usr/bin/env bash
# FirstCut installer / updater
#
# 신규 설치와 최신화(재실행)가 모두 아래 한 줄로 동작합니다:
#   curl -fsSL https://raw.githubusercontent.com/yezji/claude-firstcut/main/install.sh | bash
#
# User-facing echo messages are intentionally Korean (target audience).
set -euo pipefail

REPO="https://github.com/yezji/claude-firstcut"
BRANCH="main"
DEST="${CLAUDE_HOME:-$HOME/.claude}"
SKILLS=(firstcut-fcp firstcut-premiere)
COMMANDS=(firstcut.md firstcut-subs.md)

PREV_VER=""
[ -f "$DEST/skills/.firstcut-version" ] && PREV_VER="$(cat "$DEST/skills/.firstcut-version")"

echo ""
if [ -n "$PREV_VER" ]; then
  echo "🎬 FirstCut(퍼스트컷)을 최신 버전으로 업데이트합니다. (현재 $PREV_VER)"
else
  echo "🎬 FirstCut(퍼스트컷) — 영상 초벌컷 편집기를 설치합니다."
fi
echo ""

# 1) check for Claude Code (skills install regardless; just inform)
if ! command -v claude >/dev/null 2>&1; then
  echo "ℹ️  클로드 코드(claude 명령)가 아직 없는 것 같아요."
  echo "   스킬은 설치해 둘 테니, 클로드 코드는 나중에 여기서 설치하세요:"
  echo "   https://claude.com/claude-code"
  echo ""
fi

# 2) download the latest source
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "📦 FirstCut 최신 버전을 받는 중…"
if command -v git >/dev/null 2>&1; then
  git clone --depth 1 --branch "$BRANCH" "$REPO" "$TMP/src" >/dev/null 2>&1
else
  curl -fsSL "$REPO/archive/refs/heads/$BRANCH.tar.gz" | tar -xz -C "$TMP"
  mv "$TMP"/claude-firstcut-* "$TMP/src"
fi

SRC="$TMP/src"
[ -f "$SRC/skills/firstcut-fcp/SKILL.md" ] || { echo "❌ 내려받은 파일이 올바르지 않습니다."; exit 1; }

mkdir -p "$DEST/skills" "$DEST/commands"

# 스킬: 기존 폴더를 지우고 새로 복사 (삭제된 파일이 남지 않도록)
for s in "${SKILLS[@]}"; do
  rm -rf "${DEST:?}/skills/$s"
  cp -R "$SRC/skills/$s" "$DEST/skills/$s"
  echo "  ✔ skills/$s"
done

# 슬래시 명령어: 덮어쓰기
for c in "${COMMANDS[@]}"; do
  cp -f "$SRC/commands/$c" "$DEST/commands/$c"
  echo "  ✔ commands/$c"
done

VER="$( (cd "$SRC" && git rev-parse --short HEAD) 2>/dev/null || date +%Y%m%d )"
printf '%s\n' "$VER" > "$DEST/skills/.firstcut-version"

# 3) check ffmpeg (needed for media analysis)
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo ""
  echo "⚙️  영상 분석 도구(ffmpeg)가 필요해서 설치를 시도합니다..."
  case "$(uname -s)" in
    Darwin)
      if command -v brew >/dev/null 2>&1; then
        brew install ffmpeg && echo "   ✓ ffmpeg 설치 완료" || \
          echo "   ⚠ 자동 설치 실패. 클로드에게 'ffmpeg 설치해줘'라고 부탁하면 됩니다."
      else
        echo "   ⚠ 지금은 넘어갈게요. 클로드 코드에서 'ffmpeg 설치해줘'라고"
        echo "     부탁하면 클로드가 알아서 설치해 줍니다."
      fi ;;
    *)
      echo "   ⚠ 지금은 넘어갈게요. 클로드 코드에서 'ffmpeg 설치해줘'라고"
      echo "     부탁하면 클로드가 알아서 설치해 줍니다." ;;
  esac
fi

echo ""
if [ -n "$PREV_VER" ] && [ "$PREV_VER" = "$VER" ]; then
  echo "✅ 이미 최신 상태입니다! (버전 $VER)"
elif [ -n "$PREV_VER" ]; then
  echo "✅ 업데이트가 끝났습니다! ($PREV_VER → $VER)"
else
  echo "✅ 설치가 끝났습니다! (버전 $VER)"
fi
echo "   이미 클로드 코드가 켜져 있다면, 껐다 다시 켜야 새 버전이 적용됩니다."
echo ""
echo "사용법: 클로드 코드를 열고 아래를 입력하세요."
echo ""
echo "   /firstcut"
echo ""
echo "클로드가 편집 프로그램과 영상 폴더를 물어보고, 나머지는 알아서 진행합니다."
