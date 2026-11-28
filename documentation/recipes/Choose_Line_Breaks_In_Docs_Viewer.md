# Choose line breaks in Docs Viewer

Use the **Source editor** to decide whether a passage should flow as prose, break at specific places, or preserve every authored line. [Source editing](../reference/Source_Editing.md)

| What to write in Source | What the reader sees |
| --- | --- |
| A single newline within a paragraph | A word space. The browser wraps the text to fit the reading column. |
| A blank line | A new paragraph. |
| A backslash or two spaces immediately before a newline | A visible line break within the same paragraph. |

In *nerve (abattoir)*, single newlines make the lines easy to see in Source and give the rendered text its continuous flow.

## Break selected lines

Put a backslash at the end of each line you want to break. It is easy to spot when you revisit the source. Ordinary Markdown formatting still works in the paragraph.

```markdown
light across the table\
late in the afternoon
```

## Preserve every line in a passage

Wrap the passage in the existing Moments markup. This works in Texts too. The style preserves authored newlines and spaces and lets long lines wrap as the reading column narrows. [Reader stylesheet](../../docs-viewer/static/css/docs-viewer.css)

```html
<pre class="moment-text">
light across the table
late in the afternoon
</pre>
```

Markdown emphasis and link syntax inside this block display as written. Use backslashes in ordinary Markdown when the passage needs that formatting.

Save in Source, then check the rendered passage at reading width to see where the authored breaks and automatic wrapping fall.
