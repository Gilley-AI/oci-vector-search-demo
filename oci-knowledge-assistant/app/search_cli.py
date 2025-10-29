import os, sys, json
import oracledb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_DSN = os.environ["DB_DSN"]  # e.g., AIDEMO_tp
DB_WALLET_DIR = os.path.expanduser(os.environ.get("DB_WALLET_DIR", "~/wallet"))
DB_WALLET_PASSWORD = os.environ.get("DB_WALLET_PASSWORD")

EMBED_MODEL = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = 3

model = SentenceTransformer(EMBED_MODEL)

def query_db(vec):
    # convert vector to JSON text for TO_VECTOR(:q)
    vec_json = json.dumps([float(x) for x in vec.tolist()])

    conn = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=DB_DSN,                    # TNS alias defined in tnsnames.ora
        config_dir=DB_WALLET_DIR,      # <-- wallet directory
        wallet_location=DB_WALLET_DIR, # <-- wallet directory
        wallet_password=DB_WALLET_PASSWORD
    )
    cur = conn.cursor()
    cur.execute(f"""
    SELECT title,
           DBMS_LOB.SUBSTR(content, 4000, 1) AS content_text,
           VECTOR_DISTANCE(embedding, TO_VECTOR(:q)) AS dist
    FROM kb_docs
    ORDER BY dist
    FETCH FIRST {TOP_K} ROWS ONLY
""", (vec_json,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def answer_from_snippets(q, snippets):
    join = "\n\n".join([f"- {t}:\n{c[:400]}..." for t, c, _ in snippets])
    return f"Q: {q}\n\nBased on the knowledge base, here are the most relevant points:\n\n{join}\n\n(Generated without paid GenAI.)"

def main():
    q = " ".join(sys.argv[1:]) or "What is Oracle AI Vector Search?"
    vec = model.encode([q], normalize_embeddings=True)[0]
    rows = query_db(vec)
    print(answer_from_snippets(q, rows))

if __name__ == "__main__":
    main()
