#!/usr/bin/env python3
"""
Ponte PC -> Arduino para o projeto IPS (Sistemas de Tempo Real - IESB).

Le alertas e envia ao Arduino no formato  <sev>,<classe>,<origem>\\n
respeitando um intervalo minimo entre linhas (taxa limite), porque o
buffer de recepcao do Uno tem so 64 bytes e a tarefa RX le a serial a
cada tick de 16 ms. Em teste, rajadas sem espacamento perderam ~50% das
linhas; com 10 ms entre linhas, nenhuma foi perdida.

Modos:
  python ponte_serial.py --porta COM3 --demo
      envia um roteiro de teste e mede a latencia ponta a ponta
  python ponte_serial.py --porta /dev/ttyACM0 --eve /var/log/suricata/eve.json \\
         --criticos 10.0.0.10,10.0.0.11
      acompanha o eve.json do Suricata (como "tail -f") e encaminha os alertas
  python ponte_serial.py --porta COM3 --stress 200
      envia 200 alertas sinteticos espacados pela taxa limite
  python ponte_serial.py --porta COM3 --beeia wss://honeypot.mirondev.com:64298/ws
      assina o WebSocket do BeeIA (TCC): cada alerta novo pisca o LED branco
      (a chave vem da variavel de ambiente BEEIA_API_KEY, nunca da linha de comando)
  --eve e --beeia podem ser usados juntos: Suricata nos LEDs do laboratorio
  (HARD/SOFT) e BeeIA no LED branco, compartilhando a mesma porta serial.

A porta tambem aceita URL do pyserial, por exemplo rfc2217://localhost:4000
para falar com a simulacao do Wokwi no VS Code (ver wokwi/wokwi.toml).

Dependencias: pip install pyserial            (todos os modos)
              pip install "websockets>=12"    (so o modo --beeia)
"""
import argparse
import csv
import json
import os
import ssl
import sys
import threading
import time

import serial  # pyserial

INTERVALO_MIN_S = 0.010   # 10 ms entre linhas: taxa limite na origem


class Ponte:
    def __init__(self, porta, baud=115200, arquivo_csv="latencias.csv"):
        # serial_for_url aceita "COM3", "/dev/ttyACM0" ou "rfc2217://host:porta"
        self.ser = serial.serial_for_url(porta, baud, timeout=0.1)
        time.sleep(2.0)              # o Uno reinicia ao abrir a porta
        self.ser.reset_input_buffer()
        self.ultimo_envio = 0.0
        self.pendentes = []          # instantes de envio de alertas HARD
        self.trava = threading.Lock()
        self.trava_tx = threading.Lock()   # --eve e --beeia escrevem de threads diferentes
        self.csv = open(arquivo_csv, "w", newline="")
        self.out = csv.writer(self.csv)
        self.out.writerow(["tipo", "id", "lat_interna_us", "lat_ponta_a_ponta_ms", "deadline"])
        threading.Thread(target=self._leitor, daemon=True).start()

    def _escrever(self, linha):
        # Toda escrita passa pela taxa limite (inclusive comandos como BEE).
        # A trava impede que duas threads intercalem bytes na mesma linha.
        with self.trava_tx:
            espera = INTERVALO_MIN_S - (time.perf_counter() - self.ultimo_envio)
            if espera > 0:
                time.sleep(espera)
            self.ser.write(linha.encode())
            self.ultimo_envio = time.perf_counter()

    def enviar(self, sev, classe, origem):
        # O buffer do sketch tem 32 bytes: corta a origem para a linha caber.
        linha = f"{sev},{classe},{str(origem)[:24]}\n"
        with self.trava:
            if classe == "H" and int(sev) <= 2:
                self.pendentes.append(time.perf_counter())
        self._escrever(linha)

    def comando(self, txt):
        self._escrever(txt + "\n")

    def _leitor(self):
        while True:
            bruto = self.ser.readline()
            if not bruto:
                continue
            agora = time.perf_counter()
            linha = bruto.decode(errors="replace").strip()
            print("<-", linha)
            if linha.startswith("HARD,"):
                _, ident, lat_us, status = linha.split(",")
                with self.trava:
                    t_envio = self.pendentes.pop(0) if self.pendentes else None
                e2e = (agora - t_envio) * 1000 if t_envio else ""
                self.out.writerow(["HARD", ident, lat_us, f"{e2e:.1f}" if e2e != "" else "", status])
                self.csv.flush()
            elif linha.startswith("SOFT,"):
                _, qtd, sev, lat_ms, status = linha.split(",")
                self.out.writerow(["SOFT", qtd, "", lat_ms, status])
                self.csv.flush()


def modo_demo(p):
    roteiro = [("1", "H", "10.0.0.66"), ("3", "S", "10.0.0.70"),
               ("2", "S", "10.0.0.71"), ("3", "S", "10.0.0.70"),
               ("2", "H", "10.0.0.80")]
    for sev, classe, origem in roteiro:
        print(f"-> {sev},{classe},{origem}")
        p.enviar(sev, classe, origem)
        time.sleep(0.3)
    time.sleep(2)
    p.comando("STATS")
    time.sleep(1)


def modo_stress(p, n):
    for i in range(n):
        if i % 5 == 0:
            p.enviar(1, "H", "stress")
        else:
            p.enviar(3 if i % 2 else 2, "S", "stress")
    time.sleep(2)
    p.comando("STATS")
    time.sleep(1)


def modo_eve(p, caminho, criticos):
    """Acompanha o eve.json do Suricata e encaminha apenas eventos 'alert'."""
    with open(caminho) as f:
        f.seek(0, os.SEEK_END)
        while True:
            linha = f.readline()
            if not linha:
                time.sleep(0.005)
                continue
            try:
                ev = json.loads(linha)
            except json.JSONDecodeError:
                continue
            if ev.get("event_type") != "alert":
                continue
            sev = ev.get("alert", {}).get("severity", 3)
            destino = ev.get("dest_ip", "")
            classe = "H" if destino in criticos else "S"
            p.enviar(sev, classe, ev.get("src_ip", "?"))


# ------------------------------------------------------------ BeeIA (TCC)
# O BeeIA so usa o LED branco: todo alerta novo (new_attack) vira "BEE",
# independente do tipo ou da confianca. Os LEDs HARD/SOFT ficam reservados
# para o laboratorio do Suricata (--eve). Os demais eventos do WebSocket
# (stats, ip_blocked) nao vao para o Arduino.
def traduzir_evento(msg):
    """Recebe o dict do WebSocket e devolve a lista de comandos para o Arduino."""
    return ["BEE"] if msg.get("type") == "new_attack" else []


def modo_beeia(p, url):
    try:
        from websockets.sync.client import connect
        from websockets.exceptions import ConnectionClosed, InvalidStatus, WebSocketException
    except ImportError:
        print('# BeeIA desativado: pip install "websockets>=12"')
        return False

    chave = os.getenv("BEEIA_API_KEY", "")
    if not chave:
        print("# aviso: BEEIA_API_KEY vazia - so funciona se a API estiver sem autenticacao")
    cabecalhos = {"X-API-Key": chave} if chave else {}
    contexto = ssl.create_default_context() if url.startswith("wss://") else None

    espera = 1
    while True:
        try:
            print(f"# conectando em {url} ...")
            with connect(url, additional_headers=cabecalhos, ssl=contexto,
                         open_timeout=10, ping_interval=20) as ws:
                print("# conectado ao BeeIA")
                espera = 1
                for bruto in ws:
                    try:
                        msg = json.loads(bruto)
                    except json.JSONDecodeError:
                        continue
                    if msg.get("type") == "stats":
                        d = msg.get("data", {})
                        print(f"# stats BeeIA: total={d.get('total_attacks')} "
                              f"24h={d.get('attacks_last_24h')} bloqueados={d.get('blocked_count')}")
                    for cmd in traduzir_evento(msg):
                        d = msg.get("data") or {}
                        print(f"-> {cmd}  (BeeIA: {d.get('attack_type', '?')} de {d.get('src_ip', '?')})")
                        p.comando(cmd)
        except KeyboardInterrupt:
            return True
        except InvalidStatus as e:
            # 401/403 nao se resolvem sozinhos: chave errada ou IP fora do security group
            print(f"# BeeIA desativado - servidor recusou o WebSocket: {e}")
            return False
        except ConnectionClosed as e:
            if e.rcvd is not None and e.rcvd.code == 1008:   # policy violation = chave
                print("# BeeIA desativado - servidor fechou com 1008: BEEIA_API_KEY ausente ou invalida")
                return False
            print(f"# conexao perdida ({e}); nova tentativa em {espera} s")
        except (OSError, WebSocketException) as e:
            print(f"# conexao perdida ({e}); nova tentativa em {espera} s")
        time.sleep(espera)
        espera = min(espera * 2, 30)   # backoff exponencial, teto de 30 s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--porta", required=True, help="ex.: COM3 ou /dev/ttyACM0")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--stress", type=int, default=0)
    ap.add_argument("--eve", help="caminho do eve.json do Suricata")
    ap.add_argument("--criticos", default="", help="IPs dos servidores criticos (hard)")
    ap.add_argument("--beeia", metavar="URL",
                    help="WebSocket do BeeIA, ex.: wss://honeypot.mirondev.com:64298/ws")
    a = ap.parse_args()

    ponte = Ponte(a.porta)
    if a.demo:
        modo_demo(ponte)
    elif a.stress:
        modo_stress(ponte, a.stress)
    elif a.eve or a.beeia:
        if a.eve and a.beeia:
            # BeeIA numa thread daemon; se ela parar (chave errada), o Suricata segue.
            threading.Thread(target=modo_beeia, args=(ponte, a.beeia), daemon=True).start()
        elif a.beeia:
            sys.exit(0 if modo_beeia(ponte, a.beeia) else 1)
        try:
            modo_eve(ponte, a.eve, set(filter(None, a.criticos.split(","))))
        except KeyboardInterrupt:
            pass
    else:
        ap.print_help()
