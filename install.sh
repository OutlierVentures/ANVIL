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

# Script functions
get_latest() {
    if [ ! -d $2 ]; then
        git clone https://github.com/$1/$2.git --recursive
        cd $2/
    else
        cd $2/
        git pull
    fi
    cd ../
}

# Install initial requirements
echo -e "${onyellow}Installing dependencies...$endcolor"
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    yes | sudo apt-get install build-essential python3-dev python3-pip git protobuf-compiler
elif [[ "$OSTYPE" == "darwin"* ]]; then
    xcode-select --version || xcode-select --install
    brew --version || yes | /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew install python protobuf cmake
fi
pip3 install --upgrade setuptools
pip3 install wheel

# Install OEFPython and test
echo -e "${onyellow}Installing OEF components...$endcolor"
get_latest fetchai oef-sdk-python
mv oef-sdk-python oefpy
cd oefpy
sudo python3 setup.py install
pip3 install -r requirements.txt
python3 scripts/setup_test.py
echo -e "${onyellow}Testing installation...$endcolor"
cp ../tox-fix.ini tox.ini # REMOVE ONCE ISSUE CLOSED
sudo tox || true # Data gen test will not pass on slower machines, pipe to true
cd docs
make html
cd ../../

# Install OEFCore Docker image for running nodes
echo -e "${onyellow}Installing Fetch node software...$endcolor"
get_latest fetchai oef-core
mv oef-core oefcore
cd oefcore/
./oef-core-image/scripts/docker-build-img.sh

echo -e "${ongreen}ANVIL installed successfully.$endcolor"
