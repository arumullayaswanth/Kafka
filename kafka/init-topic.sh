#!/usr/bin/env bash
# Runs once in the kafka-init container: creates the orders topic (idempotent).
set -euo pipefail
TOPIC="${TOPIC_NAME:-orders}"
KT=/opt/kafka/bin/kafka-topics.sh

$KT --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic "$TOPIC" --partitions 3 --replication-factor 1
$KT --bootstrap-server kafka:9092 --describe --topic "$TOPIC"
