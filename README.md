# MATTUpdater - Source → Target File Update Tool

A desktop application with graphical interface for updating target files
with data from source files, supporting intelligent column matching and
new column addition.

## Features

- **Intelligent Column Matching**: Automatically matches columns between
  source and target files using prefix stripping and hybrid similarity scoring
- **New Column Addition**: Add source columns that don't exist in the target
  file as new columns with automatic prefix detection
- **SKU-Based Alignment**: Updates data row by row based on SKU matching
- **Formula Preservation**: Detects and preserves Excel formulas during update
- **Streaming Write**: Memory-efficient row-by-row writing for large files
- **Wizard Interface**: Step-by-step guided workflow

## Requirements

PySide6>=6.5.0
polars>=0.19.0
fastexcel>=0.10.0
openpyxl>=3.1.0
xlsxwriter>=3.0.0
chardet>=5.0.0

## Installation

```bash
pip install -r requirements.txt
