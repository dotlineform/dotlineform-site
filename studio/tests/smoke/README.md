# Studio Smoke Boundaries

This directory contains three retained browser entrypoints plus one small server harness:

- `studio_catalogue_route.py`: local Catalogue route boot and same-origin service isolation.
- `studio_tag_route.py`: local Tag route boot and same-origin service isolation.
- `public_catalogue_route.py`: one checked public Work route without local Studio capability.
- `studio_route_smoke_support.py`: server startup and route-ready waiting only.

Do not recreate browser module-contract suites, API mutation scripts, multi-route product-data matrices, theme interaction tests, or UI workflow narratives here. Deterministic behavior belongs under `studio/tests/python/`; normal UI behavior is accepted manually.

Use [Browser Smoke Testing](/docs/?scope=studio&doc=d-20260501-000000-49b626) before proposing another retained boundary.
