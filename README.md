# bot_python

Bot de automação Android orientado a **fluxo por etapas** (steps), com execução por instância (sequencial ou paralela), visão computacional via templates e controle de falhas por `SoftFail`/`CriticalFail`.

O projeto foi estruturado para funcionar tanto com ADB real quanto com execução totalmente testável em ambiente sem device (via mocks/fakes nos testes).

## Visão geral do funcionamento

A execução principal acontece em `python -m bot.main`:

1. Valida dependências de runtime (`PyYAML`, `opencv-python`, `numpy`).
2. Lê configurações do bot e das instâncias em YAML.
3. Para cada instância:
   - cria logger isolado;
   - conecta no device/emulador via ADB;
   - executa os steps `step_01` até `step_10` em ordem;
   - aplica circuit breaker para limitar falhas;
   - gera resumo de métricas no final;
   - faz safe shutdown dos apps.

## Arquitetura do projeto

```text
bot/
  main.py                # CLI/entrypoint
  config/                # YAMLs + loader tipado
  core/                  # ADB, visão, logger, exceções, IDs de template
  flow/                  # steps da automação + recovery para Home
  runner/                # execução por instância + multiprocess
tests/                   # testes unitários e de fluxo com mocks
docs/                    # relatórios técnicos por dia
```

### Papéis principais

- **`bot/main.py`**: parse de argumentos, carga de config, execução sequencial/paralela.
- **`bot/runner/instance_runner.py`**: orquestra uma instância ponta a ponta, coleta métricas e controla falhas.
- **`bot/core/vision.py`**: matching de templates, waits, e cliques por template.
- **`bot/core/adb.py`**: wrapper ADB para `tap`, `keyevent`, `start/stop app`, `open_url`, `screencap`.
- **`bot/flow/*.py`**: lógica de negócio de cada etapa do fluxo.

## Lógica do projeto (fluxo de negócio)

A pipeline padrão executada por instância é:

1. **Step 01 — Home**: abre app e valida tela Home com retry + recovery.
2. **Step 02 — Roleta (skeleton)**: tenta roleta inicial se estiver disponível.
3. **Step 03 — Confirm Home**: garante que recovery para Home funciona.
4. **Step 04 — Amigos**: entra em Amigos, coleta/envia presentes em loop limitado.
5. **Step 05 — Roleta principal**: executa giros configuráveis e retorna para Home.
6. **Step 06 — Noko Box**: abre caixa, diferencia vazia/cheia e coleta quando aplicável.
7. **Step 07 — VPN**: valida/conecta VPN antes do bônus.
8. **Step 08 — Chrome bônus**: abre Chrome e navega para URL de bônus.
9. **Step 09 — Coleta bônus**: retorna ao jogo e coleta bônus se disponível.
10. **Step 10 — Finalização**: confirma Home e encerra app.

### Tratamento de falhas

- **`SoftFail`**: falha recuperável do step (execução pode seguir).
- **`CriticalFail`**: falha crítica que interrompe a instância.
- **Circuit breaker** (configurável): para execução ao atingir limites de softfails/criticals.
- Em falhas críticas/inesperadas, o runner tenta salvar screenshot em `logs/snapshots/...`.

## Configuração

### 1) Configuração global do bot (`bot/config/bot.yaml`)

Principais grupos:

- **ADB/paths**: `adb_bin`, `templates_dir`, `logs_dir`.
- **Templates**: mapa lógico → arquivo PNG (`templates`).
- **Confiança**: `default_confidence` e `templates_confidence` por template.
- **Pacotes**: `chrome_package`, `vpn_package`, `chrome_activity`.
- **Parâmetros por step**: `step_01`, `step_03`, ..., `step_10`.
- **Resiliência**: `breaker`, `shutdown_retries`, `shutdown_retry_delay_s`.
- **Bônus**: `bonus_url`.

### 2) Instâncias (`bot/config/instances.yaml`)

Lista de devices/emuladores com:

- `id`
- `serial` (ADB)
- `app_package`
- `app_activity`

## Como rodar

## Requisitos

- Python 3.11+
- ADB disponível no PATH (ou configurar `adb_bin`)
- Dependências Python do `requirements.txt`

### Instalação

```bash
python -m pip install -r requirements.txt
```

### Execução sequencial

```bash
python -m bot.main --bot-config bot/config/bot.yaml --instances-config bot/config/instances.yaml
```

### Execução paralela

```bash
python -m bot.main --parallel
```

### Execução fake (2 instâncias de exemplo)

Útil para validar orquestração sem depender do arquivo de instâncias.

```bash
python -m bot.main --fake
```

## Logs, runtime e métricas

- Logs por instância em `logs/<instance_id>.log`.
- Screenshots de runtime durante execução em `runtime/<instance_id>/...`.
- Debug de visão (bounding box de matching) em `runtime/vision_debug/...`.
- Snapshot de falha crítica/erro inesperado em `logs/snapshots/<instance_id>/...`.
- Resumo final com métricas no log (steps, duração, breaker, contadores de amigos/roleta/noko etc).

## Códigos de saída da execução

- `0`: execução concluída sem falha crítica.
- `1`: sem instâncias configuradas.
- `2`: houve `CriticalFail` em alguma instância (ou no modo paralelo, algum worker falhou).
- `3`: erro inesperado durante execução da instância.

## Testes

Executar suíte completa:

```bash
python -m unittest discover -s tests -v
```

A suíte cobre visão/template matching e steps do fluxo com mocks/fakes, ajudando a manter comportamento determinístico sem depender de device físico em CI.

## Documentação adicional

Relatórios técnicos incrementais estão em `docs/` (`RELATORIO_DIA*.md`), com o histórico de evolução da arquitetura e das entregas.
