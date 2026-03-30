---
doc_id: search-result-shaping-json
title: Search Result Shaping draft JSON
last_updated: 2026-03-30
parent_id: search-result-shaping
sort_order: 10
---

## Draft JSON

file: search-result-shaping.json

specific_match_protection:
Protects strong direct matches from being hidden by consolidation or diversity rules. This is what keeps grid 7 visible even if grid the series is also a strong match.

grouping_dimensions:
Defines which fields the shaping layer uses to understand hierarchy and repetition. This is where site structure is exposed to runtime shaping.

parent_child_consolidation:
Controls the grid versus grid 1, grid 2 problem. It says when a parent can stand in for many children, what counts as an independently meaningful child, and whether children are hidden, demoted, or collapsed.

family_caps:
Stops one family from flooding the top results even when no single parent-child consolidation rule fires cleanly.

diversity:
Handles the “50 photos bury 1 video” problem. It does not hard-boost video; it says that when scores are close, a distinct kind or media type should be allowed to surface.

query_specificity:
Provides the heuristics needed to distinguish broad queries from specific ones. This is important because shaping should behave differently for grid and grid 7.

fallback_behaviour:
Ensures the shaping layer gets out of the way when no site-specific shaping rule should apply.

A few design notes:

1. This config should drive a dedicated shapeResults() stage after ranking, not the ranking engine itself.
2. Keep these as policy values only. The logic for interpreting things like "shared_family_stem" or "strong_non_family_field_match" should remain in code.
3. his is probably a phase-2 or phase-3 config surface rather than something to implement immediately, because it depends on stable ranking semantics and stable relationship fields.

```
{
  "result_shaping": {
    "enabled": true,

    "specific_match_protection": {
      "enabled": true,
      "protected_match_types": [
        "exact_id",
        "exact_title",
        "exact_title_phrase",
        "specific_child_title"
      ],
      "min_score_to_protect": 0
    },

    "grouping_dimensions": {
      "family_field": "series_id",
      "kind_field": "kind",
      "media_type_field": "media_type",
      "title_field": "title"
    },

    "parent_child_consolidation": {
      "enabled": true,
      "parent_kind": "series",
      "child_kind": "work",
      "parent_id_field": "id",
      "child_parent_field": "series_id",

      "broad_parent_query_modes": [
        "exact_parent_title",
        "parent_title_phrase",
        "shared_family_stem"
      ],

      "child_independent_match_modes": [
        "exact_child_title",
        "exact_child_id",
        "child_title_with_distinguishing_token",
        "strong_non_family_field_match"
      ],

      "child_handling_mode": "collapse",
      "max_visible_children_when_parent_matches": 2,
      "show_collapsed_child_count": true,
      "collapsed_child_label_template": "{count} works in this series"
    },

    "family_caps": {
      "enabled": true,
      "cap_mode": "soft",
      "limits": [
        { "within_top_n": 10, "max_per_family": 2 },
        { "within_top_n": 20, "max_per_family": 4 }
      ],
      "bypass_for_specific_queries": true
    },

    "diversity": {
      "enabled": true,
      "dimensions": ["kind", "media_type"],
      "apply_when_score_delta_lte": 15,
      "max_consecutive_same_dimension_value": {
        "kind": 3,
        "media_type": 4
      },
      "prefer_unrepresented_dimension_values": true
    },

    "query_specificity": {
      "numeric_suffix_counts_as_specific": true,
      "extra_token_beyond_family_name_counts_as_specific": true,
      "min_extra_distinguishing_tokens": 1
    },

    "fallback_behaviour": {
      "apply_plain_rank_order_when_no_shaping_rule_triggers": true
    }
  }
}
```
