"""Robot posting gratis untuk @arifitra_muhammad.

Membaca folder queue/<nama>/post.json + slide-1..5.jpg, lalu menerbitkan
carousel ke Instagram, Threads, dan Halaman Facebook saat jadwalnya tiba.
Status tiap platform dicatat di queue/<nama>/status.json supaya tidak
pernah terbit dua kali, dan platform yang gagal dicoba lagi di putaran berikutnya.

Hanya memakai pustaka bawaan Python (tanpa pip install).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "queue"
REPO = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
GV = os.environ.get("GRAPH_VERSION", "").strip()  # kosong = versi default aplikasi Meta
V = f"/{GV}" if GV else ""
DRY = os.environ.get("DRY_RUN") == "1"


def env(name):
    v = os.environ.get(name, "").strip()
    return v or None


def call(method, url, params):
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        # jangan pernah mencetak token
        raise RuntimeError(f"HTTP {e.code} dari {urllib.parse.urlparse(url).netloc}: {body[:500]}") from None


def wait_ready(url_base, cid, token, field):
    for _ in range(20):
        st = call("GET", f"{url_base}/{cid}", {"fields": field, "access_token": token}).get(field)
        if st in ("FINISHED", "PUBLISHED"):
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Kontainer {cid} gagal diproses: {st}")
        time.sleep(6)
    raise RuntimeError(f"Kontainer {cid} terlalu lama diproses")


def image_urls(folder, post):
    q = urllib.parse.quote
    return [f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/queue/{q(folder.name)}/{q(n)}" for n in post["images"]]


def post_instagram(post, urls):
    uid, tok = env("IG_USER_ID"), env("IG_TOKEN")
    base = f"https://graph.instagram.com{V}"
    alts = post.get("alt_text") or []
    kids = []
    for i, u in enumerate(urls):
        p = {"image_url": u, "is_carousel_item": "true", "access_token": tok}
        if i < len(alts) and alts[i]:
            p["alt_text"] = alts[i][:1000]
        kids.append(call("POST", f"{base}/{uid}/media", p)["id"])
    for k in kids:
        wait_ready(base, k, tok, "status_code")
    cid = call("POST", f"{base}/{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(kids),
                                                "caption": post["caption_instagram"][:2200], "access_token": tok})["id"]
    wait_ready(base, cid, tok, "status_code")
    mid = call("POST", f"{base}/{uid}/media_publish", {"creation_id": cid, "access_token": tok})["id"]
    if post.get("first_comment"):
        try:
            call("POST", f"{base}/{mid}/comments", {"message": post["first_comment"], "access_token": tok})
        except RuntimeError as e:
            print("  (komentar pertama IG dilewati:", e, ")")
    return mid


def post_threads(post, urls):
    uid, tok = env("THREADS_USER_ID"), env("THREADS_TOKEN")
    base = "https://graph.threads.net/v1.0"
    kids = [call("POST", f"{base}/{uid}/threads", {"media_type": "IMAGE", "image_url": u,
                                                     "is_carousel_item": "true", "access_token": tok})["id"] for u in urls]
    for k in kids:
        wait_ready(base, k, tok, "status")
    cid = call("POST", f"{base}/{uid}/threads", {"media_type": "CAROUSEL", "children": ",".join(kids),
                                                  "text": post["caption_threads"][:500], "access_token": tok})["id"]
    wait_ready(base, cid, tok, "status")
    return call("POST", f"{base}/{uid}/threads_publish", {"creation_id": cid, "access_token": tok})["id"]


def post_facebook_page(post, urls):
    pid, tok = env("FB_PAGE_ID"), env("FB_PAGE_TOKEN")
    base = f"https://graph.facebook.com{V}"
    ids = [call("POST", f"{base}/{pid}/photos", {"url": u, "published": "false", "access_token": tok})["id"] for u in urls]
    p = {"message": post["caption_facebook"], "access_token": tok}
    for i, x in enumerate(ids):
        p[f"attached_media[{i}]"] = json.dumps({"media_fbid": x})
    return call("POST", f"{base}/{pid}/feed", p)["id"]


PLATFORMS = {
    "instagram": (post_instagram, ("IG_USER_ID", "IG_TOKEN")),
    "threads": (post_threads, ("THREADS_USER_ID", "THREADS_TOKEN")),
    "facebook_page": (post_facebook_page, ("FB_PAGE_ID", "FB_PAGE_TOKEN")),
}


def run():
    """Terbitkan semua yang jatuh tempo. Mengembalikan daftar (folder, platform, ok, pesan)."""
    if not REPO:
        raise RuntimeError("GITHUB_REPOSITORY kosong; jalankan lewat GitHub Actions.")
    now = datetime.now(timezone.utc)
    events = []
    for folder in sorted(p for p in QUEUE.iterdir() if p.is_dir()) if QUEUE.exists() else []:
        pj = folder / "post.json"
        if not pj.exists():
            continue
        post = json.loads(pj.read_text(encoding="utf-8"))
        when = datetime.fromisoformat(post["publish_at"])
        if when.tzinfo is None:
            events.append((folder.name, "-", False, "publish_at wajib memakai zona waktu, mis. +09:00"))
            continue
        if when > now:
            continue
        sp = folder / "status.json"
        status = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
        urls = image_urls(folder, post)
        for name, (fn, keys) in PLATFORMS.items():
            if not post.get("platforms", {}).get(name) or status.get(name, {}).get("id"):
                continue
            if not all(env(k) for k in keys):
                status[name] = {"skip": "secret belum diisi"}
                continue
            print(f"{folder.name} → {name}")
            if DRY:
                print("  DRY_RUN: tidak benar-benar diposting")
                continue
            try:
                status[name] = {"id": fn(post, urls), "at": datetime.now(timezone.utc).isoformat()}
                print("  terbit:", status[name]["id"])
                events.append((folder.name, name, True, status[name]["id"]))
            except Exception as e:  # dicoba lagi pada jadwal berikutnya
                status[name] = {"error": str(e)[:600], "at": datetime.now(timezone.utc).isoformat()}
                print("  GAGAL:", e)
                events.append((folder.name, name, False, str(e)[:300]))
        sp.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    return events


def main():
    try:
        ev = run()
    except RuntimeError as e:
        sys.exit(str(e))
    if any(not ok for _, _, ok, _ in ev):
        sys.exit(1)


if __name__ == "__main__":
    main()
