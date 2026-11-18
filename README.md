# dotlineform.com

This repository is the source for [dotlineform.com](https://www.dotlineform.com), deployed to GitHub Pages from the tracked static site root in `site/`.

The repo also contains locally run web-apps:

- **Studio**: manage the portfolio's catalogue data.
- **Docs Viewer**: edit, manage and publish documents to the site.

Start with the [Site Workflow Guide](documentation/guide/README.md) to see how these apps prepare and release the public site.

Use [Development](documentation/development/README.md) for implementation, review and verification guidance, and review [Working](documentation/_working/README.md) when choosing or resuming work.

## External Libraries And Resources

Key projects used by the website and local tools:

| Project | Use |
| --- | --- |
| [Lucide](https://lucide.dev/) | Source of several SVG interface icons; the repository also contains custom artwork. [Shared licence notice](docs-viewer/static/icons/LICENSE.lucide) |
| [markdown-it-py](https://github.com/executablebooks/markdown-it-py) | CommonMark parsing and document rendering |
| [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) and [lxml](https://lxml.de/) | HTML parsing for document import |
| [Bleach](https://github.com/mozilla/bleach) | HTML sanitization during import |
| [Mammoth](https://github.com/mwilliamson/python-mammoth) | Word document conversion to semantic HTML |
| [Pillow](https://python-pillow.org/) | Raster image handling and document thumbnails |
| [FFmpeg](https://ffmpeg.org/) | Image and media conversion |

Third-party resources retain their own licences. Pinned Python versions live in [requirements.txt](requirements.txt); [Runtime Dependencies](documentation/development/Runtime_Dependencies.md) explains dependency and tool ownership. Include the [shared Lucide notice](docs-viewer/static/icons/LICENSE.lucide) when copying or packaging its artwork. No icon-by-icon inventory or historical version reconstruction is required.
