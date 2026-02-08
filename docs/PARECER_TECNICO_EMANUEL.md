Relatório Técnico de Finalização - Bot Python (Mobile Automation)
Data: 08 de Fevereiro de 2026

Status: Validado e Pronto para Produção

Ambiente de Teste: Linux (Debian/Ubuntu) -> Android (Physical & Emulator)

1. Visão Geral da Arquitetura
O bot foi desenvolvido utilizando um padrão de Contexto de Instância Decoplado. Isso permite que a lógica de negócio (Steps) seja independente da gestão do hardware (ADB), possibilitando a execução de múltiplas instâncias em paralelo via comando --parallel.

2. Estabilização e Compatibilidade de Ambiente
Durante a fase de validação, foram aplicadas correções críticas para garantir a execução em diversos hardwares:

Fix de Instrução Ilegal: Versões específicas das bibliotecas numpy (1.23.5) e opencv-python-headless (4.6.0.66) foram selecionadas para evitar falhas em CPUs que não suportam instruções AVX modernas (comum em servidores e ambientes de emulação).

Lazy Loading: Implementação de carregamento tardio para dependências pesadas, otimizando o consumo de memória inicial.

3. Resiliência e Gestão de Falhas
O sistema conta com mecanismos de proteção para evitar execuções infinitas ou estados de "travamento":

Circuit Breaker: Monitoramento de erros críticos (ex: HOME_NOT_FOUND). Caso uma instância atinja o limite de falhas, o motor encerra a execução daquela unidade para preservar recursos.

Safe Shutdown: Protocolo automático de encerramento que garante que o aplicativo e a VPN sejam fechados no dispositivo ao final de cada execução ou em caso de erro fatal.

Snapshots de Debug: Em cada falha, o bot gera uma captura de tela em logs/snapshots/ com o timestamp e o nome da etapa, facilitando o ajuste de templates de visão computacional.

# Guia de Execução (Desenvolvedor)
Para rodar o projeto no MEmu ou em celulares físicos:

Ambiente Virtual:

Bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Configuração de Instância: Edite bot/config/instances.yaml e insira o serial do dispositivo (ex: 127.0.0.1:21503 para MEmu).

Execução: Sempre execute a partir da raiz do projeto definindo o PYTHONPATH:

Bash
export PYTHONPATH=$PYTHONPATH:. && python bot/main.py --parallel
5. Notas sobre Visão Computacional
Os templates atuais foram validados. Caso o bot não reconheça um botão devido a diferenças de resolução no emulador:

Confira o snapshot gerado na pasta logs/.

Substitua o arquivo correspondente em bot/assets/templates/ por um recorte da tela do novo ambiente.

A confiança padrão (threshold) está configurada em 0.88, podendo ser ajustada no arquivo de configuração global.