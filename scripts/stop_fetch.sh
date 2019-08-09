#!/bin/bash

onred='\033[41m'
ongreen='\033[42m'
onyellow='\033[43m'
endcolor="\033[0m"

# Handle errors
set -e
error_report() {
    echo -e "${onred}Error: failed on line $1.$endcolor"
}
trap 'error_report $LINENO' ERR

echo -e "${onyellow}Stopping Fetch node...$endcolor"
docker stop $(docker ps -a | grep oef-search | awk '{print $1}') &> /dev/null
kill -INT $(ps | grep oef-mt-core | awk '{print $1}') &> /dev/null
echo -e "${onred}Fetch node stopped.$endcolor"
