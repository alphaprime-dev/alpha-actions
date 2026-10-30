#!/usr/bin/env bash
set -euo pipefail

if git diff --quiet -- "$FILE_PATH"; then
    echo "No manifest changes to commit."
    exit 0
fi

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add -- "$FILE_PATH"
git commit -m "$COMMIT_MESSAGE"

for attempt in 1 2 3 4 5; do
    if git push origin "HEAD:$TARGET_BRANCH"; then
        exit 0
    fi

    if [ "$attempt" -eq 5 ]; then
        break
    fi

    git fetch origin "$TARGET_BRANCH"
    if ! git rebase FETCH_HEAD; then
        git rebase --abort
        echo "Manifest update conflicts with remote changes." >&2
        exit 1
    fi
    sleep "$attempt"
done

echo "Failed to push manifest update after 5 attempts." >&2
exit 1
