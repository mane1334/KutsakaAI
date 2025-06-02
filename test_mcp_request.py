import requests
import json

url = "http://localhost:8000/tarefas"

# Conteúdo que deve ser a string JSON dentro do campo 'tarefa'
tool_execution_content = {
    "tipo": "executar_ferramenta",
    "nome_ferramenta": "listar_arquivos",
    "parametros": {"diretorio": "."}
}

# Serializar o conteúdo em uma string JSON
tarefa_json_string = json.dumps(tool_execution_content)

# O payload agora inclui o campo 'tarefa' com a string JSON
payload = {
    "tarefa": tarefa_json_string
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=4))
    except requests.exceptions.JSONDecodeError:
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"Erro na requisição: {e}") 