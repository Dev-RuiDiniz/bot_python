# Relatório Técnico — DIA 5

## Objetivo do dia
Implementar os módulos **Step 05 (Roleta Principal — 2 giros)** e **Step 06 (Noko Box)** mantendo a disciplina já adotada no Step 04: controle de timeout, tentativas, recuperação para Home, métricas operacionais e testes determinísticos com fakes.

---

## Escopo planejado (tasks do DIA 5)
1. Expandir template IDs para Roleta Principal e Noko Box.
2. Adicionar configuração de threshold por template (`templates_confidence`) com fallback para `default_confidence`.
3. Evoluir visão com `find_best()` (match + score) e debug opcional com bounding box.
4. Implementar Step 05 (esqueleto de navegação + execução de 2 giros + espera de resultado).
5. Implementar métricas e política de falha no Step 05 (SoftFail x CriticalFail).
6. Implementar Step 06 (Noko vazia vs não vazia + saída segura).
7. Cobrir Step 05/06 com testes em FakeADB.
8. Atualizar pipeline para encadear Step 01 → 02 → 03 → 04 → 05 → 06.

---

## Entregas técnicas implementadas

### 1) Template IDs expandidos
Foram centralizados novos IDs lógicos para reduzir risco de typo e padronizar uso entre fluxos:
- **Roleta Principal**: `roleta.botao_roleta_principal`, `roleta.botao_girar`, `roleta.resultado`, `roleta.botao_sair`.
- **Noko Box**: `noko.botao_noko_box`, `noko.tela`, `noko.vazia`, `noko.sair`.

**Impacto técnico:** melhora manutenção e legibilidade dos passos de automação.

### 2) Threshold por template (configurável)
Foi introduzido suporte a:
- `default_confidence` (global)
- `templates_confidence` (override por template)

A regra aplicada no motor de visão ficou:
`threshold explícito na chamada` → `templates_confidence[template]` → `default_confidence`.

**Impacto técnico:** permite tuning fino sem alterar código, importante para estabilidade em assets com variação visual.

### 3) Vision `find_best()` + debug opcional
O motor de visão passou a oferecer:
- `find_best(screen, template)` com retorno de:
  - `score`
  - `center`
  - `top_left`
  - `bottom_right`
- debug opcional via `DEBUG_VISION=1`, salvando screenshot com bounding box anotada.

**Impacto técnico:** acelera diagnóstico de falso positivo/falso negativo e facilita calibração de thresholds.

### 4) Step 05 — Roleta Principal
Implementado novo passo com:
- entrada na roleta principal;
- confirmação de tela antes de operar;
- loop de **2 giros** (configurável);
- timeouts separados:
  - `spin_timeout`
  - `result_timeout`.

#### Política de falha (Step 05)
- Se um giro falha por timeout/ausência de template final: **SoftFail** (degradação controlada, fluxo continua nos próximos steps).
- Se não conseguir retornar à Home após tentativa de saída/recovery: **CriticalFail**.

#### Métricas (Step 05)
- `spins_done`
- `timeouts`
- `recoveries`

### 5) Step 06 — Noko Box
Implementado novo passo com:
- abertura da Noko Box;
- confirmação da tela;
- detecção de estado:
  - **vazia**: registra e sai;
  - **não vazia**: executa coleta (placeholder por cliques) e sai.
- recuperação obrigatória para Home ao final.

#### Política de falha (Step 06)
- Falha em retornar para Home após saída: **CriticalFail**.

#### Métricas (Step 06)
- `opened`
- `empty`
- `collected`
- `recoveries`

### 6) Pipeline atualizado
O encadeamento padrão de execução foi atualizado para:
**Step01 → Step02 → Step03 → Step04 → Step05 → Step06**.

Também foi ampliado o resumo final de execução para incluir métricas dos novos steps.

### 7) Testes automatizados (FakeADB)
Foram adicionados testes unitários determinísticos cobrindo:

#### Step 05
- sucesso com 2 giros;
- timeout ao aguardar resultado (SoftFail);
- travamento sem recuperação para Home (CriticalFail).

#### Step 06
- Noko vazia;
- Noko não vazia com coleta simulada;
- falha de recuperação para Home (CriticalFail).

#### Vision
- retorno do `find_best()` com score + bounding box;
- resolução de threshold por override (`templates_confidence`) sobre default.

---

## Resultado do DIA 5
As tasks do DIA 5 foram concluídas com foco em robustez operacional e testabilidade:
- novos passos funcionais (05 e 06),
- configuração avançada de visão por template,
- instrumentação por métricas,
- política de falhas coerente com continuidade controlada,
- cobertura de testes sem dependência de device real.

---

## Preparação para Steps críticos (07–08)
O trabalho do DIA 5 já deixa base para endurecimento dos módulos VPN/Chrome:
- thresholds calibráveis por template,
- padrão de recovery centralizado,
- separação explícita entre **SoftFail** e **CriticalFail**,
- espaço no resumo para expansão de reason codes.

### Próximos reforços recomendados
1. Introduzir reason codes estruturados (`VPN_TIMEOUT`, `CAPTCHA_DETECTED`, `HOME_NOT_FOUND`).
2. Garantir safe shutdown com confirmação de stop apps (com retry e logs de sucesso/falha).
3. Adicionar circuit breaker por instância para evitar repetição infinita em ambiente degradado.
