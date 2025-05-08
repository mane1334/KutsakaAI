# Agente IA - Assistente Virtual Inteligente

Um assistente virtual inteligente baseado em IA que pode ajudar com diversas tarefas usando ferramentas integradas.

## Funcionalidades

- Processamento de linguagem natural usando GPT-4
- Pesquisa na web usando DuckDuckGo
- Manipulação de arquivos e diretórios
- Execução de comandos shell (com restrições de segurança)
- Cálculos matemáticos
- Sistema de histórico de conversas
- Logs estruturados

## Requisitos

- Python 3.8+
- Chave de API da OpenAI

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/agente-ia.git
cd agente-ia
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure a chave da API:
```bash
# Windows
set OPENAI_API_KEY=sua-chave-aqui

# Linux/Mac
export OPENAI_API_KEY=sua-chave-aqui
```

Ou crie um arquivo `.env` na raiz do projeto:
```
OPENAI_API_KEY=sua-chave-aqui
```

## Uso

```python
from agente import AgenteIA

# Inicializar o agente
agente = AgenteIA()

# Processar uma mensagem
resposta = agente.processar_mensagem("Olá, como você está?")

# Usar uma ferramenta específica
resultado = agente.usar_ferramenta("pesquisar_web", query="Python programming")

# Salvar histórico
agente.salvar_historico("historico.json")

# Carregar histórico
agente.carregar_historico("historico.json")
```

## Ferramentas Disponíveis

1. `pesquisar_web(query)`: Realiza pesquisas na web
2. `listar_arquivos(diretorio)`: Lista arquivos e diretórios
3. `ler_arquivo(caminho_arquivo)`: Lê conteúdo de arquivos
4. `escrever_arquivo(caminho_arquivo, conteudo)`: Escreve em arquivos
5. `executar_comando(comando)`: Executa comandos shell (com restrições)
6. `calcular(expressao)`: Realiza cálculos matemáticos

## Segurança

- Validação de caminhos de arquivo
- Limite de tamanho de arquivo (10MB)
- Extensões de arquivo permitidas (.txt, .py, .json, .md)
- Comandos shell restritos (ls, dir, echo)
- Timeout em requisições web (30 segundos)

## Logs

Os logs são salvos em `agente.log` e incluem:
- Inicialização do agente
- Processamento de mensagens
- Uso de ferramentas
- Erros e exceções

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes. 