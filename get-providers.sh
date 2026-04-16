API_URL="http://opencode:***REMOVED***@localhost:9000/provider"
PROVIDERS_JSON=$(curl -fsSL "$API_URL")
CONNECTED_PROVIDERS=$(printf '%s\n' "$PROVIDERS_JSON" | jq -r '.connected[]')

{
    printf '%s\t%s\t%s\t%s\t%s\n' "PROVIDER" "MODEL" "INPUT COST" "OUTPUT COST" "REASONING"

    for provider in $CONNECTED_PROVIDERS; do
        PROVIDER_ROWS=$(printf '%s\n' "$PROVIDERS_JSON" | jq -r --arg provider "$provider" '
            def fmt_cost:
                if . == 0 then "0"
                else (((. * 10000) | round) / 10000 | tostring)
                end;

            first(.all[] | select(.id == $provider)) as $p
            | if ($p == null) or ((($p.models // {}) | length) == 0) then
                empty
              else
                ($p.models
                | to_entries
                | map(select(
                    (.value.capabilities.input.text // false) == true and
                    (.value.capabilities.output.text // false) == true and
                    (.value.capabilities.toolcall // false) == true
                  ))
                | sort_by([.value.cost.input // 0, .value.cost.output // 0])[]
                | [
                    $provider,
                    .value.id,
                    ((.value.cost.input // 0) | fmt_cost),
                    ((.value.cost.output // 0) | fmt_cost),
                    (if (.value.capabilities.reasoning // false) then "✓" else " " end)
                  ])
              end
            | @tsv
        ')

        if [ -n "$PROVIDER_ROWS" ]; then
            printf '%s\n' "$PROVIDER_ROWS"
        fi
    done
} | column -t -s "$(printf '\t')"
