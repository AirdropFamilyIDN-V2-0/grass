#!/bin/bash
apt update && apt upgrade -y
apt install -y git python3-pip
git clone https://github.com/meKryztal/grass.git
pip3 install -r grass/requirements.txt
