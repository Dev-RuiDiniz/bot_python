# bot_python

Fundação do bot Android (DIA 1), com foco em arquitetura e execução por instância.

Atualização DIA 2: runner com isolamento por processo, safe shutdown e Step 01 robusto para validação de Home.

## Estrutura

- `bot/config`: YAML e loader de configurações (`bot.yaml` e `instances.yaml`).
- `bot/core`: wrappers de ADB, visão inicial, exceções e logger por instância.
- `bot/flow`: passos da automação (inclui `step_00_mock` para bootstrap).
- `bot/runner`: runner de instância e execução multiprocess.
- `bot/main.py`: orquestração via configuração.

## Execução

### Sequencial

```bash
python -m bot.main --bot-config bot/config/bot.yaml --instances-config bot/config/instances.yaml
```

> O fluxo padrão atual executa o `step_01_home`.

### Paralelo com config

```bash
python -m bot.main --parallel
```

### Paralelo com 2 instâncias fake (bootstrap)

```bash
python -m bot.main --fake
```


## Relatórios

- `docs/RELATORIO_DIA1.md`: relatório textual por task do DIA 1.
