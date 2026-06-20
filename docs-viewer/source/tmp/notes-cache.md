---
doc_id: notes-cache
title: "notes cache"
added_date: 2026-06-20
last_updated: 2026-06-20
---
# Notes cache  
  
`~/Library/Containers/com.apple.Notes/Data/Library/Caches/CloudKit/.../Assets` is a **Notes/iCloud CloudKit asset cache**. Notes has cached a huge amount of attachment-related data locally. Apple Notes can store attachments such as photos, videos, PDFs and other files, and iCloud Notes syncs those notes across devices and iCloud.com.
Because it is under:  
```
.../Library/Caches/CloudKit/.../Assets
```
it is much more likely to be a **local sync/cache problem** than your canonical Notes database. But do not delete it while Notes or iCloud sync is active.

Suggested safe route:

1. First confirm your notes exist in iCloud:Open Notes on another Apple device or at iCloud.com and check that the important folders and attachments are present. Apple confirms iCloud Notes can be viewed and edited across Apple devices and iCloud.com when Notes is enabled for iCloud.
2. Quit Notes completely.
```
osascript -e 'quit app "Notes"'

```
3. Stop iCloud/CloudKit processes temporarily, or simply reboot before doing anything. A reboot is the lower-risk option.
4. Move the huge cache folder aside rather than deleting it immediately:
```
mkdir -p ~/Desktop/Notes_Cache_Hold

mv ~/Library/Containers/com.apple.Notes/Data/Library/Caches/CloudKit/ceda50979a5eafafaef76d6ec1b5b00d0d277e6d/Assets \
   ~/Desktop/Notes_Cache_Hold/Assets

```
5. Reopen Notes and let it rebuild/sync. Then check:
```
df -h /System/Volumes/Data
du -hd 1 ~/Library/Containers/com.apple.Notes 2>/dev/null | sort -h

```
6. If Notes behaves normally after a day or two, delete the held cache:
```
rm -rf ~/Desktop/Notes_Cache_Hold/Assets

```
A slightly more cautious version is to rename rather than move:
```
mv ~/Library/Containers/com.apple.Notes/Data/Library/Caches/CloudKit/ceda50979a5eafafaef76d6ec1b5b00d0d277e6d/Assets \
   ~/Library/Containers/com.apple.Notes/Data/Library/Caches/CloudKit/ceda50979a5eafafaef76d6ec1b5b00d0d277e6d/Assets.old

```
Then reboot and open Notes.

Do **not** delete these folders casually:
```
~/Library/Containers/com.apple.Notes/Data/Library/Notes
~/Library/Group Containers/group.com.apple.notes

```
Those are more likely to contain actual Notes databases and metadata.

This also explains why Finder briefly reports “1 GB left” and later “50 GB”: macOS can clear caches and temporary storage when space is needed, but a giant app-specific CloudKit cache can distort the calculation until the system catches up. Apple’s storage guidance notes that macOS may clear safe caches and logs when space is needed, and that iCloud-backed data can be stored locally or made available on demand.



```
du -sh ~/Library/Group\ Containers/group.com.apple.notes
8.7G	/Users/dlf/Library/Group Containers/group.com.apple.notes

```

```
du -sh ~/Library/Containers/com.apple.Notes/Data/Library/Caches/CloudKit/*/Assets 2>/dev/null
 87G	/Users/dlf/Library/Containers/com.apple.Notes/Data/Library/Caches/CloudKit/ceda50979a5eafafaef76d6ec1b5b00d0d277e6d/Assets
 71M	/Users/dlf/Library/Containers/com.apple.Notes/Data/Library/Caches/CloudKit/e42781ad6d1f9e018bd7d1abda2cd28a3ee5d403/Assets
```

To see what makes up the 8.7 GB actual Notes container, run:
```
du -hd 1 ~/Library/Group\ Containers/group.com.apple.notes 2>/dev/null | sort -h

```

```
du -hd 1 ~/Library/Group\ Containers/group.com.apple.notes 2>/dev/null | sort -h
 68K	/Users/dlf/Library/Group Containers/group.com.apple.notes/Thumbnails
 10M	/Users/dlf/Library/Group Containers/group.com.apple.notes/Library
7.9G	/Users/dlf/Library/Group Containers/group.com.apple.notes/Accounts
8.7G	/Users/dlf/Library/Group Containers/group.com.apple.notes
```

Then list the largest files inside it:

```
find ~/Library/Group\ Containers/group.com.apple.notes -type f -size +50M -print0 2>/dev/null \
| xargs -0 du -h \
| sort -h
```

```
find ~/Library/Group\ Containers/group.com.apple.notes -type f -size +50M -print0 2>/dev/null \
> | xargs -0 du -h \
> | sort -h
 68M	/Users/dlf/Library/Group Containers/group.com.apple.notes/Accounts/06E1D01D-3068-4DE8-BF9F-9159E2EC657D/Media/48CD2177-7208-4AAB-A173-B7E44829D5D3/1_33DB18A2-5B91-4A90-94C3-2ED26F07DCDD/qrnt (dots)/qrnt (dots) : dots concentric_1.jpg
 92M	/Users/dlf/Library/Group Containers/group.com.apple.notes/Accounts/06E1D01D-3068-4DE8-BF9F-9159E2EC657D/FallbackPDFs/49456ED4-265B-45D4-84A0-3E62A0321AFF/4_8AFDBFAA-954A-45F9-82CC-DEBB3956ADA5/FallbackPDF.pdf
116M	/Users/dlf/Library/Group Containers/group.com.apple.notes/Accounts/06E1D01D-3068-4DE8-BF9F-9159E2EC657D/Media/E1E4BF8A-0171-43D0-A801-9471C857F8CC/1_47F6DDB7-B751-49B9-B636-461658D51846/qrnt.zip
238M	/Users/dlf/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite
402M	/Users/dlf/Library/Group Containers/group.com.apple.notes/Accounts/06E1D01D-3068-4DE8-BF9F-9159E2EC657D/Media/48CD2177-7208-4AAB-A173-B7E44829D5D3/1_33DB18A2-5B91-4A90-94C3-2ED26F07DCDD/qrnt (dots).zip
624M	/Users/dlf/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite-wal
4.1G	/Users/dlf/Library/Group Containers/group.com.apple.notes/Accounts/06E1D01D-3068-4DE8-BF9F-9159E2EC657D/Media/42096F5C-6550-4FE9-BEFE-6CFFBB9B0BEA/1_C3062550-3434-4881-BEB8-DB24EC1D8A96/The Crucible.mp4

```

For the 87 GB CloudKit cache, I would move it aside rather than delete immediately:
```
osascript -e 'quit app "Notes"'

mkdir -p ~/Desktop/Notes_Cache_Hold

mv ~/Library/Containers/com.apple.Notes/Data/Library/Caches/CloudKit/ceda50979a5eafafaef76d6ec1b5b00d0d277e6d/Assets \
   ~/Desktop/Notes_Cache_Hold/Assets
```

Then reboot, open Notes, and check:
```
df -h /System/Volumes/Data

du -sh ~/Library/Containers/com.apple.Notes/Data/Library/Caches/CloudKit/*/Assets 2>/dev/null

du -sh ~/Library/Group\ Containers/group.com.apple.notes

```

Do not manually delete or move:
```
~/Library/Group Containers/group.com.apple.notes
~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite*

```
Those are actual Notes data. The 87 GB Caches/CloudKit/.../Assets folder is the cleanup candidate.

For one suspect file, inspect it:
```
ls -lhT "/full/path/to/the/file.mp4"
mdls "/full/path/to/the/file.mp4"

```
```
ls -lhT "/Users/dlf/Library/Group Containers/group.com.apple.notes/Accounts/06E1D01D-3068-4DE8-BF9F-9159E2EC657D/Media/42096F5C-6550-4FE9-BEFE-6CFFBB9B0BEA/1_C3062550-3434-4881-BEB8-DB24EC1D8A96/The Crucible.mp4”

```

```
mdls "/Users/dlf/Library/Group Containers/group.com.apple.notes/Accounts/06E1D01D-3068-4DE8-BF9F-9159E2EC657D/Media/42096F5C-6550-4FE9-BEFE-6CFFBB9B0BEA/1_C3062550-3434-4881-BEB8-DB24EC1D8A96/The Crucible.mp4”

```