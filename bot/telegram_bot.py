"""Bot Telegram "Kantor ASN Go Digital" — memerintah tim AI dari HP.

Berjalan di GitHub Actions (gratis untuk repo publik) dengan long polling
selama RUN_SECONDS, lalu dijadwalkan ulang setiap 5 menit. Hanya merespons
pemilik (TELEGRAM_OWNER_ID). Tanpa pip install.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import urllib.parse
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bot"))
sys.path.insert(0, str(ROOT / "scripts"))
import brain  # noqa: E402
import render  # noqa: E402
import publish  # noqa: E402

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
OWNER = os.environ.get("TELEGRAM_OWNER_ID", "").strip()
RUN_SECONDS = int(os.environ.get("RUN_SECONDS", "280"))
REPO = os.environ.get("GITHUB_REPOSITORY", "pemilik/repo")
PAGES = os.environ.get("PAGES_URL", "").strip() or f"https://{REPO.split('/')[0].lower()}.github.io/{REPO.split('/')[-1]}/"
DRAFTS, QUEUE, STATE = ROOT / "drafts", ROOT / "queue", ROOT / "state"
WIT = brain.WIT
API = f"https://api.telegram.org/bot{TOKEN}/"

# ---------------- Telegram ----------------

def _multipart(fields, files):
    b = uuid.uuid4().hex
    out = []
    for k, v in fields.items():
        out += [f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n".encode(), str(v).encode(), b"\r\n"]
    for k, (name, data) in files.items():
        out += [f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{name}\"\r\nContent-Type: image/jpeg\r\n\r\n".encode(), data, b"\r\n"]
    out.append(f"--{b}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={b}"


def tg(method, params=None, files=None, timeout=60):
    params = params or {}
    if files:
        body, ctype = _multipart(params, files)
    else:
        body, ctype = json.dumps(params).encode(), "application/json"
    req = urllib.request.Request(API + method, data=body, headers={"content-type": ctype}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()).get("result")
    except urllib.error.HTTPError as e:
        print("Telegram", method, e.code, e.read().decode(errors="replace")[:300])
        return None


def send(text, kb=None, chat=None):
    chat = chat or OWNER
    text = text or "(kosong)"
    chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)]
    for i, c in enumerate(chunks):
        p = {"chat_id": chat, "text": c, "disable_web_page_preview": True}
        if kb and i == len(chunks) - 1:
            p["reply_markup"] = {"inline_keyboard": kb}
        tg("sendMessage", p)


def send_album(paths, caption):
    media, files = [], {}
    for i, p in enumerate(paths):
        files[f"f{i}"] = (p.name, p.read_bytes())
        m = {"type": "photo", "media": f"attach://f{i}"}
        if i == 0:
            m["caption"] = caption[:1000]
        media.append(m)
    tg("sendMediaGroup", {"chat_id": OWNER, "media": json.dumps(media)}, files, timeout=120)


def file_bytes(file_id):
    f = tg("getFile", {"file_id": file_id})
    if not f:
        return None
    with urllib.request.urlopen(f"https://api.telegram.org/file/bot{TOKEN}/{f['file_path']}", timeout=60) as r:
        return r.read()

# ---------------- kantor (status untuk monitor 3D) ----------------

OFFICE_P = STATE / "office.json"
office = json.loads(OFFICE_P.read_text(encoding="utf-8")) if OFFICE_P.exists() else {"agents": {}, "log": []}
dirty = False


def now_wit():
    return datetime.now(WIT)


def setag(ids, state, text=""):
    global dirty
    for i in ids:
        office["agents"][i] = {"state": state, "text": text, "at": now_wit().isoformat(timespec="minutes")}
    dirty = True


def log(text):
    global dirty
    office["log"] = ([{"at": now_wit().strftime("%d/%m %H:%M"), "text": text}] + office.get("log", []))[:30]
    dirty = True


def listing():
    q = []
    for d in sorted(QUEUE.glob("*/post.json")):
        post = json.loads(d.read_text(encoding="utf-8"))
        st = json.loads((d.parent / "status.json").read_text(encoding="utf-8")) if (d.parent / "status.json").exists() else {}
        done = [k for k, v in st.items() if v.get("id")]
        err = [k for k, v in st.items() if v.get("error")]
        q.append({"folder": d.parent.name, "publish_at": post.get("publish_at", ""), "topic": post.get("topic", ""),
                  "status": "terbit" if done and not err else "gagal sebagian" if err else "terjadwal", "done": done})
    dr = []
    for d in sorted(DRAFTS.glob("*/meta.json")):
        m = json.loads(d.read_text(encoding="utf-8"))
        dr.append({"id": d.parent.name, "topic": m.get("topik", ""), "at": m.get("at", "")})
    return q, dr


def flush(msg="Status kantor"):
    global dirty
    lama = (now_wit() - timedelta(hours=3)).isoformat(timespec="minutes")
    for a in office["agents"].values():
        if a.get("state") == "done" and a.get("at", "") < lama:
            a.update(state="idle", text="Siaga")
    q, dr = listing()
    office.update({"updated": now_wit().isoformat(timespec="seconds"), "queue": q[-20:], "drafts": dr})
    STATE.mkdir(exist_ok=True)
    OFFICE_P.write_text(json.dumps(office, indent=1, ensure_ascii=False), encoding="utf-8")
    dirty = False
    git_sync(msg)


def git_sync(msg):
    if os.environ.get("NO_GIT") == "1":
        return
    sh = lambda *a: subprocess.run(list(a), cwd=ROOT, capture_output=True, text=True)
    sh("git", "add", "-A", *[d for d in ("drafts", "queue", "state") if (ROOT / d).exists()])
    if sh("git", "diff", "--cached", "--quiet").returncode == 0:
        return
    sh("git", "commit", "-m", msg)
    for _ in range(3):
        sh("git", "pull", "--rebase", "--autostash")
        if sh("git", "push").returncode == 0:
            return
        time.sleep(3)
    print("git push gagal")

# ---------------- pekerjaan ----------------

def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "konten").lower()).strip("-")
    return s[:40] or "konten"


def next_slot(hhmm):
    m = re.match(r"(\d{1,2})[.:](\d{2})", hhmm or "")
    h, mi = (int(m.group(1)), int(m.group(2))) if m else (7, 30)
    t = now_wit().replace(hour=h % 24, minute=mi, second=0, microsecond=0)
    while t < now_wit() + timedelta(minutes=30):
        t += timedelta(days=1)
    return t


def draft_dir(did):
    d = DRAFTS / did
    if not (d / "meta.json").exists():
        raise ValueError(f"Draf {did} tidak ditemukan. Lihat /antrean.")
    return d


def present(did):
    d = draft_dir(did)
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    caps = json.loads((d / "caps.json").read_text(encoding="utf-8"))
    send_album(sorted(d.glob("slide-*.jpg")), f"Draf {did}: {meta.get('topik', '')}")
    slot = datetime.fromisoformat(meta["jadwal"]) if meta.get("jadwal") else next_slot(caps.get("jam"))
    cek = "\n".join(f"• {c.get('butir', '')}" + (f" — {c.get('catatan')}" if c.get("catatan") else "") for c in caps.get("cek", []))
    send(f"INSTAGRAM\n{caps.get('ig', '')}\n\n— — —\nTHREADS\n{caps.get('threads', '')}\n\n— — —\nFACEBOOK\n{caps.get('fb', '')}\n\n— — —\nKomentar pertama: {caps.get('first', '')}")
    send(f"Cek fakta Bu Ratna:\n{cek or '• Tidak ada catatan'}\n\nSaran tayang: {slot.strftime('%d/%m %H:%M')} WIT.\n"
         f"Ubah jadwal: /setuju {did} 2026-12-01 19:30\nRevisi: /revisi {did} <instruksi>",
         kb=[[{"text": f"Setujui · {slot.strftime('%d/%m %H:%M')}", "callback_data": f"ok:{did}"},
              {"text": "Terbitkan sekarang", "callback_data": f"now:{did}"}],
             [{"text": "Buang draf", "callback_data": f"del:{did}"}]])


def produce(args, bahan, photo, when=None):
    pilar, produk, words = "auto", "auto", []
    for i, w in enumerate(args.split()):
        lw = w.lower()
        if i == 0 and lw in ("desa", "kampung"):
            pilar = "desa"
        elif i == 0 and lw == "ai":
            pilar = "ai"
        elif lw.startswith("jual:"):
            produk = {"naskah": "naskah", "cat": "cat", "tidak": "none"}.get(lw[5:], "auto")
        else:
            words.append(w)
    ide = " ".join(words)
    did = now_wit().strftime("%m%d-%H%M")
    d = DRAFTS / did
    if d.exists():
        did += "b"
        d = DRAFTS / did
    for a in brain.AGENTS:
        office["agents"][a] = {"state": "idle", "text": "Siaga"}
    send(f"Rapat produksi dimulai (draf {did}). Bagas & Nadia meriset{' dari bahan Anda' if bahan else ''}…")
    setag(["bagas", "nadia"], "on", "Meriset topik"); log(f"Produksi {did} dimulai"); flush("Produksi dimulai")
    res = brain.research(pilar, ide, bahan)
    setag(["bagas", "nadia"], "done", "Riset selesai"); setag(["rizky", "ratna"], "on", "Menulis naskah"); flush("Riset selesai")
    deck = brain.write_deck(res, sell=produk != "none")
    setag(["rizky", "ratna"], "done", "Naskah siap"); setag(["dewi"], "on", "Menata slide")
    d.mkdir(parents=True, exist_ok=True)
    if photo:
        (d / "cover.jpg").write_bytes(photo)
    render.render(deck, d, photo)
    setag(["dewi"], "done", "Desain siap"); setag(["yoga", "laras", "fajar", "hendra", "maya"], "on", "Menulis caption"); flush("Desain siap")
    caps = brain.captions(res, deck, produk)
    for name, obj in (("research", res), ("deck", deck), ("caps", caps)):
        (d / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
    (d / "meta.json").write_text(json.dumps({"topik": res.get("topik", ""), "pilar": deck.get("pilar"), "produk": produk, "at": now_wit().isoformat(timespec="minutes"), "jadwal": when.isoformat(timespec="minutes") if when else ""}, ensure_ascii=False), encoding="utf-8")
    setag(["yoga", "laras", "fajar", "hendra", "maya"], "done", "Caption siap"); setag(["ratna", "sinta"], "done", "Menunggu persetujuan")
    log(f"Draf {did} siap: {res.get('topik', '')}"); flush(f"Draf {did}")
    present(did)


def revise(did, instr):
    d = draft_dir(did)
    res = json.loads((d / "research.json").read_text(encoding="utf-8"))
    old = json.loads((d / "deck.json").read_text(encoding="utf-8"))
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    send(f"Rizky & Dewi merevisi draf {did}…")
    setag(["rizky", "dewi"], "on", "Merevisi"); flush("Revisi dimulai")
    deck = brain.write_deck(res, sell=meta.get("produk") != "none", revisi=instr, old=old)
    photo = (d / "cover.jpg").read_bytes() if (d / "cover.jpg").exists() else None
    render.render(deck, d, photo)
    caps = brain.captions(res, deck, meta.get("produk", "auto"))
    (d / "deck.json").write_text(json.dumps(deck, indent=1, ensure_ascii=False), encoding="utf-8")
    (d / "caps.json").write_text(json.dumps(caps, indent=1, ensure_ascii=False), encoding="utf-8")
    setag(["rizky", "dewi"], "done", "Revisi siap"); log(f"Draf {did} direvisi"); flush(f"Revisi {did}")
    present(did)


def approve(did, when=None):
    d = draft_dir(did)
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    caps = json.loads((d / "caps.json").read_text(encoding="utf-8"))
    when = when or (datetime.fromisoformat(meta["jadwal"]) if meta.get("jadwal") else next_slot(caps.get("jam")))
    folder = QUEUE / f"{when.strftime('%Y-%m-%d_%H%M')}_{slug(meta.get('topik'))}"
    folder.mkdir(parents=True, exist_ok=True)
    for i in range(1, 6):
        shutil.copy(d / f"slide-{i}.jpg", folder / f"slide-{i}.jpg")
    post = {"publish_at": when.isoformat(timespec="seconds"), "topic": meta.get("topik", ""),
            "platforms": {"instagram": True, "threads": True, "facebook_page": True},
            "caption_instagram": caps.get("ig", ""), "caption_threads": caps.get("threads", ""), "caption_facebook": caps.get("fb", ""),
            "first_comment": caps.get("first", ""), "alt_text": caps.get("alt", []), "images": [f"slide-{i}.jpg" for i in range(1, 6)]}
    (folder / "post.json").write_text(json.dumps(post, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.rmtree(d)
    setag(["sinta"], "done", f"Terjadwal {when.strftime('%d/%m %H:%M')}"); log(f"Disetujui: {meta.get('topik', '')} → {when.strftime('%d/%m %H:%M')} WIT")
    flush(f"Jadwalkan {folder.name}")
    send(f"Masuk antrean terbit: {brain.tgl(when, True)} WIT\nFolder: {folder.name}\nBatalkan sebelum tayang: /batal {folder.name}")


def parse_when(parts):
    if parts and parts[0].lower() == "sekarang":
        return now_wit()
    txt = " ".join(parts)
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2})[.:](\d{2})", txt)
    if m:
        return datetime.strptime(m.group(1), "%Y-%m-%d").replace(hour=int(m.group(2)), minute=int(m.group(3)), tzinfo=WIT)
    m = re.search(r"(\d{1,2})[.:](\d{2})", txt)
    return next_slot(m.group(0)) if m else None


def run_publish(manual=False):
    """Bot tidak memposting sendiri (mencegah posting ganda); ia memanggil workflow Robot Posting."""
    tok = os.environ.get("GITHUB_TOKEN", "").strip()
    if not tok:
        if manual:
            send("GITHUB_TOKEN tidak tersedia; jalankan Robot Posting dari tab Actions.")
        return
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/workflows/publish.yml/dispatches",
                                 data=json.dumps({"ref": "main", "inputs": {"dry_run": "0"}}).encode(), method="POST",
                                 headers={"authorization": f"Bearer {tok}", "accept": "application/vnd.github+json", "content-type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=30)
        setag(["yoga", "laras", "fajar"], "on", "Menerbitkan")
        if manual:
            send("Robot posting dijalankan. Hasilnya dikirim ke sini dalam ±1–2 menit.")
    except urllib.error.HTTPError as e:
        send(f"Gagal menjalankan Robot Posting (kode {e.code}). Pastikan telegram.yml punya izin actions: write.")

HELP = """Kantor ASN Go Digital — perintah:

/produksi [desa|ai] [jual:naskah|cat|tidak] topik
  Tim membuat carousel 5 slide + caption. Balas (reply) sebuah berita/pasal dengan /produksi supaya dijadikan bahan riset. Kirim foto dengan caption /produksi untuk jadi sampul.
/revisi ID instruksi — perbaiki draf
/setuju ID [YYYY-MM-DD HH:MM | HH:MM | sekarang] — masukkan ke antrean terbit
/buang ID — hapus draf
/antrean — lihat draf & jadwal terbit
/batal FOLDER — batalkan jadwal sebelum tayang
/terbitkan — jalankan robot posting sekarang
/tugas NAMA pesan — perintah satu karyawan (sinta, bagas, nadia, rizky, ratna, dewi, yoga, laras, fajar, maya, hendra, putri)
/kantor — status tim + buka kantor 3D

Pesan biasa tanpa perintah dijawab Sinta. Balas (reply) jawaban seorang karyawan untuk melanjutkan obrolan dengannya."""


def handle_message(m):
    text = (m.get("text") or m.get("caption") or "").strip()
    reply = m.get("reply_to_message") or {}
    rtext = (reply.get("text") or reply.get("caption") or "").strip()
    if not text.startswith("/"):
        ctx = rtext or office.get("last_reply", "")
        if re.search(r"(jadwal|posting|post|terbit|carousel|karosel|caraosel|konten|buat|bikin|produksi|antrean|antrian|draf)", text, re.I):
            it = brain.intent(text, ctx)
            act = it.get("aksi")
            if act == "produksi" and it.get("topik"):
                send(f"Siap. Sinta meneruskan ke tim produksi:\n• Topik: {it['topik']}" + (f"\n• Jadwal diminta: {it['waktu']} WIT" if it.get("waktu") else ""))
                photo = file_bytes((m.get("photo") or [])[-1]["file_id"]) if m.get("photo") else None
                return produce(f"{it.get('pilar') or ''} {it['topik']}", it.get("bahan") or "", photo, parse_when((it.get("waktu") or "").split()))
            if act == "setujui":
                _, dr = listing()
                if not dr:
                    return send("Belum ada draf yang menunggu persetujuan. Minta saja: \"buatkan postingan tentang …\".")
                return approve(dr[-1]["id"], parse_when((it.get("waktu") or "").split()))
            if act == "terbitkan":
                q, dr = listing()
                if dr:
                    return approve(dr[-1]["id"], now_wit()) or run_publish(manual=True)
                return run_publish(manual=True)
            if act == "antrean":
                return handle_message({**m, "text": "/antrean"})
        agent = "sinta"
        for k, (n, r, _) in brain.AGENTS.items():
            if rtext.startswith(f"{n} · "):
                agent = k
        return do_task(agent, text, rtext or None)
    cmd, _, args = text.partition(" ")
    cmd = cmd.split("@")[0].lower()
    parts = args.split()
    if cmd in ("/start", "/bantuan", "/help"):
        send(HELP, kb=[[{"text": "Buka Kantor 3D", "url": PAGES}]])
    elif cmd == "/id":
        send(f"Chat ID Anda: {m['chat']['id']}")
    elif cmd == "/produksi":
        photo = None
        ph = m.get("photo") or reply.get("photo")
        if ph:
            photo = file_bytes(ph[-1]["file_id"])
        produce(args, rtext if rtext and not reply.get("photo") else "", photo)
    elif cmd == "/revisi":
        if len(parts) < 2:
            return send("Format: /revisi ID instruksi")
        revise(parts[0], args.split(None, 1)[1])
    elif cmd == "/setuju":
        if not parts:
            return send("Format: /setuju ID [YYYY-MM-DD HH:MM | HH:MM | sekarang]")
        approve(parts[0], parse_when(parts[1:]))
    elif cmd == "/buang":
        if parts:
            shutil.rmtree(draft_dir(parts[0])); log(f"Draf {parts[0]} dibuang"); flush("Buang draf"); send("Draf dibuang.")
    elif cmd == "/antrean":
        q, dr = listing()
        lines = ["DRAF menunggu persetujuan:"] + [f"• {d['id']} — {d['topic']}" for d in dr] if dr else ["Tidak ada draf."]
        lines += ["", "ANTREAN TERBIT:"] + ([f"• {x['publish_at'][:16].replace('T', ' ')} — {x['topic']} [{x['status']}]\n  {x['folder']}" for x in q[-15:]] or ["Kosong."])
        send("\n".join(lines))
    elif cmd == "/batal":
        hits = [p for p in QUEUE.iterdir() if p.is_dir() and parts and p.name.startswith(parts[0])] if QUEUE.exists() else []
        if len(hits) != 1:
            return send("Folder tidak ditemukan atau ambigu. Lihat /antrean.")
        st = hits[0] / "status.json"
        if st.exists() and any(v.get("id") for v in json.loads(st.read_text(encoding="utf-8")).values()):
            return send("Sudah terbit di sebagian platform; hapus manual dari aplikasinya.")
        shutil.rmtree(hits[0]); log(f"Jadwal dibatalkan: {hits[0].name}"); flush("Batal jadwal"); send("Jadwal dibatalkan.")
    elif cmd == "/terbitkan":
        run_publish(manual=True)
    elif cmd == "/tugas":
        if not parts or parts[0].lower() not in brain.AGENTS:
            return send("Pilih karyawan: " + ", ".join(brain.AGENTS) + "\nContoh: /tugas hendra tulis promo Simulasi CAT CPNS")
        do_task(parts[0].lower(), args.split(None, 1)[1] if len(parts) > 1 else "Laporkan apa yang bisa kamu kerjakan hari ini.", rtext or None)
    elif cmd == "/kantor":
        lines = [f"{n} ({r}): {office['agents'].get(k, {}).get('text') or 'Siaga'}" for k, (n, r, _) in brain.AGENTS.items()]
        send("Status Kantor Lantai 2\n\n" + "\n".join(lines), kb=[[{"text": "Buka Kantor 3D", "url": PAGES}]])
    else:
        send("Perintah tidak dikenal. Ketik /bantuan.")


def do_task(agent, task, ctx):
    n, r, _ = brain.AGENTS[agent]
    tg("sendChatAction", {"chat_id": OWNER, "action": "typing"})
    setag([agent], "on", "Mengerjakan tugas"); flush(f"{n} bekerja")
    out = brain.agent_task(agent, task, ctx)
    office["last_reply"] = f"{n}: {out}"[:3000]
    setag([agent], "done", "Tugas selesai"); log(f"{n}: {task[:60]}")
    send(f"{n} · {r}\n\n{out}")


def handle_callback(cb):
    if str(cb["from"]["id"]) != OWNER:
        return
    tg("answerCallbackQuery", {"callback_query_id": cb["id"]})
    act, _, did = cb.get("data", "").partition(":")
    if act == "ok":
        approve(did)
    elif act == "now":
        approve(did, now_wit()); run_publish(manual=True)
    elif act == "del":
        shutil.rmtree(draft_dir(did)); log(f"Draf {did} dibuang"); flush("Buang draf"); send("Draf dibuang.")


def process(u):
    if "callback_query" in u:
        return handle_callback(u["callback_query"])
    m = u.get("message")
    if not m:
        return
    if not OWNER:
        tg("sendMessage", {"chat_id": m["chat"]["id"], "text": f"Bot belum dikunci. Chat ID Anda: {m['chat']['id']}\nSimpan angka ini sebagai secret TELEGRAM_OWNER_ID di GitHub."})
        return
    if str(m["chat"]["id"]) != OWNER:
        return
    handle_message(m)


def safe(u):
    global dirty
    try:
        process(u)
    except Exception as e:
        traceback.print_exc()
        dirty = True
        for a in office["agents"].values():
            if a.get("state") == "on":
                a.update(state="idle", text="Terkendala")
        send(f"Maaf, pekerjaan terhenti: {e}")


def main():
    if not TOKEN:
        sys.exit("TELEGRAM_BOT_TOKEN belum diisi.")
    STATE.mkdir(exist_ok=True)
    upd = os.environ.get("UPDATE_JSON", "").strip()
    if upd:  # mode utama: dibangunkan Cloudflare untuk satu pesan
        u = json.loads(upd)
        print("Memproses pesan", u.get("update_id"))
        safe(u)
        if dirty:
            flush()
        git_sync("Kantor: proses pesan Telegram")
        return
    # mode cadangan: long polling (hanya bila webhook Cloudflare belum dipasang)
    me = tg("getMe")
    if not me:
        sys.exit("Token Telegram ditolak. Salin ulang token dari @BotFather ke secret TELEGRAM_BOT_TOKEN.")
    print(f"Bot @{me.get('username')} berjalan (mode polling).")
    bp = STATE / "bot.json"
    st = json.loads(bp.read_text(encoding="utf-8")) if bp.exists() else {"offset": 0}
    end = time.time() + RUN_SECONDS
    while time.time() < end - 8:
        ups = tg("getUpdates", {"offset": st["offset"], "timeout": int(min(25, max(1, end - time.time() - 8))),
                                "allowed_updates": ["message", "callback_query"]}, timeout=40)
        if ups is None:
            print("getUpdates gagal (token salah, atau webhook Cloudflare sudah aktif — itu normal).")
            break
        for u in ups:
            st["offset"] = u["update_id"] + 1
            bp.write_text(json.dumps(st), encoding="utf-8")
            safe(u)
        if dirty:
            flush()
    bp.write_text(json.dumps(st), encoding="utf-8")
    git_sync("Simpan posisi bot")


if __name__ == "__main__":
    main()
