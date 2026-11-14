# Laboratório do IPS com Suricata em containers

```
rede Docker "labnet" 10.77.77.0/24 (interface br-lab no host)
├── srv-hard   10.77.77.10   servidor crítico  → alertas sev 1–2 viram HARD
├── srv-soft   10.77.77.20   servidor comum    → todos os alertas viram SOFT
├── atacante   10.77.77.66   roda os ataques sob demanda
└── suricata   rede do host, escuta a br-lab → logs/eve.json → ponte_pc → Arduino
```

Requisito: Ubuntu com **Docker Engine** (`docker.io` ou `docker-ce`).
O Docker Desktop roda numa VM, e o Suricata não enxergaria a `br-lab`.

## 1. Subir o laboratório (pasta `lab-suricata`)

```bash
docker compose up -d --build
docker compose --profile ataque build      # imagem do atacante
docker logs -f suricata                    # esperar "Engine started", depois Ctrl+C
```

## 2. Testar o Suricata sem o Arduino

Num terminal, acompanhe os alertas:
```bash
sudo tail -f logs/eve.json | grep --line-buffered '"alert"'
```
Em outro:
```bash
docker compose run --rm atacante hard
```
Deve aparecer um alerta `LAB path traversal /etc/passwd` com `dest_ip` 10.77.77.10.

## 3. Ligar a ponte (Suricata + BeeIA) ao Arduino

Na pasta `STR`, com o Monitor Serial da IDE **fechado**:
```bash
source .venv/bin/activate
read -s -p "Chave BeeIA: " BEEIA_API_KEY && export BEEIA_API_KEY
sudo -E .venv/bin/python ponte_pc/ponte_serial.py --porta /dev/ttyACM0 \
     --eve lab-suricata/logs/eve.json --criticos 10.77.77.10 \
     --beeia wss://honeypot.mirondev.com:64298/ws
```
Sem a parte do BeeIA, basta tirar a linha `--beeia`. O `sudo` é necessário porque o
`eve.json` é criado pelo root dentro do container.

## 4. Roteiro de demonstração (pasta `lab-suricata`)

| Comando | Regra (severidade) | Linha na ponte | No Arduino |
|---|---|---|---|
| `docker compose run --rm atacante hard` | path traversal (1) no srv-hard | `1,H,10.77.77.66` | vermelho + sirene até o ACK |
| `docker compose run --rm atacante sqli` | SQL injection (2) no srv-hard | `2,H,...` | vermelho + sirene |
| `docker compose run --rm atacante scan` | varredura de portas (2) no srv-hard | `2,H,...` | vermelho + sirene |
| `docker compose run --rm atacante admin` | acesso a /admin (3) no srv-hard | `3,H,...` | amarelo: sev 3 nunca é hard |
| `docker compose run --rm atacante soft` | path traversal (1) no srv-soft | `1,S,...` | amarelo |
| `docker compose run --rm atacante ping` | ping (3) nos dois | 6 linhas `3,…` | amarelo, uma vez só (agregado) |
| `docker compose run --rm atacante rajada` | mistura | várias | amarelo agregado e vermelho no meio |

Pontos para o relatório:
- **Admin versus hard:** o mesmo servidor crítico gera HARD ou SOFT conforme a severidade.
- **Soft versus hard:** o mesmo ataque gera HARD no servidor crítico e SOFT no comum.
- **Rajada:** os vários soft viram um único `SOFT,<qtd>,...`, e o alerta hard no meio
  preempta e é atendido dentro dos 50 ms.

## 5. Desligar

```bash
docker compose down          # para e remove os containers e a rede
sudo rm -f logs/*.json logs/*.log   # opcional: limpa os logs
```

## Se algo der errado

| Sintoma | Causa provável |
|---|---|
| `docker logs suricata` mostra erro em `br-lab` | a rede ainda não estava ativa; `docker compose restart suricata` |
| Ataque roda, mas nenhum alerta no `eve.json` | `ip link show br-lab` precisa existir no host; confira se não é Docker Desktop |
| `Pool overlaps with other one` | a sub-rede 10.77.77.0/24 já está em uso; troque nos dois lugares do compose, no `HOME_NET` do `suricata/Dockerfile`, no `ataque.sh` e no `--criticos` |
| Ponte fica em "aguardando eve.json" | o Suricata não subiu; veja `docker logs suricata` |
| Alerta aparece no `eve.json`, mas o Arduino não reage | Monitor Serial aberto ou porta errada (veja o README principal) |
