from flask import Flask, render_template, jsonify, request, send_file
from agenteia.core.agente import AgenteIA
from agenteia.core.config import CONFIG
import asyncio
import threading
import queue
import io
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
message_queue = queue.Queue()
agente = None
modelo_status = {
    "geral": "Não carregado",
    "coder": "Não carregado"
}
historico = []

def inicializar_agente():
    global agente, modelo_status
    try:
        usar_openrouter = CONFIG.get("openrouter", {}).get("enabled", False)
        agente = AgenteIA(mcp_client=None, usar_openrouter=usar_openrouter, config=CONFIG)

        agent_status_details = agente.obter_status_agente()
        if agent_status_details.get("status") == "ativo":
            modelo_status["geral"] = agent_status_details.get("modelo_principal", "Configurado via CONFIG")
            modelo_status["coder"] = agent_status_details.get("modelo_coder", "Configurado via CONFIG")
            if usar_openrouter:
                modelo_status["geral"] = CONFIG.get("openrouter", {}).get("modelo_geral", modelo_status["geral"])
                modelo_status["coder"] = CONFIG.get("openrouter", {}).get("modelo_coder", modelo_status["coder"])
            elif CONFIG.get("llm", {}).get("provider") == "ollama":
                 modelo_status["geral"] = CONFIG.get("llm", {}).get("model", modelo_status["geral"])
                 modelo_status["coder"] = CONFIG.get("llm", {}).get("model", modelo_status["coder"])
        else:
            modelo_status["geral"] = "Erro na ativação do agente"
            modelo_status["coder"] = "Erro na ativação do agente"
        print(f"Agente inicializado. Status: {modelo_status}")
        return True
    except Exception as e:
        print(f"Erro ao inicializar agente: {str(e)}")
        modelo_status["geral"] = "Falha crítica na inicialização"
        modelo_status["coder"] = "Falha crítica na inicialização"
        return False

@app.route('/')
def home():
    return render_template('index.html', modelos_disponiveis=CONFIG.get("available_models", {}))

@app.route('/carregar_ia', methods=['POST'])
def carregar_ia():
    if inicializar_agente():
        return jsonify({
            "status": "success",
            "message": "IA carregada com sucesso com base na configuração!",
            "modelos": modelo_status
        })
    return jsonify({
        "status": "error",
        "message": "Erro ao carregar IA. Verifique os logs do servidor."
    })

@app.route('/status')
def get_status():
    if agente:
        status_agente_detalhado = agente.obter_status_agente()
        return jsonify({**modelo_status, "status_agente_detalhado": status_agente_detalhado})
    return jsonify(modelo_status)

@app.route('/upload_arquivo', methods=['POST'])
def upload_arquivo():
    if 'arquivo' not in request.files:
        return jsonify({"status": "error", "message": "Nenhum arquivo enviado."})
    arquivo = request.files['arquivo']
    if arquivo.filename == '':
        return jsonify({"status": "error", "message": "Arquivo vazio."})

    if agente is None:
        return jsonify({"status": "error", "message": "IA não carregada. Por favor, carregue a IA primeiro."})

    try:
        filename = secure_filename(arquivo.filename)
        caminho_temporario = os.path.join('temp', filename)
        os.makedirs('temp', exist_ok=True)
        arquivo.save(caminho_temporario)

        with open(caminho_temporario, 'r', encoding='utf-8') as f:
            file_content = f.read()

        prompt_com_conteudo_arquivo = f"Analise o seguinte conteúdo do arquivo '{filename}':\n\n{file_content}"

        resposta_agente = asyncio.run(agente.processar_mensagem(prompt_com_conteudo_arquivo))

        resposta_texto = str(resposta_agente)

        historico.append({"remetente": "Sistema", "mensagem": f"Arquivo '{filename}' processado."})
        historico.append({"remetente": "Agente", "mensagem": resposta_texto})

        try:
            os.remove(caminho_temporario)
        except Exception as e:
            print(f"Aviso: Não foi possível remover o arquivo temporário {caminho_temporario}: {e}")

        return jsonify({"status": "success", "message": resposta_texto})
    except Exception as e:
        print(f"Erro em /upload_arquivo: {e}")
        return jsonify({"status": "error", "message": f"Erro ao processar arquivo: {str(e)}"})

@app.route('/enviar_mensagem', methods=['POST'])
def enviar_mensagem():
    global agente
    if agente is None:
        return jsonify({"status": "error", "message": "IA não carregada. Por favor, carregue a IA primeiro."})

    data = request.get_json()
    mensagem = data.get('mensagem', '')
    perfil = data.get('perfil')

    if not mensagem:
        return jsonify({"status": "error", "message": "Mensagem vazia."})

    try:
        resposta_agente = asyncio.run(agente.processar_mensagem(mensagem, perfil=perfil))

        resposta_texto = str(resposta_agente)

        historico.append({"remetente": "Você", "mensagem": mensagem})
        historico.append({"remetente": "Agente", "mensagem": resposta_texto})
        return jsonify({"status": "success", "resposta": resposta_texto})
    except Exception as e:
        print(f"Erro em /enviar_mensagem: {e}")
        return jsonify({"status": "error", "message": f"Erro ao processar mensagem: {str(e)}"})

@app.route('/historico')
def get_historico():
    return jsonify(historico)

@app.route('/limpar_historico', methods=['POST'])
def limpar_historico():
    historico.clear()
    if agente:
        if hasattr(agente, 'limpar_historico') and callable(getattr(agente, 'limpar_historico')):
            agente.limpar_historico()
    return jsonify({"status": "success"})

@app.route('/download_historico/<tipo>')
def download_historico(tipo):
    if tipo == 'txt':
        conteudo = '\n'.join([f"{msg['remetente']}: {msg['mensagem']}" for msg in historico])
        return send_file(
            io.BytesIO(conteudo.encode()),
            mimetype='text/plain',
            as_attachment=True,
            download_name='historico.txt'
        )
    elif tipo == 'json':
        conteudo = json.dumps(historico, ensure_ascii=False, indent=2)
        return send_file(
            io.BytesIO(conteudo.encode()),
            mimetype='application/json',
            as_attachment=True,
            download_name='historico.json'
        )
    else:
        return "Tipo não suportado", 400

if __name__ == '__main__':
    os.makedirs('temp', exist_ok=True)
    app.run(debug=True)
