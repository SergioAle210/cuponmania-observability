#!/bin/sh
# Imports the data views, visualizations and dashboard into Kibana (idempotent: overwrite=true).
set -eu
curl -fsS -X POST "http://kibana:5601/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" --form file=@/setup/saved-objects.ndjson
echo
echo "Kibana saved objects imported."
