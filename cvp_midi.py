#!/usr/bin/env python3
"""API MIDI stable de CVP Access 1.5.1.

Cette couche encapsule temporairement le moteur historique v1.4.1.
Les autres modules ne doivent plus dépendre directement de midi_queue.

Aucun brute-force SET n'est fourni par cette API.
"""

from __future__ import annotations

import queue
import threading
import time


class MidiError(RuntimeError):
    pass


class MidiService:
    XG_REQUEST_PREFIX = [0xF0, 0x43, 0x30, 0x4C]
    XG_CHANGE_PREFIX = [0xF0, 0x43, 0x10, 0x4C]

    REG_RECALL_PREFIX = [
        0xF0, 0x43, 0x73, 0x01, 0x52, 0x25,
        0x11, 0x00, 0x02, 0x00,
    ]
    REG_NOTIFY_PREFIX = [
        0xF0, 0x43, 0x73, 0x01, 0x52, 0x25,
        0x00, 0x01, 0x01, 0x00, 0x01,
    ]

    def __init__(self, core, port=None):
        self.core = core
        self.port = port
        self._receiver_thread = None

    def find_port(self):
        return self.core.find_midi_port()

    def start(self):
        """Démarre le récepteur uniquement s'il n'est pas déjà actif."""
        if self.port is None:
            self.port = self.find_port()

        if not self.port:
            raise MidiError("Interface MIDI introuvable")

        proc = getattr(self.core, "midi_process", None)
        if proc is not None and proc.poll() is None:
            return self.port

        self._receiver_thread = threading.Thread(
            target=self.core.midi_receiver,
            args=(self.port,),
            daemon=True,
        )
        self._receiver_thread.start()
        time.sleep(0.8)

        proc = getattr(self.core, "midi_process", None)
        if proc is None or proc.poll() is not None:
            raise MidiError("Récepteur MIDI impossible à démarrer")

        self.drain()
        return self.port

    def stop(self):
        proc = getattr(self.core, "midi_process", None)
        if proc is None or proc.poll() is not None:
            return

        proc.terminate()
        try:
            proc.wait(timeout=1)
        except Exception:
            proc.kill()

    def drain(self):
        count = 0
        while True:
            try:
                self.core.midi_queue.get_nowait()
                count += 1
            except queue.Empty:
                return count

    def send(self, message):
        if self.port is None:
            raise MidiError("Port MIDI non initialisé")
        return bool(self.core.send_sysex(self.port, list(message)))

    def wait_for(self, predicate, timeout=1.0):
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            remaining = max(0.0, deadline - time.monotonic())
            try:
                msg = self.core.midi_queue.get(timeout=min(0.1, remaining))
            except queue.Empty:
                continue

            if predicate(msg):
                return msg

        return None

    # --------------------------------------------------------
    # CSP CVP
    # --------------------------------------------------------

    def csp_get(self, prop, index=0x00, timeout=0.5):
        return self.core.get_property(
            self.port,
            list(prop),
            index,
            timeout=timeout,
        )

    def csp_set_raw(self, prop, index, data):
        """SET uniquement pour une propriété déjà validée."""
        payload = list(data)

        if len(payload) > 0x7F:
            raise ValueError("Payload CSP > 127 octets non supporté ici")

        message = (
            list(self.core.HEADER)
            + [0x01, 0x01]
            + list(prop)
            + [index, 0x01, 0x00]
            + [0x00, len(payload)]
            + payload
            + [0xF7]
        )
        return self.send(message)

    def csp_set_u7(self, prop, index, value):
        if not 0 <= value <= 0x7F:
            raise ValueError("Valeur u7 hors plage")
        return self.csp_set_raw(prop, index, [value])

    # --------------------------------------------------------
    # XG
    # --------------------------------------------------------

    @staticmethod
    def _address(address):
        address = tuple(int(v) for v in address)
        if len(address) != 3 or any(not 0 <= v <= 0x7F for v in address):
            raise ValueError("Adresse XG attendue : 3 octets 00..7F")
        return address

    def xg_get(self, address, timeout=0.6, attempts=2):
        """XG Parameter Request GET-only."""
        address = self._address(address)

        for _ in range(max(1, attempts)):
            self.drain()

            message = (
                self.XG_REQUEST_PREFIX
                + list(address)
                + [0xF7]
            )
            if not self.send(message):
                continue

            def match(rx):
                return (
                    len(rx) >= 9
                    and rx[0] == 0xF0
                    and rx[1] == 0x43
                    and 0x10 <= rx[2] <= 0x1F
                    and rx[3] == 0x4C
                    and tuple(rx[4:7]) == address
                    and rx[-1] == 0xF7
                )

            rx = self.wait_for(match, timeout)
            if rx is not None:
                return bytes(rx[7:-1])

        return None

    def xg_set(self, address, data):
        """XG Parameter Change explicite.

        L'appelant doit utiliser seulement une adresse/valeur validée et
        restaurable. Cette méthode n'est pas destinée au brute-force.
        """
        address = self._address(address)
        data = bytes(data)

        if not data:
            raise ValueError("Payload XG vide")
        if any(v > 0x7F for v in data):
            raise ValueError("XG data doit rester 7-bit")

        return self.send(
            self.XG_CHANGE_PREFIX
            + list(address)
            + list(data)
            + [0xF7]
        )

    # --------------------------------------------------------
    # Registration
    # --------------------------------------------------------

    def recall_registration(
        self,
        number,
        *,
        count=8,
        wait_notification=True,
        settle=0.35,
        timeout=2.0,
    ):
        if not 1 <= number <= count:
            raise ValueError(f"Registration 1..{count} attendue")

        index = number - 1
        self.drain()

        ok = self.send(
            self.REG_RECALL_PREFIX
            + [index, 0xF7]
        )
        if not ok:
            return False

        notified = None
        if wait_notification:
            def match(rx):
                return (
                    len(rx) >= 13
                    and rx[:11] == self.REG_NOTIFY_PREFIX
                    and rx[11] == index
                    and rx[-1] == 0xF7
                )

            notified = self.wait_for(match, timeout)

        time.sleep(settle)
        self.drain()

        if wait_notification:
            return notified is not None
        return True
