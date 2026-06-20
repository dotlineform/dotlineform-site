---
doc_id: hd
title: "HD"
added_date: 2026-06-20
last_updated: 2026-06-20
---
# HD

```
`df -h /System/Volumes/Data`

```
Filesystem      Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s5   460Gi   383Gi    56Gi    88%    1.7M  590M    0%   /System/Volumes/Data
```

`du -hd 1 ~ 2>/dev/null | sort -h`

```
 22M	/Users/dlf/.anaconda
 25M	/Users/dlf/.bundle
 25M	/Users/dlf/.npm
 73M	/Users/dlf/.dropbox
173M	/Users/dlf/.rbenv
237M	/Users/dlf/.volta
254M	/Users/dlf/.pyenv
301M	/Users/dlf/Documents
352M	/Users/dlf/.vscode
562M	/Users/dlf/Developer
732M	/Users/dlf/.cache
743M	/Users/dlf/Movies
1.5G	/Users/dlf/.codex
1.6G	/Users/dlf/miniconda3
2.3G	/Users/dlf/Music
 35G	/Users/dlf/Library
 84G	/Users/dlf/Pictures
128G	/Users/dlf
```

Run these next:

`sudo du -xhd 1 /System/Volumes/Data 2>/dev/null | sort -h`

```
  0B	/System/Volumes/Data/cores
  0B	/System/Volumes/Data/mnt
  0B	/System/Volumes/Data/pkg
  0B	/System/Volumes/Data/sw
  0B	/System/Volumes/Data/Volumes
1.0K	/System/Volumes/Data/home
 84K	/System/Volumes/Data/MobileSoftwareUpdate
3.1M	/System/Volumes/Data/usr
4.3M	/System/Volumes/Data/.PreviousSystemInformation
385M	/System/Volumes/Data/.adobeTemp
686M	/System/Volumes/Data/.fseventsd
1.1G	/System/Volumes/Data/opt
7.2G	/System/Volumes/Data/System
8.5G	/System/Volumes/Data/private
 20G	/System/Volumes/Data/Library
 39G	/System/Volumes/Data/Applications
216G	/System/Volumes/Data/Users
293G	/System/Volumes/Data
```

`df -h /System/Volumes/Data`

```
Filesystem      Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s5   460Gi   382Gi    56Gi    88%    1.7M  592M    0%   /System/Volumes/Data
```

```
`tmutil listlocalsnapshots /System/Volumes/Data`

Snapshots for disk /System/Volumes/Data:
```
  
```
du -hd 1 ~ 2>/dev/null | sort -h
...
 22M	/Users/dlf/.anaconda
 25M	/Users/dlf/.bundle
 25M	/Users/dlf/.npm
 73M	/Users/dlf/.dropbox
173M	/Users/dlf/.rbenv
237M	/Users/dlf/.volta
254M	/Users/dlf/.pyenv
301M	/Users/dlf/Documents
352M	/Users/dlf/.vscode
562M	/Users/dlf/Developer
732M	/Users/dlf/.cache
743M	/Users/dlf/Movies
1.5G	/Users/dlf/.codex
1.6G	/Users/dlf/miniconda3
2.3G	/Users/dlf/Music
 84G	/Users/dlf/Pictures
123G	/Users/dlf/Library
216G	/Users/dlf
```

next:

```
du -hd 1 ~/Library 2>/dev/null | sort -h
...
157M	/Users/dlf/Library/HTTPStorages
165M	/Users/dlf/Library/Photos
2.0G	/Users/dlf/Library/Group Containers
2.1G	/Users/dlf/Library/Logs
4.5G	/Users/dlf/Library/Application Support
 12G	/Users/dlf/Library/Containers
 15G	/Users/dlf/Library/Caches
 88G	/Users/dlf/Library/Mobile Documents
123G	/Users/dlf/Library
(base) Michaels-MacBook-Pro:dotlineform-site dlf$ 

```

```
du -hd 1 ~/Pictures 2>/dev/null | sort -h
 84G	/Users/dlf/Pictures
 84G	/Users/dlf/Pictures/Photos Library.photoslibrary

```

```
diskutil apfs listSnapshots /System/Volumes/Data
No snapshots for disk3s5
```

```
du -hd 1 ~/Library/Application\ Support 2>/dev/null | sort -h
...
5.4M	/Users/dlf/Library/Application Support/GIMP
7.2M	/Users/dlf/Library/Application Support/DropboxElectron
 13M	/Users/dlf/Library/Application Support/com.apple.mobileAssetDesktop
 15M	/Users/dlf/Library/Application Support/com.apple.spotlight
 17M	/Users/dlf/Library/Application Support/Ableton
 26M	/Users/dlf/Library/Application Support/Codex
 32M	/Users/dlf/Library/Application Support/AddressBook
 32M	/Users/dlf/Library/Application Support/com.apple.musicapps.content
 33M	/Users/dlf/Library/Application Support/CEF
 58M	/Users/dlf/Library/Application Support/Native Instruments
 92M	/Users/dlf/Library/Application Support/SaalDesignSoftwareUK
106M	/Users/dlf/Library/Application Support/OneDrive
208M	/Users/dlf/Library/Application Support/Microsoft Edge
301M	/Users/dlf/Library/Application Support/Adobe
324M	/Users/dlf/Library/Application Support/Blurb
328M	/Users/dlf/Library/Application Support/com.adobe.dunamis
783M	/Users/dlf/Library/Application Support/Signal
911M	/Users/dlf/Library/Application Support/com.apple.wallpaper
1.2G	/Users/dlf/Library/Application Support/Code
4.5G	/Users/dlf/Library/Application Support

```

```
du -hd 1 ~/Library/Application\ Support 2>/dev/null | sort -h
...
 13M	/Users/dlf/Library/Application Support/com.apple.mobileAssetDesktop
 15M	/Users/dlf/Library/Application Support/com.apple.spotlight
 17M	/Users/dlf/Library/Application Support/Ableton
 26M	/Users/dlf/Library/Application Support/Codex
 32M	/Users/dlf/Library/Application Support/AddressBook
 32M	/Users/dlf/Library/Application Support/com.apple.musicapps.content
 33M	/Users/dlf/Library/Application Support/CEF
 58M	/Users/dlf/Library/Application Support/Native Instruments
 92M	/Users/dlf/Library/Application Support/SaalDesignSoftwareUK
106M	/Users/dlf/Library/Application Support/OneDrive
208M	/Users/dlf/Library/Application Support/Microsoft Edge
301M	/Users/dlf/Library/Application Support/Adobe
324M	/Users/dlf/Library/Application Support/Blurb
328M	/Users/dlf/Library/Application Support/com.adobe.dunamis
783M	/Users/dlf/Library/Application Support/Signal
911M	/Users/dlf/Library/Application Support/com.apple.wallpaper
1.2G	/Users/dlf/Library/Application Support/Code
4.5G	/Users/dlf/Library/Application Support

```

```
du -hd 1 ~/Library/Containers 2>/dev/null | sort -h
...
6.6M	/Users/dlf/Library/Containers/com.automattic.SimplenoteMac
8.1M	/Users/dlf/Library/Containers/com.apple.iWork.Pages
 11M	/Users/dlf/Library/Containers/com.apple.iWork.Numbers
 11M	/Users/dlf/Library/Containers/com.apple.motionappApp
 12M	/Users/dlf/Library/Containers/fr.handbrake.HandBrakeXPCService
 14M	/Users/dlf/Library/Containers/com.apple.AppStore
 15M	/Users/dlf/Library/Containers/com.charliemonroe.Downie-4
 20M	/Users/dlf/Library/Containers/com.microsoft.Outlook
 23M	/Users/dlf/Library/Containers/com.microsoft.OneDrive.FileProvider
 51M	/Users/dlf/Library/Containers/com.microsoft.m365copilot
 64M	/Users/dlf/Library/Containers/com.amazon.Lassen
 69M	/Users/dlf/Library/Containers/com.apple.wallpaper.agent
 69M	/Users/dlf/Library/Containers/com.visualcomputing.picarrange
 93M	/Users/dlf/Library/Containers/com.microsoft.Powerpoint
 94M	/Users/dlf/Library/Containers/com.apple.photoanalysisd
110M	/Users/dlf/Library/Containers/com.adobe.accmac.ACCFinderSync
129M	/Users/dlf/Library/Containers/com.apple.siri.media-indexer
133M	/Users/dlf/Library/Containers/com.microsoft.Word
136M	/Users/dlf/Library/Containers/com.microsoft.Excel
285M	/Users/dlf/Library/Containers/com.apple.mediaanalysisd
305M	/Users/dlf/Library/Containers/com.apple.geod
2.4G	/Users/dlf/Library/Containers/com.microsoft.onenote.mac
3.4G	/Users/dlf/Library/Containers/com.apple.AMPArtworkAgent
3.9G	/Users/dlf/Library/Containers/com.readitlater.PocketMac
 12G	/Users/dlf/Library/Containers

```

```
du -hd 1 ~/Library/Caches 2>/dev/null | sort -h
...
 11M	/Users/dlf/Library/Caches/com.apple.Spotlight
 12M	/Users/dlf/Library/Caches/com.apple.CloudTelemetry
 12M	/Users/dlf/Library/Caches/com.apple.installer.osinstallersetupd
 13M	/Users/dlf/Library/Caches/SharedImageCache
 16M	/Users/dlf/Library/Caches/com.apple.parsecd
 20M	/Users/dlf/Library/Caches/statsig-cache
 28M	/Users/dlf/Library/Caches/com.canva.affinity
 30M	/Users/dlf/Library/Caches/com.apple.helpd
 58M	/Users/dlf/Library/Caches/pip
 87M	/Users/dlf/Library/Caches/GeoServices
 99M	/Users/dlf/Library/Caches/org.videolan.vlc
136M	/Users/dlf/Library/Caches/com.openai.chat
182M	/Users/dlf/Library/Caches/com.apple.Music
204M	/Users/dlf/Library/Caches/Homebrew
223M	/Users/dlf/Library/Caches/SiriTTS
238M	/Users/dlf/Library/Caches/Microsoft Edge
520M	/Users/dlf/Library/Caches/ms-playwright
767M	/Users/dlf/Library/Caches/Plex
4.8G	/Users/dlf/Library/Caches/Adobe
7.2G	/Users/dlf/Library/Caches/Adobe Camera Raw 2
 15G	/Users/dlf/Library/Caches
```