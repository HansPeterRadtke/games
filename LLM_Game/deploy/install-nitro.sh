#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) -eq 0 ]] || { echo 'install_llm_game.sh must run as root' >&2; exit 1; }
[[ $(hostname -s) == nitro ]] || { echo 'install_llm_game.sh is Nitro-only' >&2; exit 1; }

DATA=${INFRA_DATA_ROOT:-/data}
APP=$DATA/src/github/games/LLM_Game
PY=$DATA/venv/bin/python3
WS_PORT=${LLM_GAME_WS_PORT:-15301}
HTTP_PORT=${LLM_GAME_HTTP_PORT:-15302}
TS=$(date +%Y%m%dT%H%M%S)
BACKUP=$DATA/var/backups/llm-game-install-$TS
REPORT=$DATA/var/llm_game/deploy/install-$TS.txt
mkdir -p "$BACKUP" "$(dirname "$REPORT")"
install -d -o hans -g hans -m 0750 "$DATA/var/llm_game/cache" "$DATA/var/llm_game/cache/huggingface" "$DATA/var/llm_game/cache/transformers" "$DATA/var/llm_game/stt" "$DATA/var/llm_game/topic_gifs"

old_pid=$(cat "$DATA/var/llm_game/stt/pid" 2>/dev/null || true)
old_service_exists=0; old_service_active=0; old_service_enabled=0
old_new_conf=0; old_legacy_proxy=0; old_legacy_cache=0
[[ -e /etc/systemd/system/llm-game-stt.service ]] && old_service_exists=1
systemctl is-active --quiet llm-game-stt.service 2>/dev/null && old_service_active=1 || true
systemctl is-enabled --quiet llm-game-stt.service 2>/dev/null && old_service_enabled=1 || true
[[ -e /etc/apache2/conf-enabled/llm-game.conf ]] && old_new_conf=1
[[ -e /etc/apache2/conf-enabled/llm-game-stt.conf ]] && old_legacy_proxy=1
[[ -e /etc/apache2/conf-enabled/llm-game-nocache.conf ]] && old_legacy_cache=1

for file in \
    /etc/apache2/conf-available/llm-game.conf \
    /etc/apache2/conf-available/llm-game-stt.conf \
    /etc/apache2/conf-available/llm-game-nocache.conf \
    /etc/systemd/system/llm-game-stt.service; do
    if [[ -e "$file" ]]; then
        cp -a "$file" "$BACKUP/$(basename "$file")"
    fi
done

restore_enabled_state() {
    local name=$1 expected=$2
    if [[ $expected -eq 1 ]]; then a2enconf "$name" >/dev/null 2>&1 || true
    else a2disconf "$name" >/dev/null 2>&1 || true
    fi
}

rollback() {
    rc=$?
    trap - ERR
    echo "install_failed=$rc" >> "$REPORT"
    if [[ $old_service_exists -eq 1 && -e "$BACKUP/llm-game-stt.service" ]]; then
        install -m 0644 "$BACKUP/llm-game-stt.service" /etc/systemd/system/llm-game-stt.service
        systemctl daemon-reload
        if [[ $old_service_active -eq 1 ]]; then systemctl restart llm-game-stt.service >/dev/null 2>&1 || true
        else systemctl stop llm-game-stt.service >/dev/null 2>&1 || true
        fi
        if [[ $old_service_enabled -eq 1 ]]; then systemctl enable llm-game-stt.service >/dev/null 2>&1 || true
        else systemctl disable llm-game-stt.service >/dev/null 2>&1 || true
        fi
    else
        systemctl stop llm-game-stt.service >/dev/null 2>&1 || true
        systemctl disable llm-game-stt.service >/dev/null 2>&1 || true
        rm -f /etc/systemd/system/llm-game-stt.service
        systemctl daemon-reload >/dev/null 2>&1 || true
    fi
    if [[ -e "$BACKUP/llm-game.conf" ]]; then install -m 0644 "$BACKUP/llm-game.conf" /etc/apache2/conf-available/llm-game.conf
    elif [[ $old_new_conf -eq 0 ]]; then rm -f /etc/apache2/conf-available/llm-game.conf
    fi
    restore_enabled_state llm-game "$old_new_conf"
    restore_enabled_state llm-game-stt "$old_legacy_proxy"
    restore_enabled_state llm-game-nocache "$old_legacy_cache"
    apache2ctl configtest >/dev/null 2>&1 && systemctl reload apache2 >/dev/null 2>&1 || true
    exit "$rc"
}
trap rollback ERR

current_service_pid=$(systemctl show -p MainPID --value llm-game-stt.service 2>/dev/null || echo 0)
for port in "$WS_PORT" "$HTTP_PORT"; do
    listeners=$(ss -ltnpH "sport = :$port" 2>/dev/null || true)
    if [[ -n "$listeners" && "$listeners" != *"pid=$current_service_pid,"* ]]; then
        echo "target port already in use by another process: $port" >&2
        exit 1
    fi
done

install -m 0644 "$APP/deploy/llm-game-stt.service" /etc/systemd/system/llm-game-stt.service
systemctl daemon-reload
systemctl enable llm-game-stt.service >/dev/null
if [[ $old_service_active -eq 1 ]]; then systemctl restart llm-game-stt.service
else systemctl start llm-game-stt.service
fi

for _ in $(seq 1 60); do
    curl -fsS --max-time 2 "http://127.0.0.1:$HTTP_PORT/http/health" >/dev/null && break
    sleep .5
done
curl -fsS --max-time 5 "http://127.0.0.1:$HTTP_PORT/http/health" >/dev/null

rendered=$(mktemp)
sed -e "s/@WS_PORT@/$WS_PORT/g" -e "s/@HTTP_PORT@/$HTTP_PORT/g" "$APP/deploy/apache.conf.in" > "$rendered"
install -m 0644 "$rendered" /etc/apache2/conf-available/llm-game.conf
rm -f "$rendered"
a2enmod alias headers proxy proxy_http proxy_wstunnel >/dev/null
a2enconf llm-game >/dev/null
a2disconf llm-game-stt >/dev/null 2>&1 || true
a2disconf llm-game-nocache >/dev/null 2>&1 || true
apache2ctl configtest
systemctl reload apache2
curl -fsS --max-time 5 http://127.0.0.1/llm_game_stt/http/health >/dev/null
sudo -u hans "$PY" "$APP/tests/stt_ws_smoke.py" --url ws://127.0.0.1/llm_game_stt/ws/ --timeout 10

new_pid=$(systemctl show -p MainPID --value llm-game-stt.service)
if [[ "$old_pid" =~ ^[0-9]+$ && "$old_pid" != "$new_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    old_cmd=$(tr '\0' ' ' < "/proc/$old_pid/cmdline" 2>/dev/null || true)
    if [[ "$old_cmd" == *server/stt_ws_server.py* ]]; then
        kill -TERM "$old_pid"
        for _ in $(seq 1 30); do kill -0 "$old_pid" 2>/dev/null || break; sleep .25; done
    fi
fi

trap - ERR
{
    echo machine=$(hostname)
    echo installed=$(date -Is)
    echo backup=$BACKUP
    echo ws_port=$WS_PORT
    echo http_port=$HTTP_PORT
    echo service_pid=$new_pid
    echo direct_health=ok
    echo apache_health=ok
    echo websocket_smoke=ok
} | tee "$REPORT"
ln -sfn "$(basename "$REPORT")" "$DATA/var/llm_game/deploy/latest-install.txt"
