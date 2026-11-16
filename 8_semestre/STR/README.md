# Laboratório — Sinalização física do IPS com Arduino + FreeRTOS

Sistemas de Tempo Real · IESB · Caio Silveira Guimarães Souza

```
lab/
├── ips_sinalizacao/ips_sinalizacao.ino   ← abrir na IDE do Arduino (etapa 3)
├── wokwi/sketch.ino, diagram.json, libraries.txt   ← colar no wokwi.com (etapa 1)
├── wokwi/wokwi.toml                      ← Wokwi no VS Code + ponte ligada à simulação (etapa 4)
├── passo-passo.md                        ← roteiro de execução e apresentação no notebook
├── lab-suricata/                         ← laboratório em containers: srv-hard, srv-soft, atacante, Suricata
└── ponte_pc/ponte_serial.py              ← PC → Arduino (demo, stress, Suricata, BeeIA/TCC)
```

O sketch das duas pastas é o mesmo. Ele já foi compilado para o ATmega328P
(16,7 KB de flash, 471 B de RAM estática) e executado num emulador AVR com o
roteiro de testes do item 3.4 — todos os alertas críticos ficaram dentro do deadline.

---

## Etapa 1 — Modelo lógico e funcional no Wokwi

1. Acesse https://wokwi.com → **New Project** → **Arduino Uno**.
2. Na aba `sketch.ino`, apague tudo e cole o conteúdo de `wokwi/sketch.ino`.
3. Na aba `diagram.json`, apague tudo e cole o conteúdo de `wokwi/diagram.json`.
   O circuito (5 LEDs, 5 resistores, buzzer e 2 botões) aparece montado.
4. Clique na seta ao lado das abas → **New file…** → `libraries.txt`, e cole o
   conteúdo de `wokwi/libraries.txt` (uma linha: `FreeRTOS`).
   Alternativa: aba **Library Manager** → `+` → procurar *FreeRTOS* (autor Phillip Stevens).
5. Clique em **▶ Start**. O LED verde deve piscar a cada ~0,5 s (heartbeat).
6. No monitor serial, digite e envie uma linha por vez:

| Envie | O que deve acontecer |
|---|---|
| `1,H,10.0.0.66` | Vermelho acende + sirene de dois tons que só para no ACK. Serial: `HARD,1,<µs>,OK` |
| `3,S,10.0.0.70` (e mais 2 ou 3 linhas S logo em seguida) | ~1 s depois o amarelo acende **uma vez só**. Serial: `SOFT,<qtd>,<sev>,~992,OK` |
| Botão vermelho (ACK) ou `ACK` | Sirene para; vermelho e azul apagam |
| `STRESS,50` ou botão preto | 10 linhas `HARD` seguidas, todas `OK`; depois um `SOFT,10,...` |
| `BEE` | LED branco pisca ~200 ms e zumbido de abelha (mudo se a sirene estiver tocando). Serial: `BEE,<contador>` |
| `STATS` | Contadores, latência máxima, `bee=` e pilha livre de cada tarefa |

O amarelo apaga sozinho após 5 s sem alertas soft. O azul só acende se algum alerta
crítico estourar o deadline de 50 ms.

> Salve o projeto no Wokwi (precisa de login) e guarde o link: ele serve de evidência
> para o relatório e para mostrar ao professor antes da bancada.

---

## Etapa 2 — Lista de materiais

| Qtde | Item | Observação |
|---|---|---|
| 1 | Arduino Uno R3 + cabo USB A-B | |
| 1 | Protoboard (400 ou 830 pontos) | |
| 5 | LED 5 mm: verde, amarelo, vermelho, azul, branco | azul e branco podem ser de qualquer outra cor |
| 5 | Resistor 220 Ω (220–330 Ω serve) | um em série com cada LED |
| 2 | Push button 4 terminais | |
| 1 | Buzzer 5 V (ativo ou passivo) | opcional — sem ele o código funciona igual |
| ~16 | Jumpers macho-macho | |
| 1 | PC com Arduino IDE | a biblioteca **FreeRTOS** precisa estar instalada (ver 3.1) |

Os botões **não** precisam do resistor de 10 kΩ da Aula 03: o código usa
`INPUT_PULLUP` (resistor interno), então o pino lê HIGH solto e LOW pressionado.

Leve num pendrive: esta pasta inteira e o ZIP da biblioteca
(https://github.com/feilipu/Arduino_FreeRTOS_Library → Code → Download ZIP),
caso o PC da faculdade não deixe usar o Gerenciador de Bibliotecas.

---

## Etapa 3 — Montagem na protoboard e execução no PC da faculdade

### 3.1 Preparar a IDE
1. Abra a Arduino IDE → **Ferramentas › Gerenciar Bibliotecas** → busque `FreeRTOS`
   (autor *Phillip Stevens*) → **Instalar**.
   Sem internet: **Sketch › Incluir Biblioteca › Adicionar biblioteca .ZIP** e escolha o ZIP do pendrive.
2. **Arquivo › Abrir** → `ips_sinalizacao/ips_sinalizacao.ino`
   (a pasta precisa ter o mesmo nome do arquivo `.ino`).
3. **Ferramentas › Placa** → *Arduino Uno*; **Porta** → a COM/ttyACM que aparecer ao plugar.
4. Clique em **✓ Verificar**. Deve compilar sem erros.

### 3.2 Montar o circuito (com o Arduino **desligado** do USB)

```
Trilho –  da protoboard  ←  GND do Arduino

D7  ── 220 Ω ── (perna longa) LED branco  (perna curta) ── trilho –
D8  ── 220 Ω ── (perna longa) LED verde   (perna curta) ── trilho –
D9  ── 220 Ω ── (perna longa) LED amarelo (perna curta) ── trilho –
D10 ── 220 Ω ── (perna longa) LED vermelho(perna curta) ── trilho –
D11 ── 220 Ω ── (perna longa) LED azul    (perna curta) ── trilho –
D12 ── (+) buzzer (–) ── trilho –

Botão ACK    (atravessando a canaleta central):  um terminal → D2,  terminal diagonal → trilho –
Botão STRESS (atravessando a canaleta central):  um terminal → D3,  terminal diagonal → trilho –
```

Confira antes de ligar: perna longa do LED = ânodo (+), voltada para o resistor.

### 3.3 Gravar e testar
1. Plugue o USB → **→ Carregar**.
2. **Ferramentas › Monitor Serial** → **115200 baud** e final de linha **Nova linha (LF)**.
3. Deve aparecer `# IPS-LED pronto...` e o verde deve piscar.
4. Repita a tabela da Etapa 1 e **anote/copie a saída do monitor** — esses números
   (latência `HARD` em µs, `SOFT` em ms, `STATS`) entram na seção de resultados do artigo.

### 3.4 Roteiro de medição para o artigo (bancada)
1. Cinco alertas `1,H,...` espaçados → anotar as cinco latências `HARD`.
2. Três a cinco alertas `S` em sequência → anotar `SOFT,<qtd>,...,<ms>`.
3. `STRESS,50` → anotar `STATS` (hard atendidos, descartes, `latHardMax_us`).
4. Opcional, com Python no PC: `pip install pyserial` e
   `python ponte_pc/ponte_serial.py --porta COM3 --demo` (gera `latencias.csv`
   com a latência ponta a ponta medida no PC).

### Se algo der errado
| Sintoma | Causa provável |
|---|---|
| `Arduino_FreeRTOS.h: No such file` | biblioteca não instalada (3.1) |
| LED da placa (pino 13) piscando sem parar e nada no serial | falta de RAM ao criar tarefas/filas — não aumente pilhas ou filas sem conferir com `STATS` |
| Caracteres estranhos no monitor | baud diferente de 115200 |
| Comando não responde | final de linha deve ser LF (ou CR); uma linha por envio |
| Botão não faz nada | botão não está atravessando a canaleta; use terminais em diagonal |

---

## Etapa 4 — Integração com o BeeIA (API do TCC na EC2)

O Uno não tem rede, e mesmo com shield Ethernet/ESP-01 ele não fecha TLS. O nginx da
EC2 só aceita **TLS 1.3** (porta 64298), e o backend (8000) não é exposto. Por isso a
integração usa o PC como gateway: a ponte assina o WebSocket `/ws` do BeeIA e manda os
comandos pela serial. Nada muda no firmware.

Cada fonte tem os seus LEDs:

| Fonte | Evento | Linha enviada | LED |
|---|---|---|---|
| BeeIA (EC2) | todo `new_attack`, de qualquer tipo | `BEE` | branco pisca ~200 ms + zumbido de abelha |
| Suricata (local) | `alert` com destino em `--criticos` e severidade 1–2 | `<sev>,H,<ip>` | vermelho + buzzer (HARD, 50 ms) |
| Suricata (local) | qualquer outro `alert` | `<sev>,S,<ip>` | amarelo agregado (SOFT) |

As duas fontes rodam juntas na mesma ponte (uma porta serial só aceita um programa):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pyserial "websockets>=12"
read -s -p "Chave BeeIA: " BEEIA_API_KEY && export BEEIA_API_KEY
sudo -E .venv/bin/python ponte_pc/ponte_serial.py --porta /dev/ttyACM0 \
     --eve lab-suricata/logs/eve.json --criticos 10.77.77.10 \
     --beeia wss://honeypot.mirondev.com:64298/ws
```

`sudo` é só para ler o `eve.json`, que pertence ao root; o `-E` repassa a chave.
Se o BeeIA cair ou a chave for recusada, a ponte avisa e o Suricata continua.
Sem `--eve`, roda só o BeeIA; sem `--beeia`, só o Suricata.

Pré-requisitos:
- O security group da porta 64298 precisa liberar o IP público de onde a ponte roda
  (o da faculdade é diferente do seu). Libere temporariamente e feche depois da apresentação.
- Porta serial no Ubuntu: `sudo usermod -aG dialout $USER` (sair e entrar na sessão) e,
  para Arduino clone (CH340), `sudo apt remove brltty`.
- O laboratório do Suricata (servidores, atacante e roteiro de ataques) está em
  [lab-suricata/README.md](lab-suricata/README.md).
- A chave vai no header `X-API-Key` (lida de `BEEIA_API_KEY`), nunca na URL nem no código.

### Testar com a simulação (sem placa), no VS Code
1. Instale a extensão **Wokwi Simulator** e ative a licença gratuita.
2. Compile: `arduino-cli lib install FreeRTOS` e
   `arduino-cli compile -b arduino:avr:uno --output-dir ips_sinalizacao/build ips_sinalizacao`.
3. Abra `wokwi/diagram.json` → **Wokwi: Start Simulator**. O `wokwi.toml` expõe a serial em `localhost:4000`.
4. `python ponte_pc/ponte_serial.py --porta rfc2217://localhost:4000 --beeia wss://honeypot.mirondev.com:64298/ws`
   (ou `--demo` no lugar de `--beeia` para gerar `latencias.csv` com a simulação).
