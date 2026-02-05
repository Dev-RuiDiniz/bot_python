# bot_python

Estrutura inicial de automação Android com ADB + OpenCV, separada por camadas:

- `bot/core`: wrappers de ADB, visão, exceções e logging.
- `bot/flow`: passos de automação baseados em `Step`.
- `bot/runner`: execução por instância e orquestração em multiprocess.
- `bot/config`: configurações externas em YAML.
- `bot/assets/templates`: templates OpenCV.

## Execução

```bash
python -m bot.main --bot-config bot/config/bot.yaml --instances-config bot/config/instances.yaml
```

Modo paralelo:

```bash
python -m bot.main --parallel
```
