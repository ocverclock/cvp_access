#!/usr/bin/env python3
"""CVP Access 1.5.1 - correctifs Song.

La classe historique reste utilisée pour toutes les fonctions déjà validées.
Seul le décodage du nom/chemin est remplacé par le codec Yamaha consolidé.
"""

from __future__ import annotations

from cvp_song import SongController as LegacySongController
from cvp_song import PROP_SONG_NAME
from cvp_yamaha import decode_yamaha_text


class SongController(LegacySongController):

    def get_name(self):
        data = self.core.get_property(
            self.port,
            PROP_SONG_NAME,
            0x00,
        )
        return decode_yamaha_text(data)
