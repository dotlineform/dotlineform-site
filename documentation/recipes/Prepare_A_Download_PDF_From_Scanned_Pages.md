# Prepare a download PDF from scanned pages

Use the source JPGs for image quality and a Finder-created PDF for the approved page order and layout. Keep a separate download copy so you can make another size from the original scans whenever needed.

## Steps

1. Use Finder’s **Create PDF** action on the source JPGs to assemble the book. Check the page order in Preview, including the front cover, interior pages or spreads, and back cover.
2. Open the Finder PDF with `pypdf`. For the image-per-page PDF used here, each page embedded its original JPEG byte for byte. Match each embedded JPEG to its source file so the replacement goes on the correct page.
3. Use Pillow to resize each source JPG proportionally with Lanczos resampling. Set the chosen pixel limit on the **long edge**, whether that edge is horizontal or vertical. Encode at the chosen JPEG quality with optimisation and retain the source colour profile.
4. In a copy of the Finder PDF, replace each embedded JPEG and update its pixel dimensions. Retain the PDF page dimensions, image placement, and colour profiles. The spreads then occupy the same space at **Actual Size** in Preview, with image resolution affecting how sharp they look when enlarged.
5. Save under a distinct download filename. Render the PDF with Poppler’s `pdftoppm` and check the page count, order, and orientation. Inspect a text-heavy spread at reading size and check the front and back covers. Record the finished file size.

## Worked example

*nerve (formaldehyde form)* has two portrait covers and 17 landscape spreads. The original Finder PDF was **18.03 MB**. The text-heavy spread used for comparison remained legible at reading size with the smaller setting.

| Long edge | Pillow JPEG quality | Finished size | Use |
| --- | --- | --- | --- |
| 1,600 px | 80 | 2.26 MB | General reading download |
| 2,000 px | 85 | 3.93 MB | More detail for zooming |

At 1,600 px, quality 75 was estimated at 1.99 MB. Quality 80 kept a little more detail for about 0.27 MB.

## If the task becomes a script

Take the approved layout PDF, source JPGs, long-edge limit, JPEG quality, and output path as inputs. Use the layout PDF to determine source order, save a separate PDF, and report the page count and file size. Keep the reading-size check on the finished copy.
