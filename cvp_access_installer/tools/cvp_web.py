#!/usr/bin/env python3
"""Local maintenance portal for CVP Access.

The service intentionally exposes only a small set of maintenance actions.
It is reachable from the CVP-ACCESS hotspot subnet and localhost, not from
arbitrary LAN interfaces.
"""

from __future__ import annotations

import glob
import hmac
import ipaddress
import json
import os
import re
import socket
import subprocess
import threading
import time
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
ADMIN_SECRET_FILE = CONFIG_DIR / "hotspot-password"
WIFI_RESULT_FILE = Path("/run/cvp-wifi-connect-result.json")
WIFI_CONNECT_HELPER = Path("/usr/local/sbin/cvp-wifi-connect")
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


def load_hardware_config():
    if not HARDWARE_CONFIG.is_file():
        return {}
    try:
        with HARDWARE_CONFIG.open("rb") as handle:
            data = tomllib.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_hardware_config(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = []

    midi_name = data.get("midi", {}).get("name")
    if isinstance(midi_name, str):
        lines += [
            "[midi]",
            "name = " + json.dumps(midi_name, ensure_ascii=False),
            "",
        ]

    keyboard_path = data.get("keyboard", {}).get("path")
    if isinstance(keyboard_path, str):
        lines += [
            "[keyboard]",
            "path = " + json.dumps(keyboard_path, ensure_ascii=False),
            "",
        ]

    tmp = HARDWARE_CONFIG.with_suffix(".tmp")
    tmp.write_text("\n".join(lines), encoding="utf-8")
    os.chmod(tmp, 0o644)
    tmp.replace(HARDWARE_CONFIG)


def selected_midi_name():
    value = load_hardware_config().get("midi", {}).get("name")
    return value if isinstance(value, str) and value.strip() else None


def selected_keyboard_path():
    value = load_hardware_config().get("keyboard", {}).get("path")
    return value if isinstance(value, str) and value.strip() else None


def save_midi_name(name):
    data = load_hardware_config()
    data.setdefault("midi", {})["name"] = name
    save_hardware_config(data)


def save_keyboard_path(path):
    data = load_hardware_config()
    data.setdefault("keyboard", {})["path"] = path
    save_hardware_config(data)


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


def connected_local_networks():
    """Return private IPv4 networks directly attached to this Raspberry."""
    rc, out, _ = run(["ip", "-j", "-4", "addr", "show"])
    if rc != 0 or not out:
        return []

    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []

    networks = []

    for interface in data:
        if interface.get("ifname") == "lo":
            continue

        for info in interface.get("addr_info", []):
            local = info.get("local")
            prefix = info.get("prefixlen")

            if not local or prefix is None:
                continue

            try:
                address = ipaddress.ip_address(local)
                network = ipaddress.ip_network(
                    f"{local}/{prefix}",
                    strict=False,
                )
            except ValueError:
                continue

            if address.is_private:
                networks.append(network)

    return networks


def client_allowed(address):
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False

    if ip.is_loopback or ip in HOTSPOT_NET:
        return True

    if ip.version != 4:
        return False

    return any(ip in network for network in connected_local_networks())


def admin_secret():
    try:
        return ADMIN_SECRET_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def request_authorized(payload):
    expected = admin_secret()
    supplied = payload.get("admin_password", "")
    return (
        bool(expected)
        and isinstance(supplied, str)
        and hmac.compare_digest(supplied, expected)
    )


def split_nmcli_escaped(line):
    fields = []
    current = []
    escaped = False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
    fields.append("".join(current))
    return fields


def scan_wifi_networks():
    # Some drivers cannot rescan while acting as an AP. The command may still
    # return cached BSS entries; the UI also offers manual SSID entry.
    _, out, _ = run(
        [
            "nmcli",
            "-t",
            "--escape",
            "yes",
            "-f",
            "SSID,SIGNAL,SECURITY",
            "device",
            "wifi",
            "list",
            "ifname",
            "wlan0",
            "--rescan",
            "yes",
        ],
        timeout=12,
    )

    by_ssid = {}
    for line in out.splitlines():
        parts = split_nmcli_escaped(line)
        if len(parts) < 3:
            continue
        ssid = parts[0].strip()
        if not ssid:
            continue
        try:
            signal = int(parts[1])
        except ValueError:
            signal = 0
        security = parts[2].strip()
        previous = by_ssid.get(ssid)
        if previous is None or signal > previous["signal"]:
            by_ssid[ssid] = {
                "ssid": ssid,
                "signal": signal,
                "security": security,
            }

    return sorted(
        by_ssid.values(),
        key=lambda item: (-item["signal"], item["ssid"].lower()),
    )


def wifi_connect_result():
    try:
        data = json.loads(WIFI_RESULT_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def launch_wifi_connect(ssid, password, hidden=False):
    if not WIFI_CONNECT_HELPER.is_file():
        return False, "Assistant de connexion Wi-Fi absent"

    request_file = Path(
        f"/run/cvp-wifi-request-{os.getpid()}-{threading.get_ident()}.json"
    )
    request_file.write_text(
        json.dumps(
            {
                "ssid": ssid,
                "password": password,
                "hidden": bool(hidden),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    os.chmod(request_file, 0o600)

    def worker():
        # Leave enough time for the HTTP response to reach the browser before
        # wlan0 leaves the hotspot.
        time.sleep(0.8)
        subprocess.run(
            [str(WIFI_CONNECT_HELPER), str(request_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            start_new_session=True,
        )

    threading.Thread(target=worker, daemon=True).start()
    return True, "Connexion Wi-Fi lancée"


def network_status():
    _, active, _ = run(
        ["nmcli", "-g", "GENERAL.CONNECTION", "device", "show", "wlan0"]
    )
    _, addr, _ = run(["ip", "-4", "-o", "addr", "show", "dev", "wlan0"])
    return {
        "connection": active or "--",
        "address": addr,
        "hotspot": active == "CVP-ACCESS",
        "hostname": socket.gethostname(),
        "wifi_result": wifi_connect_result(),
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
        "selected_keyboard": selected_keyboard_path(),
        "usb": usb_out.splitlines(),
        "events": recent_events(),
    }


DASHBOARD = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CVP Access</title>
<style>
:root{
  color-scheme:light;
  --bg:#f3f6fb;--panel:#fff;--ink:#172033;--muted:#667085;
  --line:#e5e9f0;--nav:#111827;--accent:#2563eb;--ok:#15803d;
  --warn:#b45309;--bad:#b42318;--soft:#eef4ff;--shadow:0 10px 30px rgba(15,23,42,.07)
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{background:var(--nav);color:#fff}
.header-inner{max-width:1180px;margin:auto;padding:22px 22px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.brand{display:flex;align-items:center;gap:12px}.logo{width:42px;height:42px;border-radius:12px;background:#fff;color:#111827;display:grid;place-items:center;font-weight:800}
.brand h1{font-size:1.18rem;margin:0}.brand p{margin:3px 0 0;color:#cbd5e1;font-size:.9rem}
main{max-width:1180px;margin:auto;padding:22px}
.hero{display:grid;grid-template-columns:1.35fr .65fr;gap:16px;margin-bottom:16px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);padding:18px}
.hero-main{padding:22px}.hero-main h2{margin:0 0 7px;font-size:1.45rem}.hero-main p{margin:0;color:var(--muted)}
.hero-side{display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center}
.status-dot{width:14px;height:14px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 6px #dcfce7;margin-bottom:10px}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}.span-4{grid-column:span 4}.span-6{grid-column:span 6}.span-8{grid-column:span 8}.span-12{grid-column:1/-1}
h3{font-size:1rem;margin:0 0 14px}.sub{color:var(--muted);font-size:.88rem;margin-top:-7px;margin-bottom:12px}
.row{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--line);align-items:center}.row:last-child{border-bottom:0}
.label{color:var(--muted)}.value{font-weight:650;text-align:right}
.pill{display:inline-flex;align-items:center;border-radius:999px;padding:4px 9px;font-size:.78rem;font-weight:700}
.pill.ok{background:#dcfce7;color:var(--ok)}.pill.bad{background:#fee2e2;color:var(--bad)}.pill.warn{background:#fef3c7;color:var(--warn)}
.device{padding:11px 0;border-top:1px solid var(--line)}.device:first-child{border-top:0}.device-name{font-weight:700}.selected{color:var(--ok)}
button,.btn{appearance:none;border:0;border-radius:10px;padding:9px 12px;font-weight:650;cursor:pointer;background:#111827;color:#fff;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:6px}
button:hover,.btn:hover{filter:brightness(1.06)}button.secondary,.btn.secondary{background:#475467}button.primary{background:var(--accent)}button.danger{background:var(--bad)}
button:disabled{opacity:.4;cursor:not-allowed}
.actions{display:flex;flex-wrap:wrap;gap:8px}
input,select{width:100%;padding:10px 11px;border:1px solid #cfd6e3;border-radius:10px;background:#fff;color:var(--ink);outline:none}
input:focus,select:focus{border-color:#8bb3ff;box-shadow:0 0 0 3px #dbeafe}
.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.notice{background:var(--soft);border:1px solid #cfe0ff;border-radius:12px;padding:11px 12px;color:#344054;font-size:.9rem}
.auth{background:#fff8eb;border:1px solid #fde2a7}.auth.ok{background:#ecfdf3;border-color:#b7ebc6}
pre{white-space:pre-wrap;word-break:break-word;background:#0f172a;color:#e5e7eb;padding:14px;border-radius:12px;max-height:320px;overflow:auto;font-size:.82rem}
details summary{cursor:pointer;font-weight:700}
.small{font-size:.82rem;color:var(--muted)}
#toast{position:fixed;right:18px;bottom:18px;max-width:360px;background:#111827;color:#fff;border-radius:12px;padding:11px 14px;box-shadow:0 12px 30px #0003;display:none;z-index:100}
@media(max-width:900px){.hero{grid-template-columns:1fr}.span-4,.span-6,.span-8{grid-column:1/-1}}
@media(max-width:600px){main{padding:12px}.header-inner{padding:16px}.two{grid-template-columns:1fr}.actions>*{flex:1 1 100%}}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="brand">
      <div class="logo">CVP</div>
      <div><h1>CVP Access</h1><p>Console de maintenance Melody Music</p></div>
    </div>
    <div id="topStatus" class="pill ok">En ligne</div>
  </div>
</header>

<main>
  <div class="hero">
    <section class="panel hero-main">
      <h2>État du dispositif</h2>
      <p>Diagnostic, périphériques et configuration du Raspberry CVP Access.</p>
      <div class="notice" style="margin-top:16px">
        Accès local uniquement. Hotspot : <b>10.42.0.1</b> · Réseau local : <b>&lt;hostname&gt;.local</b>
      </div>
    </section>
    <section class="panel hero-side">
      <div class="status-dot"></div>
      <b id="readyText">CVP Access opérationnel</b>
      <span id="versionText" class="small" style="margin-top:5px">Version…</span>
    </section>
  </div>

  <div class="grid">
    <section class="panel span-4"><h3>Système</h3><div id="system">Chargement…</div></section>
    <section class="panel span-4"><h3>Réseau</h3><div id="network">Chargement…</div></section>
    <section class="panel span-4"><h3>MIDI</h3><div id="midi">Chargement…</div></section>

    <section class="panel span-6">
      <h3>Périphériques</h3>
      <p class="sub">Audio Yamaha, clavier USB et périphériques détectés.</p>
      <div id="devices">Chargement…</div>
    </section>

    <section class="panel span-6">
      <h3>Connexion Wi-Fi</h3>
      <p class="sub">Si la connexion échoue, CVP-ACCESS est réactivé automatiquement.</p>
      <div class="actions" style="margin-bottom:10px"><button class="secondary" onclick="scanWifi()">Rechercher les réseaux</button></div>
      <select id="wifiList"><option value="">Recherche en attente…</option></select>
      <div class="two" style="margin-top:9px">
        <input id="manualSsid" placeholder="SSID manuel / réseau caché">
        <input id="wifiPassword" type="password" placeholder="Mot de passe du Wi-Fi">
      </div>
      <div class="actions" style="margin-top:10px"><button class="primary protected" onclick="connectWifi()">Connecter le Raspberry</button></div>
      <div id="wifiResult" class="small" style="margin-top:9px"></div>
    </section>

    <section class="panel span-12">
      <h3>Accès maintenance</h3>
      <div id="authBox" class="notice auth">
        <div class="two">
          <div>
            <b>Déverrouiller les actions</b>
            <div class="small" style="margin-top:4px">Utilise le mot de passe de CVP-ACCESS.</div>
          </div>
          <div style="display:flex;gap:8px">
            <input id="adminPassword" type="password" placeholder="Mot de passe maintenance">
            <button class="primary" onclick="unlock()">Déverrouiller</button>
          </div>
        </div>
        <div id="authMessage" class="small" style="margin-top:8px"></div>
      </div>
    </section>

    <section class="panel span-12">
      <h3>Maintenance</h3>
      <div class="actions">
        <button class="protected" onclick="action('restart')">Relancer CVP Access</button>
        <button class="secondary protected" onclick="action('doctor')">Lancer le Doctor</button>
        <a class="btn secondary" href="/keyboard-map">Carte clavier</a>
        <button class="danger protected" onclick="rebootPi()">Redémarrer le Raspberry</button>
      </div>
      <div id="actionResult" class="small" style="margin-top:10px"></div>
      <div id="doctorBox" style="display:none;margin-top:12px">
        <b>Résultat du Doctor</b>
        <pre id="doctorOutput"></pre>
      </div>
    </section>

    <section class="panel span-12">
      <details>
        <summary>Événements utiles</summary>
        <pre id="events">Chargement…</pre>
      </details>
    </section>
  </div>
</main>
<div id="toast"></div>

<script>
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let unlocked=false;
const admin=document.getElementById('adminPassword');
admin.value=sessionStorage.getItem('cvpAdmin')||'';

function toast(msg){
 const t=document.getElementById('toast'); t.textContent=msg; t.style.display='block';
 clearTimeout(window.__toastTimer); window.__toastTimer=setTimeout(()=>t.style.display='none',3200);
}
function setProtected(enabled){
 document.querySelectorAll('.protected').forEach(x=>x.disabled=!enabled);
}
function badge(s){
 const cls=s==='active'?'ok':(s==='activating'?'warn':'bad');
 return '<span class="pill '+cls+'">'+esc(s)+'</span>';
}

async function unlock(){
 const p=admin.value.trim();
 if(!p){document.getElementById('authMessage').textContent='Saisis le mot de passe de maintenance.';return}
 const r=await fetch('/api/auth/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({admin_password:p})});
 const d=await r.json();
 if(r.ok){
   sessionStorage.setItem('cvpAdmin',p); unlocked=true; setProtected(true);
   document.getElementById('authBox').classList.add('ok');
   document.getElementById('authMessage').textContent='Maintenance déverrouillée pour cette session.';
   toast('Maintenance déverrouillée');
 }else{
   sessionStorage.removeItem('cvpAdmin'); unlocked=false; setProtected(false);
   document.getElementById('authBox').classList.remove('ok');
   document.getElementById('authMessage').textContent=d.error||'Mot de passe incorrect.';
 }
}

async function refresh(){
 const r=await fetch('/api/status',{cache:'no-store'}); const d=await r.json();
 document.getElementById('versionText').textContent='Version '+d.version;
 const coreOk=d.services.cvp_access==='active';
 document.getElementById('readyText').textContent=coreOk?'CVP Access opérationnel':'CVP Access nécessite une vérification';
 document.getElementById('topStatus').className='pill '+(coreOk?'ok':'bad');
 document.getElementById('topStatus').textContent=coreOk?'En ligne':'À vérifier';

 document.getElementById('system').innerHTML=
  '<div class="row"><span class="label">Version</span><span class="value">'+esc(d.version)+'</span></div>'+
  '<div class="row"><span class="label">CVP Access</span>'+badge(d.services.cvp_access)+'</div>'+
  '<div class="row"><span class="label">Fallback Wi-Fi</span>'+badge(d.services.wifi_fallback)+'</div>'+
  '<div class="row"><span class="label">Portail Web</span>'+badge(d.services.web)+'</div>';

 let result=d.network.wifi_result||{};
 document.getElementById('network').innerHTML=
  '<div class="row"><span class="label">Connexion</span><span class="value">'+esc(d.network.connection)+'</span></div>'+
  '<div class="row"><span class="label">Hotspot</span><span class="value">'+(d.network.hotspot?'CVP-ACCESS':'Non')+'</span></div>'+
  '<div class="row"><span class="label">Nom local</span><span class="value">'+esc(d.network.hostname)+'.local</span></div>'+
  '<div class="small" style="margin-top:8px">'+esc(d.network.address||'Aucune adresse Wi-Fi')+'</div>';
 if(result.status) document.getElementById('wifiResult').textContent=result.status+' · '+(result.ssid||'')+(result.detail?' · '+result.detail:'');

 let m='';
 if(!d.midi.length)m='<span class="pill bad">Aucune interface MIDI</span>';
 for(const x of d.midi){
   const sel=d.selected_midi===x.name;
   m+='<div class="device"><div class="device-name '+(sel?'selected':'')+'">'+esc(x.name)+'</div>'+
      '<div class="small">'+esc(x.port)+' · '+esc(x.direction)+'</div>'+
      '<button class="secondary protected" style="margin-top:8px" onclick=\'selectMidi('+JSON.stringify(x.name)+')\'>'+(sel?'Sélectionnée':'Utiliser')+'</button></div>';
 }
 document.getElementById('midi').innerHTML=m;

 const audio=d.audio.length?d.audio.map(esc).join('<br>'):'Aucun audio Yamaha détecté';
 let kb='';
 if(!d.keyboards.length) kb='<span class="small">Aucun clavier USB détecté</span>';
 for(const path of d.keyboards){
   const sel=d.selected_keyboard===path;
   kb+='<div class="device"><div class="device-name '+(sel?'selected':'')+'">'+esc(path.split('/').pop())+'</div>'+
      '<button class="secondary protected" style="margin-top:8px" onclick=\'selectKeyboard('+JSON.stringify(path)+')\'>'+(sel?'Sélectionné':'Utiliser')+'</button></div>';
 }
 document.getElementById('devices').innerHTML=
  '<div class="row"><span class="label">Audio</span><span class="value">'+audio+'</span></div>'+
  '<div style="margin-top:12px"><b>Clavier</b>'+kb+'</div>'+
  '<details style="margin-top:12px"><summary class="small">USB détectés</summary><div class="small" style="margin-top:8px">'+d.usb.map(esc).join('<br>')+'</div></details>';
 document.getElementById('events').textContent=d.events.join('\n')||'Aucun événement utile récent.';
 setProtected(unlocked);
}

async function scanWifi(){
 const box=document.getElementById('wifiResult'); box.textContent='Recherche des réseaux…';
 try{
   const r=await fetch('/api/wifi/scan',{cache:'no-store'}); const d=await r.json();
   const sel=document.getElementById('wifiList'); sel.innerHTML='<option value="">Sélectionner un réseau</option>';
   for(const n of d.networks||[]){
     const o=document.createElement('option'); o.value=n.ssid;
     o.textContent=n.ssid+' · '+n.signal+'%'+(n.security?' · '+n.security:' · ouvert'); sel.appendChild(o);
   }
   box.textContent=(d.networks||[]).length+' réseau(x) détecté(s).';
 }catch(e){box.textContent='Recherche impossible. Saisis le SSID manuellement.'}
}

async function post(url,body={}){
 if(!unlocked){toast('Déverrouille d’abord la maintenance.');return null}
 body.admin_password=admin.value;
 const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const d=await r.json();
 if(r.status===401){
   unlocked=false; setProtected(false); document.getElementById('authBox').classList.remove('ok');
   document.getElementById('authMessage').textContent='Mot de passe maintenance incorrect.';
   toast('Mot de passe incorrect'); return d;
 }
 document.getElementById('actionResult').textContent=d.message||d.error||'OK';
 if(url==='/api/action/doctor' && d.output){
   document.getElementById('doctorBox').style.display='block';
   document.getElementById('doctorOutput').textContent=d.output;
 }
 toast(d.message||d.error||'OK'); setTimeout(refresh,800); return d;
}
function action(name){post('/api/action/'+name)}
function selectMidi(name){post('/api/midi/select',{name})}
function selectKeyboard(path){post('/api/keyboard/select',{path})}
function rebootPi(){if(unlocked&&confirm('Redémarrer complètement le Raspberry ?'))post('/api/action/reboot')}
async function connectWifi(){
 const manual=document.getElementById('manualSsid').value.trim();
 const listed=document.getElementById('wifiList').value;
 const ssid=manual||listed;
 if(!ssid){document.getElementById('wifiResult').textContent='Choisis ou saisis un réseau.';return}
 document.getElementById('wifiResult').textContent='Tentative de connexion à '+ssid+'…';
 const d=await post('/api/wifi/connect',{ssid,password:document.getElementById('wifiPassword').value,hidden:Boolean(manual)});
 if(d&&d.message) document.getElementById('wifiResult').textContent=d.message+' La page peut se couper pendant le changement de réseau.';
}
setProtected(false);
refresh();
if(admin.value) unlock();
setInterval(refresh,5000);
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "CVPAccessPortal/1.0"

    def allowed(self):
        return client_allowed(self.client_address[0])

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
            self.send_bytes(403, b"CVP Access portal: local Wi-Fi access only\n")
            return

        path = urlparse(self.path).path

        if path in CAPTIVE_PATHS:
            self.redirect_portal()
            return

        if path == "/captive-portal":
            body = json.dumps(
                {
                    "captive": True,
                    "user-portal-url": f"http://{HOTSPOT_IP}/",
                }
            ).encode("utf-8")
            self.send_bytes(
                200,
                body,
                "application/captive+json",
            )
            return

        if path == "/api/wifi/scan":
            self.send_json({"networks": scan_wifi_networks()})
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
            self.send_json({"error": "local Wi-Fi access only"}, 403)
            return

        length = min(int(self.headers.get("Content-Length", "0") or 0), 8192)
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self.send_json({"error": "JSON invalide"}, 400)
            return

        path = urlparse(self.path).path

        if path == "/api/auth/check":
            if request_authorized(payload):
                self.send_json({"ok": True, "message": "Maintenance déverrouillée"})
            else:
                self.send_json(
                    {"ok": False, "error": "Mot de passe maintenance incorrect"},
                    401,
                )
            return

        if not request_authorized(payload):
            self.send_json(
                {"error": "Mot de passe maintenance incorrect"},
                401,
            )
            return

        if path == "/api/wifi/connect":
            ssid = payload.get("ssid", "")
            password = payload.get("password", "")
            hidden = bool(payload.get("hidden", False))

            if not isinstance(ssid, str):
                self.send_json({"error": "SSID invalide"}, 400)
                return

            ssid = ssid.strip()
            if not ssid or len(ssid.encode("utf-8")) > 32:
                self.send_json({"error": "SSID invalide"}, 400)
                return

            if not isinstance(password, str) or len(password) > 64:
                self.send_json({"error": "Mot de passe Wi-Fi invalide"}, 400)
                return

            ok, message = launch_wifi_connect(
                ssid,
                password,
                hidden=hidden,
            )
            self.send_json(
                {"message": message},
                200 if ok else 500,
            )
            return

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

        if path == "/api/keyboard/select":
            keyboard_path = payload.get("path")
            current = set(glob.glob("/dev/input/by-id/*-event-kbd"))
            if not isinstance(keyboard_path, str) or keyboard_path not in current:
                self.send_json({"error": "Clavier USB non disponible"}, 400)
                return
            save_keyboard_path(keyboard_path)
            run(["systemctl", "restart", "cvp-access.service"], timeout=8)
            self.send_json(
                {"message": "Clavier sélectionné : " + Path(keyboard_path).name}
            )
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
