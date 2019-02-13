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

echo -e "${onyellow}Stopping Sovrin node pool...$endcolor"
docker stop $(docker ps | grep indy_pool | awk '{ print $1 }')
echo -e "${onred}Sovrin node pool stopped.$endcolor"
