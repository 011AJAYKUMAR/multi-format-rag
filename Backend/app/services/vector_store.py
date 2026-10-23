import os
import weaviate
import weaviate.classes as wvc
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

class VectorStoreService:
    def __init__(self):
        self.weaviate_url = os.getenv("WEAVIATE_URL")
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def get_client(self):
        """Initializes and returns the Weaviate client v4 connection."""
        if self.weaviate_url and self.weaviate_api_key:
            return weaviate.connect_to_weaviate_cloud(
                cluster_url=self.weaviate_url,
                auth_credentials=weaviate.auth.AuthApiKey(self.weaviate_api_key)
            )
        else:
            return weaviate.connect_to_local()

    def delete_documents_by_source(self, source_name: str):
        """Deletes all chunks belonging to a specific source file from Weaviate v4."""
        client = self.get_client()
        try:
            collection_name = "DocumentChunk"
            if not client.collections.exists(collection_name):
                return
                
            collection = client.collections.get(collection_name)
            collection.data.delete_many(
                where=wvc.query.Filter.by_property("source").equal(source_name)
            )
        except Exception as e:
            print(f"Error deleting vectors from Weaviate: {e}")
            raise e
        finally:
            client.close()

    def add_documents_to_store(self, chunks: list[str], metadata: dict):
        """Embeds text chunks locally and stores them in Weaviate v4."""
        client = self.get_client()
        try:
            collection_name = "DocumentChunk"
            if not client.collections.exists(collection_name):
                client.collections.create(name=collection_name)
            
            collection = client.collections.get(collection_name)
            vectors = self.embeddings.embed_documents(chunks)
            
            with collection.batch.dynamic() as batch:
                for chunk, vector in zip(chunks, vectors):
                    batch.add_object(
                        properties={
                            "text": chunk,
                            "source": metadata.get("source", "Unknown")
                        },
                        vector=vector
                    )
        finally:
            client.close()

    def search_similar(self, query: str, k: int = 4):
        """Performs Weaviate Hybrid Search (combining vector similarity and BM25 keyword matching)."""
        client = self.get_client()
        try:
            collection_name = "DocumentChunk"
            if not client.collections.exists(collection_name):
                return []
                
            collection = client.collections.get(collection_name)
            query_vector = self.embeddings.embed_query(query)
            
            # Execute Hybrid Search (alpha=0.5 balances keyword vs semantic weighting)
            response = collection.query.hybrid(
                query=query,
                vector=query_vector,
                alpha=0.5,
                limit=k
            )
            
            results = []
            for item in response.objects:
                results.append({
                    "text": item.properties.get("text", ""),
                    "source": item.properties.get("source", "Unknown")
                })
            return results
        finally:
            client.close()