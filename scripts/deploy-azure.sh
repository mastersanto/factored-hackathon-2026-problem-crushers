#!/usr/bin/env bash
# Deploy the demo container to Azure Container Apps (research.md §10; tasks T025-T029).
# The image is built locally (it contains the git-ignored demo subset) and pushed to a PRIVATE registry.
# The Anthropic key is read from .env.local here and stored only as a Container Apps secret; it is never
# printed, committed, or baked into the image. Idempotent: re-run to update.
set -euo pipefail

RG="${RG:-rg-problem-crushers}"
LOCATION="${LOCATION:-eastus2}"
ACR="${ACR:-problemcrushers$(az account show --query id -o tsv | tr -d '-' | cut -c1-8)}"   # globally unique
ENVNAME="${ENVNAME:-cae-problem-crushers}"
APP="${APP:-explain-this-charge}"
TAG="${TAG:-$(git rev-parse --short HEAD)}"
IMAGE="$ACR.azurecr.io/$APP:$TAG"
MAX_LLM_USD="${MAX_LLM_USD:-5.0}"

cd "$(dirname "$0")/.."
KEY=$(grep -E '^ANTHROPIC_API_KEY=' .env.local | cut -d= -f2- | tr -d '"'"'"' ')
[ -n "$KEY" ] || { echo "ANTHROPIC_API_KEY missing in .env.local (the app would run in rules mode)"; }

echo "==> providers"
for p in Microsoft.App Microsoft.OperationalInsights Microsoft.ContainerRegistry; do
  az provider register --namespace "$p" --wait >/dev/null
done
# An Azure CLI installed with `uv tool install azure-cli` has no pip, which extensions need.
AZPY="$(dirname "$(readlink -f "$(command -v az)")")/python"
[ -x "$AZPY" ] && ! "$AZPY" -m pip --version >/dev/null 2>&1 && "$AZPY" -m ensurepip --upgrade >/dev/null
az extension add --name containerapp --upgrade --only-show-errors >/dev/null

echo "==> resource group $RG ($LOCATION)"
az group create -n "$RG" -l "$LOCATION" -o none

echo "==> private registry $ACR"
az acr show -n "$ACR" -g "$RG" -o none 2>/dev/null || az acr create -n "$ACR" -g "$RG" --sku Basic --admin-enabled false -o none

echo "==> build and push $IMAGE (local build: the demo data never goes through git)"
make demo-data >/dev/null
docker build -t "$IMAGE" .
az acr login -n "$ACR" >/dev/null
docker push "$IMAGE" >/dev/null

echo "==> container apps environment $ENVNAME"
az containerapp env show -n "$ENVNAME" -g "$RG" -o none 2>/dev/null || az containerapp env create -n "$ENVNAME" -g "$RG" -l "$LOCATION" -o none

# Key for transcript check codes (specs/002): created once, random, never printed. It is kept across
# deploys, so PDFs issued earlier keep verifying.
new_transcript_key() { python3 -c 'import secrets; print(secrets.token_urlsafe(32))'; }
ENV_VARS=("ANTHROPIC_API_KEY=secretref:anthropic-key" "TRANSCRIPT_HMAC_KEY=secretref:transcript-key" "MAX_LLM_USD=$MAX_LLM_USD")

if az containerapp show -n "$APP" -g "$RG" -o none 2>/dev/null; then
  echo "==> update $APP"
  az containerapp secret set -n "$APP" -g "$RG" --secrets "anthropic-key=$KEY" -o none
  if [ -z "$(az containerapp secret list -n "$APP" -g "$RG" --query "[?name=='transcript-key'].name" -o tsv)" ]; then
    echo "==> create the transcript-key secret (once)"
    TKEY=$(new_transcript_key)
    az containerapp secret set -n "$APP" -g "$RG" --secrets "transcript-key=$TKEY" -o none
    unset TKEY
  fi
  az containerapp update -n "$APP" -g "$RG" --image "$IMAGE" --set-env-vars "${ENV_VARS[@]}" -o none
else
  echo "==> create $APP (scale to zero, one replica max)"
  TKEY=$(new_transcript_key)
  az containerapp create -n "$APP" -g "$RG" --environment "$ENVNAME" --image "$IMAGE" \
    --registry-server "$ACR.azurecr.io" --registry-identity system \
    --target-port 8080 --ingress external --min-replicas 0 --max-replicas 1 --cpu 0.5 --memory 1.0Gi \
    --secrets "anthropic-key=$KEY" "transcript-key=$TKEY" \
    --env-vars "${ENV_VARS[@]}" -o none
  unset TKEY
fi
unset KEY

URL="https://$(az containerapp show -n "$APP" -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)"
echo "==> deployed: $URL"
for i in $(seq 1 30); do curl -sf "$URL/api/health" && echo && break; sleep 5; done
