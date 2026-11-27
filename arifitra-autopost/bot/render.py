"""Merender naskah carousel (deck JSON) menjadi 5 JPG memakai Chrome headless.

Desainnya identik dengan Studio di Kantor ASN Go Digital karena kode
renderernya sama (renderer/render.html). Tanpa pip install: memakai
Google Chrome yang sudah terpasang di runner GitHub Actions.
"""
import base64
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "renderer" / "render.html"


def chrome():
    for c in (os.environ.get("CHROME_BIN"), "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if c and shutil.which(c):
            return shutil.which(c)
    raise RuntimeError("Chrome tidak ditemukan. Set CHROME_BIN.")


def render(deck, out_dir, photo_bytes=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    html = TPL.read_text(encoding="utf-8")
    deck_js = json.dumps(deck, ensure_ascii=False).replace("<", "\\u003c")
    html = html.replace("window.DECK=/*DECK*/null", "window.DECK=" + deck_js, 1)
    if photo_bytes:
        html = html.replace("window.PHOTO=/*PHOTO*/null", 'window.PHOTO="data:image/jpeg;base64,' + base64.b64encode(photo_bytes).decode() + '"', 1)
    # file sementara di folder renderer supaya font lokal ikut termuat
    fd, tmp = tempfile.mkstemp(suffix=".html", dir=TPL.parent)
    os.close(fd)
    Path(tmp).write_text(html, encoding="utf-8")
    try:
        res = subprocess.run(
            [chrome(), "--headless=new", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
             "--virtual-time-budget=15000", "--run-all-compositor-stages-before-draw", "--dump-dom", "file://" + tmp],
            capture_output=True, text=True, timeout=120)
    finally:
        os.remove(tmp)
    dom = res.stdout
    a = dom.find('<pre id="o">')
    b = dom.find("</pre>", a)
    pre = dom[a + 12:b] if a >= 0 and b > a else ""
    if not pre.startswith("BEGIN"):
        raise RuntimeError("Render gagal: " + (res.stderr or "")[-400:])
    body = [l for l in pre.splitlines() if l.startswith("data:image")]
    files = []
    for i, line in enumerate(body[:5]):
        data = line.strip().split(",", 1)[1]
        p = out_dir / f"slide-{i + 1}.jpg"
        p.write_bytes(base64.b64decode(data))
        files.append(p)
    if len(files) != 5:
        raise RuntimeError("Jumlah slide tidak 5")
    return files


if __name__ == "__main__":
    import sys
    d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(render(d, sys.argv[2]))
