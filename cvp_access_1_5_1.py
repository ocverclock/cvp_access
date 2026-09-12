#!/usr/bin/env python3
"""Extension CVP Access 1.5.1 : commandes globales de réactivation.

Conserve intégralement la runtime 1.5.1 précédente dans
cvp_access_1_5_1_base.py et ajoute deux actions :
- L : toutes les pistes Song ON ;
- RPAREN, touche ) / ° à droite du 0 : toutes les parties Style ON.
"""

from __future__ import annotations

import cvp_keyboard
from cvp_keyboard import ActionSpec
import cvp_access_1_5_1_base as base


VERSION = base.VERSION


NEW_ACTION_SPECS = {
    "song_all_tracks_on": ActionSpec(
        description="Toutes les pistes Song activées"
    ),
    "style_all_parts_on": ActionSpec(
        description="Toutes les parties Style activées"
    ),
}

cvp_keyboard.ACTION_SPECS.update(NEW_ACTION_SPECS)


class CVPActions151(base.CVPActions151):
    """Ajoute les commandes globales sans modifier les toggles individuels."""

    def dispatch(self, invocation):
        handlers = {
            "song_all_tracks_on": self.song_all_tracks_on,
            "style_all_parts_on": self.style_all_parts_on,
        }

        handler = handlers.get(invocation.name)
        if handler is not None:
            return handler()

        return super().dispatch(invocation)

    def song_all_tracks_on(self):
        """Force les 16 pistes du Song à ON et vérifie chaque piste."""
        if not self._require_song():
            return

        failures = []

        for track in range(1, 17):
            current = self.core.get_track_state(
                self.port,
                track,
            )

            if current is True:
                self.core.tracks[track] = True
                continue

            if not self.core.set_track_state(
                self.port,
                track,
                True,
            ):
                self.core.tracks[track] = None
                failures.append(track)
                continue

            verified = self.core.verify_track_state(
                self.port,
                track,
                True,
            )

            if verified is not True:
                self.core.tracks[track] = None
                failures.append(track)
                continue

            self.core.tracks[track] = True

        if failures:
            print(
                "Pistes Song : activation incomplète ->",
                ", ".join(str(track) for track in failures),
            )
            self.core.announce_action_help(
                "Activation de toutes les pistes Song incomplète"
            )
            return

        print("Pistes Song : toutes actives")
        self.core.announce_action_help(
            "Toutes les pistes Song activées"
        )

    def style_all_parts_on(self):
        """Force les 8 parties Style à ON avec la commande globale validée."""
        states = [True] * 8

        if not self.core.set_style_parts(
            self.port,
            states,
        ):
            print("Impossible d'activer toutes les parties Style.")
            self.core.announce_action_help(
                "Impossible d'activer toutes les parties Style"
            )
            return

        # Le protocole Style ne fournit pas de GET validé pour ces 8 états.
        # Le cache suit donc la commande déterministe envoyée au CVP-905.
        with self.core.style_parts_lock:
            self.core.style_parts[:] = states

        print("Parties Style : toutes actives")
        self.core.announce_action_help(
            "Toutes les parties Style activées"
        )


# La runtime historique 1.5.1 garde toute son initialisation hardware,
# ses correctifs Song, Piper et accessibilité. Seule la classe d'actions
# est étendue ici.
base.legacy.VERSION = VERSION
base.legacy.CVPActions = CVPActions151


def main():
    return base.main()


if __name__ == "__main__":
    main()
