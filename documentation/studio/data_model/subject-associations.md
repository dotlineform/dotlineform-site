---
draft: false
doc_id: d-20260927-135604-05446e
title: Subject Associations
added_date: "2026-09-27 13:56:04"
last_updated: "2026-10-20"
summary: Retired document Subject contract; current Projects associations use Catalogue token references.
parent_id: d-20260423-000000-d015e6
---
# Subject Associations

Document Subjects were retired on 2026-10-20. Source `work_id`/`folder_path` declarations, scalar management/public `subject`, assignment controls, Subject-derived thumbnails and Work Document Coverage have no active producer or consumer. Catalogue Work identity and canonical Work-to-Series membership remain separate active contracts.

[Reports](../Reports.md#current-reports) owns Projects' explicit snapshot lifecycle and Work/Gallery token → Series → physical-folder associations. [Semantic Tokens Architecture](../Semantic_Tokens_Architecture.md#catalogue-identity-and-document-associations) owns explicit token identity and the intentional Work relationship/Gallery mention distinction. [Media And Asset Handling](../Media_And_Asset_Handling.md#assigned-document-thumbnails) owns independent document thumbnail copies and generated `has_thumbnail`.

[Subject Retirement](../Subject_Retirement.md) retains the rationale and reference examples; its [delivery](../deliveries/Subject_Retirement_Delivery.md) records the completed source cleanup/reset and evidence limits. There is no Subject compatibility alias or replacement Subject index. This file is retained as a retirement pointer pending an explicit repository-document retirement decision.
