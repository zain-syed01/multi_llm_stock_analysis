import hashlib
from typing import List
import chromadb
from ingest import fetch_ticker_data, NewsArticle

client = chromadb.PersistentClient(path="./chroma_data")


# Creating collection for stock news

collection = client.get_or_create_collection(name="stock_news")

def store_news(ticker: str, news: List[NewsArticle]):
    if not news:
        return 0

    documents = []
    metadata = []
    ids = []

    for article in news:
        text_content = f"{article.title}. {article.summary or ''}".strip()
        documents.append(text_content)

        metadata.append({
            "ticker": ticker.upper(),
            "publisher": article.publisher,
            "link": article.link
        })

        unique_string = article.link or article.title
        article_id = hashlib.sha256(unique_string.encode("utf-8")).hexdigest()[:16]
        ids.append(f"{ticker.upper()}_{article_id}")


    collection.upsert(
        documents=documents,
        metadatas=metadata,
        ids=ids
    )

    return len(documents)




def query_news(ticker: str, query_text: str, n_results: int = 2):

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where={"ticker": ticker.upper()}

    )

    return results
    
    


if __name__ == "__main__":
    symbol = "NVDA"
    print(f"1. Fetching data for {symbol}...")
    payload = fetch_ticker_data(symbol)

    print(f"2. Storing {len(payload.news)} articles in ChromaDB...")
    count = store_news(symbol, payload.news)
    print(f"Successfully upserted {count} articles.")

    print("\n3. Testing Semantic Search...")
    search_prompt = "AI deals, GPUs, and enterprise partnerships"
    query_output = query_news(ticker=symbol, query_text=search_prompt, n_results=2)

    docs = query_output.get("documents", [[]])[0]
    metas = query_output.get("metadatas", [[]])[0]
    distances = query_output.get("distances", [[]])[0]

    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, distances), start=1):
        print(f"\n--- Match #{rank} (Distance: {dist:.4f}) ---")
        print(f"Publisher: {meta.get('publisher')}")
        print(f"Link: {meta.get('link')}")
        print(f"Content: {doc}")





