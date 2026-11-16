/*
 * IPS - Sinalizacao fisica de alertas em tempo real
 * Disciplina: Sistemas de Tempo Real - IESB
 * Autor: Caio Silveira Guimaraes Souza
 *
 * Placa: Arduino Uno (ATmega328P, 2 KB de RAM)
 * Biblioteca: FreeRTOS (Phillip Stevens / feilipu) - instalar pelo
 *             Gerenciador de Bibliotecas da IDE, buscando "FreeRTOS".
 *
 * Protocolo serial (115200 baud, uma linha por alerta, terminada em \n):
 *   <severidade>,<classe>,<origem>
 *     severidade: 1 (alta), 2 (media), 3 (baixa)  -> mesma escala do Suricata
 *     classe    : H = servidor critico (hard real-time)
 *                 S = servidor de menor criticidade (soft real-time)
 *     origem    : texto livre (ex.: IP do atacante), apenas para o log
 *   Exemplo: 1,H,10.0.0.66
 *
 * Comandos: ACK        -> reconhece o alarme critico (mesmo que o botao)
 *           STRESS,<n> -> injeta n alertas sinteticos (teste de carga)
 *           STATS      -> imprime estatisticas e pilha livre das tarefas
 *           BEE        -> novo alerta do BeeIA (TCC): pisca o LED branco e
 *                         zumbe como uma abelha (se a sirene nao estiver ativa)
 *
 * Saidas no monitor serial (CSV, para analise posterior):
 *   HARD,<id>,<latencia_us>,<OK|MISS>
 *   SOFT,<qtd_agregada>,<sev_max>,<latencia_ms>,<OK|MISS>
 *
 * Tarefas (prioridade maior = mais urgente):
 *   CRIT (3) alerta hard -> LED vermelho + sirene, mede deadline
 *   RX   (2) le a serial, classifica e encaminha para a fila certa
 *   AGG  (1) agrega alertas soft numa janela e acende o LED amarelo
 *   Timer one-shot (200 ms): apaga o LED branco do BeeIA
 *   Timer periodico (90 ms): sirene de dois tons ate o ACK
 *   Timer periodico (~30 ms): zumbido de abelha do BeeIA (cede a sirene)
 *   Timer de software (500 ms): heartbeat verde, leitura do botao de
 *            stress (avisa a RX) e apagamento do amarelo
 */

#include <Arduino_FreeRTOS.h>
#include <queue.h>
#include <semphr.h>
#include <timers.h>

// ----------------------------------------------------------------- Pinos
const uint8_t PIN_BTN_ACK    = 2;   // INT0 - botao de reconhecimento
const uint8_t PIN_BTN_STRESS = 3;   // botao de teste de carga
const uint8_t PIN_LED_OK     = 8;   // verde    - heartbeat do sistema
const uint8_t PIN_LED_SOFT   = 9;   // amarelo  - alertas soft agregados
const uint8_t PIN_LED_HARD   = 10;  // vermelho - alerta critico (hard)
const uint8_t PIN_LED_MISS   = 11;  // azul     - deadline perdido
const uint8_t PIN_BUZZER     = 12;  // buzzer   - reforco do alerta critico
const uint8_t PIN_LED_BEE    = 7;   // branco   - novo alerta do BeeIA (TCC)
const uint16_t PISCA_BEE_MS  = 200; // duracao da piscada do LED branco

// Sirene do alerta critico: alterna agudo/grave com uma pausa, e so para no
// ACK (alarme "travado", como num painel de seguranca). A pausa faz um buzzer
// ATIVO (que ignora a frequencia) bipar em vez de dar um tom continuo.
const uint16_t FASE_SIRENE_MS = 90;
// As tabelas de tons ficam na flash (PROGMEM): no AVR um array "const" comum
// ocuparia RAM, e o Uno so tem 2 KB. Leitura com pgm_read_word().
const uint16_t SIRENE_HZ[] PROGMEM = { 3200, 1600, 3200, 1600, 3200, 1600, 0 };
const uint8_t  N_FASES_SIRENE = sizeof(SIRENE_HZ) / sizeof(SIRENE_HZ[0]);

// Zumbido do BeeIA: tons graves (180-260 Hz) trocando rapido, o que soa como
// o "bzzz" de uma abelha passando. O buzzer e compartilhado: a sirene do
// alerta HARD tem prioridade, entao o zumbido nao toca (ou para no meio)
// enquanto a sirene estiver ativa. O LED branco pisca de qualquer jeito.
const uint16_t FASE_ZUMBIDO_MS = 30;   // 2 ticks do FreeRTOS no AVR
const uint16_t ZUMBIDO_HZ[] PROGMEM = { 180, 230, 200, 260, 190, 240,
                                        210, 250, 195, 235, 185, 220 };
const uint8_t  N_FASES_ZUMBIDO = sizeof(ZUMBIDO_HZ) / sizeof(ZUMBIDO_HZ[0]);

// --------------------------------------------- Parametros de tempo real
const uint32_t DEADLINE_HARD_US = 50000UL; // 50 ms: leitura -> LED vermelho
const uint16_t JANELA_SOFT_MS   = 1000;    // janela de agregacao (debounce)
const uint16_t DEADLINE_SOFT_MS = 1500;    // 1o evento da janela -> LED amarelo
const uint16_t SOFT_APAGA_MS    = 5000;    // amarelo apaga apos inatividade
const uint16_t PERIODO_MON_MS   = 500;     // periodo do timer de monitoracao
const uint16_t STRESS_PADRAO    = 50;

// ---------------------------------------------------------------- Tipos
enum TipoEvento : uint8_t { EV_ALERTA = 0, EV_ACK = 1 };

struct Evento {
  uint8_t  tipo;
  uint8_t  sev;
  char     classe;
  uint16_t id;
  uint32_t t;      // micros() no momento em que a linha foi lida
};

// ------------------------------------------------- Objetos do FreeRTOS
QueueHandle_t     qHard, qSoft;
SemaphoreHandle_t mtxSerial;
TaskHandle_t      hCrit, hRx, hAgg;
TimerHandle_t     tmBee;           // one-shot: apaga o LED branco
TimerHandle_t     tmSirene;        // periodico: alterna os tons da sirene
volatile bool     sireneAtiva = false;
TimerHandle_t     tmZumbido;       // periodico: fases do zumbido da abelha
volatile uint8_t  faseZumbido = 0; // 0 = parado; 1..N = proxima fase

// --------------------------------------------------------- Estatisticas
volatile uint16_t nRecebidos = 0, nHard = 0, nSoft = 0;
volatile uint16_t nMissHard = 0, nMissSoft = 0, nDescartes = 0, nBee = 0;
volatile uint32_t latHardMax = 0;
volatile TickType_t ultimoSoft = 0;
uint16_t proximoId = 1;

// ------------------------------------------------------------ Prototipos
void tarefaRx(void *p);
void tarefaCritica(void *p);
void tarefaAgregador(void *p);
void timerMonitor(TimerHandle_t t);
void timerApagaBee(TimerHandle_t t);
void timerSirene(TimerHandle_t t);
void timerZumbido(TimerHandle_t t);
void isrAck();
void enfileirarAlerta(uint8_t sev, char classe);
void gerarStress(uint16_t n);
void imprimirStats();

// =======================================================================
void setup() {
  Serial.begin(115200);

  pinMode(PIN_LED_OK, OUTPUT);
  pinMode(PIN_LED_SOFT, OUTPUT);
  pinMode(PIN_LED_HARD, OUTPUT);
  pinMode(PIN_LED_MISS, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_BEE, OUTPUT);
  pinMode(PIN_BTN_ACK, INPUT_PULLUP);     // pull-up interno: sem resistor
  pinMode(PIN_BTN_STRESS, INPUT_PULLUP);

  // Filas pequenas de proposito: o Uno so tem 2 KB de RAM.
  qHard     = xQueueCreate(6, sizeof(Evento));
  qSoft     = xQueueCreate(10, sizeof(Evento));
  mtxSerial = xSemaphoreCreateMutex();

  //                 funcao           nome    pilha param prio handle
  BaseType_t ok =  xTaskCreate(tarefaCritica,   "CRIT", 140, NULL, 3, &hCrit);
  ok &=            xTaskCreate(tarefaRx,        "RX",   170, NULL, 2, &hRx);
  ok &=            xTaskCreate(tarefaAgregador, "AGG",  140, NULL, 1, &hAgg);

  TimerHandle_t tm = xTimerCreate("MON", pdMS_TO_TICKS(PERIODO_MON_MS),
                                  pdTRUE, NULL, timerMonitor);
  if (tm != NULL) xTimerStart(tm, 0);
  tmBee = xTimerCreate("BEE", pdMS_TO_TICKS(PISCA_BEE_MS), pdFALSE, NULL, timerApagaBee);
  tmSirene = xTimerCreate("SIR", pdMS_TO_TICKS(FASE_SIRENE_MS), pdTRUE, NULL, timerSirene);
  tmZumbido = xTimerCreate("ZUM", pdMS_TO_TICKS(FASE_ZUMBIDO_MS), pdTRUE, NULL, timerZumbido);

  attachInterrupt(digitalPinToInterrupt(PIN_BTN_ACK), isrAck, FALLING);

  if (!ok || !qHard || !qSoft || !mtxSerial || !tm || !tmBee || !tmSirene || !tmZumbido) {
    Serial.println(F("# ERRO: memoria insuficiente para criar os objetos"));
  }
  Serial.println(F("# IPS-LED pronto. Formato: sev,classe,origem (ex.: 1,H,10.0.0.66)"));
  Serial.println(F("# Comandos: ACK | STRESS,n | STATS | BEE"));
  // A biblioteca inicia o escalonador do FreeRTOS logo apos o setup().
}

void loop() {
  // Executado dentro da tarefa ociosa (idle). Nada a fazer aqui.
}

// ===================================================== Interrupcao (ACK)
void isrAck() {
  static uint32_t ultimo = 0;
  uint32_t agora = millis();
  if (agora - ultimo < 200) return;          // debounce do botao
  ultimo = agora;

  Evento e = { EV_ACK, 0, 'H', 0, micros() };
  BaseType_t acordou = pdFALSE;
  xQueueSendFromISR(qHard, &e, &acordou);
  if (acordou == pdTRUE) portYIELD_FROM_ISR();
}

// ===================================================== Tarefa RX (prio 2)
// Le linhas da serial, classifica e encaminha para a fila correta.
void tarefaRx(void *p) {
  (void)p;
  static char buf[32];
  uint8_t n = 0;

  for (;;) {
    if (ulTaskNotifyTake(pdTRUE, 0) > 0) gerarStress(STRESS_PADRAO);  // botao

    while (Serial.available() > 0) {
      char c = Serial.read();
      bool fimLinha = (c == '\n' || c == '\r');   // aceita LF, CR ou CRLF
      if (!fimLinha) { if (n < sizeof(buf) - 1) buf[n++] = c; continue; }
      buf[n] = '\0';
      n = 0;
      if (buf[0] == '\0') continue;

      if (strcmp(buf, "ACK") == 0) {
        Evento e = { EV_ACK, 0, 'H', 0, micros() };
        xQueueSend(qHard, &e, 0);
      } else if (strncmp(buf, "STRESS", 6) == 0) {
        uint16_t qtd = (buf[6] == ',') ? (uint16_t)atoi(buf + 7) : STRESS_PADRAO;
        gerarStress(qtd);
      } else if (strncmp(buf, "BEE", 3) == 0) {
        // Alerta do BeeIA: acende o branco e (re)inicia o timer one-shot,
        // que o apaga sozinho. Alertas seguidos estendem a piscada.
        digitalWrite(PIN_LED_BEE, HIGH);
        xTimerReset(tmBee, 0);
        // Zumbido so se a sirene nao estiver tocando. Secao critica curta:
        // sem ela, a CRIT poderia ligar a sirene entre o teste e o tone().
        taskENTER_CRITICAL();
        bool zumbir = !sireneAtiva;
        if (zumbir) { faseZumbido = 1; tone(PIN_BUZZER, pgm_read_word(&ZUMBIDO_HZ[0])); }
        taskEXIT_CRITICAL();
        if (zumbir) xTimerReset(tmZumbido, 0);
        nBee++;
        if (xSemaphoreTake(mtxSerial, pdMS_TO_TICKS(50)) == pdTRUE) {
          Serial.print(F("BEE,")); Serial.println(nBee);
          xSemaphoreGive(mtxSerial);
        }
      } else if (strcmp(buf, "STATS") == 0) {
        imprimirStats();
      } else if (buf[0] >= '1' && buf[0] <= '3' && buf[1] == ',') {
        char classe = (buf[2] == 'H' || buf[2] == 'h') ? 'H' : 'S';
        enfileirarAlerta(buf[0] - '0', classe);
      } else if (xSemaphoreTake(mtxSerial, pdMS_TO_TICKS(50)) == pdTRUE) {
        Serial.print(F("# linha invalida: "));
        Serial.println(buf);
        xSemaphoreGive(mtxSerial);
      }
    }
    vTaskDelay(1);   // polling a cada tick (16 ms no AVR)
  }
}

// Regra de priorizacao por severidade:
//   servidor critico (H) com severidade 1 ou 2 -> rota HARD (imediata)
//   qualquer outro caso                        -> rota SOFT (agregada)
void enfileirarAlerta(uint8_t sev, char classe) {
  // Contadores tambem lidos por outras tarefas: secao critica curta.
  taskENTER_CRITICAL();
  uint16_t id = proximoId++;
  nRecebidos++;
  taskEXIT_CRITICAL();

  Evento e = { EV_ALERTA, sev, classe, id, micros() };
  bool hard = (classe == 'H' && sev <= 2);
  if (xQueueSend(hard ? qHard : qSoft, &e, 0) != pdPASS) {   // fila cheia
    taskENTER_CRITICAL(); nDescartes++; taskEXIT_CRITICAL();
  }
}

void gerarStress(uint16_t n) {
  for (uint16_t i = 0; i < n; i++) {
    // 1 em cada 5 alertas e critico; o resto e ruido soft
    if (i % 5 == 0) enfileirarAlerta(1, 'H');
    else            enfileirarAlerta((i % 2) ? 3 : 2, 'S');
  }
}

// ================================================ Tarefa CRITICA (prio 3)
// Maior prioridade: preempta as demais assim que chega um alerta hard.
void tarefaCritica(void *p) {
  (void)p;
  Evento e;
  for (;;) {
    if (xQueueReceive(qHard, &e, portMAX_DELAY) != pdTRUE) continue;

    if (e.tipo == EV_ACK) {
      sireneAtiva = false;          // antes do noTone: o callback respeita a flag
      xTimerStop(tmSirene, 0);
      noTone(PIN_BUZZER);
      digitalWrite(PIN_LED_HARD, LOW);
      digitalWrite(PIN_LED_MISS, LOW);
      if (xSemaphoreTake(mtxSerial, pdMS_TO_TICKS(50)) == pdTRUE) {
        Serial.println(F("ACK"));
        xSemaphoreGive(mtxSerial);
      }
      continue;
    }

    // 1) Atuacao fisica primeiro: e isso que tem deadline
    digitalWrite(PIN_LED_HARD, HIGH);
    if (!sireneAtiva) {             // 1o tom ja aqui; o timer cuida do resto
      sireneAtiva = true;
      tone(PIN_BUZZER, pgm_read_word(&SIRENE_HZ[0]));
      xTimerStart(tmSirene, 0);
    }
    uint32_t lat = micros() - e.t;

    // 2) Verificacao do deadline
    bool miss = lat > DEADLINE_HARD_US;
    nHard++;
    if (lat > latHardMax) latHardMax = lat;
    if (miss) { nMissHard++; digitalWrite(PIN_LED_MISS, HIGH); }

    // 3) Log, fora do caminho critico
    if (xSemaphoreTake(mtxSerial, pdMS_TO_TICKS(50)) == pdTRUE) {
      Serial.print(F("HARD,")); Serial.print(e.id);
      Serial.print(',');        Serial.print(lat);
      Serial.println(miss ? F(",MISS") : F(",OK"));
      xSemaphoreGive(mtxSerial);
    }
  }
}

// ============================================== Tarefa AGREGADOR (prio 1)
// Debounce/agregacao: junta os alertas soft de uma janela e sinaliza uma
// unica vez. A propria janela limita a taxa de atualizacao do LED.
void tarefaAgregador(void *p) {
  (void)p;
  Evento e;
  for (;;) {
    if (xQueueReceive(qSoft, &e, portMAX_DELAY) != pdTRUE) continue;

    uint32_t t0 = e.t;
    uint16_t qtd = 1;
    uint8_t  sevMax = e.sev;              // 1 e a mais grave
    TickType_t fim = xTaskGetTickCount() + pdMS_TO_TICKS(JANELA_SOFT_MS);

    for (;;) {
      TickType_t agora = xTaskGetTickCount();
      if ((int16_t)(fim - agora) <= 0) break;
      if (xQueueReceive(qSoft, &e, fim - agora) == pdTRUE) {
        qtd++;
        if (e.sev < sevMax) sevMax = e.sev;
      }
    }

    digitalWrite(PIN_LED_SOFT, HIGH);
    ultimoSoft = xTaskGetTickCount();
    uint32_t latMs = (micros() - t0) / 1000UL;
    bool miss = latMs > DEADLINE_SOFT_MS;
    nSoft += qtd;
    if (miss) nMissSoft++;

    if (xSemaphoreTake(mtxSerial, pdMS_TO_TICKS(100)) == pdTRUE) {
      Serial.print(F("SOFT,")); Serial.print(qtd);
      Serial.print(',');        Serial.print(sevMax);
      Serial.print(',');        Serial.print(latMs);
      Serial.println(miss ? F(",MISS") : F(",OK"));
      xSemaphoreGive(mtxSerial);
    }
  }
}

// ============================================ Timer de software (500 ms)
// Roda na tarefa de servico de timers do FreeRTOS: nao pode bloquear.
void timerMonitor(TimerHandle_t t) {
  (void)t;
  static bool led = false, btnAnterior = HIGH;

  led = !led;
  digitalWrite(PIN_LED_OK, led);          // heartbeat: sistema vivo

  bool btn = digitalRead(PIN_BTN_STRESS);
  // O daemon de timers roda com prioridade 3 (igual a CRIT). Gerar a carga
  // aqui competiria com a tarefa critica; por isso so avisamos a RX.
  if (btnAnterior == HIGH && btn == LOW) xTaskNotifyGive(hRx);
  btnAnterior = btn;

  if (digitalRead(PIN_LED_SOFT) &&
      (TickType_t)(xTaskGetTickCount() - ultimoSoft) > pdMS_TO_TICKS(SOFT_APAGA_MS)) {
    digitalWrite(PIN_LED_SOFT, LOW);
  }
}

void imprimirStats() {
  if (xSemaphoreTake(mtxSerial, pdMS_TO_TICKS(100)) != pdTRUE) return;
  Serial.print(F("# STATS recebidos=")); Serial.print(nRecebidos);
  Serial.print(F(" hard="));             Serial.print(nHard);
  Serial.print(F(" soft="));             Serial.print(nSoft);
  Serial.print(F(" missHard="));         Serial.print(nMissHard);
  Serial.print(F(" missSoft="));         Serial.print(nMissSoft);
  Serial.print(F(" descartes="));        Serial.print(nDescartes);
  Serial.print(F(" latHardMax_us="));    Serial.print(latHardMax);
  Serial.print(F(" bee="));              Serial.println(nBee);
  Serial.print(F("# PILHA livre (bytes) CRIT="));
  Serial.print(uxTaskGetStackHighWaterMark(hCrit));
  Serial.print(F(" RX="));  Serial.print(uxTaskGetStackHighWaterMark(hRx));
  Serial.print(F(" AGG=")); Serial.println(uxTaskGetStackHighWaterMark(hAgg));
  xSemaphoreGive(mtxSerial);
}

// ================================== Timer one-shot do BeeIA (200 ms)
void timerApagaBee(TimerHandle_t t) {
  (void)t;
  digitalWrite(PIN_LED_BEE, LOW);
}

// ======================== Timer periodico da sirene (90 ms por fase)
// Roda no daemon de timers: so troca a frequencia, nunca bloqueia.
void timerSirene(TimerHandle_t t) {
  (void)t;
  static uint8_t fase = 0;
  if (!sireneAtiva) { noTone(PIN_BUZZER); fase = 0; return; }
  fase = (fase + 1) % N_FASES_SIRENE;
  uint16_t hz = pgm_read_word(&SIRENE_HZ[fase]);
  if (hz) tone(PIN_BUZZER, hz);
  else    noTone(PIN_BUZZER);
}

// ===================== Timer periodico do zumbido do BeeIA (~30 ms/fase)
// Roda no daemon de timers (como a sirene, entao os dois nunca executam ao
// mesmo tempo). Se a sirene assumiu o buzzer, sai sem tocar nele.
void timerZumbido(TimerHandle_t t) {
  if (sireneAtiva || faseZumbido == 0) {   // sirene manda no buzzer
    faseZumbido = 0;
    xTimerStop(t, 0);
    return;
  }
  if (faseZumbido >= N_FASES_ZUMBIDO) {    // fim do "bzzz"
    noTone(PIN_BUZZER);
    faseZumbido = 0;
    xTimerStop(t, 0);
    return;
  }
  tone(PIN_BUZZER, pgm_read_word(&ZUMBIDO_HZ[faseZumbido++]));
}
