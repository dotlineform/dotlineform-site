---
draft: false
doc_id: d-20261124-213832-f8d2c1
title: Docs Viewer Math Rendering
added_date: "2026-11-24 21:38:32"
last_updated: "2026-11-24"
summary: Design for authoring TeX in Docs Viewer and generating native MathML for the reader.
parent_id: d-20261118-151521-a0f9c3
---
# Docs Viewer math rendering

**Status:** Implemented and checked on the Library draft *qubit calculations*. This note records the rendering boundary and the reasons for it. [Authoring reference](../reference/Source_Editing.md#math)

## Source syntax

Keep TeX in the document's Markdown. Use `$…$` for inline expressions and `$$` on separate lines around a display equation. A literal dollar can be escaped as `\$`. Code spans and code blocks retain their literal text. In table cells, use TeX delimiters such as `\lvert` and `\rangle` for ket notation so the Markdown table can identify its column separators.

```markdown
The initial state is $\lvert 0\rangle$.

$$
H\lvert 0\rangle = \frac{1}{\sqrt{2}}\left(\lvert 0\rangle + \lvert 1\rangle\right)
$$
```

## Build and reader responsibilities

The Docs document builder configures the shared Python Markdown renderer with the `dollarmath` plugin from `mdit-py-plugins`. The plugin recognises the delimiters and supplies the expression and display mode to the `latex2mathml` callback. Links discovery uses those same rules and treats equations as text, so it can find authored Markdown links without converting every equation a second time. [Docs Markdown integration](../../docs-viewer/build/docs_builder/math_rendering.py) · [Markdown plugin API](https://mdit-py-plugins.readthedocs.io/en/stable/_modules/mdit_py_plugins/dollarmath/index.html) · [Python requirements](../../requirements.txt)

The callback takes the converter's MathML tree, decodes symbol references within text nodes and serialises the tree with XML escaping. Characters such as `<` and `&` stay text inside the generated HTML. The callback strips link, class and style attributes supplied by TeX commands so expressions emit presentation markup. Conversion errors identify the document and a short expression excerpt. [Converter implementation](https://github.com/roniemartinez/latex2mathml/blob/master/latex2mathml/converter.py) · [Document rendering](../../docs-viewer/build/docs_builder/payloads.py)

The Python dependencies run during generation and the result is included in the document's `content_html`. A Docs-owned image summary installs the same math rules on the restricted summary formatter and uses its inline render path. Publication carries the generated HTML through the usual document artifact. Manage and Public display the equations with the browser's native MathML rendering. [Summary formatter](../../docs-viewer/build/docs_builder/summary_formatting.py) · [Working generation and publication](../reference/Builder.md)

## First document

The Library draft *qubit calculations* (`d-20261124-212917-2cf593`) was the first document converted. The source cleanup marked up bare TeX, removed imported math markers and restored table cells from the surrounding Bloch sphere and Deutsch algorithm explanations.

The exact Working build produced 103 inline and 21 display expressions without warnings. Generated HTML inspection confirmed fractions, roots, sums, subscripts and ket notation. The local reader loaded all expressions in the native MathML namespace, including 47 within table cells. Focused checks covered escaped dollars, fenced code and literal comparison signs. [Exact generation](../reference/Builder.md#exact-generation)
