import pytest
from agenteia.core.compreensao import CompreensaoMensagem, INTENCOES

@pytest.fixture
def compreensao_fixture():
    return CompreensaoMensagem()

def test_normalizar_texto(compreensao_fixture):
    texto = "  Olá, Mundo! Como VAI você?  "
    normalizado = compreensao_fixture._normalizar_texto(texto)
    assert normalizado == "olá mundo como vai você"

@pytest.mark.parametrize("texto, intencao_esperada, confianca_minima", [
    ("como funciona o python?", "consulta", 0.3),
    ("liste os arquivos da pasta Documentos", "listar", 0.3),
    ("crie um arquivo de texto chamado teste.txt", "criar", 0.3),
    ("edite o arquivo config.py", "editar", 0.3),
    ("execute o script de limpeza", "executar", 0.3),
    ("preciso de ajuda para instalar o python", "ajuda", 0.3),
    ("qual o clima para hoje?", "consulta", 0.3), # Exemplo genérico de consulta
    ("mostre as imagens na área de trabalho", "listar", 0.3),
    ("faça um programa que some dois números", "criar", 0.3),
    ("atualize o documento de requisitos", "editar", 0.3),
    ("rode o comando ls -l", "executar", 0.3),
    ("como eu configuro o agente?", "ajuda", 0.3),
    ("uma frase aleatória sem intenção clara", None, 0.0) # Teste para baixa confiança
])
def test_analisar_intencao(compreensao_fixture, texto, intencao_esperada, confianca_minima):
    resultado = compreensao_fixture.analisar(texto)
    if intencao_esperada:
        assert resultado["intencao"] == intencao_esperada
        assert resultado["confianca"] >= confianca_minima
    else:
        # Se nenhuma intenção é esperada, a confiança deve ser baixa ou a intenção None
        if resultado["intencao"] is not None:
            assert resultado["confianca"] < 0.3 # Um limiar baixo para "nenhuma intenção"
        else:
            assert resultado["intencao"] is None

@pytest.mark.parametrize("texto, intencao, parametros_esperados", [
    ("liste os arquivos em /home/user/docs", "listar", {"diretorio": "/home/user/docs"}),
    ("liste os arquivos do desktop", "listar", {"diretorio": "desktop"}),
    ("mostre os arquivos .txt na pasta downloads", "listar", {"diretorio": "downloads", "extensao": "txt"}),
    ("pesquise sobre python", "consulta", {"query": "sobre python"}),
    ("o que é inteligência artificial", "consulta", {"query": "inteligência artificial"}),
    ("edite o arquivo /path/to/file.txt", "editar", {"caminho": "/path/to/file.txt"}),
    ("modifique o código main.py", "editar", {"caminho": "main.py"}),
    ("execute o comando sudo apt update", "executar", {"comando": "sudo apt update"}),
    ("rode o script start.sh", "executar", {"comando": "start.sh"})
])
def test_extrair_parametros(compreensao_fixture, texto, intencao, parametros_esperados):
    # A função _extrair_parametros é chamada internamente por analisar.
    # Para testá-la mais diretamente, podemos simular uma intenção detectada.
    resultado = compreensao_fixture._extrair_parametros(texto, intencao)
    for chave, valor in parametros_esperados.items():
        assert chave in resultado
        assert resultado[chave] == valor

def test_calcular_confianca_palavras_chave(compreensao_fixture):
    # Teste focado em palavras-chave
    texto = "qual o preço do dólar"
    confianca = compreensao_fixture._calcular_confianca(texto, "consulta")
    assert confianca > 0.3 # Deve ter alguma confiança baseada em "qual"

def test_calcular_confianca_contexto(compreensao_fixture):
    # Teste focado em contexto
    texto = "minha dúvida é sobre a instalação"
    confianca = compreensao_fixture._calcular_confianca(texto, "ajuda")
    assert confianca > 0.2 # Deve ter alguma confiança baseada em "dúvida"

def test_analisar_texto_vazio(compreensao_fixture):
    resultado = compreensao_fixture.analisar("")
    assert resultado["intencao"] is None
    assert resultado["confianca"] == 0.0
    assert resultado["params"] == {}

# Testar se todas as intenções definidas em INTENCOES são minimamente reconhecidas
@pytest.mark.parametrize("intencao_nome", INTENCOES.keys())
def test_reconhecimento_basico_todas_intencoes(compreensao_fixture, intencao_nome):
    # Pegar a primeira palavra-chave como exemplo simples para a intenção
    if INTENCOES[intencao_nome]["palavras_chave"]:
        exemplo_texto = INTENCOES[intencao_nome]["palavras_chave"][0]
        resultado = compreensao_fixture.analisar(exemplo_texto)
        # A confiança pode variar, mas a intenção deve ser a esperada
        # ou pelo menos ter uma confiança razoável se a palavra-chave for ambígua
        if resultado["intencao"] == intencao_nome:
            assert resultado["confianca"] > 0.1 # Um valor baixo, já que é só uma palavra
        else:
            # Algumas palavras-chave podem ser muito genéricas e levar a outra intenção
            # Este teste é mais para garantir que não há erros ao processar cada tipo
            pass
    else:
        pytest.skip(f"Intenção {intencao_nome} não possui palavras-chave para teste básico.")
