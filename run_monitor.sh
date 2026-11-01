#!/usr/bin/env bash
set -e

python3 -m pip install -r requirements.txt
cp .env.example .env
python3 monitor.py
