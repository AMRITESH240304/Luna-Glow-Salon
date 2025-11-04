import google.generativeai as genai
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv(".env")

class KnowledgeBase:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGODB_URI")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.db_name = "KnowledgeBase"
        self.collection_name = "Embeddings"
        self.index_name = "vector_index"

        if not self.mongo_uri or not self.gemini_api_key:
            raise ValueError("Missing MONGO_URI or GEMINI_API_KEY in .env file")

        genai.configure(api_key=self.gemini_api_key)
        self.client = MongoClient(self.mongo_uri)
        self.collection = self.client[self.db_name][self.collection_name]
        
    async def _get_embedding(self, text: str):
        """Generate an embedding vector for a given text using Gemini."""
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="SEMANTIC_SIMILARITY"
        )
        return response["embedding"]
    
    async def search(self, query: str, top_k: int = 3):
        """Search for the most semantically similar answers."""
        try:
            query_vector = await self._get_embedding(query)
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": self.index_name,
                        "queryVector": query_vector,
                        "path": "embedding",
                        "numCandidates": 100,
                        "limit": top_k
                    }
                }
            ]
            results = list(self.collection.aggregate(pipeline))
            return results
        except Exception as e:
            print(f"[KnowledgeBase] Vector search failed: {e}")
            return []
        
    async def add_entry(self, question: str, answer: str):
        """Store a new Q&A pair into the knowledge base."""
        try:
            combined_text = f"Q: {question}\nA: {answer}"
            embedding = await self._get_embedding(combined_text)
            document = {
                "question": question,
                "answer": answer,
                "embedding": embedding
            }
            result = self.collection.insert_one(document)
            print(f"[KnowledgeBase] Added new knowledge (id={result.inserted_id})")
            return result.inserted_id
        except Exception as e:
            print(f"[KnowledgeBase] Failed to add entry: {e}")
            return None

    async def find_all_answers(self, question: str):
        """
        Find all answers to a question.
        """
        try:
            results = await self.search(question, top_k=5)
            if not results:
                return []
            # make object and reutrn list of answers and questions
            answers = [res.get("answer") for res in results]
            questions = [res.get("question") for res in results]
            return {"answers": answers, "questions": questions}
        
        except Exception as e:
            print(f"[KnowledgeBase] Error finding answers: {e}")
            return []

    async def find_best_answer(self, question: str):
        """
        Find the best-matching answer to a question
        """
        try:
            results = await self.search(question, top_k=1)
            if not results:
                return None

            best = results[0]
            answer = best.get("answer")
            return answer
        except Exception as e:
            print(f"[KnowledgeBase] Error finding best answer: {e}")
            return None
    