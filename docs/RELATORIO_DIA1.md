# Relatório de Entrega — DIA 1 (Fundação)

Este documento descreve, tarefa por tarefa, o que foi implementado no projeto até o momento.

## 1) Criar repositório e estrutura de pastas (10%)
**Status:** ✅ Concluída

Foi mantida/organizada a estrutura em camadas:
- `bot/config` (arquivos YAML + loader)
- `bot/core` (ADB, visão, logger, exceções)
- `bot/flow` (passos de automação)
- `bot/runner` (execução por instância e paralelo)
- `bot/main.py` (orquestração)

## 2) Config loader (YAML) (10%)
**Status:** ✅ Concluída

Foi criado `bot/config/loader.py` com:
- `load_yaml()` para leitura e validação de YAML;
- `load_bot_config()` para `bot.yaml`;
- `load_instances_config()` para `instances.yaml`;
- dataclasses `BotConfig`, `InstanceConfig`, `InstancesConfig`.

Também há mensagem explícita quando `PyYAML` não está instalado.

## 3) Logger por instância (10%)
**Status:** ✅ Concluída

Em `bot/core/logger.py`, `setup_instance_logger()` cria:
- logger nomeado por instância (`bot.instance.<id>`);
- output em console;
- arquivo dedicado por instância: `logs/<instance_id>.log`.

## 4) Wrapper ADB básico (15%)
**Status:** ✅ Concluída

No `bot/core/adb.py` foram disponibilizados os métodos pedidos:
- `connect()`
- `screencap()`
- `tap()`
- `start_app()`
- `stop_app()`

Além disso, foi mantido alias `launch_app()` por compatibilidade.

## 5) Classe Vision inicial (15%)
**Status:** ✅ Concluída

No `bot/core/vision.py`:
- carregamento de templates por nome (`load_template()`);
- cache interno de templates para reaproveitamento;
- método `exists()` para checagem booleana rápida;
- métodos auxiliares de matching (`match_template`, `wait_for`).

## 6) Exceptions do bot (5%)
**Status:** ✅ Concluída

No `bot/core/exceptions.py` estão definidos:
- `SoftFail`
- `CriticalFail`

(derivados de `BotError`).

## 7) InstanceRunner (15%)
**Status:** ✅ Concluída

Em `bot/runner/instance_runner.py`:
- criação de contexto por instância (`adb`, `vision`, `logger`, `config`);
- ciclo de execução com `connect()`, `start_app()`, execução de steps e `stop_app()`;
- tratamento de `SoftFail` (recuperável) e `CriticalFail` (retorno de erro).

Foi incluído um passo inicial mock (`Step00Mock`) para validação de bootstrap.

## 8) Multiprocess runner (10%)
**Status:** ✅ Concluída

Em `bot/runner/multiprocess.py`:
- execução paralela por `multiprocessing.Pool`;
- mapeamento de jobs por instância;
- suporte a execução de múltiplas instâncias em paralelo.

No `main.py`, o modo `--fake` permite disparar 2 instâncias fake em paralelo para teste de base.

## 9) main.py (10%)
**Status:** ✅ Concluída

`bot/main.py` está orquestrando:
- parsing de argumentos CLI;
- carregamento de configurações via loader;
- execução sequencial ou paralela;
- opção `--fake` para bootstrap paralelo sem dependência de inventário real.

---

## Resumo final
As 9 tarefas do **DIA 1** foram implementadas na base atual com foco em fundação técnica, separação por camadas e fluxo mínimo executável para evolução dos próximos dias.
