#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
apt-get install -y python3-pip python3.10-distutils python3-venv
python3 -m venv venv3
venv3/bin/pip install numpy sentence-transformers pypdf python-docx --no-cache-dir
