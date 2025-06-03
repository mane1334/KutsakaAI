# AgenteIA

Um assistente virtual inteligente com múltiplas capacidades e ferramentas.

## Funcionalidades

### 1. Processamento de Texto
- Análise de sentimento
- Geração de resumos
- Classificação de texto
- Extração de entidades
- Verificação de plágio

### 2. Manipulação de Dados
- Conversão entre formatos (JSON, CSV, XML)
- Validação de dados
- Filtragem e ordenação
- Agregação e estatísticas
- Visualização de dados

### 3. Segurança
- Verificação de segurança de URLs
- Sanitização de input
- Validação de permissões
- Criptografia de dados
- Verificação de vulnerabilidades

### 4. Otimização
- Otimização de código
- Análise de performance
- Redução de complexidade
- Melhoria de legibilidade
- Refatoração de código

### 5. Documentação
- Geração de documentação
- Extração de comentários
- Validação de documentação
- Atualização de docs
- Geração de exemplos

### 6. Integração
- Verificação de APIs
- Validação de webhooks
- Teste de conexão
- Monitoramento de serviços
- Sincronização de dados

### 7. Desenvolvimento
- Geração de testes
- Validação de código
- Execução de testes
- Geração de propriedades
- Análise de complexidade

### 8. Suporte
- Geração de logs
- Análise de erros
- Monitoramento do sistema
- Verificação de saúde
- Limpeza de recursos

## Estrutura do Projeto (Project Structure)

Uma visão geral da organização das pastas principais no projeto:

-   `agenteia/`: Contém o código fonte principal do AgenteIA, incluindo o core, ferramentas e configurações.
-   `tests/`: Contém os testes unitários e de integração.
-   `historico/`: Armazena o histórico de interações (se aplicável).
-   `logs/`: Contém os arquivos de log da aplicação.
-   `pages/`: Módulos relacionados às diferentes páginas/seções da interface Streamlit.
-   `vector_db/`: Diretório para armazenamento de banco de dados vetoriais (ex: ChromaDB).
-   `requirements.txt`: Dependências principais da aplicação.
-   `requirements-dev.txt`: Dependências para desenvolvimento, testes e documentação.
-   `requirements-office.txt`: Dependências opcionais para funcionalidades de manipulação de documentos Office.
-   `.env.example`: Arquivo de exemplo para configuração de variáveis de ambiente.

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/agenteia.git
cd agenteia
```

2. Crie um ambiente virtual e ative-o (recomendado):
```bash
python -m venv venv
# No Windows:
# venv\Scripts\activate
# No macOS/Linux:
# source venv/bin/activate
```

3. Instale as dependências:
```bash
# Instale as dependências core
pip install -r requirements.txt

# Para desenvolvimento (inclui ferramentas de teste, linting, documentação):
# pip install -r requirements-dev.txt
# Ou instale junto com as core:
# pip install -r requirements.txt -r requirements-dev.txt

# Para funcionalidades opcionais de processamento de documentos Office:
# pip install -r requirements-office.txt
# Ou instale junto com as core:
# pip install -r requirements.txt -r requirements-office.txt
```

4. Configure as variáveis de ambiente:
   Copie o arquivo `.env.example` para `.env` e edite-o com suas configurações:
   ```bash
   cp .env.example .env
   ```
   Ou, se preferir, crie um arquivo `.env` manualmente e adicione as variáveis necessárias (veja `.env.example` para uma lista de variáveis comuns como `OPENROUTER_API_KEY`, `OLLAMA_API_BASE`, etc.).

5. Execute o aplicativo:
```bash
streamlit run interface.py
```

## Gerenciando Dependências (Managing Dependencies)

Este projeto utiliza múltiplos arquivos de requisitos para diferentes propósitos:

-   `requirements.txt`: Contém as dependências essenciais para executar a aplicação principal.
-   `requirements-dev.txt`: Inclui pacotes necessários para desenvolvimento, como linters, formatadores, ferramentas de teste e bibliotecas para geração de documentação. Instale estas se você pretende contribuir com o desenvolvimento ou rodar testes.
-   `requirements-office.txt`: Lista dependências opcionais necessárias para funcionalidades específicas de processamento de documentos do Microsoft Office (Word, Excel, PowerPoint). Instale estas apenas se precisar dessas funcionalidades.

É altamente recomendável usar um ambiente virtual (virtual environment) para gerenciar as dependências do projeto, conforme demonstrado na seção de instalação.

## Uso

O AgenteIA pode ser usado através da interface web iniciada com `streamlit run interface.py`.
Consulte a documentação interna ou o código para mais detalhes sobre cada funcionalidade e o uso de APIs (se aplicável).

## Solução de Problemas (Troubleshooting)

-   **Erro de Módulo Não Encontrado (ModuleNotFoundError)**:
    -   Certifique-se de que seu ambiente virtual está ativado.
    -   Verifique se instalou as dependências necessárias: `pip install -r requirements.txt`.
    -   Se o erro for relacionado a uma ferramenta de desenvolvimento, instale `pip install -r requirements-dev.txt`.
    -   Para funcionalidades de Office, instale `pip install -r requirements-office.txt`.
-   **Problemas com `pywin32` no Linux/macOS**:
    -   A dependência `pywin32` é específica para Windows e está listada em `requirements-office.txt`.
    -   Se você não estiver usando funcionalidades do Office no Windows, você geralmente não precisará instalar `requirements-office.txt` ou pode remover/comentar a linha do `pywin32` de `requirements-office.txt` se for customizar a instalação.
-   **Verifique as Variáveis de Ambiente**: Alguns erros podem ocorrer se as variáveis de ambiente (no arquivo `.env`) não estiverem configuradas corretamente (ex: chaves de API, endpoints de serviços).

## Contribuindo

Contribuições são bem-vindas! Por favor, leia o guia de contribuição antes de enviar um pull request. (Obs: Guia de contribuição não encontrado no projeto, idealmente seria um `CONTRIBUTING.md`)

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.
