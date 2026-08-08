#!/usr/bin/env bash
# FirstCut one-line installer
#
# End users paste exactly one line into their terminal:
#   curl -fsSL https://raw.githubusercontent.com/yezji/claude-firstcut/main/install.sh | bash
#
# NOTE: after creating the repo, replace REPO below with your GitHub id.
# User-facing echo messages are intentionally Korean (target audience).
set -e

REPO="yezji/claude-firstcut"
BRANCH="main"
DEST="$HOME/.claude/skills"

echo ""
echo "🎬 FirstCut(퍼스트컷) — 영상 초벌컷 편집기를 설치합니다."
echo ""

# 1) check for Claude Code (skills install regardless; just inform)
if ! command -v claude >/dev/null 2>&1; then
  echo "ℹ️  클로드 코드(claude 명령)가 아직 없는 것 같아요."
  echo "   스킬은 설치해 둘 테니, 클로드 코드는 나중에 여기서 설치하세요:"
  echo "   https://claude.com/claude-code"
  echo ""
fi

# 2) download and install skills
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
echo "⬇️  스킬을 내려받는 중..."
curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" | tar -xz -C "$TMP"

SRC="$(find "$TMP" -maxdepth 2 -type d -name skills | head -1)"
if [ -z "$SRC" ]; then
  echo "❌ 다운로드에 실패했습니다. install.sh 상단의 REPO 주소를 확인하세요."
  exit 1
fi

mkdir -p "$DEST"
for skill_dir in "$SRC"/*/; do
  name="$(basename "$skill_dir")"
  rm -rf "${DEST:?}/$name"
  cp -r "$skill_dir" "$DEST/$name"
  echo "   ✓ $name 스킬 설치 완료"
done

# install /firstcut commands
CMD_SRC="$(dirname "$SRC")/commands"
if [ -d "$CMD_SRC" ]; then
  mkdir -p "$HOME/.claude/commands"
  cp "$CMD_SRC"/*.md "$HOME/.claude/commands/"
  echo "   ✓ /firstcut 명령 설치 완료"
fi

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
echo "✅ 설치가 끝났습니다!"
echo ""
echo "사용법: 클로드 코드를 열고 아래를 입력하세요."
echo ""
echo "   /firstcut"
echo ""
echo "클로드가 편집 프로그램과 영상 폴더를 물어보고, 나머지는 알아서 진행합니다."
