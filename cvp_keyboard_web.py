#!/usr/bin/env python3
"""Web-facing keyboard editor helpers for CVP Access 1.7."""

from __future__ import annotations

from cvp_action_catalog import ACTION_CATALOG, CATEGORY_LABELS, action_text, public_catalog
from cvp_keyboard import parse_action
from cvp_keyboard_layout import EDITOR_LAYERS, RESERVED_KEYS, editor_keys
from cvp_keyboard_profiles import (
    ProfileError,
    RevisionConflict,
    activate_profile,
    create_profile,
    delete_profile,
    duplicate_profile,
    get_profile,
    list_profiles,
    rename_profile,
    save_profile,
)


def _variants():
    result = []
    for item in public_catalog():
        if item["deprecated"]:
            continue
        name = item["id"]
        values = item["values"]
        if item["parameter_required"]:
            for value in values:
                raw = f"{name}:{value}"
                result.append(
                    {
                        "value": raw,
                        "label": action_text(name, value),
                        "description": item["description"],
                        "category": item["category"],
                        "category_label": item["category_label"],
                        "synonyms": item["synonyms"],
                    }
                )
        else:
            result.append(
                {
                    "value": name,
                    "label": item["label"],
                    "description": item["description"],
                    "category": item["category"],
                    "category_label": item["category_label"],
                    "synonyms": item["synonyms"],
                }
            )
    return result


def catalog_payload():
    return {
        "layers": [{"prefix": prefix, "label": label} for prefix, label in EDITOR_LAYERS],
        "rows": editor_keys(),
        "reserved": RESERVED_KEYS,
        "categories": CATEGORY_LABELS,
        "actions": _variants(),
    }


def _binding_labels(bindings):
    labels = {}
    for combo, raw in bindings.items():
        try:
            invocation = parse_action(raw)
            labels[combo] = action_text(invocation.name, invocation.parameter)
        except ValueError:
            labels[combo] = raw
    return labels


def config_payload(profile_id=None):
    profile = get_profile(profile_id)
    profile["binding_labels"] = _binding_labels(profile["bindings"])
    return profile


def profiles_payload():
    return list_profiles()


def handle_write(path, payload):
    try:
        if path == "/api/keyboard/apply":
            result = save_profile(
                payload.get("profile_id"),
                payload.get("revision"),
                payload.get("changes"),
            )
            result["binding_labels"] = _binding_labels(result["bindings"])
            return {"ok": True, "profile": result}, 200

        if path == "/api/keyboard/profiles/create":
            source_id = payload.get("source_id")
            profile = create_profile(payload.get("name"), source_id=source_id)
            changes = payload.get("changes") or []
            if changes:
                profile = save_profile(profile["id"], profile["revision"], changes)
            profile["binding_labels"] = _binding_labels(profile["bindings"])
            return {"ok": True, "profile": profile, "profiles": list_profiles()}, 201

        if path == "/api/keyboard/profiles/duplicate":
            profile = duplicate_profile(payload.get("source_id"), payload.get("name"))
            profile["binding_labels"] = _binding_labels(profile["bindings"])
            return {"ok": True, "profile": profile, "profiles": list_profiles()}, 201

        if path == "/api/keyboard/profiles/rename":
            profile = rename_profile(payload.get("profile_id"), payload.get("name"))
            profile["binding_labels"] = _binding_labels(profile["bindings"])
            return {"ok": True, "profile": profile, "profiles": list_profiles()}, 200

        if path == "/api/keyboard/profiles/delete":
            return {"ok": True, "profiles": delete_profile(payload.get("profile_id"))}, 200

        if path == "/api/keyboard/profiles/activate":
            result = activate_profile(payload.get("profile_id"))
            profile = result["profile"]
            profile["binding_labels"] = _binding_labels(profile["bindings"])
            return {
                "ok": True,
                "message": "Configuration activée. CVP Access a redémarré correctement.",
                "profile": profile,
                "profiles": list_profiles(),
            }, 200

        return {"error": "Action clavier inconnue"}, 404
    except RevisionConflict as exc:
        return {"error": str(exc), "conflict": True}, 409
    except ProfileError as exc:
        return {"error": str(exc)}, 400
    except Exception as exc:
        return {"error": f"Erreur interne de configuration clavier : {exc}"}, 500


KEYBOARD_EDITOR = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CVP Access — Configuration clavier</title>
<style>
:root{color-scheme:light;--bg:#f3f6fb;--panel:#fff;--ink:#172033;--muted:#667085;--line:#dfe5ee;--accent:#2563eb;--ok:#15803d;--warn:#b45309;--bad:#b42318;--shadow:0 10px 30px rgba(15,23,42,.07)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
header{background:#111827;color:#fff}.head{max-width:1440px;margin:auto;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;gap:14px}
h1{font-size:1.15rem;margin:0}.head a{color:#fff}.wrap{max-width:1440px;margin:auto;padding:18px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);padding:16px}
.toolbar{display:grid;grid-template-columns:minmax(240px,1fr) auto;gap:14px;margin-bottom:14px}.profile-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:end}
label{font-weight:650;font-size:.88rem}select,input{width:100%;padding:10px;border:1px solid #b9c2cf;border-radius:9px;background:#fff;font:inherit}
button,.btn{border:1px solid #c9d1dc;border-radius:9px;padding:9px 12px;background:#fff;color:var(--ink);font:inherit;font-weight:650;cursor:pointer}
button:hover{border-color:#8da2c0}button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #93c5fd;outline-offset:2px}
button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}button.danger{color:var(--bad)}button:disabled{opacity:.5;cursor:not-allowed}
.badge{display:inline-flex;padding:3px 8px;border-radius:999px;font-size:.78rem;font-weight:700}.badge.ok{background:#dcfce7;color:var(--ok)}.badge.warn{background:#fef3c7;color:var(--warn)}
.layers{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0}.layers button[aria-selected="true"]{background:#111827;color:#fff;border-color:#111827}
.layout{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(300px,.75fr);gap:14px}.keyboard{overflow-x:auto;padding-bottom:4px}
.krow{display:flex;gap:5px;min-width:980px;margin-bottom:5px}.key{min-height:72px;flex-basis:0;min-width:44px;padding:6px 5px;display:flex;flex-direction:column;justify-content:space-between;text-align:left;background:#fff}
.key .name{font-size:.78rem;font-weight:800}.key .fn{font-size:.69rem;line-height:1.12;color:#344054;overflow-wrap:anywhere}.key.selected{outline:3px solid var(--accent);outline-offset:1px}.key.modified{background:#fff7ed;border-color:#f59e0b}.key.reserved{background:#f3f4f6}.key.unassignable{background:#f8fafc;color:#98a2b3}
.editor h2{margin:0 0 4px;font-size:1.15rem}.muted{color:var(--muted);font-size:.88rem}.current{padding:10px;margin:10px 0;background:#f8fafc;border-radius:9px}
.categories{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}.categories button{padding:6px 9px;font-size:.82rem}.categories button.active{background:#e8efff;border-color:#7aa2ef}
.actions{max-height:330px;overflow:auto;border:1px solid var(--line);border-radius:10px}.action{display:block;width:100%;text-align:left;border:0;border-bottom:1px solid var(--line);border-radius:0;padding:10px}.action:last-child{border-bottom:0}.action strong{display:block}.action span{display:block;color:var(--muted);font-size:.78rem;margin-top:2px}
.pending{margin-top:14px}.change{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-top:1px solid var(--line)}.change:first-child{border-top:0}.change small{display:block;color:var(--muted)}
.sticky{position:sticky;bottom:10px;margin-top:14px;background:#111827;color:#fff;border-radius:12px;padding:12px 14px;display:flex;justify-content:space-between;align-items:center;gap:10px;box-shadow:0 10px 28px rgba(0,0,0,.18)}.sticky .buttons{display:flex;gap:8px}.sticky button{background:#fff}.sticky .primary{background:#2563eb;color:#fff}
.manager{margin-top:14px;display:grid;grid-template-columns:1fr auto;gap:8px}.manager .wide{grid-column:1/-1}.status{min-height:22px;margin-top:8px;font-size:.88rem}.status.bad{color:var(--bad)}.status.ok{color:var(--ok)}
@media(max-width:900px){.toolbar,.layout{grid-template-columns:1fr}.editor{order:-1}.krow{min-width:900px}.sticky{align-items:flex-start;flex-direction:column}}
</style>
</head>
<body>
<header><div class="head"><h1>CVP Access 1.7 — Configuration clavier</h1><a href="/">Retour maintenance</a></div></header>
<main class="wrap">
<section class="panel toolbar">
 <div>
  <label for="profileSelect">Configuration ouverte</label>
  <select id="profileSelect" onchange="selectProfile(this.value)"></select>
  <div id="profileState" class="muted" style="margin-top:6px"></div>
 </div>
 <div class="profile-actions">
  <button onclick="activateSelected()" id="activateBtn">Activer cette configuration</button>
  <a class="btn" href="/keyboard-map" target="_blank" rel="noopener">Voir / imprimer la carte</a>
 </div>
</section>

<section class="panel">
 <div class="layers" id="layers" role="tablist" aria-label="Couche clavier"></div>
 <div class="layout">
  <div class="keyboard" id="keyboard" aria-label="Clavier AZERTY interactif"></div>
  <aside class="editor">
   <h2 id="selectedTitle">Sélectionne une touche</h2>
   <div id="selectedCombo" class="muted"></div>
   <div class="current"><strong>Affectation</strong><div id="currentAction">—</div></div>
   <button class="danger" id="unassignBtn" onclick="unassign()" disabled>Désaffecter</button>
   <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
   <label for="searchAction">Rechercher une fonction</label>
   <input id="searchAction" type="search" placeholder="Ex. solo 8, Main C, volume Song" oninput="renderActions()">
   <div class="categories" id="categories"></div>
   <div class="actions" id="actions" aria-live="polite"></div>
  </aside>
 </div>

 <div class="pending">
  <h3>Modifications en attente</h3>
  <div id="changes" class="muted">Aucune modification.</div>
 </div>

 <div class="manager">
  <div>
   <label for="profileName">Nom de configuration</label>
   <input id="profileName" maxlength="80" placeholder="Ex. Accompagnement gospel">
  </div>
  <button onclick="saveAs()">Enregistrer sous…</button>
  <div class="wide profile-actions">
   <button onclick="renameSelected()">Renommer</button>
   <button onclick="duplicateSelected()">Dupliquer</button>
   <button class="danger" onclick="deleteSelected()">Supprimer</button>
  </div>
 </div>
 <div>
  <label for="adminPassword">Mot de passe maintenance pour enregistrer/activer</label>
  <input id="adminPassword" type="password" autocomplete="current-password">
 </div>
 <div id="status" class="status" role="status" aria-live="polite"></div>

 <div class="sticky">
  <strong id="dirtyCount">0 modification en attente</strong>
  <div class="buttons">
   <button onclick="resetPending()">Tout annuler</button>
   <button class="primary" id="saveBtn" onclick="saveCurrent()">Enregistrer</button>
  </div>
 </div>
</section>
</main>

<script>
let catalog=null, profiles=null, profile=null, layer="", selectedKey=null, pending={}, category="all";
const $=id=>document.getElementById(id);
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const password=()=>{const v=$("adminPassword").value;sessionStorage.setItem("cvpAdmin",v);return v};
$("adminPassword").value=sessionStorage.getItem("cvpAdmin")||"";

async function api(url,opts={}){
 const r=await fetch(url,opts);let d={};
 try{d=await r.json()}catch(e){}
 if(!r.ok)throw new Error(d.error||("Erreur HTTP "+r.status));
 return d;
}
async function post(url,data){
 return api(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...data,admin_password:password()})});
}
function status(msg,bad=false){$("status").textContent=msg;$("status").className="status "+(bad?"bad":"ok")}
function comboFor(key){return layer?layer+"+"+key:key}
function rawFor(combo){
 if(Object.prototype.hasOwnProperty.call(pending,combo)) return pending[combo];
 return profile?.bindings?.[combo]??null;
}
function labelForRaw(raw){
 if(raw===null||raw===undefined)return "Non affectée";
 const a=catalog.actions.find(x=>x.value===raw);
 return a?a.label:raw;
}
function currentCombo(){return selectedKey?comboFor(selectedKey):null}

async function boot(){
 [catalog,profiles]=await Promise.all([api("/api/keyboard/catalog"),api("/api/keyboard/profiles")]);
 renderProfiles();renderLayers();renderCategories();
 const id=profiles.active_profile_id||profiles.profiles[0]?.id;
 if(id)await loadProfile(id);
}
function renderProfiles(){
 const sel=$("profileSelect");sel.innerHTML="";
 for(const p of profiles.profiles){
  const o=document.createElement("option");o.value=p.id;o.textContent=p.name+(p.active?" — ACTIVE":"");sel.appendChild(o);
 }
 if(profile)sel.value=profile.id;
}
async function loadProfile(id){
 profile=await api("/api/keyboard/config?id="+encodeURIComponent(id));
 pending={};selectedKey=null;$("profileSelect").value=id;
 $("profileName").value=profile.name;
 renderAll();
}
async function selectProfile(id){
 if(Object.keys(pending).length&&!confirm("Abandonner les modifications en attente ?")){$("profileSelect").value=profile.id;return}
 await loadProfile(id);
}
function renderLayers(){
 const box=$("layers");box.innerHTML="";
 for(const l of catalog.layers){
  const b=document.createElement("button");b.type="button";b.textContent=l.label;b.dataset.prefix=l.prefix;
  b.setAttribute("role","tab");b.setAttribute("aria-selected",String(layer===l.prefix));
  b.onclick=()=>{layer=l.prefix;selectedKey=null;renderAll()};box.appendChild(b);
 }
}
function renderKeyboard(){
 const root=$("keyboard");root.innerHTML="";
 for(const row of catalog.rows){
  const div=document.createElement("div");div.className="krow";
  for(const item of row){
   const b=document.createElement("button");b.type="button";b.className="key";b.style.flexGrow=item.width;
   const key=item.key;const combo=item.assignable?comboFor(key):"";
   let label=item.label, fn="";
   if(item.reserved){b.classList.add("reserved");fn=item.reserved_label+" — Réservée";b.disabled=true}
   else if(!item.assignable){b.classList.add("unassignable");fn="Modificateur";b.disabled=true}
   else{
    const raw=rawFor(combo);fn=labelForRaw(raw);
    if(Object.prototype.hasOwnProperty.call(pending,combo))b.classList.add("modified");
    if(selectedKey===key)b.classList.add("selected");
    b.onclick=()=>{selectedKey=key;renderAll();$("selectedTitle").focus?.()};
   }
   b.innerHTML='<span class="name">'+esc(label)+'</span><span class="fn">'+esc(fn)+'</span>';
   b.setAttribute("aria-label",label+", "+fn);div.appendChild(b);
  }
  root.appendChild(div);
 }
}
function renderSelected(){
 const combo=currentCombo();
 if(!combo){$("selectedTitle").textContent="Sélectionne une touche";$("selectedCombo").textContent="";$("currentAction").textContent="—";$("unassignBtn").disabled=true;return}
 $("selectedTitle").textContent=selectedKey;$("selectedTitle").tabIndex=-1;
 $("selectedCombo").textContent=combo;
 const raw=rawFor(combo);$("currentAction").textContent=labelForRaw(raw);
 $("unassignBtn").disabled=raw===null;
}
function renderCategories(){
 const root=$("categories");root.innerHTML="";
 const entries=[["all","Toutes"],...Object.entries(catalog.categories)];
 for(const [id,label] of entries){
  const b=document.createElement("button");b.type="button";b.textContent=label;b.className=category===id?"active":"";
  b.onclick=()=>{category=id;renderCategories();renderActions()};root.appendChild(b);
 }
}
function renderActions(){
 const root=$("actions"),q=$("searchAction").value.trim().toLowerCase();root.innerHTML="";
 const filtered=catalog.actions.filter(a=>{
  if(category!=="all"&&a.category!==category)return false;
  const hay=[a.label,a.description,a.category_label,...(a.synonyms||[])].join(" ").toLowerCase();
  return !q||hay.includes(q);
 });
 if(!filtered.length){root.innerHTML='<div class="muted" style="padding:10px">Aucune fonction trouvée.</div>';return}
 for(const a of filtered){
  const b=document.createElement("button");b.type="button";b.className="action";
  b.innerHTML="<strong>"+esc(a.label)+"</strong><span>"+esc(a.description)+"</span>";
  b.onclick=()=>assign(a.value);root.appendChild(b);
 }
}
function assign(raw){
 const combo=currentCombo();if(!combo){status("Sélectionne d’abord une touche.",true);return}
 pending[combo]=raw;renderAll();
}
function unassign(){const combo=currentCombo();if(combo){pending[combo]=null;renderAll()}}
function renderChanges(){
 const root=$("changes"),entries=Object.entries(pending);
 $("dirtyCount").textContent=entries.length+" modification"+(entries.length>1?"s":"")+" en attente";
 $("saveBtn").disabled=!entries.length||profile?.protected;
 if(!entries.length){root.className="muted";root.textContent="Aucune modification.";return}
 root.className="";
 root.innerHTML="";
 for(const [combo,after] of entries){
  const before=profile.bindings[combo]??null;
  const row=document.createElement("div");row.className="change";
  row.innerHTML='<div><strong>'+esc(combo)+'</strong><small>'+esc(labelForRaw(before))+' → '+esc(labelForRaw(after))+'</small></div>';
  const b=document.createElement("button");b.textContent="Annuler";b.onclick=()=>{delete pending[combo];renderAll()};row.appendChild(b);root.appendChild(row);
 }
}
function renderProfileState(){
 if(!profile)return;
 const mismatch=profile.active&&!profile.active_file_matches_profile;
 $("profileState").innerHTML=(profile.active?'<span class="badge ok">ACTIVE</span>':'<span class="badge warn">NON ACTIVE</span>')+
  (profile.protected?' &nbsp; Profil usine protégé':'')+(mismatch?' &nbsp; keyboard.toml a été modifié hors du portail':'');
 $("activateBtn").disabled=profile.active||Object.keys(pending).length>0;
}
function renderAll(){renderProfiles();renderLayers();renderKeyboard();renderSelected();renderActions();renderChanges();renderProfileState()}
function resetPending(){pending={};renderAll()}
function changesPayload(){return Object.entries(pending).map(([combo,action])=>({combo,action}))}

async function saveCurrent(){
 if(profile.protected){status("Le profil usine est en lecture seule. Utilise Enregistrer sous…",true);return}
 try{
  const d=await post("/api/keyboard/apply",{profile_id:profile.id,revision:profile.revision,changes:changesPayload()});
  profile=d.profile;pending={};profiles=await api("/api/keyboard/profiles");status("Configuration enregistrée.");renderAll();
 }catch(e){status(e.message,true)}
}
async function saveAs(){
 const name=$("profileName").value.trim();if(!name){status("Saisis le nom de la nouvelle configuration.",true);return}
 try{
  const d=await post("/api/keyboard/profiles/create",{name,source_id:profile.id,changes:changesPayload()});
  profiles=d.profiles;profile=d.profile;pending={};status("Nouvelle configuration enregistrée : "+profile.name);renderAll();
 }catch(e){status(e.message,true)}
}
async function renameSelected(){
 const name=$("profileName").value.trim();if(!name){status("Saisis le nouveau nom.",true);return}
 try{const d=await post("/api/keyboard/profiles/rename",{profile_id:profile.id,name});profile=d.profile;profiles=await api("/api/keyboard/profiles");status("Configuration renommée.");renderAll()}catch(e){status(e.message,true)}
}
async function duplicateSelected(){
 const name=$("profileName").value.trim();if(!name){status("Saisis le nom de la copie.",true);return}
 try{const d=await post("/api/keyboard/profiles/duplicate",{source_id:profile.id,name});profiles=d.profiles;profile=d.profile;pending={};status("Configuration dupliquée.");renderAll()}catch(e){status(e.message,true)}
}
async function deleteSelected(){
 if(!confirm("Supprimer la configuration « "+profile.name+" » ?"))return;
 try{const d=await post("/api/keyboard/profiles/delete",{profile_id:profile.id});profiles=d.profiles;const id=profiles.active_profile_id||profiles.profiles[0]?.id;if(id)await loadProfile(id);status("Configuration supprimée.")}catch(e){status(e.message,true)}
}
async function activateSelected(){
 if(Object.keys(pending).length){status("Enregistre ou annule les modifications avant d’activer ce profil.",true);return}
 try{const d=await post("/api/keyboard/profiles/activate",{profile_id:profile.id});profiles=d.profiles;profile=d.profile;status(d.message);renderAll()}catch(e){status(e.message,true)}
}
document.addEventListener("keydown",e=>{
 if(["INPUT","SELECT","TEXTAREA"].includes(document.activeElement?.tagName))return;
 if(e.ctrlKey||e.altKey||e.metaKey)return;
 const map={" ":"SPACE","Enter":"ENTER","Escape":"ESC","ArrowUp":"UP","ArrowDown":"DOWN","ArrowLeft":"LEFT","ArrowRight":"RIGHT","PageUp":"PAGEUP","PageDown":"PAGEDOWN","Home":"HOME","End":"END","Insert":"INSERT","Delete":"DELETE"};
 let k=map[e.key]||(/^F([1-9]|1[0-6])$/.test(e.key)?e.key:null);
 if(!k&&e.key.length===1&&/[a-z]/i.test(e.key))k=e.key.toUpperCase();
 if(k){const item=catalog?.rows.flat().find(x=>x.key===k&&x.assignable&&!x.reserved);if(item){selectedKey=k;renderAll()}}
});
boot().catch(e=>status(e.message,true));
</script>
</body></html>
"""
