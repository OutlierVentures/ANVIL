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

##### DETECT PREVIOUS RUN #####
if [ -e indy -o -e indysdk -o -e oefcore -o -e oefpy ]; then
	rm -rf ./indy ./indysdk ./oefcore ./oefpy
fi


##### CORE DEPENDENCIES #####

echo -e "${onyellow}Installing core tools...$endcolor"

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    yes | sudo apt-get install build-essential \
                               git \
                               cmake \
                               python3 \
                               python3-pip \
                               python3-pytest
    # Python 3.7 for Quart
    yes | sudo apt install software-properties-common
    yes | sudo add-apt-repository ppa:deadsnakes/ppa
    yes | sudo apt install python3.7
elif [[ "$OSTYPE" == "darwin"* ]]; then
    xcode-select --version || xcode-select --install
    brew --version || yes | /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    python3.7 --version || brew install python
    cmake --version || brew install cmake
fi

pip3 install --upgrade setuptools
pip3 install wheel

##### SOVRIN #####

echo -e "${onyellow}Installing Sovrin...$endcolor"

# Install Hyperledger Indy - large repo so fetch incrementally
git clone https://github.com/hyperledger/indy-sdk.git --depth 1
mv indy-sdk indy
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88
    sudo add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial master"
    sudo apt-get update
    sudo apt-get install -y libindy
    pip3 install base58
elif [[ "$OSTYPE" == "darwin"* ]]; then
    cd indy/libindy
    chmod +x mac.build.sh
    ./mac.build.sh
    cd ../..
fi

# Install Python wrapper for Hyperledger Indy and Quart
pip3 install python3-indy quart

##### FETCH #####

echo -e "${onyellow}Installing Fetch...$endcolor"

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    yes | sudo apt-get install protobuf-compiler \
                               libprotobuf-dev \
                               unzip \
                               tox
    bazel version || echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list && \
                     curl https://bazel.build/bazel-release.pub.gpg | sudo apt-key add - && \
                     sudo apt-get update && \
                     sudo apt-get install bazel
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew upgrade protobuf || brew install protobuf
    if brew ls --versions bazel >/dev/null; then
        if [[ $(brew outdated bazel) ]]; then
            HOMEBREW_NO_AUTO_UPDATE=1 brew upgrade bazelbuild/tap/bazel
        fi
    else
        brew tap bazelbuild/tap
        HOMEBREW_NO_AUTO_UPDATE=1 brew install bazelbuild/tap/bazel
    fi
fi
pip3 install gitpython

# Install OEF SDK
pip3 install oef

# Install OEFCore for running nodes
get_latest fetchai oef-mt-core
mv oef-mt-core oefcore
cd oefcore
bazel build mt-core/main/src/cpp:app
cd ..

## Install OEF search (Pluto)
get_latest oef-search-pluto
mv oef-search-pluto oefsearch

echo -e "${ongreen}ANVIL installed successfully.$endcolor"


