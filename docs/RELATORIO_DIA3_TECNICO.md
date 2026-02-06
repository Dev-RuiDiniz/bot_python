# RELATÓRIO TÉCNICO — DIA 3

## Contexto
Este relatório descreve a execução das tarefas do **DIA 3**, cujo objetivo era:
1) tornar o projeto testável sem ADB real,
2) consolidar contratos (configs/templates/logs),
3) implementar o próximo bloco do fluxo com segurança,
4) ajustar compatibilidade removendo fixtures binárias versionadas.

---

## 1) Dependency hygiene (obrigatório)
**Status:** ✅ Concluído

### Entregas
- `requirements.txt` com dependências explícitas:
  - `PyYAML`
  - `opencv-python`
  - `numpy`
- Validação de imports em bootstrap via `validate_runtime_dependencies()`.
- Mensagem clara para instalação quando faltarem pacotes.

### Resultado técnico
- Falhas por dependência ausente agora são explícitas e antecipadas no startup.
- Contrato de runtime mais previsível para execução local e CI.

---

## 2) Interface de ADB (contrato) + FakeADB
**Status:** ✅ Concluído

### Entregas
- Criação da interface `IAdb` (Protocol) com operações mínimas do fluxo:
  - `connect`, `tap`, `keyevent`, `start_app`, `stop_app`, `screencap`.
- `ADBClient` real adaptado para implementar o contrato.
- Runner/steps tipados para depender da interface, não de implementação concreta.
- `FakeADB` com:
  - `screencap()` baseado em sequência de telas mock,
  - registro de chamadas (`tap`, `start_app`, `stop_app`, etc.),
  - avanço controlado de estado de tela.

### Resultado técnico
- Fluxo desacoplado de device real.
- Base sólida para testes determinísticos e sem ADB.

---

## 3) Fixtures de tela + simulador de estado
**Status:** ✅ Concluído (com ajuste de compatibilidade)

### Entregas
- Inicialmente foram criadas fixtures PNG versionadas para testes.
- Após feedback de compatibilidade (**"Arquivos binários não são compatíveis"**), houve refatoração:
  - remoção de todos os binários em `tests/fixtures/**`,
  - geração de imagens mock em runtime por helper textual (`tests/support/mock_images.py`),
  - uso de `TemporaryDirectory` nos testes.

### Resultado técnico
- Mantida a mesma semântica de testes de visão/fluxo.
- Repositório sem dependência de arquivos binários versionados.

---

## 4) Testes unitários do Vision
**Status:** ✅ Concluído

### Cobertura entregue
- `exists()`
- `wait_for()` com timeout/poll
- `click_template()` validando clique no centro

### Observação de ambiente
- Os testes de Vision permanecem com `skip` automático quando `opencv-python` (`cv2`) não está disponível.

---

## 5) Testes do Step 01 sem device
**Status:** ✅ Concluído

### Cenários implementados
- Sucesso (home aparece)
- Erro de conexão (fecha e recupera)
- Crash (stop + relaunch)
- `CriticalFail` após `max_attempts`

### Resultado técnico
- Validação de comportamento crítico do Step 01 sem depender de dispositivo.

---

## 6) Revisão de logs: correlação e tentativa
**Status:** ✅ Concluído

### Entregas
- Padronização dos logs de tentativa no Step 01 com prefixo:
  - `[inst=][step=][attempt=]`
- Snapshot de falha com metadados coerentes no nome e no log.

### Resultado técnico
- Melhor rastreabilidade por instância/etapa/tentativa.

---

## 7) Recovery reutilizável
**Status:** ✅ Concluído

### Entregas
- Extração da rotina para `recover_to_home()` reutilizável.
- Reuso no Step 01.
- Reuso no Step 03 (confirmação de Home).

### Resultado técnico
- Menor duplicação e comportamento de recovery consistente.

---

## 8) Implementação Step 02 — Roleta inicial (esqueleto)
**Status:** ✅ Concluído

### Entregas
- Fluxo skeleton com `SoftFail` por padrão quando indisponível.
- Caminho positivo implementado:
  - detecta `roleta.popup_roleta_disponivel`,
  - entra,
  - gira 1x,
  - fecha.

### Resultado técnico
- Próximo bloco do fluxo operacionalizado com fallback seguro.

---

## 9) Implementação Step 03 — Confirmação da Home
**Status:** ✅ Concluído

### Entregas
- Step 03 utilizando `recover_to_home()`.
- Em falha de recuperação: `CriticalFail`.

### Resultado técnico
- Garantia explícita de retorno ao estado base antes de prosseguir no pipeline.

---

## 10) Consolidação do pipeline
**Status:** ✅ Concluído

### Entregas
- Runner atualizado para sequência padrão:
  - `Step01Home` → `Step02Roleta` → `Step03ConfirmHome`

### Resultado técnico
- Fluxo principal do DIA 3 encadeado com tolerância a falhas recuperáveis.

---

## Limitações de ambiente observadas
1. Ambiente com restrição de rede/proxy para instalação de dependências via `pip install -r requirements.txt`.
2. Ausência local de `opencv-python` em parte das execuções (testes de Vision com skip planejado).

---

## Conclusão
O objetivo do DIA 3 foi atingido:
- projeto ficou testável sem ADB real,
- contratos de runtime/config/templates/logs foram consolidados,
- fluxo avançou com Step 02/03 e recovery reutilizável,
- e o ajuste de compatibilidade de artefatos binários foi concluído com geração de mocks em runtime.
