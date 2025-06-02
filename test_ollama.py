import requests
import json

def test_ollama():
    url = "http://localhost:11434/api/chat"
    data = {
        "model": "qwen3:1.7b",
        "messages": [{"role": "user", "content": "oi"}]
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_ollama() 