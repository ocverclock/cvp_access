#!/usr/bin/env python3
"""CVP Access 1.6.0-RC1.

Adds the accessible one-button MIDI recorder while preserving the validated
1.5.2 Yamaha control path.

Recorder scope in RC1:
- F15 short/long state machine;
- channel 1 capture through the existing permanent MIDI receiver;
- Standard MIDI File save with date + daily index;
- selected recording shared with the local Web portal;
- playback through ALSA aplaymidi.
"""

from __future__ import annotations

import os

# Enable the recorder in the shared runtime before entering the 1.5.2 stack.
os.environ.setdefault("CVP_RECORDER_ENABLED", "1")

import cvp_access_1_5_2 as base  # noqa: E402


VERSION = "1.6.0-RC1"

# The 1.5.2 wrapper already installs the current action class. Only the runtime
# version and the explicit recorder feature flag change here.
base.base.legacy.VERSION = VERSION


def main():
    return base.main()


if __name__ == "__main__":
    main()
