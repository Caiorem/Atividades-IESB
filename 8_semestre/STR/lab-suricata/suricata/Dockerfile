# Suricata do laboratorio (pacote do Ubuntu 24.04, versao 7.x).
# So as regras locais (local.rules) sao carregadas, para o resultado de cada
# ataque ser previsivel. Para usar tambem as regras ET Open, rode
# "suricata-update" e troque -S por -s no CMD.
FROM ubuntu:24.04
RUN apt-get update \
 && apt-get install -y --no-install-recommends suricata \
 && rm -rf /var/lib/apt/lists/*
COPY local.rules /etc/suricata/rules/local.rules

# -i br-lab  : interface da bridge do laboratorio (nome fixado no compose)
# -k none    : ignora checksum; em veth/bridge o offload deixa checksums
#              "invalidos" e o Suricata descartaria os fluxos TCP
# HOME_NET   : a sub-rede do laboratorio
CMD ["suricata", "-i", "br-lab", "-k", "none", \
     "-S", "/etc/suricata/rules/local.rules", \
     "-l", "/var/log/suricata", \
     "--set", "vars.address-groups.HOME_NET=[10.77.77.0/24]", \
     "--set", "vars.address-groups.EXTERNAL_NET=any"]
