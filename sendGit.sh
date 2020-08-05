#!/bin/bash

git config --global credential.helper 'cache --timeout=3600'
git pull
git add *
git commit -m "$1"
git push
