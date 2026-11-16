#!/bin/sh
# Install the PCDD command-line tool.
#
#   curl -fsSL https://pcdd.dev/install.sh | sh
#
# Installs uv (https://docs.astral.sh/uv/) with its official installer if it is
# missing, then installs or upgrades `pcdd` from PyPI as a uv tool.
# Source: https://github.com/aledepaoligampel/pcdd/blob/main/site/install.sh
set -eu

say() { printf '%s\n' "pcdd: $*"; }
fail() { printf '%s\n' "pcdd: error: $*" >&2; exit 1; }

find_uv() {
  if command -v uv >/dev/null 2>&1; then
    command -v uv
    return 0
  fi
  for candidate in \
    "${UV_INSTALL_DIR:+$UV_INSTALL_DIR/uv}" \
    "${XDG_BIN_HOME:+$XDG_BIN_HOME/uv}" \
    "${XDG_DATA_HOME:+$XDG_DATA_HOME/../bin/uv}" \
    "$HOME/.local/bin/uv" \
    "$HOME/.cargo/bin/uv"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

install_uv() {
  url=https://astral.sh/uv/install.sh
  say "uv not found; installing it from $url"
  if command -v curl >/dev/null 2>&1; then
    installer=$(curl -LsSf "$url") || fail "could not download $url"
  elif command -v wget >/dev/null 2>&1; then
    installer=$(wget -qO- "$url") || fail "could not download $url"
  else
    fail "curl or wget is required to install uv"
  fi
  printf '%s\n' "$installer" | sh || fail "the uv installer failed"
}

main() {
  : "${HOME:?HOME must be set}"
  if ! uv=$(find_uv); then
    install_uv
    uv=$(find_uv) || fail "uv was installed but could not be found; open a new terminal and run: uv tool install pcdd"
  fi

  say "installing pcdd with $uv"
  "$uv" tool install --upgrade pcdd

  bin_dir=$("$uv" tool dir --bin 2>/dev/null || true)
  tool="$bin_dir/pcdd"
  [ -n "$bin_dir" ] && [ -x "$tool" ] || fail "pcdd did not install correctly"
  say "done: $("$tool" --version 2>/dev/null || echo installed)"

  found=$(command -v pcdd 2>/dev/null || true)
  if [ -z "$found" ]; then
    say "$bin_dir is not on your PATH yet. Run: $uv tool update-shell  (then open a new terminal)"
  elif [ "$found" != "$tool" ]; then
    say "warning: another pcdd at $found comes first on your PATH; remove it or put $bin_dir first"
  else
    say "next: cd your-project && pcdd init"
  fi
}

main "$@"
