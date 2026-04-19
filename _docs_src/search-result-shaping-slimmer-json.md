---
doc_id: search-result-shaping-json-slimmer
title: "Search Result Shaping draft slimmer JSON"
last_updated: 2026-03-30
parent_id: ""
sort_order: 110
published: false
---
## Slimmer JSON

file: search-result-shaping-slimmer.json

A slimmer v1 should focus only on the immediate series/work redundancy problem and avoid broader diversity logic for now.

This v1 does only five things.

It knows the hierarchy.
Series are parents, works are children, and works point to their parent by series_id.

It protects obvious specific hits.
So grid 7 can still surface even if grid the series also matches.

It decides when parent-child consolidation should trigger.
That is for cases like grid, where the parent series is probably the intended representative result.

It collapses rather than fully hides child works.
That is usually safer for v1 because it reduces noise without making results feel mysteriously missing.

It falls back to plain rank order when no consolidation rule applies.
So it stays narrow in scope.

I would use this version first because it is:
easy to explain,
easy to test,
and much less likely to create side effects than a full diversification layer.

The corresponding plain-language rule set is:

If the query strongly matches a series name, treat the series as the representative result.

Keep at most a small number of visible child works when that happens.

Protect clearly specific child queries from being collapsed away.

If none of those conditions apply, do nothing special.

For implementation, this is the simplest useful pipeline:
	1.	rank results normally
	2.	detect whether a parent series is a strong direct match
	3.	find child works belonging to that parent
	4.	keep protected children
	5.	collapse the rest beyond the visible cap
	6.	otherwise leave results untouched

This is probably the right first site-specific shaping layer before attempting media-type diversity or broader family caps.

```
{
  "result_shaping": {
    "enabled": true,

    "grouping": {
      "parent_kind": "series",
      "child_kind": "work",
      "child_parent_field": "series_id"
    },

    "specific_match_protection": {
      "enabled": true,
      "protected_match_types": [
        "exact_id",
        "exact_title",
        "exact_title_phrase",
        "specific_child_title"
      ]
    },

    "parent_child_consolidation": {
      "enabled": true,
      "trigger_modes": [
        "exact_parent_title",
        "parent_title_phrase",
        "shared_family_stem"
      ],
      "child_handling_mode": "collapse",
      "max_visible_children_when_parent_matches": 2,
      "show_collapsed_child_count": true,
      "collapsed_child_label_template": "{count} works in this series"
    },

    "query_specificity": {
      "numeric_suffix_counts_as_specific": true,
      "extra_token_beyond_family_name_counts_as_specific": true
    },

    "fallback_behaviour": {
      "apply_plain_rank_order_when_no_consolidation_rule_triggers": true
    }
  }
}
```
