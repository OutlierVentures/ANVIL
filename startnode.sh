#!/bin/bash

ongreen='\033[42m'
onyellow='\033[43m'
endcolor="\033[0m"

echo -e "${onyellow}Starting node...$endcolor"
./oefcore/oef-core-image/scripts/docker-run.sh -p 3333:3333 -d -- && \
echo -e "${ongreen}Node is running.$endcolor"