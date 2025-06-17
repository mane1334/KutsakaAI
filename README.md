# KutsakaAI Multi-Provider Project
Version: 1.0.2-beta

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

## 🔌 OpenRouter Setup
1. Get key: https://openrouter.ai/keys
2. `.env`:
```env
AI_PROVIDER="openrouter"
OPENROUTER_API_KEY="sk-or-..."
HTTP_REFERER="https://seu-site.com"
X_TITLE="Seu App Name" # Optional: Sets X-Title header for OpenRouter
```

## 🛡️ Políticas de Segurança
- All inputs validated (Zod)
- Content moderation ON (Conceptual: Requires provider-specific implementation, e.g., via OpenRouter `transforms` or OpenAI Moderation API)
- Auto-key rotation (cron/daily) (Operational Note: This is an infrastructure task, not implemented in the application code itself but a recommended practice.)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/mane1334/KutsakaAI.git
cd agenteia
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. Execute o aplicativo:
```bash
streamlit run interface.py
```

## Uso

O AgenteIA pode ser usado através da interface web ou via API. Consulte a documentação para mais detalhes sobre cada funcionalidade.

## Contribuindo

Contribuições são bem-vindas! Por favor, leia o guia de contribuição antes de enviar um pull request.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.
