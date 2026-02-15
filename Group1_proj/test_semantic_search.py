from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os

# Load environment variables
print("[*] Loading environment variables...")
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")
print("[✓] Environment variables loaded")

# Create embeddings client using OpenRouter credentials
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Use the embeddings object's query embedder for semantic searches
db = Chroma(
    persist_directory="./cyber_vector_db",
    embedding_function=embeddings
)

results = db.similarity_search(
    "Show me critical CVEs related to SQL injection",
    k=5
)

for r in results:
    print(r.page_content)
    print("----")