#!/usr/bin/env python3
"""
CVP Access - fonctions Song avancées.

Protocole validé sur Yamaha CVP-905 firmware 1.03 :
- détection Song
- longueur
- position
- Loop A/B
- métronome GET/SET
- conservation automatique du métronome lors d'une navigation Song arrière
"""

import time


PROP_SONG_NAME = [0x04, 0x00, 0x01, 0x01]
PROP_SONG_PRESENT = [0x04, 0x01, 0x00, 0x01]
PROP_SONG_LENGTH = [0x04, 0x00, 0x1B, 0x01]
PROP_SONG_LOOP = [0x04, 0x00, 0x0D, 0x01]

# Validé GET + SET sur CVP-905 firmware 1.03 :
# 00 = OFF / 01 = ON
PROP_METRONOME = [0x07, 0x00, 0x00, 0x01]


def decode_14bit(high, low):
    return (high << 7) | low


def encode_14bit(value):
    return [
        (value >> 7) & 0x7F,
        value & 0x7F,
    ]


def decode_yamaha_text(data):
    if data is None:
        return None

    if len(data) == 0:
        return ""

    if len(data) < 2:
        return None

    text_size = decode_14bit(data[0], data[1])

    if text_size == 0:
        return ""

    payload = data[2:]

    if len(payload) < text_size:
        return None

    payload = payload[:text_size]

    result = bytearray()
    pos = 0

    while pos < len(payload):
        highbits = payload[pos]
        pos += 1

        chunk_len = min(
            7,
            len(payload) - pos,
        )

        for index in range(chunk_len):
            value = payload[pos + index]

            bit = (
                highbits
                >> (chunk_len - index - 1)
            ) & 1

            if bit:
                value |= 0x80

            result.append(value)

        pos += chunk_len

    try:
        return result.decode("utf-8").rstrip("\x00")
    except UnicodeDecodeError:
        return result.decode(
            "latin-1",
            errors="replace",
        ).rstrip("\x00")


class SongController:

    def __init__(self, core, port):
        self.core = core
        self.port = port

        # Mémoire volontairement indépendante du CVP :
        # le CVP efface ses points A/B quand Loop passe OFF.
        self.loop_a = None
        self.loop_b = None

    # --------------------------------------------------------
    # Détection Song
    # --------------------------------------------------------

    def get_name(self):
        data = self.core.get_property(
            self.port,
            PROP_SONG_NAME,
            0x00,
        )
        return decode_yamaha_text(data)

    def get_track_present(self, track):
        if not 1 <= track <= 16:
            return None

        data = self.core.get_property(
            self.port,
            PROP_SONG_PRESENT,
            0x0F + track,
        )

        if data is None or len(data) != 1:
            return None

        return data[0] != 0

    def is_loaded(self):
        name = self.get_name()

        # Cas normal avec Song chargé : réponse immédiate.
        if name:
            return True

        known_tracks = 0

        for track in range(1, 17):
            state = self.get_track_present(track)

            if state is True:
                return True

            if state is False:
                known_tracks += 1

        # Critère validé :
        # song_name EMPTY + aucune piste présente.
        if name == "" and known_tracks == 16:
            return False

        # Communication incomplète : ne pas conclure à tort.
        return None

    # --------------------------------------------------------
    # Longueur / position
    # --------------------------------------------------------

    def get_length(self):
        data = self.core.get_property(
            self.port,
            PROP_SONG_LENGTH,
            0x00,
        )

        if data is None or len(data) != 4:
            return None

        return (
            decode_14bit(data[0], data[1]),
            decode_14bit(data[2], data[3]),
        )

    def get_position(self):
        return self.core.get_song_position(
            self.port
        )

    def set_position(self, measure, beat=1):
        return self.core.set_song_position(
            self.port,
            measure,
            beat,
        )

    def verify_position(self, measure, beat=1):
        return self.core.verify_song_position(
            self.port,
            measure,
            beat,
        )

    # --------------------------------------------------------
    # Métronome
    # --------------------------------------------------------

    def get_metronome(self):
        """Retourne True=ON, False=OFF, None=lecture impossible."""
        data = self.core.get_property(
            self.port,
            PROP_METRONOME,
            0x00,
        )

        if data is None or len(data) != 1:
            return None

        if data[0] == 0x00:
            return False

        if data[0] == 0x01:
            return True

        return None

    def set_metronome(self, enabled):
        """Commande validée : 07 00 00 01 idx=00, 00/01."""
        value = 0x01 if enabled else 0x00

        message = (
            self.core.HEADER
            + [0x01, 0x01]
            + PROP_METRONOME
            + [0x00, 0x01, 0x00]
            + [0x00, 0x01]
            + [value]
            + [0xF7]
        )

        return self.core.send_sysex(
            self.port,
            message,
        )

    def verify_metronome(
        self,
        expected,
        attempts=5,
    ):
        time.sleep(0.05)

        for attempt in range(attempts):
            state = self.get_metronome()

            if state is expected:
                return state

            if attempt < attempts - 1:
                time.sleep(0.05)

        return None

    def _remember_metronome_for_backward_navigation(self):
        """
        Lit l'état juste avant une navigation arrière.
        Seul ON doit être restauré : si le métronome était OFF,
        CVP Access ne doit surtout pas l'activer.
        """
        state = self.get_metronome()

        if state is None:
            print(
                "Métronome : état inconnu avant navigation arrière."
            )

        return state is True

    def _restore_metronome_after_backward_navigation(
        self,
        was_on,
    ):
        """
        Le CVP-905 coupe le métronome lors d'un déplacement Song arrière.
        S'il était ON avant le déplacement, le remettre ON si nécessaire.
        Une éventuelle erreur de restauration ne doit pas annuler une
        navigation Song qui, elle, a déjà réussi.
        """
        if not was_on:
            return True

        current = self.get_metronome()

        if current is True:
            return True

        if not self.set_metronome(True):
            print(
                "Position Song modifiée, mais impossible "
                "de restaurer le métronome."
            )
            return False

        verified = self.verify_metronome(True)

        if verified is not True:
            print(
                "Position Song modifiée, mais la restauration "
                "du métronome n'a pas pu être confirmée."
            )
            return False

        print("Métronome restauré -> ON")
        return True

    def goto(self, measure):
        loaded = self.is_loaded()

        if loaded is False:
            return "no_song", None

        if loaded is None:
            return "song_unknown", None

        if measure < 1:
            return "invalid", None

        length = self.get_length()

        if length is not None:
            max_measure = length[0]

            if measure > max_measure:
                return "invalid", max_measure

        # F3 peut aller aussi bien vers l'avant que vers l'arrière.
        # On lit donc la position courante afin de savoir s'il faut
        # préserver le métronome.
        current_position = self.get_position()

        backward = (
            current_position is not None
            and measure < current_position[0]
        )

        metronome_was_on = False

        if backward:
            metronome_was_on = (
                self._remember_metronome_for_backward_navigation()
            )

        if not self.set_position(
            measure,
            1,
        ):
            return "send_error", None

        verified = self.verify_position(
            measure,
            1,
        )

        if verified is None:
            return "verify_error", None

        if backward:
            self._restore_metronome_after_backward_navigation(
                metronome_was_on
            )

        return "ok", verified[0]

    def move(self, delta):
        loaded = self.is_loaded()

        if loaded is False:
            return "no_song", None

        if loaded is None:
            return "song_unknown", None

        position = self.get_position()

        if position is None:
            return "read_error", None

        current_measure, _ = position

        target = max(
            1,
            current_measure + delta,
        )

        length = self.get_length()

        if length is not None:
            target = min(
                target,
                length[0],
            )

        if target == current_measure:
            return "ok", current_measure

        backward = target < current_measure
        metronome_was_on = False

        if backward:
            metronome_was_on = (
                self._remember_metronome_for_backward_navigation()
            )

        if not self.set_position(
            target,
            1,
        ):
            return "send_error", None

        verified = self.verify_position(
            target,
            1,
        )

        if verified is None:
            return "verify_error", None

        if backward:
            self._restore_metronome_after_backward_navigation(
                metronome_was_on
            )

        return "ok", verified[0]

    # --------------------------------------------------------
    # LOOP A/B
    # --------------------------------------------------------

    def get_loop(self):
        data = self.core.get_property(
            self.port,
            PROP_SONG_LOOP,
            0x00,
        )

        if data is None or len(data) != 9:
            return None

        enabled = data[0] != 0

        measure_a = decode_14bit(
            data[1],
            data[2],
        )
        beat_a = decode_14bit(
            data[3],
            data[4],
        )
        measure_b = decode_14bit(
            data[5],
            data[6],
        )
        beat_b = decode_14bit(
            data[7],
            data[8],
        )

        # Une boucle déjà active dans le CVP peut initialiser notre mémoire
        # uniquement tant que CVP Access n'a encore mémorisé aucun point.
        #
        # Dès que l'utilisateur définit A ou B avec CVP Access, cette mémoire
        # locale devient prioritaire. Cela évite qu'une ancienne boucle du CVP
        # (par exemple 15 -> 16) écrase les nouveaux points saisis (12 -> 30).
        if (
            enabled
            and self.loop_a is None
            and self.loop_b is None
        ):
            self.loop_a = measure_a
            self.loop_b = measure_b

        return (
            enabled,
            measure_a,
            beat_a,
            measure_b,
            beat_b,
        )

    def set_loop(
        self,
        enabled,
        measure_a,
        measure_b,
    ):
        if measure_a is None:
            measure_a = 1

        if measure_b is None:
            measure_b = 2

        if measure_a < 1:
            return False

        if measure_b <= measure_a:
            return False

        data = (
            [0x01 if enabled else 0x00]
            + encode_14bit(measure_a)
            + encode_14bit(1)
            + encode_14bit(measure_b)
            + encode_14bit(1)
        )

        message = (
            self.core.HEADER
            + [0x01, 0x01]
            + PROP_SONG_LOOP
            + [0x00, 0x01, 0x00]
            + [0x00, len(data)]
            + data
            + [0xF7]
        )

        return self.core.send_sysex(
            self.port,
            message,
        )

    def verify_loop(
        self,
        expected_enabled,
        measure_a=None,
        measure_b=None,
        attempts=5,
    ):
        time.sleep(0.10)

        last = None

        for attempt in range(attempts):
            state = self.get_loop()

            if state is not None:
                last = state

                if not expected_enabled:
                    if state[0] is False:
                        return state

                elif (
                    state[0] is True
                    and state[1] == measure_a
                    and state[2] == 1
                    and state[3] == measure_b
                    and state[4] == 1
                ):
                    return state

            if attempt < attempts - 1:
                time.sleep(0.05)

        return None

    def set_point_a(self):
        loaded = self.is_loaded()

        if loaded is False:
            return "no_song", None

        if loaded is None:
            return "song_unknown", None

        position = self.get_position()

        if position is None:
            return "read_error", None

        self.loop_a = position[0]

        return "ok", self.loop_a

    def set_point_b(self):
        loaded = self.is_loaded()

        if loaded is False:
            return "no_song", None

        if loaded is None:
            return "song_unknown", None

        if self.loop_a is None:
            return "missing_a", None

        position = self.get_position()

        if position is None:
            return "read_error", None

        candidate = position[0]

        if candidate <= self.loop_a:
            return "invalid_b", candidate

        self.loop_b = candidate

        return "ok", self.loop_b

    def toggle_loop(self):
        loaded = self.is_loaded()

        if loaded is False:
            return "no_song", None

        if loaded is None:
            return "song_unknown", None

        current = self.get_loop()

        if current is None:
            return "read_error", None

        enabled = current[0]

        if enabled:
            # get_loop() a déjà sauvegardé A/B localement.
            measure_a = self.loop_a or current[1]
            measure_b = self.loop_b or current[3]

            if not self.set_loop(
                False,
                measure_a,
                measure_b,
            ):
                return "send_error", None

            verified = self.verify_loop(
                False
            )

            if verified is None:
                return "verify_error", None

            # IMPORTANT : ne jamais effacer self.loop_a / self.loop_b.
            return "off", (
                measure_a,
                measure_b,
            )

        if self.loop_a is None or self.loop_b is None:
            return "missing_points", None

        if self.loop_b <= self.loop_a:
            return "invalid_b", self.loop_b

        if not self.set_loop(
            True,
            self.loop_a,
            self.loop_b,
        ):
            return "send_error", None

        verified = self.verify_loop(
            True,
            self.loop_a,
            self.loop_b,
        )

        if verified is None:
            return "verify_error", None

        return "on", (
            self.loop_a,
            self.loop_b,
        )
