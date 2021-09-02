#!/bin/bash

echo "Run $1 on $2."

network=""
if [ $# -eq 2 ]; then
  network="--network $2"
fi

echo "Start: brownie run '$(pwd)/scripts/$1' $network"
brownie run "$(pwd)/scripts/$1" $network
