#!/bin/bash
cd source

echo "Inicializing the LAD app..."

echo "Installing Flask..."
pip install Flask

echo "Installing Peewee..."
pip install peewee

echo "Installing Dash..."
pip install dash

echo "Installing Pandas..."
pip install pandas

echo "Installing Dash-Bootstrap-Components..."
pip install dash-bootstrap-components

echo "Libraries installation completed."

echo "Executing the LAD Accounting-Dash app..."

python3 app.py
