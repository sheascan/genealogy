#!/bin/bash
DEPLOY_URL="https://script.google.com/macros/s/AKfycbx5AguEgIVILADoTs8i5a9OSVY1A4Mk-ZsQyEGlSccT0BG86hZLaMsOqthiHE7JmBfjqA/exec"

curl -sL "$DEPLOY_URL" -o family/sheets/mapping.csv

