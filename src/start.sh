#!/bin/bash

echo "runpod-worker-helloworld: Starting RunPod Handler"
python3 -u /rp_handler.py
python3 -u /rp_handler.py --test_input "$(cat test_input-with-hole.json)"
python3 -u /rp_handler.py --test_input "$(cat test_input-custom-bin.json)"
python3 -u /rp_handler.py --test_input "$(cat test_shirt-bin.json)"