import os, glob
import oracledb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import json

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_DSN = os.environ["DB_DSN"]
EMBED_MODEL = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Wallet settings for mTLS
DB_WALLET_DIR = os.environ.get("DB_WALLET_DIR", os.path.expanduser("~/wallet"))
DB_WALLET_PASSWORD = os.environ.get("DB_WALLET_PASSWORD")

# Initialize model
print("Loading embedding model:", EMBED_MODEL)
model = SentenceTransformer(EMBED_MODEL)

# Connect to Oracle
print("Connecting to database...")
# mTLS (thin driver) using wallet config dir + TNS alias in DB_DSN
conn = oracledb.connect(
    user=DB_USER,
    password=DB_PASSWORD,
    dsn=DB_DSN,  # e.g., AIDEMO_tp
    config_dir=DB_WALLET_DIR,
    wallet_location=DB_WALLET_DIR,
    wallet_password=DB_WALLET_PASSWORD
)
cur = conn.cursor()

# Load and insert text files
corpus_dir = os.path.join(os.path.dirname(__file__), "..", "data", "corpus")
files = sorted(glob.glob(os.path.join(corpus_dir, "*.txt")))

if not files:
    print("❌ No text files found in data/corpus. Add .txt files first.")
    exit()

# ...

for path in files:
    title = os.path.basename(path).replace("_", " ").replace(".txt", "")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Create embedding as a Python list (384 floats)
    embedding = model.encode([content], normalize_embeddings=True)[0].tolist()

    # ✅ Serialize to JSON so SQL sees it as text, not an array bind
    embedding_json = json.dumps(embedding)

    cur.execute("""
        INSERT INTO kb_docs (title, content, embedding)
        VALUES (:1, :2, TO_VECTOR(:3))
    """, (title, content, embedding_json))
    print("✅ Loaded:", title)

conn.commit()
cur.close()
conn.close()
print("\n🎉 All documents loaded successfully!")
