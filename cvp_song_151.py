#!/usr/bin/env python3
"""CVP Access 1.5.1 - correctifs Song.

La classe historique reste utilisée pour toutes les fonctions déjà validées.
La couche 1.5.1 corrige :
- le décodage du nom/chemin via le codec Yamaha consolidé ;
- l'écriture et la vérification de la position Song, absentes du moteur v1.4.1.
"""

from __future__ import annotations

import time

from cvp_song import SongController as LegacySongController
from cvp_song import PROP_SONG_NAME, encode_14bit
from cvp_yamaha import decode_yamaha_text


PROP_SONG_POSITION = [0x04, 0x00, 0x0A, 0x01]


class SongController(LegacySongController):

    def get_name(self):
        data = self.core.get_property(
            self.port,
            PROP_SONG_NAME,
            0x00,
        )
        return decode_yamaha_text(data)

    def set_position(self, measure, beat=1):
        """Déplace le Song à une mesure/temps via la propriété Yamaha validée."""
        if measure < 1 or beat < 1:
            return False

        data = (
            encode_14bit(measure)
            + encode_14bit(beat)
        )

        message = (
            self.core.HEADER
            + [0x01, 0x01]
            + PROP_SONG_POSITION
            + [0x00, 0x01, 0x00]
            + [0x00, len(data)]
            + data
            + [0xF7]
        )

        return self.core.send_sysex(
            self.port,
            message,
        )

    def verify_position(
        self,
        measure,
        beat=1,
        attempts=5,
    ):
        """Relit la position afin de confirmer le déplacement demandé."""
        time.sleep(0.10)

        last_position = None

        for attempt in range(attempts):
            position = self.get_position()

            if position is not None:
                last_position = position

                if position == (measure, beat):
                    return position

            if attempt < attempts - 1:
                time.sleep(0.05)

        print(
            "Vérification position Song : "
            f"attendu mesure {measure}, temps {beat}, "
            + (
                "position inconnue"
                if last_position is None
                else (
                    f"lu mesure {last_position[0]}, "
                    f"temps {last_position[1]}"
                )
            )
        )

        return None
