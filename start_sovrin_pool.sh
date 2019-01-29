#!/bin/bash

# Keep the image build in this script rather than installer for 2 reasons:
# 1. Hyperledger indy node software dependencies stay up to date
# 2. For mainnet, building pool is unnecessary so no need to have it in the installer

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

echo -e "${onyellow}Starting Sovrin node pool...$endcolor"
docker build -f indy/ci/indy-pool.dockerfile -t indy_pool .
docker run -itd -p 9701-9708:9701-9708 indy_pool
echo -e "${ongreen}Sovrin node pool is running.$endcolor"
