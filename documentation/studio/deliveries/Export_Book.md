---
draft: false
doc_id: d-20261117-195407-c3ee13
title: Export Book
added_date: "2026-11-17 19:54:07"
last_updated: "2026-11-17"
summary: Compare PDF and EPUB for whole-Book export from the saved Tree and for reading downloaded editions.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Export Book

Export a complete Book from Manage as a local file for review and optional distribution. Living Memory needs an export alongside its web edition. Moments needs an export from a Book that has never been published. The first format and its release criteria remain open. [Portfolio Books](Portfolio_Books.md)

## Shared Authoring And Export

The saved Book Tree supplies the order. The export includes the ready authored TOC in its Tree position, ready Root and Part chapters, and ready **Both** or **Export only** opening and back matter. It omits drafts, private Sections, empty Parts and **Web only** pages. Generate the TOC from that same selection and respect the Book’s Part-heading link setting. A ready TOC host and its chapters remain exportable when the host is excluded from web publication. [Book editions](Sub_Scope_Index_Architecture.md#book-editions)

Manage supplies the selected Book and format. The exporter resolves the saved Working edition, reads the selected bodies and their referenced media, and writes the finished artifact to a local destination. Keep document IDs and heading fragments through preparation so both formats can turn links between included pages into internal destinations. Review links outside the selection for intended online targets. The current Collection Export supplies an HTML snapshot of checked rows, with its own flat index. Its document, media and link preparation are candidates for reuse where they fit. [Collection Export](Export.md)

## Creating The Files

| Decision | PDF | Reflowable EPUB |
| --- | --- | --- |
| Layout | Compose a fixed page with print styles. Choose page size, margins, typography and breaks, then check long pieces and images against those dimensions. The same pages can be viewed onscreen and printed. | Package styled XHTML in an EPUB container. Text can wrap and paginate to fit the screen and the reader’s settings. Keep headings, paragraphs, verse and illustrations meaningful as the layout changes. |
| Assembly | Combine the selected pages into one print HTML document, embed the required media in the resulting PDF and give chapters and linked headings distinct anchors. The earlier Playwright experiment makes Chromium PDF rendering a candidate. Verify the generated links, outline and reading order in the file. [Playwright PDF API](https://playwright.dev/python/docs/api/class-page#page-pdf) | Package the cover, chapter XHTML, stylesheet and referenced media with title, author, language and identifier metadata. Use Tree order for the EPUB spine. Derive the app’s navigation and the in-book TOC from the same entries, and resolve chapter links to packaged files and fragments. [EPUB 3.3](https://www.w3.org/TR/epub-33/) |
| Review | Open the finished PDF in a browser and a device viewer. Check the cover, page breaks, image detail, selectable text and working TOC and heading links. Check reading order and text alternatives as part of reviewing a tagged PDF. | Check package conformance with EPUBCheck, then open the EPUB in the intended reader apps. Check the cover, navigation, heading links, illustrations and line wrapping with a narrow viewport and larger text. [EPUBCheck](https://github.com/w3c/epubcheck) |

PDF is a first candidate for Moments if the position of words and lines is central to the edition. Try its preformatted verse and axis-aligned text in reflowable EPUB to see which visual relationships survive on a phone-sized screen. EPUB also supports fixed layout, which trades reflow for control of the page and still uses an EPUB reader. Living Memory can help evaluate the benefit of reflow for longer prose. [Moments export typography](Export.md#artifact-contract) · [EPUB layout](https://www.w3.org/TR/epub-33/#sec-fixed-layouts)

## Opening A Download

| Reader’s device | PDF | EPUB |
| --- | --- | --- |
| **Mac or Windows** | The link may open in the browser’s PDF viewer. If the file downloads, open it from Downloads in the browser or a PDF app such as Preview on Mac. [Firefox PDF viewer](https://support.mozilla.org/en-US/kb/view-pdf-files-firefox-or-choose-another-viewer) · [Apple Preview](https://support.apple.com/guide/books/import-books-audiobooks-or-pdfs-ibkseed72068/mac) | On Mac, open the saved file with Books or use **File → Import** in Books. On Windows, install an EPUB reader such as Thorium Reader and import the saved file. [Apple Books](https://support.apple.com/guide/books/import-books-audiobooks-or-pdfs-ibkseed72068/mac) · [Thorium Reader](https://www.edrlab.org/software/thorium-reader/) |
| **iPhone or iPad** | Open the PDF from the browser or find the saved file in Files and open it in Preview on supported versions. [iPhone Preview](https://support.apple.com/en-lamr/guide/iphone/iph7a0cdad0c/26/ios/26) · [iPad Preview](https://support.apple.com/en-kw/guide/ipad/ipad3322bc9a/ipados) | Save the EPUB to Files and tap it to open in Apple Books, if installed. [Apple Books on iPhone and iPad](https://support.apple.com/en-au/108362) |
| **Android** | Open the file in the browser or a PDF app. Google Play Books can also import PDFs when PDF uploading is enabled. [Chrome on Android](https://support.google.com/chrome/answer/16215622?co=GENIE.Platform%3DAndroid) · [Google Play Books](https://support.google.com/googleplay/answer/11012086?co=GENIE.Platform%3DAndroid) | Find the saved file in Downloads or Files and open it with an EPUB reader. In Google Play Books, use **Open with → Play Books** and find the book under **Library → Uploads**. [Google Play Books](https://support.google.com/googleplay/answer/11012086?co=GENIE.Platform%3DAndroid) |
| **Dedicated e-reader** | Kobo supports transferring an unprotected PDF over USB. The page stays fixed, so check how it fits on the intended screen. [Kobo transfer instructions](https://help.kobo.com/hc/en-us/articles/360024775093-Add-non-protected-PDF-and-ePub-files-to-your-Kobo-eReader-using-your-computer) | Transfer an unprotected EPUB to a compatible Kobo over USB. For Kindle, submit the EPUB through **Send to Kindle** and open it from the Kindle library. [Kobo transfer instructions](https://help.kobo.com/hc/en-us/articles/360024775093-Add-non-protected-PDF-and-ePub-files-to-your-Kobo-eReader-using-your-computer) · [Amazon transfer instructions](https://digprjsurvey.amazon.com/csad/help/node/TCUBEdEkbIhK07ysFu) |

A public link should name its format, for example **Download Moments (PDF)** or **Download Moments (EPUB)**. A short EPUB instruction can tell readers to open the saved file in their ebook app. PDF is already supported by **Add file**. For EPUB, add the file type to the attachment flow and verify the delivered download retains its `.epub` filename and uses `application/epub+zip`. Attach the reviewed file to the existing public Moments page or, for Living Memory, to a public introduction, then release it through ordinary Save and Publish. [Docs Images And Assets](Docs_Images_And_Assets.md#add-a-new-image-or-download) · [EPUB 3.3](https://www.w3.org/TR/epub-33/)

## Before Choosing The First Format

- Use a small Moments selection to compare a short piece, a long or axis-aligned poem, and an illustration. Note where PDF page breaks and EPUB wrapping affect the reading.
- Use Living Memory to check an opening page before the TOC, an illustrated chapter, a link to another chapter’s heading and one example of edition-specific matter. Use Moments to verify that a publication-excluded host can supply the complete export, including working contents and links.
- Try the actual download and opening flow on desktop and mobile. Add an e-reader check if that audience is a reason to offer EPUB. Choose the first format and agree on the minimum layout and reader checks before implementing it.
