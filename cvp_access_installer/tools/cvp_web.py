#!/usr/bin/env python3
"""Local maintenance portal for CVP Access.

The service intentionally exposes only a small set of maintenance actions.
It is reachable from the CVP-ACCESS hotspot subnet and localhost, not from
arbitrary LAN interfaces.
"""

from __future__ import annotations

import glob
import html
import ipaddress
import json
import os
import re
import subprocess
import threading
import tomllib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


HOTSPOT_NET = ipaddress.ip_network("10.42.0.0/24")
HOTSPOT_IP = "10.42.0.1"
RUNTIME = Path(os.environ.get("CVP_RUNTIME_DIR", "/opt/cvp-access"))
CONFIG_DIR = Path(os.environ.get("CVP_CONFIG_DIR", "/etc/cvp-access"))
HARDWARE_CONFIG = CONFIG_DIR / "hardware.toml"
KEYBOARD_MAP = CONFIG_DIR / "keyboard-map.html"
CVP_USER = os.environ.get("CVP_USER", "pi")

CAPTIVE_PATHS = {
    "/generate_204",
    "/gen_204",
    "/hotspot-detect.html",
    "/library/test/success.html",
    "/connecttest.txt",
    "/ncsi.txt",
    "/success.txt",
    "/canonical.html",
    "/redirect",
}


def run(args, timeout=5):
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def service_state(name):
    rc, out, _ = run(["systemctl", "is-active", name])
    return out or ("active" if rc == 0 else "inactive")


def parse_midi_devices():
    _, out, _ = run(["amidi", "-l"])
    devices = []
    for line in out.splitlines():
        match = re.match(
            r"^\s*(IO|I|O)\s+(hw:\d+,\d+,\d+)\s+(.+?)\s*$",
            line,
        )
        if not match:
            continue
        devices.append(
            {
                "direction": match.group(1),
                "port": match.group(2),
                "name": match.group(3),
            }
        )
    return devices


def selected_midi_name():
    if not HARDWARE_CONFIG.is_file():
        return None
    try:
        with HARDWARE_CONFIG.open("rb") as handle:
            data = tomllib.load(handle)
        value = data.get("midi", {}).get("name")
        return value if isinstance(value, str) and value.strip() else None
    except Exception:
        return None


def save_midi_name(name):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = HARDWARE_CONFIG.with_suffix(".tmp")
    if name:
        content = "[midi]\nname = " + json.dumps(name, ensure_ascii=False) + "\n"
    else:
        content = "[midi]\nname = \"\"\n"
    tmp.write_text(content, encoding="utf-8")
    os.chmod(tmp, 0o644)
    tmp.replace(HARDWARE_CONFIG)


def runtime_version():
    for path in (
        RUNTIME / "cvp_access_1_5_1_base.py",
        RUNTIME / "cvp_access.py",
    ):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        match = re.search(r'^VERSION\s*=\s*["\']([^"\']+)', text, re.M)
        if match:
            return match.group(1)
    return "inconnue"


def recent_events():
    _, out, _ = run(
        [
            "journalctl",
            "-u",
            "cvp-access.service",
            "-n",
            "120",
            "--no-pager",
            "-o",
            "cat",
        ],
        timeout=6,
    )
    keywords = (
        "MIDI",
        "Audio",
        "Piste",
        "Tempo",
        "Transpose",
        "Style",
        "Song",
        "Erreur",
        "erreur",
        "introuvable",
        "opérationnel",
        "operationnel",
        "Impossible",
    )
    lines = [
        line
        for line in out.splitlines()
        if any(word in line for word in keywords)
    ]
    return lines[-30:]


def network_status():
    _, active, _ = run(
        ["nmcli", "-g", "GENERAL.CONNECTION", "device", "show", "wlan0"]
    )
    _, addr, _ = run(["ip", "-4", "-o", "addr", "show", "dev", "wlan0"])
    return {
        "connection": active or "--",
        "address": addr,
        "hotspot": active == "CVP-ACCESS",
    }


def build_status():
    midi = parse_midi_devices()
    _, audio_out, _ = run(["aplay", "-l"])
    audio_lines = [
        line.strip()
        for line in audio_out.splitlines()
        if "Clavinova" in line or "Yamaha" in line
    ]
    keyboards = glob.glob("/dev/input/by-id/*-event-kbd")
    _, usb_out, _ = run(["lsusb"])
    return {
        "version": runtime_version(),
        "services": {
            "cvp_access": service_state("cvp-access.service"),
            "wifi_fallback": service_state("cvp-wifi-fallback.service"),
            "web": service_state("cvp-web.service"),
        },
        "network": network_status(),
        "midi": midi,
        "selected_midi": selected_midi_name(),
        "audio": audio_lines,
        "keyboards": keyboards,
        "usb": usb_out.splitlines(),
        "events": recent_events(),
    }


DASHBOARD = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CVP Access — Maintenance</title>
<style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#16181d;background:#f4f5f7}
body{margin:0}header{background:#111827;color:white;padding:18px 20px}
header h1{margin:0;font-size:1.35rem}header p{margin:.35rem 0 0;color:#cbd5e1}
main{max-width:1050px;margin:auto;padding:16px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.card{background:white;border-radius:12px;padding:15px;box-shadow:0 1px 4px #0002;margin-bottom:12px}
h2{font-size:1rem;margin:0 0 10px}.row{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid #eee}.row:last-child{border:0}
.ok{color:#08752f;font-weight:700}.bad{color:#b42318;font-weight:700}.muted{color:#667085}
button,a.btn{border:0;border-radius:8px;padding:9px 11px;margin:3px;background:#1f2937;color:white;text-decoration:none;display:inline-block;cursor:pointer}
button.secondary,a.secondary{background:#475467}button.danger{background:#b42318}
pre{white-space:pre-wrap;word-break:break-word;background:#111827;color:#e5e7eb;padding:10px;border-radius:8px;max-height:270px;overflow:auto}
.device{padding:9px 0;border-top:1px solid #eee}.device:first-child{border-top:0}.selected{font-weight:700;color:#08752f}
small{color:#667085}.notice{background:#eef4ff;padding:10px;border-radius:8px;margin-bottom:12px}
</style>
</head>
<body>
<header><h1>CVP Access — Maintenance</h1><p>Melody Music · Raspberry autonome</p></header>
<main>
<div class="notice">Cette page fonctionne localement, sans Internet. Accès de secours : <b>10.42.0.1</b>.</div>
<div class="grid">
<section class="card"><h2>Système</h2><div id="system">Chargement…</div></section>
<section class="card"><h2>Réseau</h2><div id="network">Chargement…</div></section>
<section class="card"><h2>MIDI</h2><div id="midi">Chargement…</div></section>
<section class="card"><h2>Périphériques</h2><div id="devices">Chargement…</div></section>
</div>
<section class="card"><h2>Actions</h2>
<button onclick="action('restart')">Relancer CVP Access</button>
<button class="secondary" onclick="action('doctor')">Lancer le Doctor</button>
<a class="btn secondary" href="/keyboard-map">Carte clavier</a>
<button class="danger" onclick="rebootPi()">Redémarrer le Raspberry</button>
<div id="actionResult" class="muted" style="margin-top:8px"></div>
</section>
<section class="card"><h2>Événements utiles</h2><pre id="events">Chargement…</pre></section>
</main>
<script>
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const badge=s=>'<span class="'+(s==='active'?'ok':'bad')+'">'+esc(s)+'</span>';
async function refresh(){
 const r=await fetch('/api/status',{cache:'no-store'}); const d=await r.json();
 document.getElementById('system').innerHTML=
  '<div class="row"><span>Version</span><b>'+esc(d.version)+'</b></div>'+
  '<div class="row"><span>CVP Access</span>'+badge(d.services.cvp_access)+'</div>'+
  '<div class="row"><span>Fallback Wi-Fi</span>'+badge(d.services.wifi_fallback)+'</div>'+
  '<div class="row"><span>Portail Web</span>'+badge(d.services.web)+'</div>';
 document.getElementById('network').innerHTML=
  '<div class="row"><span>Connexion</span><b>'+esc(d.network.connection)+'</b></div>'+
  '<div class="row"><span>Hotspot</span><b>'+(d.network.hotspot?'CVP-ACCESS':'non')+'</b></div>'+
  '<small>'+esc(d.network.address||'')+'</small>';
 let m='';
 if(!d.midi.length)m='<span class="bad">Aucune interface MIDI bidirectionnelle détectée</span>';
 for(const x of d.midi){
   const sel=d.selected_midi===x.name;
   m+='<div class="device"><div class="'+(sel?'selected':'')+'">'+esc(x.name)+'</div>'+
      '<small>'+esc(x.port)+' · '+esc(x.direction)+'</small><br>'+
      '<button class="secondary" onclick=\'selectMidi('+JSON.stringify(x.name)+')\'>'+(sel?'Sélectionnée':'Utiliser')+'</button></div>';
 }
 document.getElementById('midi').innerHTML=m;
 const audio=d.audio.length?d.audio.join('<br>'):'Aucun audio Yamaha détecté';
 const kb=d.keyboards.length?d.keyboards.join('<br>'):'Aucun clavier USB détecté';
 document.getElementById('devices').innerHTML=
  '<b>Audio</b><div>'+audio+'</div><br><b>Clavier</b><div>'+kb+'</div>'+
  '<br><small>'+d.usb.map(esc).join('<br>')+'</small>';
 document.getElementById('events').textContent=d.events.join('\n')||'Aucun événement utile récent.';
}
async function post(url,body={}){
 const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const d=await r.json(); document.getElementById('actionResult').textContent=d.message||d.error||'OK'; setTimeout(refresh,800);
}
function action(name){post('/api/action/'+name)}
function selectMidi(name){post('/api/midi/select',{name})}
function rebootPi(){if(confirm('Redémarrer complètement le Raspberry ?'))post('/api/action/reboot')}
refresh(); setInterval(refresh,4000);
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "CVPAccessPortal/1.0"

    def allowed(self):
        try:
            ip = ipaddress.ip_address(self.client_address[0])
            return ip.is_loopback or ip in HOTSPOT_NET
        except ValueError:
            return False

    def send_bytes(self, code, body, content_type="text/plain; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        if extra:
            for key, value in extra.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload, code=200):
        self.send_bytes(
            code,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def redirect_portal(self):
        self.send_bytes(
            302,
            b"",
            extra={"Location": f"http://{HOTSPOT_IP}/"},
        )

    def do_GET(self):
        if not self.allowed():
            self.send_bytes(403, b"CVP Access portal: hotspot access only\n")
            return

        path = urlparse(self.path).path

        if path in CAPTIVE_PATHS:
            self.redirect_portal()
            return

        if path == "/api/status":
            self.send_json(build_status())
            return

        if path == "/keyboard-map":
            if not KEYBOARD_MAP.is_file():
                self.send_bytes(404, b"Keyboard map unavailable\n")
                return
            self.send_bytes(
                200,
                KEYBOARD_MAP.read_bytes(),
                "text/html; charset=utf-8",
            )
            return

        if path == "/" or path == "/index.html":
            self.send_bytes(
                200,
                DASHBOARD.encode("utf-8"),
                "text/html; charset=utf-8",
            )
            return

        self.redirect_portal()

    def do_POST(self):
        if not self.allowed():
            self.send_json({"error": "hotspot access only"}, 403)
            return

        length = min(int(self.headers.get("Content-Length", "0") or 0), 8192)
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self.send_json({"error": "JSON invalide"}, 400)
            return

        path = urlparse(self.path).path

        if path == "/api/midi/select":
            name = payload.get("name")
            current = {item["name"] for item in parse_midi_devices()}
            if not isinstance(name, str) or name not in current:
                self.send_json({"error": "Interface MIDI non disponible"}, 400)
                return
            save_midi_name(name)
            run(["systemctl", "restart", "cvp-access.service"], timeout=8)
            self.send_json({"message": f"Interface MIDI sélectionnée : {name}"})
            return

        if path == "/api/action/restart":
            rc, _, err = run(["systemctl", "restart", "cvp-access.service"], timeout=10)
            self.send_json(
                {"message": "CVP Access relancé" if rc == 0 else err or "Échec"},
                200 if rc == 0 else 500,
            )
            return

        if path == "/api/action/doctor":
            doctor = RUNTIME / "cvp_doctor_151.py"
            if not doctor.is_file():
                self.send_json({"error": "Doctor 1.5.1 absent"}, 404)
                return
            env_args = [
                "runuser", "-u", CVP_USER, "--", "env",
                f"HOME=/home/{CVP_USER}",
                f"CVP_RUNTIME_DIR={RUNTIME}",
                f"CVP_CONFIG_FILE={CONFIG_DIR / 'keyboard.toml'}",
                "python3", str(doctor),
            ]
            rc, out, err = run(env_args, timeout=30)
            result = (out + ("\n" + err if err else "")).strip()
            Path("/run/cvp-access-doctor.txt").write_text(result + "\n", encoding="utf-8")
            self.send_json(
                {
                    "message": "Doctor terminé" if rc == 0 else "Doctor terminé avec alertes",
                    "output": result,
                },
                200,
            )
            return

        if path == "/api/action/reboot":
            self.send_json({"message": "Redémarrage demandé"})
            threading.Thread(
                target=lambda: subprocess.run(
                    ["systemctl", "reboot"],
                    check=False,
                ),
                daemon=True,
            ).start()
            return

        self.send_json({"error": "Action inconnue"}, 404)

    def log_message(self, fmt, *args):
        print(
            f"{self.client_address[0]} - "
            + fmt % args,
            flush=True,
        )


def main():
    server = ThreadingHTTPServer(("0.0.0.0", 80), Handler)
    print("CVP Access maintenance portal listening on port 80", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
