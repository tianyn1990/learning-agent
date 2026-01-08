#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

recreate="${1:-}"

if [[ "$recreate" == "--recreate" ]]; then
  rm -rf .venv
fi

if [[ -d ".venv" ]]; then
  echo "已存在 .venv；如需重建请运行: bash ./scripts/bootstrap_venv.sh --recreate"
  exit 0
fi

arch_cmd=()
if [[ "$(uname -s)" == "Darwin" ]]; then
  # Prefer native arm64 on Apple Silicon hardware to avoid wheel-arch mismatch.
  if sysctl -n hw.optional.arm64 >/dev/null 2>&1 && [[ "$(sysctl -n hw.optional.arm64)" == "1" ]]; then
    arch_cmd=(arch -arm64)
  fi
fi

"${arch_cmd[@]}" python3 -m venv .venv

current_machine="$("$ROOT_DIR/.venv/bin/python" -c 'import platform; print(platform.machine())')"
target_machine="$("${arch_cmd[@]}" "$ROOT_DIR/.venv/bin/python" -c 'import platform; print(platform.machine())')"
echo "Python (current shell): ${current_machine}"
echo "Python (target install): ${target_machine}"

"${arch_cmd[@]}" "$ROOT_DIR/.venv/bin/python" -m pip install -U pip
"${arch_cmd[@]}" "$ROOT_DIR/.venv/bin/python" -m pip install -r requirements.txt
"${arch_cmd[@]}" "$ROOT_DIR/.venv/bin/python" -m pip install -e .

echo "完成。请在当前 shell 中执行: source .venv/bin/activate"
