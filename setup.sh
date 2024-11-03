#!/bin/bash
apt update && apt upgrade -y
apt install -y git python3-pip
pip3 install -r grass/requirements.txt
