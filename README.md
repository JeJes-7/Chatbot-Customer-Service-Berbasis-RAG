# Chatbot-Customer-Service-Berbasis-RAG
TokoTeknoku CS Bot: RAG + Telegram Chatbot

Chatbot Customer Service untuk toko e-commerce/ritel (data dummy) yang menjawab pertanyaan pelanggan seputar garansi, return, spesifikasi produk, promo, dan profil toko. Jawaban dihasilkan dengan **Retrieval-Augmented Generation (RAG)**, sehingga bot hanya menjawab berdasarkan dokumen resmi dan tidak mengarang informasi.

## Latar Belakang

Tim customer service sering kewalahan menjawab pertanyaan berulang. Bot berbasis aturan terlalu kaku, sedangkan LLM biasa rentan memberi informasi garansi atau harga yang salah (halusinasi). Proyek ini menggabungkan pencarian dokumen (vector database) dengan LLM agar jawaban fleksibel sekaligus akurat.

## Fitur

- Menjawab dalam bahasa Indonesia 
- Pencarian semantik pada knowledge base (SOP garansi, kebijakan return, spesifikasi, promo, profil toko)
- Skrip evaluasi otomatis
- Channel: **Telegram bot** (polling). Kode webhook WhatsApp Cloud API dan endpoint REST `/chat` juga tersedia

## Arsitektur

```
Pelanggan (Telegram)
        │
        ▼
 telegram_bot.py ──► rag.py ──► ChromaDB (vector DB)
                        │            ▲
                        │            │ ingest.py (chunking + embedding)
                        ▼            │
                  LLM (Gemini)    data/kb/*.md
                        │
                        ▼
        Jawaban / [ESKALASI] ke agen CS
```

Lapisan RAG dipisahkan dari lapisan channel, sehingga channel lain (WhatsApp, web) bisa dipasang tanpa mengubah `rag.py`.

## Teknologi

| Komponen | Teknologi |
|---|---|
| Bahasa | Python 3.13 |
| Vector database | ChromaDB |
| Embedding | `intfloat/multilingual-e5-small` (sentence-transformers) |
| LLM | Gemini lewat library `openai` (kompatibel dengan Ollama dan Groq) |
| Channel | python-telegram-bot, FastAPI (webhook WhatsApp dan `/chat`) |

## Struktur Proyek

```
cs-rag-wa/
├── data/kb/                 # Knowledge base dummy (Markdown)
│   ├── sop_garansi.md
│   ├── kebijakan_return.md
│   ├── spesifikasi_laptop.md
│   ├── promo.md
│   └── profil_toko.md
├── ingest.py                # Chunking + embedding + indexing ke ChromaDB
├── rag.py                   # Retrieval + generasi jawaban
├── telegram_bot.py          # Bot Telegram
├── app.py                   # FastAPI: webhook WhatsApp + endpoint /chat
├── evaluasi.py              # Evaluasi otomatis
├── requirements.txt
└── .env                     # Tidak di-commit
```

## Cara Menjalankan

1. Clone dan install dependensi:
   ```bash
   pip install -r requirements.txt
   pip install python-telegram-bot openai
   ```
2. Buat file `.env`:
   ```dotenv
   LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   LLM_API_KEY=isi_api_key
   LLM_MODEL=nama_model
   TELEGRAM_TOKEN=isi_token_dari_BotFather
   ```
3. Bangun vector database dari knowledge base:
   ```bash
   python ingest.py
   ```
4. Tes tanpa channel:
   ```bash
   python rag.py "Gimana cara klaim garansi untuk laptop yang layarnya garis-garis?"
   ```
5. Jalankan bot Telegram:
   ```bash
   python telegram_bot.py
   ```
6. (Opsional) Jalankan API lokal, lalu buka `http://localhost:8000/docs`:
   ```bash
   uvicorn app:app --port 8000
   ```

## Evaluasi

```bash
python evaluasi.py
```

Skrip menguji pertanyaan yang ada di dokumen (jawaban harus memuat kata kunci yang benar) dan pertanyaan di luar dokumen (bot harus menolak dan mengeskalasi). Hasil pengujian awal: **9/9 (100%)** pada set uji awal. Set uji diperluas dengan pertanyaan profil toko dan pertanyaan jebakan.

## Contoh Percakapan

> **Pelanggan:** Gimana cara klaim garansi untuk laptop yang layarnya garis-garis?
> **Bot:** Langkah klaim: 1) siapkan invoice dan kartu garansi, 2) cadangkan data, 3) isi formulir klaim, dst. sesuai SOP.
>
> **Pelanggan:** Berapa harga iPhone 15?
> **Bot:** Maaf, saya belum menemukan informasi itu di dokumen resmi kami. Saya teruskan ke tim CS ya.

## Keterbatasan dan Rencana Pengembangan

- Knowledge base berisi data dummy, ganti dengan dokumen SOP asli
- Memori percakapan masih in-memory, rencana diganti Redis
- Belum ada loader PDF/DOCX
- Notifikasi eskalasi ke agen CS (email/Slack) belum diimplementasikan
- Integrasi WhatsApp Cloud API sudah diimplementasikan, tetapi pengujian langsung terkendala penguncian akun Meta

Penulis

Jesika Yudiani Putri
