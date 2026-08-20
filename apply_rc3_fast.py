#!/usr/bin/env python3
from pathlib import Path
import py_compile
import shutil
import sys


def main():
    bundle = Path(__file__).resolve().parent
    root = (
        Path(sys.argv[1]).expanduser().resolve()
        if len(sys.argv) > 1
        else Path.cwd().resolve()
    )

    targets = [
        "cvp_access_v1.5.py",
        "cvp_speech.py",
    ]

    for name in targets:
        src = bundle / name
        dst = root / name

        if not src.is_file():
            raise SystemExit(f"Fichier absent : {src}")

        if not dst.is_file():
            raise SystemExit(f"Fichier cible absent : {dst}")

        backup = dst.with_name(
            dst.name + ".bak-RC3-fast"
        )

        if not backup.exists():
            shutil.copy2(dst, backup)

        shutil.copy2(src, dst)

    for name in targets:
        py_compile.compile(
            str(root / name),
            doraise=True,
        )

    print()
    print("RC3 FAST : MISE A JOUR APPLIQUEE")
    print("=" * 56)
    print("Cache volumes        : actif")
    print("Verification SET     : acceleree")
    print("Fallback de controle : conserve")
    print("Annonces volumes     : anciennes valeurs ignorees")
    print("Syntaxe Python       : OK")


if __name__ == "__main__":
    main()
