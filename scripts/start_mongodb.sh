#! /bin/bash

ROOT="$( cd "$( cd "$(dirname "$0")" ; pwd -P )/../.." ; pwd -P )"
TIMESTAMP="$(date +%Y.%m.%d.%H%M%S)"

# start mongodb
mongod --dbpath "$ROOT/data/db" \
    --bind_ip 127.0.0.1 --port 27017 \
    --logpath "$ROOT/data/log/mongo_"$TIMESTAMP".log" \
    --auth \
    --fork

echo "MongoDB Started"