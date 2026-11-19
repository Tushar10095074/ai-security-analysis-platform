#!/usr/bin/env bash
# Delete every GCP resource created for the AI Security Analysis Platform POC, and nothing else.
#
#   ./scripts/gcp/down.sh          # asks you to type the project ID to confirm
#   ./scripts/gcp/down.sh --yes    # no prompt
#
# Removes: Cloud Run service, IAM binding, service account, Artifact Registry repo (and its images).
set -euo pipefail

P="${PROJECT_ID:-white-watch-464115-t0}"
R="${REGION:-us-east1}"
SVC=ai-security-platform
REPO=ai-security-platform
SA="ai-security-platform-run@$P.iam.gserviceaccount.com"

echo "This permanently deletes in project $P ($R):"
echo "  - Cloud Run service       $SVC"
echo "  - IAM binding             roles/aiplatform.user for $SA"
echo "  - Service account         $SA"
echo "  - Artifact Registry repo  $REPO (all images)"
if [ "${1:-}" != "--yes" ]; then
  read -r -p "Type the project ID to confirm: " ANSWER
  [ "$ANSWER" = "$P" ] || { echo "Aborted - nothing deleted."; exit 1; }
fi

echo "=== 1/4 Cloud Run service"
if gcloud run services describe "$SVC" --region "$R" --project "$P" >/dev/null 2>&1; then
  gcloud run services delete "$SVC" --region "$R" --project "$P" --quiet
else echo "not found - skipped"; fi

echo "=== 2/4 IAM binding"
if gcloud projects get-iam-policy "$P" --flatten='bindings[].members' \
     --filter="bindings.members:serviceAccount:$SA AND bindings.role:roles/aiplatform.user" \
     --format='value(bindings.role)' | grep -q aiplatform; then
  gcloud projects remove-iam-policy-binding "$P" --member "serviceAccount:$SA" \
    --role roles/aiplatform.user --condition None --format none
  echo "removed"
else echo "not found - skipped"; fi

echo "=== 3/4 Service account"
if gcloud iam service-accounts describe "$SA" --project "$P" >/dev/null 2>&1; then
  gcloud iam service-accounts delete "$SA" --project "$P" --quiet
else echo "not found - skipped"; fi

echo "=== 4/4 Artifact Registry repository"
if gcloud artifacts repositories describe "$REPO" --location "$R" --project "$P" >/dev/null 2>&1; then
  gcloud artifacts repositories delete "$REPO" --location "$R" --project "$P" --quiet
else echo "not found - skipped"; fi

echo
echo "DONE. All POC resources removed. Recreate any time with: ./scripts/gcp/up.sh"
