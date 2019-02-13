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

echo -e "${onyellow}Starting Fetch node...$endcolor"
./oefcore/oef-core-image/scripts/docker-run.sh -p 3333:3333 -d --
echo -e "${ongreen}Fetch node is running.$endcolor"
