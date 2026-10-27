#!/usr/bin/env bash
# Publish small diagnostics (job logs tail, QA report) to the ci-logs branch so they are readable without auth.
set -uo pipefail
JOB="$1"; shift; D=$(mktemp -d); git -C "$D" init -q; cd "$D"
git remote add origin "https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
for i in 1 2 3 4 5 6; do
  rm -rf "$D"/* ; (git fetch -q --depth 1 origin ci-logs && git checkout -q -B ci-logs FETCH_HEAD) || git checkout -q --orphan ci-logs
  mkdir -p "runs/${GITHUB_RUN_ID}/${JOB}"
  for f in "$@"; do [ -e "$f" ] && cp -r "$f" "runs/${GITHUB_RUN_ID}/${JOB}/" ; done
  git add -A && git -c user.name=wwb-ci -c user.email=ci@localhost commit -qm "logs ${GITHUB_RUN_ID} ${JOB}" || exit 0
  git push -q origin HEAD:ci-logs && exit 0; sleep $((i * 3))
done
