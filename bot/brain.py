"""Otak tim kantor: prompt yang sama dengan Kantor ASN Go Digital.

Memakai Claude API (ANTHROPIC_API_KEY). Bila kosong, memakai Gemini API
tier gratis (GEMINI_API_KEY) sebagai cadangan tanpa biaya.
"""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

WIT = timezone(timedelta(hours=9))

BRIEF = (
    "Konteks merek: akun pribadi Arif Itra Muhammad (Instagram @arifitra_muhammad, Threads @arifitra_muhammad, Facebook). "
    "Arif adalah ASN, pejabat ahli perencanaan program di Dinas Pemberdayaan Masyarakat Kampung (DPMK) Kabupaten Kepulauan Yapen, Papua, "
    "sekaligus konten kreator dan pengusaha digital. Niche: (1) update pemerintahan desa/kampung: regulasi, berita, tata kelola, Dana Desa/ADD, "
    "BUMDes/BUMKam, musyawarah, perencanaan dan keuangan desa; (2) perkembangan AI untuk ASN dan perangkat desa: tools, prompt, cara kerja lebih cepat. "
    "Audiens: ASN daerah, kepala dan perangkat desa/kampung, pendamping desa, pengurus BUMDes, calon ASN. Di Papua desa disebut kampung; tulis "
    "\"desa/kampung\" bila relevan. Produk (brand ASN Go Digital, toko lynk.id/asngodigital, aktivasi via WhatsApp 081389491337): Generator Naskah Dinas "
    "(pembuat surat dinas sesuai tata naskah dinas untuk pemda dan pemerintah desa) dan Simulasi CAT CPNS 2026/2027 (latihan SKD). Aturan wajib: bahasa "
    "Indonesia yang jelas, bersemangat, santun; akurat, jangan mengarang nomor, tahun, atau isi pasal peraturan (bila tidak yakin tulis umum dan masukkan "
    "ke daftar cek); netral politik karena ASN dilarang politik praktis; tidak menyerang instansi atau pejabat; jualan hanya halus dan relevan; tanpa emoji di teks slide."
)

AGENTS = {
    "sinta": ("Sinta", "Resepsionis & Manajer Jadwal", "Kamu mengatur kalender konten, jam tayang, dan antrean terbit."),
    "bagas": ("Bagas", "Analis Regulasi Desa", "Kamu ahli regulasi desa/kampung dan selalu menandai nomor peraturan yang perlu dicek ke JDIH."),
    "nadia": ("Nadia", "Analis Tren AI untuk ASN", "Kamu mengubah perkembangan AI jadi tips praktis untuk ASN dan perangkat desa."),
    "rizky": ("Rizky", "Penulis Naskah Carousel", "Kamu penulis naskah carousel yang tajam: judul kapital yang bikin berhenti scroll, poin singkat, penutup yang mengajak."),
    "ratna": ("Bu Ratna", "Editor & Verifikator Fakta", "Kamu editor senior: memeriksa fakta, ejaan, bahasa baku, netralitas ASN, dan risiko hukum konten."),
    "dewi": ("Dewi", "Desainer Grafis", "Kamu desainer carousel bergaya navy-kuning-merah, tegas dan mudah dibaca di HP."),
    "yoga": ("Yoga", "Manajer Instagram", "Kamu mengelola Instagram: caption, hashtag, Reels, kolaborasi, pertumbuhan follower."),
    "laras": ("Laras", "Manajer Threads", "Kamu mengelola Threads: utas singkat yang memancing diskusi dan balasan."),
    "fajar": ("Fajar", "Manajer Facebook", "Kamu mengelola Facebook, Halaman, dan grup perangkat desa."),
    "maya": ("Maya", "Community Manager", "Kamu membalas komentar dan DM dengan ramah, mengarahkan calon pembeli ke WhatsApp aktivasi."),
    "hendra": ("Hendra", "Sales ASN Go Digital", "Kamu sales produk digital ASN Go Digital: funnel konten ke lynk.id ke WhatsApp, soft-selling, promo."),
    "putri": ("Putri", "Analis Data & Growth", "Kamu membaca insight (jangkauan, simpan, bagikan, follower) dan memberi keputusan konten berikutnya."),
}

SCHEMA = open(os.path.join(os.path.dirname(__file__), "deck_schema.json"), encoding="utf-8").read()


def _post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API {e.code}: {e.read().decode(errors='replace')[:300]}") from None


def llm(prompt, big=False, want_json=False):
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        model = os.environ.get("CLAUDE_MODEL_BIG" if big else "CLAUDE_MODEL", "").strip() or "claude-sonnet-5-5"
        r = _post("https://api.anthropic.com/v1/messages",
                  {"model": model, "max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]},
                  {"x-api-key": key, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in r.get("content", []))
    gkey = os.environ.get("GEMINI_API_KEY", "").strip()
    if gkey:
        model = os.environ.get("GEMINI_MODEL", "").strip() or "gemini-3.8-flash"
        cfg = {"responseMimeType": "application/json"} if want_json else {}
        r = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                  {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": cfg},
                  {"x-goog-api-key": gkey})
        return "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"])
    raise RuntimeError("Belum ada otak: isi secret ANTHROPIC_API_KEY (Claude) atau GEMINI_API_KEY (gratis).")


def ask_json(prompt, big=False):
    txt = llm(prompt, big=big, want_json=True)
    m = re.search(r"\{[\s\S]*\}", txt)
    return json.loads(m.group(0) if m else txt)


HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def tgl(d, jam=False):
    s = f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]} {d.year}"
    return s + (d.strftime(" %H:%M") if jam else "")


def today():
    return tgl(datetime.now(WIT))


def research(pilar, ide, bahan):
    pil = {"desa": "pemerintahan desa/kampung", "ai": "AI untuk ASN"}.get(pilar, "pilih yang paling berpotensi menarik engagement hari ini")
    return ask_json(
        f"Kamu tim riset kantor konten (Bagas: analis regulasi desa; Nadia: analis tren AI untuk ASN). {BRIEF}\nHari ini {today()}.\n"
        f"Pilar diminta: {pil}.\nIde dari Direktur: {ide or '(bebas, pilih topik evergreen yang paling dibutuhkan audiens)'}\n"
        f"Bahan riset dari Direktur (jadikan sumber utama bila ada, jangan menambah fakta spesifik di luar ini):\n"
        f"{bahan or '(tidak ada; gunakan pengetahuan umum yang mapan dan hindari angka/nomor yang tidak pasti)'}\n"
        'Balas HANYA JSON: {"pilar":"desa|ai","topik":"judul topik","sudut":"sudut pandang unik","hook":"kalimat pembuka",'
        '"poin":["5-7 poin isi yang akurat"],"harus_dicek":["klaim/nomor yang wajib dicek sebelum terbit"],"alasan":"kenapa topik ini akan disimpan & dibagikan"}')


def write_deck(res, sell=True, revisi=None, old=None):
    extra = ""
    if revisi and old:
        extra = f"\nIni naskah sebelumnya:\n{json.dumps(old, ensure_ascii=False)}\nRevisi dari Direktur: {revisi}\nPertahankan yang tidak diminta berubah."
    d = ask_json(
        f"Kamu Rizky (penulis naskah carousel) bersama Bu Ratna (editor). {BRIEF}\nRiset tim:\n{json.dumps(res, ensure_ascii=False)}\n"
        "Tulis naskah carousel 5 slide dengan gaya edukasi tegas seperti akun pelatihan desa: judul kapital yang memancing (mis. \"KADES WAJIB PAHAM! ... ITU BERBEDA!\"), "
        "slide 2 daftar 5 poin dengan nomor merah, slide 3 daftar fokus di latar navy, slide 4 perbandingan dua kolom berisi aksi (kata kerja tebal + penjelasan), "
        "slide 5 penutup \"Siapkan\" + kotak pesan pamungkas. "
        + ("Boleh menyinggung produk secara halus hanya di slide 5 box2 bila relevan. " if sell else "Jangan ada jualan di slide. ")
        + "Patuhi batas huruf agar muat di desain. Bahasa baku, tanpa emoji." + extra +
        f"\nBalas HANYA JSON persis dengan struktur ini (isi semua field, array items persis 5 kecuali left 3 item dan right 4 item):\n{SCHEMA}", big=True)
    if not d.get("cover"):
        raise RuntimeError("Naskah tidak lengkap")
    d["pilar"] = d.get("pilar") or res.get("pilar") or "desa"
    return d


def captions(res, deck, produk="auto"):
    prod = {"auto": "Hendra memilih produk paling relevan (Generator Naskah Dinas untuk topik administrasi/surat/desa, Simulasi CAT CPNS untuk topik karier/CPNS), atau tidak menjual bila tidak cocok.",
            "none": "Jangan menjual produk apa pun.", "naskah": "Sisipkan Generator Naskah Dinas secara halus.",
            "cat": "Sisipkan Simulasi CAT CPNS 2026/2027 secara halus."}.get(produk, "")
    return ask_json(
        f"Kamu tim media sosial: Yoga (Instagram), Laras (Threads), Fajar (Facebook), Hendra (sales), Maya (komunitas), dan Bu Ratna (cek fakta). {BRIEF}\n"
        f"Riset: {json.dumps(res, ensure_ascii=False)}\nNaskah carousel: {json.dumps(deck, ensure_ascii=False)}\nProduk: {prod} "
        "Arahkan pembelian ke lynk.id/asngodigital (link di bio) dan aktivasi lewat WhatsApp 081389491337 hanya bila menjual.\n"
        'Balas HANYA JSON: {"ig":"caption Instagram maks 1800 huruf: baris pertama hook kuat, isi ringkas, ajakan simpan/bagikan/follow @arifitra_muhammad, CTA produk halus bila ada, lalu 8-12 hashtag relevan di akhir",'
        '"threads":"maks 450 huruf, gaya ngobrol, diakhiri pertanyaan pemantik balasan, maks 1 hashtag","fb":"caption Facebook gaya bercerita maks 1100 huruf, sapaan rekan ASN dan perangkat desa/kampung, ajakan bagikan ke grup kantor",'
        '"first":"komentar pertama pemantik diskusi","alt":["5 alt text singkat untuk tiap slide"],"cek":[{"butir":"hal yang harus dicek atau sudah aman","catatan":"saran perbaikan atau sumber pengecekan seperti JDIH"}],"jam":"saran jam tayang WIT format HH:MM"}')


def agent_task(agent_id, task, context=None):
    n, r, d = AGENTS[agent_id]
    ctx = f"\n\nPesan sebelumnya yang dibalas Pak Arif:\n{context}" if context else ""
    return llm(f"Kamu adalah {n}, {r} di Kantor Virtual ASN Go Digital lantai 2, bekerja untuk Pak Arif (Direktur). {d} {BRIEF} "
               "Jawab dalam bahasa Indonesia, ringkas, praktis, langsung bisa dipakai, tanpa basa-basi pembuka. Format untuk Telegram: teks biasa, tanpa tabel markdown. "
               "PENTING: kamu TIDAK bisa membuat, menjadwalkan, atau menerbitkan postingan sendiri, dan jangan pernah mengaku sudah melakukannya. "
               "Bila Pak Arif ingin postingan dibuat/dijadwalkan, katakan cukup ketik misalnya: buatkan postingan tentang <topik> besok jam 07.30 — tim produksi akan mengerjakannya. "
               f"Kamu tidak bisa membuka internet: bila butuh data terbaru, minta Pak Arif menempelkan teks sumbernya. Hari ini {today()}.{ctx}\n\nTugas dari Pak Arif:\n{task}")


def intent(text, ctx=""):
    """Membaca maksud pesan bebas: produksi, setujui, terbitkan, antrean, atau obrolan."""
    now = datetime.now(WIT)
    return ask_json(
        f"Kamu Sinta, resepsionis kantor konten. Hari ini {tgl(now, True)} WIT.\n"
        f"Konteks pesan sebelumnya (mis. daftar ide dari rekan):\n{ctx[:2500] or '(tidak ada)'}\n\nPesan Pak Arif: {text}\n\n"
        "Tentukan maksudnya. aksi:\n- produksi: minta dibuatkan/dijadwalkan postingan atau carousel baru (termasuk dari ide nomor sekian di konteks).\n"
        "- setujui: menyetujui draf yang sudah ada. - terbitkan: minta draf terakhir diterbitkan sekarang.\n- antrean: tanya jadwal/antrean. - obrolan: selain itu.\n"
        "Untuk produksi, isi topik selengkap mungkin (salin judul ide dari konteks bila merujuk nomor). Bila ada beberapa ide diminta, ambil yang pertama disebut.\n"
        "waktu: tanggal-jam tayang yang diminta dalam format YYYY-MM-DD HH:MM (zona WIT), atau 'sekarang', atau kosong bila tidak disebut. 'pagi' tanpa jam = 07:30, 'sore' = 16:30, 'malam' = 19:30.\n"
        'Balas HANYA JSON: {"aksi":"produksi|setujui|terbitkan|antrean|obrolan","pilar":"desa|ai|","topik":"","waktu":""}')
