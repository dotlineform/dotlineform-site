"""Small semantic DOCX fixtures for Docs Import adapter tests."""

from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile


def _inline_image_xml(relationship_id: str, description: str, image_id: int) -> str:
    return f"""
    <w:p><w:r><w:drawing><wp:inline>
      <wp:docPr id="{image_id}" name="Image {image_id}" descr="{description}"/>
      <a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <pic:pic><pic:blipFill><a:blip r:embed="{relationship_id}"/></pic:blipFill></pic:pic>
      </a:graphicData></a:graphic>
    </wp:inline></w:drawing></w:r></w:p>
    """


def embedded_image_docx_bytes() -> bytes:
    """DOCX with supported, unsupported, and unreadable embedded images."""

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
            xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t>Word Image Import</w:t></w:r></w:p>
    {_inline_image_xml("rIdPng", "", 1)}
    {_inline_image_xml("rIdTiff", "Unsupported diagram", 2)}
    {_inline_image_xml("rIdMissing", "Unreadable diagram", 3)}
    <w:sectPr/>
  </w:body>
</w:document>
"""
    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="tiff" ContentType="image/tiff"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""
    package_relationships_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    document_relationships_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rIdPng" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/supported.png"/>
  <Relationship Id="rIdTiff" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/unsupported.tiff"/>
  <Relationship Id="rIdMissing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/missing.png"/>
</Relationships>
"""
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/></w:style>
</w:styles>
"""

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", package_relationships_xml)
        archive.writestr("word/_rels/document.xml.rels", document_relationships_xml)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", styles_xml)
        archive.writestr("word/media/supported.png", b"word-png-bytes")
        archive.writestr("word/media/unsupported.tiff", b"word-tiff-bytes")
    return output.getvalue()


def semantic_docx_bytes(
    *,
    include_title: bool = True,
    include_heading_6: bool = True,
    include_unknown_style: bool = True,
) -> bytes:
    title = (
        '<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr>'
        '<w:r><w:t>A Word Title</w:t></w:r></w:p>'
        '<w:p><w:pPr><w:pStyle w:val="Subtitle"/></w:pPr>'
        '<w:r><w:t>A useful subtitle</w:t></w:r></w:p>'
        if include_title
        else ""
    )
    heading_6 = (
        '<w:p><w:pPr><w:pStyle w:val="Heading6"/></w:pPr>'
        '<w:r><w:t>Clamped Section</w:t></w:r></w:p>'
        if include_heading_6
        else ""
    )
    unknown_style = (
        '<w:p><w:pPr><w:pStyle w:val="Mystery"/></w:pPr>'
        '<w:r><w:t>Unknown style body.</w:t></w:r></w:p>'
        if include_unknown_style
        else ""
    )
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {title}
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>First Section</w:t></w:r></w:p>
    <w:p>
      <w:r><w:t xml:space="preserve">Body with </w:t></w:r>
      <w:r><w:rPr><w:b/></w:rPr><w:t>bold</w:t></w:r>
      <w:r><w:t xml:space="preserve"> and </w:t></w:r>
      <w:r><w:rPr><w:i/></w:rPr><w:t>italic</w:t></w:r>
      <w:r><w:t xml:space="preserve"> plus </w:t></w:r>
      <w:hyperlink r:id="rIdLink"><w:r><w:t>a link</w:t></w:r></w:hyperlink>
      <w:r><w:t>.</w:t></w:r>
    </w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>Details</w:t></w:r></w:p>
    <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr><w:r><w:t>First item</w:t></w:r></w:p>
    <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr><w:r><w:t>Second item</w:t></w:r></w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Name</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>Value</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Alpha</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>1</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
    <w:p><w:pPr><w:pStyle w:val="Heading5"/></w:pPr><w:r><w:t>Deep Section</w:t></w:r></w:p>
    {heading_6}
    {unknown_style}
    <w:sectPr/>
  </w:body>
</w:document>
"""
    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>
"""
    package_relationships_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    document_relationships_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rIdNumbering" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
  <Relationship Id="rIdLink" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com/path" TargetMode="External"/>
</Relationships>
"""
    style_records = [
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>',
        '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/></w:style>',
        '<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/></w:style>',
        *[
            f'<w:style w:type="paragraph" w:styleId="Heading{level}"><w:name w:val="Heading {level}"/><w:basedOn w:val="Normal"/></w:style>'
            for level in range(1, 7)
        ],
        '<w:style w:type="paragraph" w:styleId="Mystery"><w:name w:val="Mystery Style"/><w:basedOn w:val="Normal"/></w:style>',
    ]
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        + "".join(style_records)
        + "</w:styles>"
    )
    numbering_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="0">
    <w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/></w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>
"""

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", package_relationships_xml)
        archive.writestr("word/_rels/document.xml.rels", document_relationships_xml)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", styles_xml)
        archive.writestr("word/numbering.xml", numbering_xml)
    return output.getvalue()
