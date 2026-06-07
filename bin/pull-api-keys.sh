#!/usr/bin/env bash
# bin/pull-api-keys.sh
# Pull Gemini API keys from the local Mema Vault and print a comma-separated
# string ready to be used as the GENAI_API_KEY environment variable.
#
# Usage:
#   MEMA_VAULT_MASTER_KEY=... ./bin/pull-api-keys.sh
#   MEMA_VAULT_MASTER_KEY=... ./bin/pull-api-keys.sh --export
#
# --export  print in `export GENAI_API_KEY="..."` form
set -euo pipefail

VAULT="${VAULT_PATH:-$HOME/.agents/skills/mema-vault/scripts/vault.py}"
[ -f "$VAULT" ] || { echo "vault.py not found at $VAULT" >&2; exit 1; }
[ -n "${MEMA_VAULT_MASTER_KEY:-}" ] || { echo "MEMA_VAULT_MASTER_KEY is not set" >&2; exit 1; }

# Try the most recent first; fall back to older names if missing.
SERVICES=("Gemini AI Studio 3" "gemini_aistudio_3" "gemini_aistudio_2" "gemini_aistudio_1")
KEYS=()
SEEN=" "
for svc in "${SERVICES[@]}"; do
  if out="$("$VAULT" get --show "$svc" 2>/dev/null)"; then
    key="$(printf '%s' "$out" | awk -F': ' '/^Pass: /{print $2}')"
    if [ -n "$key" ] && [[ "$SEEN" != *" $key "* ]]; then
      KEYS+=("$key")
      SEEN+="$key "
    fi
  fi
done

[ "${#KEYS[@]}" -gt 0 ] || { echo "no Gemini keys found in vault" >&2; exit 1; }

JOINED="$(IFS=,; echo "${KEYS[*]}")"
case "${1:-}" in
  --export) echo "export GENAI_API_KEY=\"$JOINED\"" ;;
  *)        echo "$JOINED" ;;
esac
