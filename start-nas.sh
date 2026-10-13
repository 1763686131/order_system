#!/bin/sh
set -u

PROJECT_ROOT=$(CDPATH= cd "$(dirname "$0")" && pwd)
OFFLINE_IMAGE="$PROJECT_ROOT/Settings/order-backend.tar"
IMAGE_NAME="order-backend:latest"

cd "$PROJECT_ROOT" || exit 1

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "Docker Compose is not available."
    exit 1
fi

echo "===================================="
echo "Project Root: $PROJECT_ROOT"
echo "Image: $IMAGE_NAME"
echo "===================================="

echo "===================================="
echo "Loading offline image first..."
echo "===================================="
if [ -f "$OFFLINE_IMAGE" ]; then
    docker load -i "$OFFLINE_IMAGE"
    if [ $? -ne 0 ]; then
        if docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
            echo "Offline image load failed, using existing local image."
        else
            echo "Offline image load failed. Falling back to online build."
            docker build -t "$IMAGE_NAME" "$PROJECT_ROOT/backend" || exit 1
        fi
    elif ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
        echo "Offline image loaded, but $IMAGE_NAME was not found."
        echo "Falling back to online build."
        docker build -t "$IMAGE_NAME" "$PROJECT_ROOT/backend" || exit 1
    else
        echo "Offline image is ready."
    fi
else
    echo "Offline image not found: $OFFLINE_IMAGE"
    if docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
        echo "Using existing local image."
    else
        echo "Falling back to online build."
        docker build -t "$IMAGE_NAME" "$PROJECT_ROOT/backend" || exit 1
    fi
fi

echo "===================================="
echo "Starting service with Docker Compose..."
echo "===================================="
$COMPOSE_CMD up -d
