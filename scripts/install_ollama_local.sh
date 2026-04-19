#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${OLLAMA_INSTALL_DIR:-$ROOT_DIR/tools/ollama}"
ARCHIVE_URL="${OLLAMA_ARCHIVE_URL:-https://ollama.com/download/ollama-linux-amd64.tar.zst}"
FORCE="${1:-}"

mkdir -p "$INSTALL_DIR"

if [[ -x "$INSTALL_DIR/bin/ollama" && "$FORCE" != "--force" ]]; then
  echo "Ollama already installed at $INSTALL_DIR"
  exit 0
fi

for tool in curl tar zstd; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing required tool: $tool" >&2
    exit 1
  fi
done

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

archive_path="$tmp_dir/ollama.tar.zst"
echo "Downloading Ollama archive from $ARCHIVE_URL"
curl --fail --show-error --location "$ARCHIVE_URL" -o "$archive_path"
rm -rf "$INSTALL_DIR/bin" "$INSTALL_DIR/lib"
mkdir -p "$INSTALL_DIR"
zstd -d -c "$archive_path" | tar -xf - -C "$INSTALL_DIR"

echo "Installed Ollama under $INSTALL_DIR"
echo "Binary: $INSTALL_DIR/bin/ollama"
