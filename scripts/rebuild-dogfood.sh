#!/usr/bin/env bash
#
# Rebuild the `dogfood` integration branch: reset it to main, then merge every
# topic branch given (or every local topic/* branch if none are named). Pushing
# it publishes ghcr.io/bothari/athenaeum:testing.
#
#   scripts/rebuild-dogfood.sh                       # all topic/* branches
#   scripts/rebuild-dogfood.sh topic/new-ui topic/x  # just these
#
# dogfood is THROWAWAY. It is never merged into anything and never branched off:
# topic branches graduate to main individually via PR, and dogfood is recreated
# from main each time. That is what lets a risky topic sit for months without
# blocking releases — and why force-pushing it is safe.
#
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [ "$#" -gt 0 ]; then
    topics=("$@")
else
    mapfile -t topics < <(git for-each-ref --format='%(refname:short)' refs/heads/topic/)
fi

if [ "${#topics[@]}" -eq 0 ]; then
    echo "No topic branches found (looked for topic/*). Nothing to integrate." >&2
    exit 1
fi

# Refuse to clobber uncommitted work: this switches branches.
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "Working tree is dirty. Commit or stash first." >&2
    exit 1
fi

starting_ref=$(git rev-parse --abbrev-ref HEAD)
restore() { git checkout -q "$starting_ref" 2>/dev/null || true; }
trap restore EXIT

git fetch -q origin
echo "Resetting dogfood to origin/main"
git checkout -q -B dogfood origin/main

failed=()
for t in "${topics[@]}"; do
    if git merge --no-edit -q "$t" 2>/dev/null; then
        echo "  merged  $t"
    else
        # Leave the rest mergeable rather than aborting the whole rebuild: a
        # conflicting topic is reported and skipped, not allowed to block the others.
        git merge --abort 2>/dev/null || true
        echo "  CONFLICT $t (skipped)"
        failed+=("$t")
    fi
done

echo
echo "dogfood = origin/main + $(( ${#topics[@]} - ${#failed[@]} )) topic branch(es)"
if [ "${#failed[@]}" -gt 0 ]; then
    echo "skipped (conflicts): ${failed[*]}"
fi
echo
echo "Push to publish :testing —"
echo "    git push -f origin dogfood"
