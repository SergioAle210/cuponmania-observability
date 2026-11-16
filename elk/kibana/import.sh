#!/bin/sh
# Imports the data views, visualizations and dashboard into Kibana (idempotent: overwrite=true),
# then makes the dashboard Kibana's home page. Without it Kibana opens its "Elasticsearch" search
# home page, which calls the security API (disabled in this lab) and shows an error.
set -eu
KIBANA=http://kibana:5601
DASHBOARD_ID=cuponmania-salud-api

curl -fsS -X POST "$KIBANA/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" --form file=@/setup/saved-objects.ndjson
echo
echo "Kibana saved objects imported."

# Kibana 9 serves this setting only on its internal route; the public /api/kibana/settings
# answers 400 in this configuration. Idempotent.
curl -fsS -X POST "$KIBANA/internal/kibana/settings" \
  -H "kbn-xsrf: true" -H "x-elastic-internal-origin: kibana" -H "Content-Type: application/json" \
  -d "{\"changes\":{\"defaultRoute\":\"/app/dashboards#/view/$DASHBOARD_ID\"}}" > /dev/null
echo "Kibana home page set to the dashboard $DASHBOARD_ID."
