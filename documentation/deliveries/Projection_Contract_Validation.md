---
draft: false
doc_id: d-20260523-224407-911c73
title: Projection Contract Validation
added_date: "2026-05-23 22:44:07"
last_updated: "2026-11-18"
parent_id: d-20260524-214228-7247ef

---
# Projection Contract Audit

Former cross-boundary projection audit and manifest. [Current projection enforcement](../reference/Projection_Contract.md#current-enforcement)

`tests/audits/projection_contract.py` validated the shape of `tests/contracts/projection_contract.json` and scanned selected assets for prohibited source references and selected JSON keys. Its private-field scan targeted the retired Catalogue archive. The manifest also retained former Analysis scope paths and the retired document-locations output.

The audit and manifest were retired with the site suite. Both former paths are available at the recovery revision. [Site test retirement](Review_Test_Policy_And_Checks.md#recovery)
