# Documentação do Sistema de Gerenciamento de Tarefas

## Visão Geral
O Sistema de Gerenciamento de Tarefas é uma extensão do AgenteIA que permite monitorar e gerenciar tarefas de geração de código de forma assíncrona. Este documento descreve a arquitetura, componentes e como utilizar o sistema.

## Estrutura do Projeto

```
agenteia/
├── core/
│   ├── ferramentas/
│   │   ├── __init__.py
│   │   ├── monitoramento.py   # Sistema de monitoramento de tarefas
│   │   └── geracao_codigo.py  # Geração de código com monitoramento
│   └── tarefas.py            # Gerenciador de tarefas em segundo plano
├── pages/
│   └── tarefas.py         # Interface Streamlit para gerenciamento
└── interface.py              # Interface principal do AgenteIA
```

## Componentes Principais

### 1. Módulo de Monitoramento (`monitoramento.py`)

Responsável por rastrear o progresso das tarefas assíncronas.

**Principais funcionalidades:**
- Criação de tarefas com descrição e estágios
- Atualização de progresso em tempo real
- Registro de erros e mensagens
- Consulta de status de tarefas

**Classes Principais:**
- `MonitorTarefas`: Classe principal para gerenciar o ciclo de vida das tarefas
- `Tarefa`: Estrutura de dados para armazenar informações de uma tarefa

### 2. Geração de Código (`geracao_codigo.py`)

Implementa a geração de código com suporte a monitoramento.

**Funcionalidades:**
- Geração de código com validação
- Execução de código gerado
- Análise de resultados
- Integração com o sistema de monitoramento

### 3. Gerenciador de Tarefas (`tarefas.py`)

Gerencia tarefas em segundo plano.

**Funcionalidades:**
- Criação de tarefas assíncronas
- Atualização de status
- Recuperação de resultados
- Tratamento de erros

### 4. Interface de Gerenciamento (`pages/tarefas.py`)
Interface Streamlit para interação com o sistema de tarefas.

**Funcionalidades:**
- Visualização de tarefas ativas
- Detalhes de tarefas individuais
- Criação de novas tarefas de geração de código
- Atualização em tempo real do status

## Fluxo de Uso

1. **Iniciar uma Nova Tarefa**
   - Acesse a aba "Tarefas" no menu principal
   - Preencha o formulário de nova tarefa
   - Acompanhe o progresso em tempo real

2. **Monitorar Tarefas Existentes**
   - Visualize todas as tarefas ativas
   - Acompanhe o progresso de cada tarefa
   - Consulte detalhes como mensagens de erro e resultados

3. **Gerenciar Tarefas**
   - Cancele tarefas em andamento (em desenvolvimento)
   - Exporte resultados
   - Consulte histórico de tarefas concluídas

## Configuração

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o script de configuração:
   ```bash
   python setup_tarefas.py
   ```

3. Inicie a interface:
   ```bash
   streamlit run interface.py
   ```

## Boas Práticas

1. **Tratamento de Erros**
   - Sempre utilize blocos try-except para operações que podem falhar
   - Registre mensagens de erro detalhadas

2. **Atualização de Progresso**
   - Atualize o progresso em intervalos razoáveis
   - Forneça mensagens descritivas sobre o andamento

3. **Gerenciamento de Recursos**
   - Libere recursos quando não forem mais necessários
   - Limpe arquivos temporários após o uso

## Limitações Conhecidas

1. O cancelamento de tarefas em andamento ainda não está implementado
2. O histórico de tarefas não é persistido entre reinicializações
3. A interface pode ficar lenta com um grande número de tarefas

## Próximos Passos

1. Implementar persistência de tarefas em banco de dados
2. Adicionar suporte a notificações por e-mail
3. Melhorar a interface de relatórios
4. Adicionar suporte a cancelamento de tarefas

## Suporte

Para relatar problemas ou solicitar recursos, abra uma issue no repositório do projeto.
