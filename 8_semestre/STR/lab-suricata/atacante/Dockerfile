# Maquina atacante do laboratorio: curl + nmap + ping e o roteiro de ataques.
FROM alpine:3.20
RUN apk add --no-cache bash curl nmap iputils
COPY ataque.sh /usr/local/bin/ataque
RUN chmod +x /usr/local/bin/ataque
ENTRYPOINT ["ataque"]
CMD ["ajuda"]
