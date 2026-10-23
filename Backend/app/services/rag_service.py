import os
from langchain_groq import ChatGroq
from app.services.vector_store import VectorStoreService
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.vector_store_service = VectorStoreService()
        
        self.llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0.2,
            groq_api_key=self.groq_api_key
        )
        
        # In-memory conversation history buffer
        self.chat_history = []

    def clear_history(self):
        """Clears the conversational memory buffer."""
        self.chat_history = []

    def answer_question(self, question: str, selected_sources: list[str] = None):
        """Retrieves relevant document chunks and generates an answer using context and history."""
        try:
            docs = self.vector_store_service.search_similar(question, k=6)
            
            if selected_sources and len(selected_sources) > 0:
                docs = [doc for doc in docs if doc["source"] in selected_sources]

            if not docs:
                return {
                    "answer": "I couldn't find any relevant information in the selected documents to answer your question.",
                    "sources": []
                }

            context = "\n\n".join([doc["text"] for doc in docs])
            sources = list(set([doc["source"] for doc in docs]))

            # Format the last 4 conversation turns for context memory
            history_str = "\n".join([
                f"User: {turn['question']}\nAssistant: {turn['answer']}" 
                for turn in self.chat_history[-4:]
            ])

            prompt = f"""You are a helpful, professional AI assistant. Answer the user's question accurately based ONLY on the provided document context and the conversation history below. If the answer cannot be found in the context, state clearly that you don't know.

Conversation History:
{history_str}

Document Context:
{context}

User Question: {question}

Detailed Answer:"""

            response = self.llm.invoke(prompt)
            answer_text = response.content

            # Save turn to history buffer
            self.chat_history.append({
                "question": question,
                "answer": answer_text
            })
            
            return {
                "answer": answer_text,
                "sources": sources
            }
            
        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": []
            }