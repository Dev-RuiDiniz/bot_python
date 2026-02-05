# RELATÓRIO TÉCNICO — DIA 2

## Contexto
Este relatório consolida as tarefas executadas no **DIA 2** com foco na entrada do fluxo real, robustez do runner e implementação da **ETAPA 1 — Home**.

---

## 1) Runner com isolamento real por instância (Process)
**Status:** ✅ Concluído

### Implementação
- Substituição de `multiprocessing.Pool` por `multiprocessing.Process` por instância.
- Execução de cada instância em processo dedicado com retorno de resultado via `Queue`.
- Coleta de resultados por índice da instância para preservar ordenação da lista de retorno.
- `join()` obrigatório para todos os processos.
- Fallback para `process.exitcode` quando necessário.

### Ganho técnico
- Isolamento efetivo de falhas por instância.
- Melhor rastreabilidade de saída por processo.
- Base mais previsível para escalabilidade e debugging.

---

## 2) Safe Shutdown mínimo obrigatório
**Status:** ✅ Concluído

### Implementação
- Rotina `_safe_shutdown()` chamada sempre em `finally` no runner.
- Encerramento best effort de:
  - app do jogo (`instance.app_package`),
  - Chrome (`chrome_package`),
  - VPN (`vpn_package`).
- Tratamento tolerante a erro (não interrompe fluxo de finalização).

### Ganho técnico
- Redução de lixo operacional entre execuções.
- Menor acoplamento do resultado final a falhas de desligamento.

---

## 3) Utilitário `click_template()` no Vision
**Status:** ✅ Concluído

### Implementação
- Novo método `click_template()`:
  - captura screenshot via `capture_fn`,
  - executa template matching,
  - chama `adb.tap(center)` automaticamente,
  - registra log com confiança (`confidence`) e coordenadas (`coords`).
- Suporte a IDs lógicos de templates com resolução por:
  - `template_map` (configuração explícita),
  - fallback por conversão lógica (`a.b.c -> a/b/c.png`).

### Ganho técnico
- Reuso de ação “encontrar + clicar” em passos de fluxo.
- Menos duplicação de código e mais consistência de logging.

---

## 4) Step 01 — Abertura do jogo e validação de Home
**Status:** ✅ Concluído

### Implementação
- `Step01Home` como passo padrão do fluxo.
- A cada tentativa:
  - `start_app(...)`,
  - `wait_for(home.tela_home)` com timeout configurável.
- Tratamentos de exceção/estado:
  - detecção de `erros.popup_erro_conexao` + tentativa de fechamento/recovery,
  - detecção de `erros.app_crash` + `stop_app` e relançamento.
- Encerramento em `CriticalFail` após estourar `max_attempts`.

### Ganho técnico
- Primeira etapa operacional de produção com resiliência mínima.
- Melhor comportamento frente a falhas comuns de boot/login/tela.

---

## 5) Recovery para voltar à Home
**Status:** ✅ Concluído

### Implementação
- Helper `_recover_to_home()` no Step 01.
- Tentativa de retorno com `KEYCODE_BACK` até limite configurável.
- Fallback opcional por template `home.botao_home` via `click_template()`.

### Ganho técnico
- Recuperação padronizada entre estados intermediários inesperados.

---

## 6) Padronização de IDs de templates e estrutura de assets
**Status:** ✅ Concluído

### Implementação
- IDs lógicos padronizados no `bot/config/bot.yaml`:
  - `home.tela_home`
  - `home.botao_home`
  - `erros.popup_erro_conexao`
  - `erros.app_crash`
  - `roleta.botao_roleta`
- Estrutura de diretórios criada:
  - `bot/assets/templates/home/`
  - `bot/assets/templates/erros/`
  - `bot/assets/templates/roleta/`

### Ganho técnico
- Convenção única para escala de novos templates.
- Menor ambiguidade entre nome lógico e caminho físico.

---

## 7) Snapshots em falha (fase 1)
**Status:** ✅ Concluído

### Implementação
- Snapshot automático em `CriticalFail` e exceção inesperada.
- Padrão de armazenamento:
  - `logs/snapshots/<inst>/<timestamp>_<step>.png`
- Operação best effort (log de warning em falha de captura).

### Ganho técnico
- Evidência visual forense para investigação de falhas em campo.

---

## 8) Smoke test real em 1 instância
**Status:** ⚠️ Parcial (limitado pelo ambiente)

### Execuções realizadas
- Compilação dos módulos Python (`compileall`) concluída.
- Smoke de `run_instance(...)` executado.
- Smoke de `run_parallel(...)` executado para validar isolamento por processo e coleta de código.

### Limitações observadas
- Ambiente sem binário `adb`, inviabilizando execução E2E real com dispositivo.
- Ambiente sem `PyYAML` e com restrição de rede/proxy para instalação.

### Conclusão do smoke
- A robustez de orquestração/controle foi exercitada.
- A validação funcional final de device/UI permanece dependente de ambiente com ADB + templates reais + dispositivo/emulador ativo.

---

## Configurações adicionadas (DIA 2)
- `chrome_package`
- `vpn_package`
- `step_01.max_attempts`
- `step_01.home_timeout_s`
- `step_01.recovery_back_limit`

---

## Riscos / Pontos de atenção para DIA 3
1. **Cobertura de templates reais**: os diretórios existem, mas o fluxo depende das imagens reais de produção.
2. **Sem ADB no ambiente de CI local**: validar estratégia de teste com mocks/fakes de ADB.
3. **Telemetria**: evoluir logs para incluir correlação de tentativa/estado.
4. **Timeout tuning**: calibrar `threshold` e `timeout` por device/perfil.

---

## Fechamento
O objetivo do DIA 2 foi atingido em nível de arquitetura e robustez inicial da ETAPA 1 (Home), com pendências práticas restritas ao ambiente de execução (ADB/rede/dependências) e à necessidade de templates reais para validação funcional ponta-a-ponta.
