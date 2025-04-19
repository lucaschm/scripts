#!/bin/bash

# CONFIG
DOCKER_CONTAINER="docker-minecraft-1"
WORLD_DIR="/home/ubu/docker/minecraft-server/main-world"
USERNAME="SteveTheThird"
BACKUP_DIR="/home/ubu/minecraft-backups/$USERNAME"
LOG_FILE="/home/ubu/docker/minecraft-server/logs/latest.log"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Notify players
echo "Sending warning to players..."
docker exec -i $DOCKER_CONTAINER rcon-cli "say Server will restart in 30 seconds!"

# Wait 5 minutes
sleep 30

# Stop Minecraft server
echo "Stopping Minecraft server..."
docker stop $DOCKER_CONTAINER

# Check if the user has been online in the past 24 hours
if [ "$(find "$LOG_FILE" -mmin -1440)" ] && grep -q "$USERNAME" "$LOG_FILE"; then
    echo "$USERNAME was online in the last 24 hours. Proceeding with backup..."

    # Create backup directory if not exists
    mkdir -p "$BACKUP_DIR"

    # Create the backup
    BACKUP_NAME="world-$TIMESTAMP"
    cp -r "$WORLD_DIR" "$BACKUP_DIR/$BACKUP_NAME"
    echo "Backup created: $BACKUP_NAME"

    # Remove old backups (keep only 10)
    BACKUPS=($(ls -dt $BACKUP_DIR/world-*))
    COUNT=${#BACKUPS[@]}
    if [ $COUNT -gt 10 ]; then
        for ((i=10; i<$COUNT; i++)); do
            echo "Removing old backup: ${BACKUPS[$i]}"
            rm -rf "${BACKUPS[$i]}"
        done
    fi
else
    echo "$USERNAME was not online in the last 24 hours. Skipping backup."
fi

# Start Minecraft server
echo "Starting Minecraft server..."
docker start $DOCKER_CONTAINER