FROM debian:bullseye-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    asterisk \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p \
    /var/lib/asterisk/sounds/en \
    /var/lib/asterisk/moh \
    /var/lib/asterisk/keys \
    /var/lib/asterisk/documentation \
    /var/spool/asterisk/voicemail \
    /var/spool/asterisk/monitor \
    /var/spool/asterisk/tmp \
    /var/run/asterisk \
    /var/log/asterisk && \
    touch /var/lib/asterisk/astdb.sqlite3 && \
    sqlite3 /var/lib/asterisk/astdb.sqlite3 \
        "CREATE TABLE IF NOT EXISTS astdb (key VARCHAR(256) NOT NULL UNIQUE, value VARCHAR(256) NOT NULL);" && \
    chmod 777 /var/lib/asterisk/astdb.sqlite3 && \
    chown -R asterisk:asterisk \
        /var/lib/asterisk \
        /var/spool/asterisk \
        /var/run/asterisk \
        /var/log/asterisk \
        /etc/asterisk

COPY ari.conf /etc/asterisk/ari.conf
COPY extensions.conf /etc/asterisk/extensions.conf
COPY http.conf /etc/asterisk/http.conf
COPY asterisk.conf /etc/asterisk/asterisk.conf
COPY pjsip.conf /etc/asterisk/pjsip.conf

EXPOSE 5060/udp 5061/tcp 8088/tcp

CMD ["asterisk", "-f", "-vvv"]
