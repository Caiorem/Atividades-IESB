# Servidor web minimo do laboratorio (usado pelo srv-hard e pelo srv-soft).
# Responde HTTP na porta 80 e a ping; a pagina mostra o nome do servidor.
FROM python:3.12-alpine
WORKDIR /srv
ENV NOME="SERVIDOR"
EXPOSE 80
CMD ["sh", "-c", "printf '<h1>%s</h1><p>%s</p>\\n' \"$NOME\" \"$(hostname -i)\" > index.html && exec python -m http.server 80"]
