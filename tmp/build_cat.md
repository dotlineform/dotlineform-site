


(base) Michaels-MacBook-Pro:dotlineform-site dlf$ ./scripts/build_catalogue.py

==> Build Plan
Planner state: var/build_catalogue_state.json
Planner version: 4
Selected modes: moment, work, work_details
Workbook changes:
- works: 1 changed/new, 0 removed
- series: 1 changed/new, 0 removed
- work_details: 0 changed/new, 0 removed
- work_files groups: 0
- work_links groups: 0
- moments: 0 changed/new, 0 removed
Media changes:
- work sources: 1 changed/new, 0 removed
- work detail sources: 0 changed/new, 0 removed
- moment sources: 0 changed/new, 0 removed
Prose changes:
- work prose sources: 1 changed/new, 0 removed
- series prose sources: 1 changed/new, 0 removed
- moment prose sources: 0 changed/new, 0 removed
Planned scope:
- work media candidates: 1
- work detail media candidates: 0
- moment media candidates: 0
- work generation ids: 1
- moment generation ids: 0
- series generation ids: 1
- stale generated files to delete: 0
- stale local media files to delete: 0
- rebuild catalogue search: yes
Draft candidates (work): 1
Draft detail candidates (work_details): 0
Draft moment candidates (moment): 0

==> Copy Draft Work Files
+ /Users/dlf/miniconda3/bin/python3 /Users/dlf/Developer/dotlineform/dotlineform-site/scripts/copy_draft_media_files.py --mode work --ids-file /var/folders/6b/fp0n5d2d20n3_qz782zkzyjm0000gn/T/draft-pipeline-ys1p734j/draft_ids.txt --copied-ids-file /var/folders/6b/fp0n5d2d20n3_qz782zkzyjm0000gn/T/draft-pipeline-ys1p734j/copied_ids.txt --write
Copied:
/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/projects/simultaneous equations/00541 - model 7 - boundary condition.jpg
-> /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/make_srcset_images/01941.jpg
Wrote copied IDs manifest: /var/folders/6b/fp0n5d2d20n3_qz782zkzyjm0000gn/T/draft-pipeline-ys1p734j/copied_ids.txt (1 ids)
Work rows: 1, copied: 1, missing source: 0

==> Generate Srcset Derivatives
+ bash /Users/dlf/Developer/dotlineform/dotlineform-site/scripts/make_srcset_images.sh /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/make_srcset_images /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/srcset_images 4
[07:45:05] START 01941.jpg -> 01941
Wrote thumb: /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/srcset_images/thumb/01941-thumb-96.webp
Wrote thumb: /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/srcset_images/thumb/01941-thumb-192.webp
Wrote primary-800: /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/srcset_images/primary/01941-primary-800.webp
Wrote primary-1200: /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/srcset_images/primary/01941-primary-1200.webp
Wrote primary-1600: /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/srcset_images/primary/01941-primary-1600.webp
[07:45:13] DONE  01941 (thumb=2, primary-800=1, primary-1200=1, primary-1600=1)
Deleted 1 source file(s) from: /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/make_srcset_images
Done. Primaries written to: /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/srcset_images/primary
Done. Thumbnails written to: /Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/website/pipeline/works/srcset_images/thumb
Derivative report:
  written total: 5 (thumb=2, primary-800=1, primary-1200=1, primary-1600=1)
  dry-run total: 0 (thumb=0, primary-800=0, primary-1200=0, primary-1600=0)

==> Skip Work Detail Copy/Srcset
No work-detail media candidates in this run.

==> Skip Moment Copy/Srcset
No moment-media candidates in this run.

==> Generate Work Pages
+ /Users/dlf/miniconda3/bin/python3 /Users/dlf/Developer/dotlineform/dotlineform-site/scripts/generate_work_pages.py /Users/dlf/Developer/dotlineform/dotlineform-site/data/works.xlsx --work-ids-file /var/folders/6b/fp0n5d2d20n3_qz782zkzyjm0000gn/T/draft-pipeline-ys1p734j/generate_ids.txt --moment-ids-file /var/folders/6b/fp0n5d2d20n3_qz782zkzyjm0000gn/T/draft-pipeline-ys1p734j/generate_moment_ids.txt --series-ids simultaneous-equations --write
[1/1] WRITE (work): _works/01941.md
Updated status to 'published' for 1 row(s).
Set published_date for 1 row(s).
Updated work width_px/height_px for 1 row(s).

Done. Wrote: 1 works. Skipped: 1939 works.
Downloads copied: 0. Missing/unresolved: 0.
Workbook: /Users/dlf/Developer/dotlineform/dotlineform-site/data/works.xlsx
Note: if the workbook is open in Excel, close and reopen it to see changes.
Traceback (most recent call last):
  File "/Users/dlf/Developer/dotlineform/dotlineform-site/scripts/generate_work_pages.py", line 3069, in <module>
    main()
  File "/Users/dlf/Developer/dotlineform/dotlineform-site/scripts/generate_work_pages.py", line 1927, in main
    primary_work_id = require_series_primary_work_id(
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/dlf/Developer/dotlineform/dotlineform-site/scripts/generate_work_pages.py", line 927, in require_series_primary_work_id
    raise ValueError(f"Series '{sid}' missing primary_work_id")
ValueError: Series 'simultaneous-equations' missing primary_work_id

Pipeline failed at command: /Users/dlf/miniconda3/bin/python3 /Users/dlf/Developer/dotlineform/dotlineform-site/scripts/generate_work_pages.py /Users/dlf/Developer/dotlineform/dotlineform-site/data/works.xlsx --work-ids-file /var/folders/6b/fp0n5d2d20n3_qz782zkzyjm0000gn/T/draft-pipeline-ys1p734j/generate_ids.txt --moment-ids-file /var/folders/6b/fp0n5d2d20n3_qz782zkzyjm0000gn/T/draft-pipeline-ys1p734j/generate_moment_ids.txt --series-ids simultaneous-equations --write
(base) Michaels-MacBook-Pro:dotlineform-site dlf$ 