#!/usr/bin/env bash
# Roteiro de ataques do laboratorio. Cada cenario dispara regras conhecidas do
# suricata/local.rules, entao o resultado no Arduino e previsivel:
#
#   hard   path traversal (sev 1) no servidor critico     -> HARD: vermelho + sirene
#   sqli   SQL injection  (sev 2) no servidor critico     -> HARD
#   admin  acesso a /admin (sev 3) no servidor critico    -> SOFT (sev 3 nunca e hard)
#   soft   path traversal (sev 1) no servidor comum       -> SOFT: amarelo
#   ping   3 pings em cada servidor (sev 3)               -> SOFT agregado
#   scan   varredura de portas no servidor critico (sev 2)-> HARD
#   rajada mistura de tudo acima, para ver a agregacao e a preempcao
set -u
HARD=10.77.77.10
SOFT=10.77.77.20

req() { curl -s --path-as-is -o /dev/null -w "  HTTP %{http_code}  $1\n" --max-time 3 "$1"; }

case "${1:-ajuda}" in
  hard)  req "http://$HARD/../../etc/passwd" ;;
  sqli)  req "http://$HARD/produtos?id=1%20UNION%20SELECT%20senha%20FROM%20usuarios" ;;
  admin) req "http://$HARD/admin" ;;
  soft)  req "http://$SOFT/../../etc/passwd" ;;
  ping)  ping -c 3 -i 0.3 "$HARD"; ping -c 3 -i 0.3 "$SOFT" ;;
  scan)  nmap -sT -T4 --top-ports 100 "$HARD" | tail -3 ;;
  rajada)
    for i in 1 2 3; do req "http://$SOFT/admin"; req "http://$SOFT/../../etc/passwd"; done
    req "http://$HARD/../../etc/passwd"
    ping -c 3 -i 0.2 "$SOFT"
    ;;
  *) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//' ;;
esac
