#!/bin/bash
while ! command -v pip &> /dev/null
do
    echo "Waiting for pip to be installed..."
    sleep 2
done
pip install pytesseract pdfplumber Pillow pypdf
