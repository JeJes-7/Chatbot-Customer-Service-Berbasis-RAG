import os, sys
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv(override=True)
EMB = SentenceTransformer("intfloat/multilingual-e5-small")
col = chromadb.PersistentClient(path="chroma_db").get_collection("knowledge_base")
llm = OpenAI(base_url=os.getenv("LLM_BASE_URL"), api_key=os.getenv("LLM_API_KEY", "ollama"))
MODEL = os.getenv("LLM_MODEL")

TOP_K = 4
MAX_DIST = 0.5  # cosine distance; sesuaikan setelah uji

SYSTEM = """Kamu adalah asisten Customer Service TokoTeknoku di WhatsApp.
Aturan ketat:
1. Jawab HANYA berdasarkan bagian <konteks>. Jangan menambah angka, harga, durasi, atau kebijakan dari luar konteks.
2. Jika konteks tidak memuat jawabannya, jawab persis: "Maaf, saya belum menemukan informasi itu di dokumen resmi kami. Saya teruskan ke tim CS ya, mohon tunggu." lalu tulis [ESKALASI] di baris terakhir.
3. Gunakan bahasa Indonesia santai-sopan, ringkas, cocok untuk WhatsApp. Untuk prosedur, gunakan daftar bernomor.
4. Jika pertanyaan ambigu (misalnya produk atau tanggal pembelian tidak jelas), ajukan satu pertanyaan klarifikasi."""

def retrieve(query):
    q = EMB.encode(["query: " + query], normalize_embeddings=True).tolist()
    r = col.query(query_embeddings=q, n_results=TOP_K)
    hits = []
    for doc, meta, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0]):
        if dist <= MAX_DIST:
            hits.append((doc, meta, dist))
    return hits

def answer(question, history=None):
    """history: list of {"role": "user"|"assistant", "content": str}"""
    history = history or []
    # gabungkan pesan user sebelumnya agar follow-up tetap relevan saat retrieval
    prev = [m["content"] for m in history if m["role"] == "user"][-1:]
    hits = retrieve(" ".join(prev + [question]))

    if not hits:
        return ("Maaf, saya belum menemukan informasi itu di dokumen resmi kami. "
                "Saya teruskan ke tim CS ya, mohon tunggu."), True

    context = "\n\n".join(f"[{m['source']}]\n{d}" for d, m, _ in hits)
    msgs = history[-6:] + [{
        "role": "user",
        "content": f"<konteks>\n{context}\n</konteks>\n\nPertanyaan pelanggan: {question}",
    }]
    resp = llm.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        reasoning_effort="low",
        messages=[{"role": "system", "content": SYSTEM}] + msgs,
    )
    text = resp.choices[0].message.content.strip()
    escalate = "[ESKALASI]" in text
    return text.replace("[ESKALASI]", "").strip(), escalate

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Gimana cara klaim garansi untuk laptop yang layarnya garis-garis?"
    ans, esc = answer(q)
    print(ans, "\n[eskalasi]" if esc else "")