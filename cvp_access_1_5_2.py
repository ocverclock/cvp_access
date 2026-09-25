#!/usr/bin/env python3
"""CVP Access 1.5.2-RC1.

Conserve la base fonctionnelle 1.5.1 et formalise le paquet autonome de
maintenance (réseau, portail Web, Samba et carte clavier) sans modifier le
protocole Yamaha validé.

La couche runtime conserve également les ajouts 1.5.1 :
- L : toutes les pistes Song ON ;
- RPAREN, touche ) / ° à droite du 0 : toutes les parties Style ON ;
- SHIFT + touche piste Song : piste sélectionnée ON, les 15 autres OFF.
"""

from __future__ import annotations

import cvp_keyboard
from cvp_keyboard import ActionSpec
import cvp_access_1_5_1_base as base


VERSION = "1.5.2-RC1"


# Action metadata is centralised in cvp_action_catalog.py (1.7).\nclass CVPActions151(base.CVPActions151):
    """Ajoute les commandes globales et le Solo sans modifier les toggles."""

    def dispatch(self, invocation):
        handlers = {
            "song_all_tracks_on": self.song_all_tracks_on,
            "style_all_parts_on": self.style_all_parts_on,
            "song_track_solo": self.song_track_solo,
        }

        handler = handlers.get(invocation.name)
        if handler is not None:
            if invocation.parameter is None:
                return handler()
            return handler(invocation.parameter)

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

    def song_track_solo(self, selected_track):
        """Active une seule piste Song et coupe les quinze autres."""
        if not self._require_song():
            return

        if not 1 <= selected_track <= 16:
            print("Piste Solo invalide :", selected_track)
            return

        # Activer d'abord la nouvelle piste Solo. En passant d'un Solo à un
        # autre, cela évite un bref trou de son avant de couper l'ancienne.
        if not self.core.set_track_state(
            self.port,
            selected_track,
            True,
        ):
            self.core.tracks[selected_track] = None
            print(
                f"Impossible d'activer la piste Solo {selected_track}."
            )
            self.core.announce_action_help(
                f"Impossible d'activer le Solo piste {selected_track}"
            )
            return

        send_failures = []

        for track in range(1, 17):
            if track == selected_track:
                continue

            if not self.core.set_track_state(
                self.port,
                track,
                False,
            ):
                self.core.tracks[track] = None
                send_failures.append(track)

        verify_failures = []

        for track in range(1, 17):
            expected = track == selected_track
            verified = self.core.verify_track_state(
                self.port,
                track,
                expected,
            )

            if verified is not expected:
                self.core.tracks[track] = None
                verify_failures.append(track)
                continue

            self.core.tracks[track] = expected

        failures = sorted(
            set(send_failures + verify_failures)
        )

        if failures:
            print(
                f"Solo piste {selected_track} : vérification incomplète ->",
                ", ".join(str(track) for track in failures),
            )
            self.core.announce_action_help(
                f"Solo piste {selected_track} incomplet"
            )
            return

        print(f"Solo piste {selected_track} -> ON")
        self.core.announce_song_solo(selected_track)

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


# La base 1.5.1 garde toute son initialisation hardware,
# ses correctifs Song, Piper et accessibilité. Seule la classe d'actions
# est étendue ici.
base.legacy.VERSION = VERSION
base.legacy.CVPActions = CVPActions151


def main():
    return base.main()


if __name__ == "__main__":
    main()
