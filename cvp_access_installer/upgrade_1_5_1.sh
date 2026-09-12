#!/usr/bin/env bash
set -Eeuo pipefail

[[ ${EUID} -eq 0 ]] || {
    echo "Run with: sudo bash cvp_access_installer/upgrade_1_5_1.sh"
    exit 1
}

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_DIR="$(cd "$INSTALLER_DIR/.." && pwd -P)"
RUNTIME_DIR="/opt/cvp-access"
CONFIG_FILE="/etc/cvp-access/keyboard.toml"

# La runtime 1.5.1 précédente reste la base stable. Le nouveau frontend
# l'étend et doit donc disposer de ce module dans /opt/cvp-access.
install -d -m 0755 "$RUNTIME_DIR"
install -m 0644 \
    "$REPO_DIR/cvp_access_1_5_1_base.py" \
    "$RUNTIME_DIR/cvp_access_1_5_1_base.py"

# Migration non destructive d'une configuration déjà installée.
# Ne jamais écraser une personnalisation existante.
if [[ -f "$CONFIG_FILE" ]]; then
    python3 - "$CONFIG_FILE" <<'PY'
from pathlib import Path
import re
import sys
import tomllib

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

with path.open("rb") as handle:
    data = tomllib.load(handle)

keys = data.get("keys", {})
song_keys = [
    "A", "Z", "E", "R", "T", "Y", "U", "I",
    "Q", "S", "D", "F", "G", "H", "J", "K",
]

# Ancien profil officiel Solo ALT -> nouveau profil Solo SHIFT.
# On retire uniquement les anciennes affectations exactes créées par CVP Access.
for track, key in enumerate(song_keys, start=1):
    combo = f"ALT+{key}"
    action = f"song_track_solo:{track}"
    if keys.get(combo) == action:
        pattern = re.compile(
            rf'^\s*"{re.escape(combo)}"\s*=\s*"{re.escape(action)}"\s*\n?',
            re.MULTILINE,
        )
        text = pattern.sub("", text)
        print(f"Migration clavier : suppression {combo} -> {action}")

bindings = {
    "L": "song_all_tracks_on",
    "RPAREN": "style_all_parts_on",
}
for track, key in enumerate(song_keys, start=1):
    bindings[f"SHIFT+{key}"] = f"song_track_solo:{track}"

lines = text.splitlines()
keys_start = next(
    (i for i, line in enumerate(lines) if line.strip() == "[keys]"),
    None,
)

if keys_start is None:
    lines += ["", "[keys]"]
    keys_start = len(lines) - 1

keys_end = len(lines)
for i in range(keys_start + 1, len(lines)):
    stripped = lines[i].strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        keys_end = i
        break

for combo, action in bindings.items():
    if combo in keys:
        if keys.get(combo) != action:
            print(
                f"WARNING: touche {combo} déjà personnalisée -> "
                f"{keys.get(combo)} ; conservation de cette affectation."
            )
        continue

    lines.insert(keys_end, f'"{combo}" = "{action}"')
    keys_end += 1
    print(f"Ajout clavier : {combo} -> {action}")

path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
fi

# L'installateur RC3 historique réalise ensuite copie runtime, compilation,
# génération des WAV, Doctor et redémarrage. Les nouvelles touches sont déjà
# présentes dans keyboard.toml avant cette étape.
exec bash "$INSTALLER_DIR/upgrade_1_5_1_base.sh"
