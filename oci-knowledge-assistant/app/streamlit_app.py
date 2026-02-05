import os, json
import streamlit as st
import oracledb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# --- Load env ---
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_DSN = os.environ["DB_DSN"]  # e.g., AIDEMO_tp (TNS alias from wallet)
# DB_WALLET_DIR = os.path.expanduser(os.environ.get("DB_WALLET_DIR", "~/wallet"))
# DB_WALLET_PASSWORD = os.environ.get("DB_WALLET_PASSWORD")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# --- App title ---
st.set_page_config(page_title="Oracle AI Knowledge Assistant", layout="wide")
st.title("🔎 Oracle AI Knowledge Assistant (Vector Search)")

@st.cache_resource(show_spinner=False)
def get_model():
    return SentenceTransformer(EMBED_MODEL)

@st.cache_resource(show_spinner=False)
def get_db_params():
    return {
        "user": DB_USER,
        "password": DB_PASSWORD,
        "dsn": DB_DSN,
    }

def connect():
    params = get_db_params()
    return oracledb.connect(**params)

def to_text(c):
    return c.read() if hasattr(c, "read") else c

with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Top-K passages", 1, 5, 3)
    show_context = st.checkbox("Show retrieved context", True)
    st.markdown("**DB alias:** " + DB_DSN)

q = st.text_input("Ask a question", "How does vector search work on Oracle?")
go = st.button("Search")

if go:
    try:
        with st.spinner("Loading model…"):
            model = get_model()
        with st.spinner("Embedding query…"):
            vec = model.encode([q], normalize_embeddings=True)[0]
            vec_json = json.dumps([float(x) for x in vec.tolist()])

        with st.spinner("Querying database…"):
            conn = connect()
            cur = conn.cursor()
            cur.execute(f"""
                SELECT title,
                       DBMS_LOB.SUBSTR(content, 4000, 1) AS content_text,
                       VECTOR_DISTANCE(embedding, TO_VECTOR(:q)) AS dist
                FROM kb_docs
                ORDER BY dist
                FETCH FIRST {top_k} ROWS ONLY
            """, (vec_json,))
            rows = cur.fetchall()
            cur.close(); conn.close()

        if not rows:
            st.warning("No rows returned. Did you load any documents into kb_docs?")
        else:
            # Simple synthesized answer from snippets (strict $0 mode)
            snippets = [(t, to_text(c), d) for t, c, d in rows]
            bullet = "\n\n".join([f"- **{t}**\n{c[:400]}…" for t, c, _ in snippets])
            st.subheader("Answer")
            st.write(f"**Q:** {q}")
            st.write("Based on the knowledge base, here are the most relevant points:\n\n" + bullet)

            if show_context:
                st.subheader("Retrieved context")
                for i, (t, c, d) in enumerate(snippets, 1):
                    with st.expander(f"{i}. {t}  •  distance={d:.4f}", expanded=(i==1)):
                        st.code(c)

    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()
