#!/bin/bash

# Install library Dash
echo "Installing Flask..."
pip install Flask

# Install library pandas
echo "Installing Peewee..."
pip install peewee

echo "Libraries installation completed."

echo "Executing the main python programm..."
python3 lad.py