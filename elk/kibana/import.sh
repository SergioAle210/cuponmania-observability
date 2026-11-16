#!/bin/sh
# Importación idempotente con validación del resultado JSON, no solo del HTTP 200.
set -eu
exec python /setup/import_objects.py
