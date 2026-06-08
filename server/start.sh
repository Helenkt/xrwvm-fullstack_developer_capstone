#!/usr/bin/env bash
set -e

gunicorn djangoproj.wsgi:application --bind 0.0.0.0:${PORT:-8000}
