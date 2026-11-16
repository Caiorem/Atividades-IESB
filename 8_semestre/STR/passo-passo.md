# Passo a passo de execução — IPS com Arduino + FreeRTOS

```bash
STR=~/Documents/Faculdade/Atividades-IESB/8_semestre/STR
```

---

## 1. Preparação (uma vez só)

Na pasta `STR`:

```bash
cd $STR
python3 -m venv .venv
source .venv/bin/activate
pip install pyserial "websockets>=12"
```

## 2. Teste de conexão com a API do BeeIA

```bash
telnet honeypot.mirondev.com 64298        # conectou = porta liberada na AWS (Ctrl+] e "quit" para sair)
read -s -p "Chave BeeIA: " BEEIA_API_KEY && export BEEIA_API_KEY   # cola a chave, nada aparece, Enter
curl -H "X-API-Key: $BEEIA_API_KEY" https://honeypot.mirondev.com:64298/api/stats
```

✅ Volta um JSON. Timeout = IP não liberado no security group; `401` = chave errada.

## 3. Subir o laboratório do Suricata

```bash
cd $STR/lab-suricata
docker compose up -d --build
docker compose --profile ataque build
docker logs -f suricata        # espere "Engine started", depois Ctrl+C
```

### Teste sem Arduino

```bash
# Terminal A
sudo tail -f logs/eve.json | grep --line-buffered '"alert"'

# Terminal B
docker compose run --rm atacante hard
```

✅ Aparece no Terminal A um alerta `LAB path traversal /etc/passwd`.

---

# Apresentação

### Terminal 1: conferir o laboratório

```bash
cd $STR/lab-suricata
docker compose ps        # srv-hard, srv-soft e suricata precisam estar "Up"
                         # se não estiverem: docker compose up -d
```

### Terminal 2: Arduino IDE

```bash
cd ~/Documents/Faculdade/arduino_ide
./arduino-ide --no-sandbox
```

1. Abrir `STR/ips_sinalizacao/ips_sinalizacao.ino`.
2. **Placa:** Arduino Uno. **Porta:** `/dev/ttyACM0` (ou `/dev/ttyUSB0` se for clone).
3. **Verificar → Carregar**.
4. Monitor Serial (**115200**, **Nova linha**): aparece `# IPS-LED pronto`. Testar `BEE`, `1,H,teste` e o botão ACK.
5. ⚠️ **Fechar o Monitor Serial** antes do Terminal 3. Senão a ponte não abre a porta.

### Terminal 3: ponte (Suricata + BeeIA → Arduino)

```bash
cd $STR
source .venv/bin/activate
read -s -p "Chave BeeIA: " BEEIA_API_KEY && export BEEIA_API_KEY   # se for terminal novo
sudo -E .venv/bin/python ponte_pc/ponte_serial.py --porta /dev/ttyACM0 \
     --eve lab-suricata/logs/eve.json --criticos 10.77.77.10 \
     --beeia wss://honeypot.mirondev.com:64298/ws
```

✅ Aparecem `# conectado ao BeeIA` e `# Suricata: lendo ...`.

### Terminal 4: ataques no laboratório do Suricata

```bash
cd $STR/lab-suricata
```

| Comando | ✅ No Arduino |
|---|---|
| `docker compose run --rm atacante hard` | vermelho + sirene (aperte ACK) |
| `docker compose run --rm atacante soft` | amarelo |
| `docker compose run --rm atacante admin` | amarelo (gravidade 3 no servidor crítico) |
| `docker compose run --rm atacante scan` | vermelho + sirene |
| `docker compose run --rm atacante rajada` | amarelo agregado e vermelho no meio |
| (esperar ataques reais na EC2) | branco pisca a cada alerta do BeeIA |

### Terminal 5: ataque ao honeypot do BeeIA

> ⚠️ **Fazer pelo 4G do celular, NÃO pela rede do notebook.**
> Se o BeeIA bloquear o IP atacante, ele corta todo o acesso desse IP à EC2, e a
> ponte cai junto. Se acontecer, desbloqueie o IP pelo dashboard.

```bash
ssh root@honeypot.mirondev.com
```

Digite qualquer coisa (`ls`, `whoami`) e saia. O branco pisca quando a sessão fecha.

---

## Fim

```bash
# Ctrl+C na ponte (Terminal 3)
cd $STR/lab-suricata && docker compose down
```
