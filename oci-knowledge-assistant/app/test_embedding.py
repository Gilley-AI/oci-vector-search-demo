from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
text = "Oracle AI Vector Search enables semantic retrieval in Autonomous Database."
emb = model.encode([text])

print("✅ Embedding generated!")
print("Vector length:", len(emb[0]))
print("First 5 values:", emb[0][:5])
