#!/usr/bin/env bash
# Executed over SSH from the tested runner checkout, not from the old server tree.
set -euo pipefail

deploy_path="${1:?Usage: deploy-remote.sh /absolute/repo/path tested-sha}"
revision="${2:?Missing tested commit SHA}"
[[ "$deploy_path" == /* && "$deploy_path" != / && "$revision" =~ ^[0-9a-f]{40}$ ]] || {
  echo "Invalid deployment path or commit SHA." >&2; exit 1;
}
cd "$deploy_path"
repo_root="$(pwd -P)"
[[ "$(git rev-parse --show-toplevel)" == "$repo_root" ]] || {
  echo "Deployment path must be the root of the existing repository clone." >&2; exit 1;
}
[[ "$(git remote get-url origin)" =~ ^(https://github\.com/|git@github\.com:|ssh://git@github\.com/)shellshocked59/aig(\.git)?$ ]] || {
  echo "Deployment checkout has an unexpected origin." >&2; exit 1;
}
mkdir -p .deploy/releases
chmod 755 .deploy .deploy/releases
exec 9>.deploy/deploy.lock
flock -n 9 || { echo "Another AIG deployment is in progress." >&2; exit 1; }
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || {
  echo "Server checkout has tracked changes; refusing to overwrite them." >&2; exit 1;
}
git fetch origin main
git merge-base --is-ancestor "$revision" origin/main || {
  echo "Requested commit is not on origin/main." >&2; exit 1;
}
if [[ -f .deploy/current-sha ]]; then
  previous_revision="$(cat .deploy/current-sha)"
  if [[ "$previous_revision" != "$revision" ]] && git merge-base --is-ancestor "$revision" "$previous_revision"; then
    echo "Refusing to replace a newer deployment with this older workflow run." >&2
    exit 1
  fi
fi
git checkout --detach "$revision"

docker_cmd=(docker)
file_cmd=()
if ! docker info >/dev/null 2>&1; then
  docker_cmd=(sudo -n docker)
  file_cmd=(sudo -n)
fi
"${docker_cmd[@]}" info >/dev/null
"${docker_cmd[@]}" compose version

# Keep database credentials on the server and preserve them across deployments.
if [[ ! -f .env.production ]]; then
  (umask 077; printf 'POSTGRES_PASSWORD=%s\n' "$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')" > .env.production)
  echo "Created server-local .env.production with a generated database password."
fi
export AIG_RELEASE_SHA="$revision"
# sudo normally drops exported variables; supply the revision through a file too.
printf 'AIG_RELEASE_SHA=%s\n' "$revision" > .deploy/release.env
compose=("${docker_cmd[@]}" compose --env-file "$repo_root/.env.production" --env-file "$repo_root/.deploy/release.env" -p aig-production -f "$repo_root/compose.prod.yaml")
"${compose[@]}" config --quiet
release_dir="$(mktemp -d "$repo_root/.deploy/releases/$revision.XXXXXX")"
"${docker_cmd[@]}" build --target frontend-export \
  --build-arg PUBLIC_API_BASE_URL=https://api.agentstrategy.online \
  --build-arg "APP_REVISION=$revision" --output "type=local,dest=$release_dir" .
# mktemp defaults to 0700; Apache must be able to traverse the release directory.
"${file_cmd[@]}" chmod -R a+rX "$release_dir"
"${compose[@]}" build api
if ! "${compose[@]}" up -d --wait --wait-timeout 180; then
  "${compose[@]}" logs --no-color --tail=100
  exit 1
fi
"${compose[@]}" exec -T api python - < scripts/production-smoke.py
container_id="$("${compose[@]}" ps -q api)"
actual_revision="$("${docker_cmd[@]}" inspect "$container_id" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')"
[[ "$actual_revision" == "$revision" ]] || { echo "API image revision mismatch." >&2; exit 1; }

# Publish the frontend only after the new API passes its checks; keep old releases.
if [[ -e dist && ! -L dist ]]; then
  mv dist ".deploy/dist-before-$(date +%s)"
fi
next_link=".deploy/dist-next-$$"
ln -s "$release_dir" "$next_link"
mv -Tf "$next_link" dist
printf '%s\n' "$revision" > .deploy/current-sha
echo "Deployed tested commit $revision to $repo_root."
