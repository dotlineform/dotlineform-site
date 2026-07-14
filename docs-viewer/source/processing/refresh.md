---
doc_id: refresh
title: refresh
added_date: "2026-07-14 17:47"
last_updated: "2026-07-14 17:47"
parent_id: sketch-250309a-ink
---
# refresh


Originally, the refreshRequested flag was used to trigger a one-time refresh of the curve when the refresh button was clicked. That flag would cause the curve to be drawn only in that frame and then be cleared in subsequent frames.

Now, the approach has changed: instead of using a one-time refresh trigger, the refresh button directly generates and stores the new curve in a global variable (currentCurve). The draw() function then continuously redraws the curve every frame if currentCurve is not null. This persistent storage means that there’s no longer a need for a flag to indicate when to refresh—the curve is always available and drawn until a new one is generated.

In short, refreshRequested isn’t needed any more because the drawing logic now relies on the presence of currentCurve rather than a transient flag.
