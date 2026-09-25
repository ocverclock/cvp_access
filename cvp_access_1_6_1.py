#!/usr/bin/env python3
"""CVP Access 1.6.1-RC1.

Consolidation of the accessible MIDI recorder introduced in 1.6.0-RC1 while
preserving the validated Yamaha control stack.

1.6.1-RC1 consolidates:
- F14 / F16 recording selection with generated navigation cues;
- F15 recording / playback state machine;
- fast pre-generated recorder feedback;
- compact maintenance portal;
- explicit release metadata and diagnostics.
"""

from __future__ import annotations

import os

# Recorder remains opt-in at the shared runtime level and is enabled by the
# 1.6.x frontend before entering the 1.5.2 compatibility stack.
os.environ.setdefault("CVP_RECORDER_ENABLED", "1")

import cvp_access_1_5_2 as base  # noqa: E402


VERSION = "1.6.1-RC1"

# Keep the legacy runtime banner / Doctor import aligned with the release.
base.base.legacy.VERSION = VERSION


def main():
    return base.main()


if __name__ == "__main__":
    main()
