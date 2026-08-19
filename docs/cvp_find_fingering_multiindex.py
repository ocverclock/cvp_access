#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import threading
import time
from datetime import datetime
from pathlib import Path

PREVIOUS_REPORT = Path('fingering_adaptive_report.json')
OUTPUT_REPORT = Path('fingering_multiindex_report.json')
FIRST_MIN, FIRST_MAX = 0x00, 0x0F
SECOND_MIN, SECOND_MAX = 0x00, 0x0F
THIRD_REMAIN_MIN, THIRD_REMAIN_MAX = 0x40, 0x7F
INDEX_MIN, INDEX_MAX = 0x00, 0x1F
FAST_TIMEOUT = 0.055
NORMAL_TIMEOUT = 0.16
DELAY = 0.004
STABLE_READS = 2


def load_engine():
    path = Path(__file__).resolve().with_name('cvp_probe_readonly.py')
    if not path.is_file():
        raise SystemExit(f'ERREUR : moteur absent : {path}')
    spec = importlib.util.spec_from_file_location('cvp_probe_engine', path)
    if spec is None or spec.loader is None:
        raise SystemExit('ERREUR : impossible de charger cvp_probe_readonly.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def start_midi(engine):
    if not engine.check_port_free():
        raise SystemExit(1)
    port = engine.find_midi_port()
    if port is None:
        raise SystemExit('ERREUR : interface Prodipe MIDI introuvable')
    print('MIDI :', port, '-', engine.MIDI_NAME)
    thread = threading.Thread(target=engine.midi_receiver, args=(port,), daemon=True)
    thread.start()
    time.sleep(0.35)
    return port


def hx(data):
    if data is None:
        return '-'
    return ' '.join(f'{b:02X}' for b in data)


def sig_text(sig):
    return ' '.join(f'{b:02X}' for b in sig)


def sig_from_text(text):
    return [int(x, 16) for x in text.split()]


def state_json(state):
    return {'status': state[0], 'data_hex': hx(state[1])}


def state_from_json(obj):
    status = obj.get('status')
    data_hex = obj.get('data_hex')
    if not data_hex or data_hex == '-':
        data = None
    else:
        data = tuple(int(x, 16) for x in data_hex.split())
    return status, data


def get_once(engine, port, sig, index, timeout):
    result = engine.get_property(port, sig, index, timeout=timeout)
    data = result['data']
    return result['status'], tuple(data) if data is not None else None


def get_stable(engine, port, sig, index, timeout=NORMAL_TIMEOUT, reads=STABLE_READS):
    values = []
    for _ in range(reads):
        values.append(get_once(engine, port, sig, index, timeout))
        time.sleep(0.012)
    first = values[0]
    if all(value == first for value in values):
        return first
    return 'UNSTABLE', None


def load_previous_responders():
    responders = {}
    if not PREVIOUS_REPORT.is_file():
        print('Rapport précédent absent :', PREVIOUS_REPORT)
        return responders
    payload = json.loads(PREVIOUS_REPORT.read_text(encoding='utf-8'))
    source = payload.get('baseline_responses', {})
    for signature, obj in source.items():
        state = state_from_json(obj)
        if state[0] in ('DATA', 'EMPTY'):
            responders[signature] = state
    print('Rapport précédent chargé :', PREVIOUS_REPORT)
    print('Signatures idx=00 déjà connues :', len(responders))
    return responders


def scan_remaining_idx0(engine, port, responders):
    print('\nPHASE 1 - COMPLÉMENT IDX=00 / THIRD 40..7F')
    print('=' * 72)
    total = ((FIRST_MAX-FIRST_MIN+1) * (SECOND_MAX-SECOND_MIN+1) * (THIRD_REMAIN_MAX-THIRD_REMAIN_MIN+1))
    done = 0
    new_count = 0
    for first in range(FIRST_MIN, FIRST_MAX + 1):
        for second in range(SECOND_MIN, SECOND_MAX + 1):
            for third in range(THIRD_REMAIN_MIN, THIRD_REMAIN_MAX + 1):
                done += 1
                sig = [first, second, third, 0x01]
                state = get_stable(engine, port, sig, 0x00, timeout=FAST_TIMEOUT)
                if state[0] in ('DATA', 'EMPTY'):
                    key = sig_text(sig)
                    if key not in responders:
                        new_count += 1
                    responders[key] = state
                    if state[0] == 'DATA':
                        print('[DATA]', key, 'idx=00 ->', hx(state[1]))
                if done % 256 == 0:
                    print('...', f'{done}/{total}', f'(nouvelles réponses : {new_count})')
                time.sleep(DELAY)
    print('\nComplément idx=00 terminé.')
    print('Nouvelles signatures :', new_count)
    print('Total signatures répondantes idx=00 :', len(responders))


def scan_all_indexes_fingered(engine, port, responders):
    print('\nPHASE 2 - FINGERED / INDEXES 00..1F')
    print('=' * 72)
    print('On sonde uniquement les signatures qui répondent déjà à idx=00.\n')
    pairs = {}
    signatures = sorted(responders.keys())
    total = len(signatures) * (INDEX_MAX - INDEX_MIN + 1)
    done = 0
    for signature_text in signatures:
        sig = sig_from_text(signature_text)
        for index in range(INDEX_MIN, INDEX_MAX + 1):
            done += 1
            state = get_stable(engine, port, sig, index)
            if state[0] in ('DATA', 'EMPTY'):
                key = f'{signature_text}|{index:02X}'
                pairs[key] = state
                if state[0] == 'DATA':
                    print('[DATA]', signature_text, f'idx={index:02X}', '->', hx(state[1]))
            if done % 128 == 0:
                print('...', f'{done}/{total}', f'(couples stables : {len(pairs)})')
            time.sleep(DELAY)
    print('\nScan multi-index FINGERED terminé.')
    print('Couples stables conservés :', len(pairs))
    return pairs


def compare_ai(engine, port, fingered_pairs):
    print('\nPHASE 3 - AI FULL KEYBOARD')
    print('=' * 72)
    changes = []
    ai_states = {}
    items = sorted(fingered_pairs.items())
    for number, (key, old_state) in enumerate(items, 1):
        signature_text, index_text = key.split('|')
        sig = sig_from_text(signature_text)
        index = int(index_text, 16)
        state = get_stable(engine, port, sig, index)
        ai_states[key] = state
        if state[0] != 'UNSTABLE' and state != old_state:
            changes.append(key)
            print('[CHANGE]', signature_text, f'idx={index:02X}', ': Fingered=', f'{old_state[0]}:{hx(old_state[1])}', '-> AI=', f'{state[0]}:{hx(state[1])}')
        if number % 128 == 0:
            print('...', f'{number}/{len(items)}')
        time.sleep(DELAY)
    print('\nChangements observés :', len(changes))
    return ai_states, changes


def confirm_return(engine, port, fingered_pairs, ai_states, changes):
    print('\nPHASE 4 - RETOUR FINGERED / CONFIRMATION')
    print('=' * 72)
    confirmed = []
    for key in changes:
        signature_text, index_text = key.split('|')
        sig = sig_from_text(signature_text)
        index = int(index_text, 16)
        original = fingered_pairs[key]
        ai = ai_states[key]
        returned = get_stable(engine, port, sig, index, reads=3)
        print(signature_text, f'idx={index:02X}', ': F1=', f'{original[0]}:{hx(original[1])}', '| AI=', f'{ai[0]}:{hx(ai[1])}', '| F2=', f'{returned[0]}:{hx(returned[1])}')
        if returned == original and ai != original and ai[0] != 'UNSTABLE':
            confirmed.append(key)
    print('\nCandidats reproductibles :', len(confirmed))
    return confirmed


def save_report(responders, fingered_pairs, ai_states, changes, confirmed):
    payload = {
        'generated_at': datetime.now().isoformat(),
        'source_previous_report': str(PREVIOUS_REPORT) if PREVIOUS_REPORT.is_file() else None,
        'idx0_responders': {k: state_json(v) for k, v in responders.items()},
        'fingered_pairs': {k: state_json(v) for k, v in fingered_pairs.items()},
        'ai_states': {k: state_json(v) for k, v in ai_states.items()},
        'changes': changes,
        'confirmed': confirmed,
    }
    OUTPUT_REPORT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    engine = load_engine()
    port = start_midi(engine)
    try:
        print('\nCVP ACCESS - FINGERING TYPE V2 MULTI-INDEX')
        print('=' * 72)
        print('GET uniquement : aucun SET / RESET / EVENTS.\n')
        input('1) Mets le CVP sur FINGERED et ne change rien d\'autre, puis appuie sur Entrée...')
        responders = load_previous_responders()
        scan_remaining_idx0(engine, port, responders)
        fingered_pairs = scan_all_indexes_fingered(engine, port, responders)
        input('\n2) Passe UNIQUEMENT sur AI FULL KEYBOARD, puis appuie sur Entrée...')
        ai_states, changes = compare_ai(engine, port, fingered_pairs)
        if not changes:
            save_report(responders, fingered_pairs, ai_states, changes, [])
            print('\nRÉSUMÉ FINAL')
            print('=' * 72)
            print('Aucun changement stable détecté sur les signatures/indexes répondants.')
            print('Rapport :', OUTPUT_REPORT)
            return
        input('\n3) Reviens UNIQUEMENT sur FINGERED, puis appuie sur Entrée...')
        confirmed = confirm_return(engine, port, fingered_pairs, ai_states, changes)
        save_report(responders, fingered_pairs, ai_states, changes, confirmed)
        print('\nRÉSUMÉ FINAL')
        print('=' * 72)
        if not confirmed:
            print('Aucun candidat reproductible.')
        else:
            print('CANDIDATS REPRODUCTIBLES :')
            for key in confirmed:
                signature_text, index_text = key.split('|')
                old = fingered_pairs[key]
                new = ai_states[key]
                print(signature_text, f'idx={index_text}', ': Fingered=', f'{old[0]}:{hx(old[1])}', '-> AI Full Keyboard=', f'{new[0]}:{hx(new[1])}')
        print('\nRapport :', OUTPUT_REPORT)
    finally:
        engine.cleanup()


if __name__ == '__main__':
    main()
