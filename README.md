# bot_python

Fundação do bot Android (DIA 1), com foco em arquitetura e execução por instância.

Atualização DIA 3: execução testável sem ADB real, contratos consolidados de configuração/templates/logs e novos passos do fluxo (Step 02 skeleton + Step 03 confirmação da Home).

## Estrutura

- `bot/config`: YAML e loader de configurações (`bot.yaml` e `instances.yaml`).
- `bot/core`: contrato ADB (`IAdb`), ADB real/fake, visão, exceções, logger e validação de dependências.
- `bot/flow`: passos da automação e recovery reutilizável.
- `bot/runner`: runner de instância e execução multiprocess.
- `tests`: testes unitários e fixtures de telas mock para execução sem device.
- `bot/main.py`: orquestração via configuração.

## Dependências

```bash
python -m pip install -r requirements.txt
```

## Execução

### Sequencial

```bash
python -m bot.main --bot-config bot/config/bot.yaml --instances-config bot/config/instances.yaml
```

### Paralelo com config

```bash
python -m bot.main --parallel
```

## Testes

```bash
python -m unittest discover -s tests -v
```
