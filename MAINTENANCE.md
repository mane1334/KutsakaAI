# Documentação de Manutenção - Agente IA

## Estrutura do Projeto
```
.
├── agente.py          # Arquivo principal do agente
├── config.py          # Configurações do sistema
├── VERSION           # Controle de versão
├── MAINTENANCE.md    # Esta documentação
├── logs/             # Diretório de logs
└── temp_audio/       # Diretório para arquivos de áudio temporários
```

## Sistema de Logs
Os logs são estruturados em diferentes níveis:
- DEBUG: Informações detalhadas para debugging
- INFO: Informações gerais de operação
- WARNING: Avisos que não impedem a operação
- ERROR: Erros que podem afetar funcionalidades
- CRITICAL: Erros críticos que podem parar o sistema

### Formato dos Logs
```
TIMESTAMP - NÍVEL - MENSAGEM
Exemplo: 2024-03-20 10:30:45 - INFO - Agente iniciado com sucesso
```

## Atualizações do Sistema
1. Verificar a versão atual em `VERSION`
2. Fazer backup dos arquivos de configuração
3. Atualizar os arquivos necessários
4. Testar as novas funcionalidades
5. Atualizar o arquivo `VERSION` e `CHANGELOG`

## Troubleshooting

### Problemas Comuns

1. **Erro de Conexão com LLM**
   - Verificar se o servidor LM Studio está rodando
   - Confirmar as configurações em `config.py`
   - Verificar a porta e URL do servidor

2. **Problemas com Reconhecimento de Voz**
   - Verificar se o microfone está funcionando
   - Confirmar instalação do Faster-Whisper
   - Verificar permissões do sistema

3. **Erros de Permissão de Arquivo**
   - Verificar permissões do diretório de logs
   - Confirmar permissões do diretório temp_audio
   - Verificar permissões de escrita

### Logs de Erro
Os logs de erro são salvos em `logs/error.log` com o formato:
```
TIMESTAMP - ERROR - [CONTEXTO] - MENSAGEM
Exemplo: 2024-03-20 10:30:45 - ERROR - [LLM] - Falha na conexão com o servidor
```

## Manutenção Regular

### Diária
- Verificar logs de erro
- Limpar arquivos temporários
- Verificar espaço em disco

### Semanal
- Fazer backup das configurações
- Verificar atualizações disponíveis
- Analisar logs de performance

### Mensal
- Revisar e limpar logs antigos
- Verificar integridade do sistema
- Atualizar documentação

## Contato e Suporte
Para problemas e sugestões:
1. Verificar a documentação
2. Consultar os logs
3. Abrir uma issue no repositório

## Procedimentos de Backup
1. Fazer backup de `config.py`
2. Salvar logs importantes
3. Documentar alterações feitas
4. Testar restauração do backup 