#!/bin/bash

onred='\033[41m'
onyellow='\033[43m'
endcolor="\033[0m"

echo -e "${onyellow}Stopping node...$endcolor"
docker stop $(docker ps | grep oef-core-image | awk '{ print $1 }') && \
echo -e "${onred}Node stopped.$endcolor"