It’s not just “more data exists.” The current full build is already materially dominated by page rendering, not by the `/series/` JSON or index pages.

Current measurements:
- Full build: about `42s`
- Profile hot spots:
  - `_layouts/work.html`: `16.4s` across `1031` pages
  - `_layouts/work_details.html`: `14.2s` across `1679` pages
  - `_layouts/default.html`: `4.5s`
  - `_layouts/series.html`: negligible at `0.038s`

So the main story is page-count growth plus expensive per-page work in the two biggest collections. At 30% content, if the site grows similarly without changes, a full build getting into the `~1.5-3 minute` range later would not surprise me.

The clearest remedial action is in those two layouts. Both are doing repeated `site.static_files | where: "path", ... | first` checks per page, which means Jekyll scans the static file list thousands of times during one build. That is the kind of thing that scales worse than plain content growth.

My assessment:
- No immediate emergency. `42s` for a full Jekyll build of this shape is still workable.
- But there is real technical debt to pay down before the site is near complete.
- The `/series/` sorting change is not the problem.

What I’d do next, in order:
1. Remove the per-page `site.static_files` scans and replace them with precomputed metadata.
   - Best option: generate `has_work_details_json` into the source/front matter or a build data file.
   - This is the highest-confidence win.
2. Use `--incremental --watch` for local iteration only.
   - Good developer-time improvement.
   - Not a production fix, and Jekyll incremental can be imperfect, so keep full builds for final verification.
3. Re-profile after the static-file lookup fix.
   - If build time is still climbing badly, then evaluate whether every `work_detail` page truly needs standalone HTML output, or whether some can remain JSON-driven.
4. Keep an eye on repeated Liquid work in high-volume layouts.
   - With 2700+ generated pages already, even small per-page costs matter.

If you want, I can do the next step now: profile-driven cleanup of those `site.static_files` lookups so we can see how much build time that alone saves.
