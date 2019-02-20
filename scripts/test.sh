#!/bin/bash

ongreen='\033[42m'
onyellow='\033[43m'
endcolor="\033[0m"

echo -e "${onyellow}Testing Fetch install...$endcolor"
cd oefpy
sudo tox -e py37
cd ..

echo -e "${onyellow}Testing Sovrin install...$endcolor"
# If tests run immediately after installer and node pool starter in the same session,
# need to grab the dynamic linking envrionment variables
if [[ "$OSTYPE" == "darwin"* ]]; then
    source ~/.bash_profile
fi
cd indy/wrappers/python
pytest

echo -e "${ongreen}Tests complete, see results above.$endcolor"
