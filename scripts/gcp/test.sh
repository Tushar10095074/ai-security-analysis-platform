#!/usr/bin/env bash
# End-to-end smoke test of the deployed POC.
#
#   ./scripts/gcp/test.sh            # full test, makes ONE Vertex AI call (~$0.002)
#   ./scripts/gcp/test.sh --no-ai    # skip the Vertex AI call (free)
set -uo pipefail

P="${PROJECT_ID:-white-watch-464115-t0}"
R="${REGION:-us-east1}"
URL=$(gcloud run services describe ai-security-platform --region "$R" --project "$P" \
      --format='value(status.url)' 2>/dev/null)
[ -n "$URL" ] || { echo "Service not found. Deploy with ./scripts/gcp/up.sh"; exit 1; }
TOKEN=$(gcloud auth print-identity-token)
AUTH="Authorization: Bearer $TOKEN"
FAIL=0
check() { if [ "$2" = "$3" ]; then echo "  [PASS] $1 ($2)"; else echo "  [FAIL] $1 (got $2, want $3)"; FAIL=1; fi; }
json() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }

echo "Service: $URL"
echo "1. Security"
check "no token is rejected" "$(curl -s -o /dev/null -w '%{http_code}' "$URL/health")" 403

echo "2. Health"
check "/health" "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" "$URL/health")" 200
check "/ready"  "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" "$URL/ready")" 200

echo "3. Ingest event"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EVENT=$(cat <<EOF
{"source":"custom","source_event_id":"smoke-test","event_type":"misconfiguration","severity":"high",
 "title":"Smoke test: storage bucket allows public read",
 "description":"Synthetic test event: a test bucket policy grants allUsers read.",
 "resource":{"provider":"custom","resource_type":"storage.bucket","resource_id":"smoke-test-bucket",
             "internet_exposed":true,"business_criticality":"medium"},
 "observed_at":"$NOW","evidence":{"policy_binding":"allUsers:objectViewer"}}
EOF
)
RESP=$(curl -s -w '\n%{http_code}' -H "$AUTH" -H 'Content-Type: application/json' -d "$EVENT" "$URL/api/v1/events")
check "POST /api/v1/events" "$(echo "$RESP" | tail -1)" 202
ID=$(echo "$RESP" | head -1 | json 'd["event_id"]')
echo "  event_id: $ID"
check "GET event" "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" "$URL/api/v1/events/$ID")" 200

echo "4. Deterministic risk"
RISK=$(curl -s -X POST -H "$AUTH" "$URL/api/v1/events/$ID/analyze")
echo "  score/level: $(echo "$RISK" | json 'str(d["risk_score"]) + " / " + d["risk_level"]')"
check "risk level" "$(echo "$RISK" | json 'd["risk_level"]')" high

if [ "${1:-}" != "--no-ai" ]; then
  echo "5. Vertex AI analysis (1 Gemini call)"
  AI=$(curl -s -w '\n%{http_code}' -X POST -H "$AUTH" "$URL/api/v1/events/$ID/ai-analysis")
  check "POST ai-analysis" "$(echo "$AI" | tail -1)" 200
  BODY=$(echo "$AI" | head -n -1)
  check "provider" "$(echo "$BODY" | json 'd.get("provider")')" vertex_ai
  echo "  model:   $(echo "$BODY" | json 'd.get("model")')"
  echo "  summary: $(echo "$BODY" | json 'd.get("summary","")[:300]')"
  echo "  action:  $(echo "$BODY" | json '(d.get("recommended_actions") or [""])[0][:300]')"
  SAME=$([ "$(curl -s -H "$AUTH" "$URL/api/v1/events/$ID/risk")" = "$RISK" ] && echo identical || echo changed)
  check "risk unchanged after AI" "$SAME" identical
else
  echo "5. Vertex AI analysis skipped (--no-ai)"
fi

echo
[ $FAIL -eq 0 ] && echo "RESULT: ALL PASSED" || echo "RESULT: FAILURES ABOVE"
exit $FAIL
