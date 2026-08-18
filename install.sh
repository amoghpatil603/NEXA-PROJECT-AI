#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3.10-venv
python3 -m venv .venv
.venv/bin/pip install numpy sentence-transformers pypdf python-docx --no-cache-dir
