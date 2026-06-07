#!/usr/bin/env bash
# Update .po and .mo files for all supported languages.
#
# 1. Extract all _()/{% trans %} strings from templates + Python into messages.pot.
# 2. Merge new strings into each language's .po file (preserves existing translations).
# 3. Compile .po -> .mo.
#
# Run from the project root. Requires `pybabel` (Flask-Babel installs it).
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[1/3] Extract"
pybabel extract -F web/babel.cfg -o web/translations/messages.pot .

for lang in en id; do
  echo "[2/3] Update $lang"
  pybabel update -i web/translations/messages.pot -d web/translations -l "$lang" --previous --no-fuzzy-matching
done

echo "[3/3] Compile"
pybabel compile -d web/translations

echo "Done."
echo "  msgids: $(grep -c '^msgid \"' web/translations/messages.pot)"
echo "  en filled: $(python3 -c "
import re
with open('web/translations/en/LC_MESSAGES/messages.po') as f: c = f.read()
t = re.findall(r'msgid \"([^\"]+)\"\nmsgstr \"([^\"]*)\"', c)
print(sum(1 for m, s in t if m and s))")"
echo "  id filled: $(python3 -c "
import re
with open('web/translations/id/LC_MESSAGES/messages.po') as f: c = f.read()
t = re.findall(r'msgid \"([^\"]+)\"\nmsgstr \"([^\"]*)\"', c)
print(sum(1 for m, s in t if m and s))")"
