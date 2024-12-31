#!/bin/sh
source .venv/bin/activate
cd web
python -m flask --app app run -p $PORT --debug