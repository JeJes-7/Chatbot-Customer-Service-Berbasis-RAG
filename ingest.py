import os, re, glob
import chromadb
from sentence_transformers import SentenceTransformer

EMB = SentenceTransformer("intfloat/multilingual-e5-small")
client = chromadb.PersistentClient(path="chroma_db")

def chunk_markdown(path):
    text = open(path, encoding="utf-8").read()
    title = re.search(r"^# (.+)$", text, re.M).group(1)
    parts = re.split(r"^## ", text, flags=re.M)[1:]
    for p in parts:
        heading, _, body = p.partition("\n")
        yield {
            "text": f"{title} - {heading.strip()}\n{body.strip()}",
            "source": os.path.basename(path),
            "section": heading.strip(),
        }

def main():
    try:
        client.delete_collection("knowledge_base")
    except Exception:
        pass
    col = client.create_collection("knowledge_base", metadata={"hnsw:space": "cosine"})

    chunks = [c for f in glob.glob("data/kb/*.md") for c in chunk_markdown(f)]
    embs = EMB.encode(["passage: " + c["text"] for c in chunks],
                      normalize_embeddings=True).tolist()
    col.add(
        ids=[f"c{i}" for i in range(len(chunks))],
        documents=[c["text"] for c in chunks],
        embeddings=embs,
        metadatas=[{"source": c["source"], "section": c["section"]} for c in chunks],
    )
    print(f"Ter-index: {len(chunks)} chunk")

if __name__ == "__main__":
    main()