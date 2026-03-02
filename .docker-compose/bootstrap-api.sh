#!/bin/bash

# Run server (overrides Dockerfile CMD instruction).
stdbuf -i0 -o0 -e0 fastapi run --workers 1 --host 0.0.0.0 --port 9000 --reload src/main.py
