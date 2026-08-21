#!/bin/sh
set -e

python docker/bootstrap.py
exec python run_server.py
