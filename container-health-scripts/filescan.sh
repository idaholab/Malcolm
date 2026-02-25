#!/usr/bin/env bash

set -euo pipefail

( [[ "${PIPELINE_DISABLED:-false}" == 'true' ]] || [[ "${FILESCAN_DISABLED:-false}" == 'true' ]] ) && exit 0

JQ_EVAL=$(
    curl --fail --silent -XGET http://localhost:${FILESCAN_HEALTH_PORT:-8001}/health | \
        jq '.state == "running"
            and (
              .programs
              | with_entries(select(.key != "fileserve"))
              | ([ .[][].healthy ] | all)
            )
            and (
              .programs
              | with_entries(select(.key != "fileserve"))
              | ([ .[][].state == "running" ] | all)
            )
          ' 2>/dev/null
)
[[ "$JQ_EVAL" == "true" ]] && exit 0 && exit 1

