#!/bin/bash
CONTAINER=hermes-agent
if ! docker exec $CONTAINER pgrep -f 'hermes-cmd-server.py' > /dev/null 2>&1; then
    echo "[$(date)] cmd-server down, restarting..."
    docker exec -d $CONTAINER python3 /opt/data/stock-web-system/hermes-cmd-server.py
fi
