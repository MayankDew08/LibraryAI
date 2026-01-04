import json
from locust import HttpUser, task, between
import random

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(1)
    def call_root(self):
        self.client.get("/")
        
    @task(3)
    def call_rag_query(self):
        book_id= random.randint(15,50)
        query=["What is the main theme of the book?",
               "How can I apply the concepts discussed in the book?",
               "What are the key takeaways from the book?",
               "How can this book be applied to real-world scenarios?",
               "What are some critical analyses of the book?"]
        question=random.choice(query)
        payload={
            "question": question,
            "num_chunks":5
        }
        self.client.post(f"/rag/books/{book_id}/query",data=json.dumps(payload),headers={"Content-Type":"application/json"})
        
    @task(1)
    def call_get_summary(self):
        book_id= random.randint(16,50)
        self.client.get(f"/student/books/{book_id}/summary")
        
    @task(1)
    def call_get_qa(self):
        book_id= random.randint(16,50)
        self.client.get(f"/student/books/{book_id}/qa")
    
    @task(1)
    def call_get_audio(self):
        book_id= random.randint(16,50)
        self.client.get(f"/student/books/{book_id}/audio")
        
        