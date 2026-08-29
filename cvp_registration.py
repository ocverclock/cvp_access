#!/usr/bin/env python3
"""Registration Memory — CVP Access 1.5.1."""

from __future__ import annotations


class RegistrationController:
    """Rappel Registration 1..8 validé sur CVP-905."""

    def __init__(self, midi):
        self.midi = midi

    def recall(self, number, verify_notification=False):
        return self.midi.recall_registration(
            number,
            count=8,
            wait_notification=verify_notification,
        )
