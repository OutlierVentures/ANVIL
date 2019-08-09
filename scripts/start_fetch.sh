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
cd oefsearch
python3 scripts/launch.py -c ./scripts/launch_config.json --background &> /dev/null
cd ../oefcore
bazel run mt-core/main/src/cpp:app -- --config_file `pwd`/mt-core/main/src/cpp/config.json &> /dev/null &
echo -e "${ongreen}Fetch node is running.$endcolor"
