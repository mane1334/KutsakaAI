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

def inicializar_agente(modelo_geral, modelo_coder):
    global agente
    try:
        agente = AgenteIA(modelo_geral=modelo_geral, modelo_coder=modelo_coder)
        modelo_status["geral"] = modelo_geral
        modelo_status["coder"] = modelo_coder
        return True
    except Exception as e:
        print(f"Erro ao inicializar agente: {str(e)}")
        return False

@app.route('/')
def home():
    return render_template('index.html', modelos=config.AVAILABLE_MODELS)

@app.route('/carregar_ia', methods=['POST'])
def carregar_ia():
    data = request.get_json()
    modelo_geral = config.AVAILABLE_MODELS[int(data['modelo_geral'])]
    modelo_coder = config.AVAILABLE_MODELS[int(data['modelo_coder'])]

    if inicializar_agente(modelo_geral, modelo_coder):
        return jsonify({
            "status": "success",
            "message": "IA carregada com sucesso!",
            "modelos": modelo_status
        })
    return jsonify({
        "status": "error",
        "message": "Erro ao carregar IA"
    })

@app.route('/status')
def get_status():
    return jsonify(modelo_status)

@app.route('/upload_arquivo', methods=['POST'])
def upload_arquivo():
    if 'arquivo' not in request.files:
        return jsonify({"status": "error", "message": "Nenhum arquivo enviado."})
    arquivo = request.files['arquivo']
    if arquivo.filename == '':
        return jsonify({"status": "error", "message": "Arquivo vazio."})

    try:
        filename = secure_filename(arquivo.filename)
        caminho = os.path.join('temp', filename)
        os.makedirs('temp', exist_ok=True)
        arquivo.save(caminho)

        if agente is None:
            return jsonify({"status": "error", "message": "IA não carregada."})

        resposta = agente.processar_arquivo(caminho)
        historico.append({"remetente": "Sistema", "mensagem": f"Arquivo '{filename}' processado"})
        historico.append({"remetente": "Agente", "mensagem": resposta})

        # Limpar arquivo temporário
        try:
            os.remove(caminho)
        except:
            pass

        return jsonify({"status": "success", "message": resposta})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/enviar_mensagem', methods=['POST'])
def enviar_mensagem():
    global agente
    if agente is None:
        return jsonify({"status": "error", "message": "IA não carregada."})
    data = request.get_json()
    mensagem = data.get('mensagem', '')
    temperatura = data.get('temperatura')
    top_p = data.get('top_p')
    perfil = data.get('perfil')
    if not mensagem:
        return jsonify({"status": "error", "message": "Mensagem vazia."})
    try:
        resposta = agente.processar_mensagem(
            mensagem,
            temperatura=temperatura,
            top_p=top_p,
            perfil=perfil
        )
        historico.append({"remetente": "Você", "mensagem": mensagem})
        historico.append({"remetente": "Agente", "mensagem": resposta})
        return jsonify({"status": "success", "resposta": resposta})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/historico')
def get_historico():
    return jsonify(historico)

@app.route('/limpar_historico', methods=['POST'])
def limpar_historico():
    historico.clear()
    if agente:
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
    app.run(debug=True)