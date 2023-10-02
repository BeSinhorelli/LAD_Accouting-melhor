#!/bin/bash

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

echo "Installing OpenPYXL..."
pip install openpyxl

echo "Libraries installation completed."

echo "Executing the LAD Accounting-Dash app..."
cd source
python3 app.py
