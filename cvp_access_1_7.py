#!/usr/bin/env python3
"""CVP Access 1.7.0-RC1.

Adds the Web keyboard editor and named configuration profiles while preserving
the validated Yamaha/SysEx and Recorder runtime from 1.6.1-RC2.
"""

from __future__ import annotations

import os

os.environ.setdefault("CVP_RECORDER_ENABLED", "1")

import cvp_access_1_5_2 as base  # noqa: E402


VERSION = "1.7.0-RC1"

# Keep the legacy runtime banner / Doctor import aligned with the release.
base.base.legacy.VERSION = VERSION


def main():
    return base.main()


if __name__ == "__main__":
    main()
