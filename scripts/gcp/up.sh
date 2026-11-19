#!/usr/bin/env bash
# Create (or update) every GCP resource for the AI Security Analysis Platform POC in one command.
# Safe to re-run: existing resources are reused. Touches only resources named ai-security-platform*.
#
#   ./scripts/gcp/up.sh
#
# Requires: gcloud signed in, Docker running, run from anywhere inside the repo.
set -euo pipefail

P="${PROJECT_ID:-white-watch-464115-t0}"
R="${REGION:-us-east1}"            # organisation policy allows only us-east1
REPO=ai-security-platform
SVC=ai-security-platform
SA_NAME=ai-security-platform-run
SA="$SA_NAME@$P.iam.gserviceaccount.com"
MODEL="${VERTEX_MODEL:-gemini-2.5-flash}"
LABELS="app=ai-security-platform,env=poc,owner=tushar,cost-center=poc"

cd "$(git rev-parse --show-toplevel)"
TAG=$(git rev-parse --short HEAD)
[ -n "$(git status --porcelain --untracked-files=no)" ] && TAG="$TAG-dirty"
IMAGE="$R-docker.pkg.dev/$P/$REPO/api:$TAG"
step() { echo; echo "=== $*"; }

step "1/5 Artifact Registry repository: $REPO"
if ! gcloud artifacts repositories describe "$REPO" --location "$R" --project "$P" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO" --project "$P" --location "$R" \
    --repository-format docker --description "AI Security Analysis Platform POC images" --labels "$LABELS"
else
  echo "exists - reusing"
fi
POLICY=$(mktemp)
cat > "$POLICY" <<'EOF'
[
  {"name": "keep-latest-3", "action": {"type": "Keep"}, "mostRecentVersions": {"keepCount": 3}},
  {"name": "delete-older", "action": {"type": "Delete"}, "condition": {"tagState": "any", "olderThan": "1d"}}
]
EOF
gcloud artifacts repositories set-cleanup-policies "$REPO" --project "$P" --location "$R" \
  --policy "$POLICY" --no-dry-run --format none
rm -f "$POLICY"

step "2/5 Build and push image (local Docker, no Cloud Build): $IMAGE"
docker build -q -t "$IMAGE" .
gcloud auth configure-docker "$R-docker.pkg.dev" --quiet >/dev/null 2>&1
docker push -q "$IMAGE"
DIGEST=$(gcloud artifacts docker images describe "$IMAGE" --format='value(image_summary.digest)')

step "3/5 Runtime service account: $SA"
if ! gcloud iam service-accounts describe "$SA" --project "$P" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SA_NAME" --project "$P" \
    --display-name "AI Security Platform Cloud Run runtime" \
    --description "Least-privilege runtime identity for the ai-security-platform POC"
  sleep 10   # IAM propagation
else
  echo "exists - reusing"
fi

step "4/5 Grant roles/aiplatform.user to the service account (only role)"
gcloud projects add-iam-policy-binding "$P" --member "serviceAccount:$SA" \
  --role roles/aiplatform.user --condition None --format none

step "5/5 Deploy private Cloud Run service: $SVC"
gcloud run deploy "$SVC" --project "$P" --region "$R" \
  --image "$R-docker.pkg.dev/$P/$REPO/api@$DIGEST" \
  --service-account "$SA" \
  --no-allow-unauthenticated --ingress all \
  --min-instances 0 --max-instances 1 \
  --cpu 1 --memory 512Mi --cpu-throttling --no-cpu-boost \
  --concurrency 20 --timeout 60 \
  --set-env-vars "ENVIRONMENT=gcp-poc,AI_PROVIDER=vertex,VERTEX_PROJECT=$P,VERTEX_LOCATION=$R,VERTEX_MODEL=$MODEL,VERTEX_THINKING_BUDGET=0,VERTEX_MAX_OUTPUT_TOKENS=2048,VERTEX_MAX_CALLS_PER_INSTANCE=20" \
  --labels "$LABELS" --quiet

URL=$(gcloud run services describe "$SVC" --project "$P" --region "$R" --format='value(status.url)')
echo
echo "DONE. Service URL: $URL"
echo "Test it with: ./scripts/gcp/test.sh"
