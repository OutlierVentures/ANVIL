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

# Script functions
get_latest() {
    if [ ! -d $2 ]; then
        git clone https://github.com/$1/$2.git --recursive
        cd $2
    else
        cd $2
        git pull
    fi
    cd ..
}


##### CORE DEPENDENCIES #####

echo -e "${onyellow}Installing core tools...$endcolor"

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    yes | sudo apt-get install build-essential \
                               git \
                               cmake \
                               python3-dev \
                               python3-pip \
                               python3-pytest
elif [[ "$OSTYPE" == "darwin"* ]]; then
    xcode-select --version || xcode-select --install
    brew --version || yes | /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew install python cmake
fi

pip3 install --upgrade setuptools
pip3 install wheel


##### FETCH #####

echo -e "${onyellow}Installing Fetch...$endcolor"

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    yes | sudo apt-get install python3-sphinx \
                               protobuf-compiler \
                               libprotobuf-dev \
                               tox
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew install protobuf
fi

# Install OEFPython
get_latest fetchai oef-sdk-python
mv oef-sdk-python oefpy
cd oefpy
sudo python3 setup.py install
pip3 install -r requirements.txt
python3 scripts/setup_test.py

# Tox environment fix for Python 3.7
cp ../scripts/tox-fix.ini tox.ini # REMOVE ONCE ISSUE CLOSED

# Build docs
cd docs
make html
cd ../..

# Install OEFCore Docker image for running nodes
get_latest fetchai oef-core
mv oef-core oefcore
cd oefcore
./oef-core-image/scripts/docker-build-img.sh
cd ..


##### SOVRIN #####

echo -e "${onyellow}Installing Sovrin...$endcolor"

# Install Hyperledger Indy
get_latest hyperledger indy-sdk
mv indy-sdk indy
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88
    sudo add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial master"
    sudo apt-get update
    sudo apt-get install -y libindy
    pip3 install base58
elif [[ "$OSTYPE" == "darwin"* ]]; then
    curl https://sh.rustup.rs -sSf | sh -s -- -y
    export PATH="$HOME/.cargo/bin:$PATH" # so can use cargo without relog
    brew install pkg-config \
                 https://raw.githubusercontent.com/Homebrew/homebrew-core/65effd2b617bade68a8a2c5b39e1c3089cc0e945/Formula/libsodium.rb \
                 automake \
                 autoconf \
                 openssl \
                 zeromq \
                 zmq
    export PKG_CONFIG_ALLOW_CROSS=1
    export CARGO_INCREMENTAL=1
    export RUST_LOG=indy=trace
    export RUST_TEST_THREADS=1
    for version in `ls -t /usr/local/Cellar/openssl/`; do
        export OPENSSL_DIR=/usr/local/Cellar/openssl/$version
        break
    done
    cd indy/libindy
    cargo build
    export LIBRARY_PATH=$(pwd)/target/debug
    cd ../cli
    cargo build
    echo 'export DYLD_LIBRARY_PATH='$LIBRARY_PATH'
export LD_LIBRARY_PATH='$LIBRARY_PATH >> ~/.bash_profile 
    cd ../..
fi

# Install Python wrapper for Hyperledger Indy and Quart
pip3 install python3-indy quart

# Testing Sovrin is done once connected to a node pool
# Hence Sovrin tests are in a separate file

echo -e "${ongreen}ANVIL installed successfully.$endcolor"
