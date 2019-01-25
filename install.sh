#!/bin/bash

onred='\033[41m'
ongreen='\033[42m'
onyellow='\033[43m'
endcolor="\033[0m"

# Handle errors
set -e
error_report() {
    echo -e "${onred}Error: install.sh failed on line $1.$endcolor"
}
trap 'error_report $LINENO' ERR

# Install initial requirements
echo -e "${onyellow}Installing dependencies...$endcolor"
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    yes | sudo apt-get install build-essential python3-dev python3-pip python3-sphinx git protobuf-compiler
elif [[ "$OSTYPE" == "darwin"* ]]; then
    xcode-select --version || xcode-select --install
    brew --version || yes | /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew install python sphinx-doc protobuf
fi
pip3 install --upgrade setuptools
pip3 install wheel

# Install OEFPython and test
echo -e "${onyellow}Installing OEF components...$endcolor"
git clone https://github.com/fetchai/oef-sdk-python.git --recursive
cd oef-sdk-python/
sudo python3 setup.py install
echo -e "${onyellow}Testing installation...$endcolor"
python3 scripts/setup_test.py
cp ../tox-fix.ini tox.ini # REMOVE ONCE ISSUE CLOSED
sudo tox # Run tests
cd docs
make html

# Install OEFCore Docker image for running nodes
echo -e "${onyellow}Installing Fetch node software...$endcolor"
cd ../..
git clone https://github.com/fetchai/oef-core.git --recursive
cd oef-core/
./oef-core-image/scripts/docker-build-img.sh
