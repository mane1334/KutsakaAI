"""
Interface web do MCP Server usando FastAPI.
"""

from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import psutil
import requests
from fastapi.responses import JSONResponse
import json

from .server import MCPServer
from ..ferramentas import listar_arquivos, ler_arquivo, escrever_arquivo, criar_diretorio, copiar_arquivo, mover_arquivo, remover_arquivo, remover_diretorio, executar_comando, pesquisar_web
from ..ferramentas.documentos import criar_documento_word, criar_curriculo, criar_relatorio, converter_para_word

# Modelos Pydantic
class TarefaRequest(BaseModel):
    """Modelo para requisição de tarefa."""
    tarefa: str
    agente_id: Optional[str] = None
    
class FerramentaRequest(BaseModel):
    """Modelo para requisição de ferramenta."""
    nome: str
    parametros: Dict[str, Any]
    
class AgenteInfo(BaseModel):
    """Modelo para informações do agente."""
    nome: str
    especialidades: List[str]
    status: str
    
class FerramentaInfo(BaseModel):
    """Modelo para informações da ferramenta."""
    nome: str
    usos: int
    erros: int
    tempo_medio: float
    
# Inicializar FastAPI
app = FastAPI(
    title="MCP Server API",
    description="API para gerenciamento de agentes e ferramentas",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar MCP Server
mcp = MCPServer()

# Registrar ferramentas no MCP Server
mcp.registrar_ferramenta("listar_arquivos", listar_arquivos)
mcp.registrar_ferramenta("ler_arquivo", ler_arquivo)
mcp.registrar_ferramenta("escrever_arquivo", escrever_arquivo)
mcp.registrar_ferramenta("criar_diretorio", criar_diretorio)
mcp.registrar_ferramenta("copiar_arquivo", copiar_arquivo)
mcp.registrar_ferramenta("mover_arquivo", mover_arquivo)
mcp.registrar_ferramenta("remover_arquivo", remover_arquivo)
mcp.registrar_ferramenta("remover_diretorio", remover_diretorio)
mcp.registrar_ferramenta("executar_comando", executar_comando)
mcp.registrar_ferramenta("criar_documento_word", criar_documento_word)
mcp.registrar_ferramenta("criar_curriculo", criar_curriculo)
mcp.registrar_ferramenta("criar_relatorio", criar_relatorio)
mcp.registrar_ferramenta("converter_para_word", converter_para_word)
mcp.registrar_ferramenta("pesquisar_web", pesquisar_web)

# Rotas
@app.get("/")
async def root():
    """Rota raiz."""
    return {"mensagem": "MCP Server API"}

@app.get("/status")
async def obter_status():
    """Obtém o status do sistema."""
    try:
        # Verificar status do Ollama
        try:
            response = requests.get("http://localhost:11434/api/version")
            ollama_online = response.status_code == 200
        except:
            ollama_online = False
            
        # Obter métricas do sistema
        cpu_uso = psutil.cpu_percent()
        memoria_uso = psutil.virtual_memory().percent
        disco_uso = psutil.disk_usage('/').percent
        
        return {
            "ollama_online": ollama_online,
            "cpu_uso": cpu_uso,
            "memoria_uso": memoria_uso,
            "disco_uso": disco_uso
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agentes/{nome}")
async def registrar_agente(nome: str, agente_info: AgenteInfo):
    """Registra um novo agente."""
    mcp.logger.info(f"Recebida requisição de registro para agente '{nome}' com informações: {agente_info.dict()}") # Log de depuração
    
    # Chamar o método registrar do gerenciador de agentes com as informações fornecidas
    # O gerenciador de agentes irá armazenar estas informações e não o objeto agente completo aqui
    # Note: A lógica atual do GerenciadorAgentes espera o objeto agente, precisaremos ajustar isso também.
    # Por enquanto, vamos apenas passar as informações que recebemos.
    if mcp.registrar_agente_info(nome, agente_info.dict()): # Passar um dicionário com as informações
        return {"mensagem": f"Agente {nome} registrado com sucesso"}
    raise HTTPException(status_code=400, detail=f"Erro ao registrar agente {nome}")

@app.get("/agentes")
async def listar_agentes():
    """Lista todos os agentes registrados."""
    agentes_info = {}
    for nome, info in mcp.gerenciador_agentes._agentes.items():
        agentes_info[nome] = {
            'nome': nome,
            'especialidades': info.get('especialidades', []),
            'status': info.get('status', 'desconhecido'),
            'provedor_modelo': info.get('provedor_modelo', None),
            'modelo_geral': info.get('modelo_geral', None),
            'modelo_coder': info.get('modelo_coder', None),
            'tarefas': info.get('tarefas', 0),
            'erros': info.get('erros', 0),
            'ultima_tarefa': info.get('ultima_tarefa', None).isoformat() if info.get('ultima_tarefa') else None
        }
    return agentes_info

@app.post("/tarefas")
async def distribuir_tarefa(request: TarefaRequest):
    """Distribui uma tarefa para o MCP Server para execução (geralmente execução de ferramenta)."""
    try:
        # Analisar o conteúdo da tarefa. Esperamos uma string JSON com detalhes da execução da ferramenta.
        try:
            tarefa_data = json.loads(request.tarefa)
            
            # Verificar se é uma tarefa de execução de ferramenta
            if isinstance(tarefa_data, dict) and tarefa_data.get("tipo") == "executar_ferramenta":
                nome_ferramenta = tarefa_data.get("nome_ferramenta")
                parametros = tarefa_data.get("parametros", {})
                
                if not nome_ferramenta:
                    raise ValueError("Nome da ferramenta não especificado na tarefa de execução.")
                    
                # Chamar o método executar_ferramenta do MCP Server
                mcp.logger.info(f"Encaminhando execução da ferramenta '{nome_ferramenta}' para mcp.executar_ferramenta com parâmetros: {parametros}")
                resultado_execucao = mcp.executar_ferramenta(nome_ferramenta, **parametros)
                mcp.logger.info(f"Execução via mcp.executar_ferramenta concluída. Resultado: {resultado_execucao}")
                
                return {"resultado": resultado_execucao} # Retorna o resultado da execução da ferramenta
            
            # Se não for uma tarefa de execução de ferramenta reconhecida, pode ser uma tarefa genérica ou inválida
            else:
                mcp.logger.warning(f"Tarefa recebida não é uma tarefa de execução de ferramenta reconhecida: {request.tarefa}")
                return {"mensagem": "Formato de tarefa inválido ou não suportado para execução direta.", "tarefa_recebida": tarefa_data}
                
        except json.JSONDecodeError:
            # Lidar com casos onde a tarefa não é um JSON válido
            mcp.logger.warning(f"Tarefa recebida não é um JSON válido: {request.tarefa}")
            raise HTTPException(status_code=400, detail="Formato de tarefa inválido. Espera-se um JSON para execução de ferramenta.")
            
        except ValueError as ve:
            # Lidar com erros de validação (ferramenta não encontrada, input inválido, etc.) dentro da lógica de execução de ferramenta
            mcp.logger.error(f"Erro de validação na tarefa: {ve}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Erro na requisição: {str(ve)}")
        
        except Exception as e:
            # Lidar com erros inesperados durante a execução da ferramenta
            mcp.logger.error(f"Erro inesperado ao processar tarefa de execução de ferramenta: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro interno do servidor ao executar ferramenta: {str(e)}")
            
    except Exception as e: # Captura erros do try mais externo para garantir
        mcp.logger.error(f"Erro inesperado na rota /tarefas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor ao processar tarefa: {str(e)}")

@app.get("/ferramentas")
async def listar_ferramentas_mcp():
    """Lista todas as ferramentas registradas no MCP Server."""
    ferramentas_info = {}
    # A instância global 'mcp' em api.py contém a lista de ferramentas registradas
    if mcp:
        for nome, ferramenta_obj in mcp.gerenciador_ferramentas._ferramentas.items():
            ferramentas_info[nome] = {
                "nome": nome,
                "descricao": getattr(ferramenta_obj, "description", "Sem descrição") # Tenta obter a descrição da ferramenta
            }
    return JSONResponse(content=ferramentas_info)

@app.post("/ferramentas/{nome}")
async def registrar_ferramenta(nome: str, ferramenta: Any):
    """Registra uma nova ferramenta."""
    if mcp.registrar_ferramenta(nome, ferramenta):
        return {"mensagem": f"Ferramenta {nome} registrada com sucesso"}
    raise HTTPException(status_code=400, detail=f"Erro ao registrar ferramenta {nome}")

@app.post("/ferramentas/{nome}/executar")
async def executar_ferramenta(nome: str, request: FerramentaRequest):
    """Executa uma ferramenta."""
    try:
        resultado = mcp.executar_ferramenta(nome, **request.parametros)
        return {"resultado": resultado}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/metricas")
async def obter_metricas():
    """Obtém métricas do sistema."""
    return mcp.monitorar_recursos()

@app.get("/relatorio")
async def gerar_relatorio():
    """Gera relatório do sistema."""
    return mcp.gerar_relatorio()

def iniciar_servidor(host: str = "0.0.0.0", porta: int = 8000):
    """Inicia o servidor web."""
    uvicorn.run(app, host=host, port=porta)

if __name__ == "__main__":
    iniciar_servidor() 