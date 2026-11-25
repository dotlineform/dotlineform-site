# Library Editorial Review

The Library gathers material developed in conversations, from edited chat extracts to summaries. *Living Memory* explores whether a selection can form a coherent reading sequence. This document brings together the structural edits, editorial choices and scans for that work. See the [Library and Book Style Guide](doc_styles.md) for the presentation rules and proposed tokens.

## Decide What to Keep as a Tool

Use a **one-off pass** when it answers a bounded question or makes a finite set of edits. Save the resulting content or evidence when it will be used again. Use a **report** when you repeatedly need to see material across documents to decide what to work on. Use an **authoring workflow** when the same choice recurs while editing a document and belongs in its saved source. Start with the existing controls where they can express the choice.

| Area | One-off work | Durable home or workflow |
| --- | --- | --- |
| Lists and panels | Review representative imports and rewrite list-heavy passages during chapter editing. | Use standard Markdown for ordinary lists. Try the proposed panel directive for short examples, comparisons and definitions. |
| Titles, subtitles and headings | Audit the imported heading structure and review compact headings in a few essays. | Use ordered heading levels, an optional subtitle style and the proposed compact heading annotation. |
| Inline labels | Identify useful sequences and recurring terms in the imported designs. | Start with text conventions. Adopt structured tags when there is a defined use such as filtering or term discovery. |
| References | The Library extraction and removal pass is complete. Reuse its JSON for per-document shortlisting. | Keep the inventory as Working editorial data. Maintain Selected Reading and any book bibliography as authored pages. |
| Spelling and grammar | Run a candidate scan by batch and review changes in context. | Follow a small house word list and spelling convention during normal editing. |
| Images | Use the thumbnail snapshot to select a sample and classify the work. | Use Thumbs in Docs Media for recurring cross-document review. Replace or annotate individual images in Source. |
| Tables | Inventory the sizing overrides and check representative dense tables at narrow widths. | Use existing Table options in Source. Consider one default at the agreed scope if small type consistently works. |
| Index and glossary | Collect subject and term candidates from the selected material. | Curate navigable pages in the Library and in the relevant Book edition. |

## Prose and Section Review

Build paragraphs where a passage explains a relationship, makes an argument or changes direction. Keep bullets where the reader benefits from scanning parallel items, and use numbering when the order matters or an item is referred to by number.

When reviewing a short main section, decide what the material needs in the document or the eventual chapter.

| Editorial decision | When to use it |
| --- | --- |
| Expand section | Keep the `h2` when it identifies a major topic. Add context or explanation so a lay reader can follow it. |
| Compact `h2` | Keep the section in the outline when it marks a quieter transition in a continuous essay. |
| Panel or merge | Use a panel for a self-contained example, comparison or definition. If most sections are fragments of this kind, consider incorporating them into a more complete document or chapter. |

Review figure titles in context. Move wording that describes the figure into its caption. Keep a heading when it introduces a passage containing the figure. For material intended as a fragment, choose the section heading during chapter compilation. [Image editing](../../reference/Media_And_Asset_Handling.md#add-a-new-image-or-download)

## Heading Cleanup

- The `h4` pass changed 207 headings across 59 Library documents into bold labels or genuine `h2` and `h3` sections. In the three sections with images, the optional circuit illustration received a bold label and the two longer passages in *Quantum compilers* received `h3`s.
- The `h3` pass promoted 298 headings across 82 documents. It treated each sequence of peer headings together and retained existing subsections in the mixed outlines. The [compact heading candidate list](#compact-heading-candidates-from-the-h3-cleanup) records the affected documents.

Review absent or repeated `h1`s and any other skipped levels during the passage edit. Retain or update existing links to a heading where applicable.

## H2 Section Scan

The [Library editorial review workbook](Library_Editorial_Review.xlsx) is a snapshot of all 433 Working Library documents. Its **Library** sheet joins the heading cleanup list by document ID and adds counts for each scan signal. **H2 review** identifies the individual sections and their source lines, with fields for the editorial decision and notes. **Scan rules** records the thresholds.

The scan flagged 774 of 1,160 main sections. The signals are short prose, list-shaped material and little explanatory prose. They can overlap. The list signal includes both Markdown lists and runs of short unbulleted entries. Review the section in context to decide whether it needs expansion, a compact heading or a panel.

Start with the recent heading cleanup by filtering **H3 promotions** above zero. Within that set, **Majority pattern** identifies 25 documents with mostly list-shaped sections and 13 with mostly short prose. Keep future scan results and editorial notes tied to the document ID so a fresh scan can update the evidence while carrying the notes forward.

## References and Technical Review

The one-off Library pass removed 317 headed reference sections from 316 documents. The Docs workspace inventory at `working/source/collections/library/reference-inventory.json` holds 2,412 candidate entries, grouped by document ID. It includes a reusable prompt, any original numbering and table notes, and source paths and line ranges for recovery from commit `cad35800db4f`. The bibliographic details are transcribed from the original material. Existing in-text cues were retained for the editing pass.

Use the edited document and its inventory record to ask ChatGPT for a short reading list. Give each selected source a sentence explaining what it offers, and check the identity and bibliographic details of the shortlist. A document can have a short local list when the sources help the reader follow a quotation, an explanation or a figure. A topic-based Library **Selected Reading** page can give readers a route into the material. A Book bibliography can consolidate repeat entries across the chapters that actually appear in that edition.

Treat technical accuracy as part of editing chapters whose purpose is technical explanation. Focus review on the claims, definitions, equations and figures the explanation depends on. Use the bibliography to give readers a route into the subject and keep explicit source relationships where the prose already relies on them.

## Spelling, Grammar and Notation Review

A read-only search can find likely variants across hundreds of documents. Review the resulting candidates by batch before changing source. During a chapter edit, check the rhythm of the prose, transitions left over from chat turns, and consistent use of symbols and terms. Keep automated checks focused on repeatable patterns that the editor can recognise and verify quickly. [House spelling and notation](doc_styles.md#spelling-and-notation)

## Image Review and Triage

The one-off Library contact sheet showed the value of a visual pass without opening each document. Use **Docs Media → Working → Thumbs** with the Library filter to browse the saved results and open larger previews. **Referenced by** links to the documents that use each image. [Docs Media](/docs/?doc=d-20260812-212735-6d9cf3) · [Docs Media inventory](../../reference/Media_And_Asset_Handling.md#docs-media-inventory-report)

For the first pass, use a temporary list of images marked **Keep**, **Repair**, **Redraw** or **Remove**. Record a short decision against the owning document and filename as needed. Start with a small batch from chapters likely to be edited. Consider saved review status only if a second pass needs to pick up outstanding decisions across sessions.

## Table Review

Do a one-off inventory of the Library settings and review a few narrow and wide examples before deciding whether to bulk-adjust the Markdown or make small type the default at the agreed scope. [Table presentation](doc_styles.md#tables)

Tables earn their space when rows and columns help compare like items. Shorten crowded headings and keep lengthy explanations in prose.

## Index and Glossary

Give the Library a curated subject index with links to useful documents. Try placing it near the top of the Library if it becomes a regular route into the collection. Make a separate glossary for terms readers may want to look up, with a short definition and links to the places that explain or use the term.

For *Living Memory*, try a glossary and selective subject index in the back matter. Link to included chapters or headings in the edition. Use chapter links for reflowable EPUB and decide on page references when there is a fixed-page edition. Start with authored Markdown pages assembled from a one-off extraction of candidate subjects and terms. Consider a generator when the material has dependable term or heading anchors and rebuilding it has become a recurring job. [Book editions](../../reference/Collections_And_Books.md#book-editions) · [Export Book proposal](../Export_Book.md)

## First Editorial Pass

Choose a few chapters likely to be used together in *Living Memory*. Give each a prose pass, shortlist its reading where useful, and review its figures and tables at the intended reading width. Use Docs Media Thumbs to find the qubit figures and the denser map for the first image review. Record the rules that work across the sample here.

## Compact Heading Candidates from the H3 Cleanup

The one-off Library pass promoted 298 headings across 82 documents from third-level headings to main sections. All the promoted headings use ordinary Markdown. The 68 flat outlines are the first candidates to review when the compact style is available. In the 14 mixed outlines, review compact styling for individual main sections alongside their existing subsections.

| Library document | Promoted headings | Outline after the edit |
| --- | ---: | --- |
| [Aliveness of Images](/docs/?collection=library&doc=d-20261017-172422-3921c8) | 6 | Flat |
| [Archetypal Patterns](/docs/?collection=library&doc=d-20261017-174644-6d7f78) | 5 | Flat |
| [Brain machines](/docs/?collection=library&doc=d-20261017-231636-6bdc1b) | 4 | With subsections |
| [Brain Structure](/docs/?collection=library&doc=d-20261018-111445-823b77) | 7 | Flat |
| [Brains & Organisms Inside a Mathematical Universe](/docs/?collection=library&doc=d-20261018-163309-a8c088) | 5 | Flat |
| [Bridging Systems](/docs/?collection=library&doc=d-20261018-164432-3924d1) | 9 | Flat |
| [Buddhism, Neuroscience](/docs/?collection=library&doc=d-20261018-171054-0e8f96) | 4 | Flat |
| [Consciousness Windows Across Scales](/docs/?collection=library&doc=d-20261018-184252-5c4879) | 5 | Flat |
| [Continuity Without Memory — Neuroscience × Buddhism](/docs/?collection=library&doc=d-20261018-191608-b3e36d) | 4 | Flat |
| [Default mode network](/docs/?collection=library&doc=d-20261122-192029-cdd891) | 1 | Flat |
| [Does Rebirth Imply Memory Outside the Brain?](/docs/?collection=library&doc=d-20261025-091719-c87850) | 1 | Flat |
| [Emergence Ladder](/docs/?collection=library&doc=d-20261025-214006-ff0888) | 5 | Flat |
| [Entropy & Evolution Under Two Cosmologies](/docs/?collection=library&doc=d-20260809-130120-3054b0) | 5 | Flat |
| [Evolutionary Psychology](/docs/?collection=library&doc=d-20260809-130120-a7bc91) | 3 | With subsections |
| [Feedback and Correction: Evolution’s Long Arc of Honesty](/docs/?collection=library&doc=d-20261027-165149-c32c62) | 5 | Flat |
| [Feedback Loops — Balancing Expansion and Refinement in the Translation Membrane](/docs/?collection=library&doc=d-20261027-165837-39cc63) | 5 | Flat |
| [Feedback Loops — Mathematical Form vs. Neurological Implementation](/docs/?collection=library&doc=d-20261027-165633-1b8015) | 2 | Flat |
| [From Observer to Participant](/docs/?collection=library&doc=d-20261123-121511-76ff9d) | 5 | Flat |
| [Geometry in quantum mechanics](/docs/?collection=library&doc=d-20261114-134541-0b8636) | 4 | With subsections |
| [Gödel Numbers](/docs/?collection=library&doc=d-20261114-162155-29c4b1) | 3 | Flat |
| [Gödel Theory — Importance & Relevance](/docs/?collection=library&doc=d-20261114-163605-1eeb31) | 4 | Flat |
| [Gödel — Reflective Summary](/docs/?collection=library&doc=d-20261114-163045-dbfff1) | 3 | Flat |
| [Gödel — Why & How](/docs/?collection=library&doc=d-20261114-163925-f409a3) | 4 | Flat |
| [Higher‑D Unification](/docs/?collection=library&doc=d-20261121-142007-cb09d2) | 2 | Flat |
| [Hopfield Attractor Networks — Resilience & Failure Adaptation](/docs/?collection=library&doc=d-20261017-221439-845822) | 2 | Flat |
| [Hopfield Attractor-Network Memory](/docs/?collection=library&doc=d-20261017-220718-82b513) | 1 | With subsections |
| [How many living creatures are there on earth?](/docs/?collection=library&doc=d-20261018-202531-230319) | 4 | Flat |
| [How Memories Are Stored](/docs/?collection=library&doc=d-20261121-145945-589f50) | 2 | With subsections |
| [Image-Making as Translation](/docs/?collection=library&doc=d-20261121-160859-105931) | 2 | With subsections |
| [Infantile Amnesia — Why We Don't Remember Early Years](/docs/?collection=library&doc=d-20261121-173604-14106e) | 7 | Flat |
| [Insect Swarm Brain](/docs/?collection=library&doc=d-20261121-180540-e2e0f7) | 1 | Flat |
| [Integrated Epistemology Model — Buddhism, Kant, Science](/docs/?collection=library&doc=d-20261121-181059-c8d6f5) | 1 | Flat |
| [Intention as Probabilistic Autonomy](/docs/?collection=library&doc=d-20261121-182223-81fbfc) | 3 | Flat |
| [Irrational Geometry of Reality](/docs/?collection=library&doc=d-20261121-184044-1dbf14) | 4 | Flat |
| [Is Gödel’s Theorem Itself Unprovable?](/docs/?collection=library&doc=d-20261114-163358-297d16) | 3 | Flat |
| [Jung on Memory](/docs/?collection=library&doc=d-20261121-190847-3c362b) | 5 | Flat |
| [Jung × I Ching — Synchronicity & Archetypes over Select · Change · Reconstruct](/docs/?collection=library&doc=d-20261121-190054-070cca) | 3 | Flat |
| [Jung’s Alchemy × Memory](/docs/?collection=library&doc=d-20261121-185036-ebf486) | 6 | Flat |
| [Key Characteristics of Networks](/docs/?collection=library&doc=d-20261123-103822-aade99) | 1 | Flat |
| [Language as Measurement](/docs/?collection=library&doc=d-20261121-192131-bbe801) | 4 | Flat |
| [Laws as the Memory of the Universe](/docs/?collection=library&doc=d-20261121-201317-09046f) | 7 | Flat |
| [Markov Theory and Memory](/docs/?collection=library&doc=d-20261121-224324-e32352) | 5 | Flat |
| [Mathematics as illusion](/docs/?collection=library&doc=d-20261121-230830-ba12a6) | 4 | With subsections |
| [Maths × Poetry](/docs/?collection=library&doc=d-20261121-230030-a29586) | 4 | Flat |
| [Memory - Replay vs Statistical Reconstruction](/docs/?collection=library&doc=d-20261122-215339-c0604a) | 1 | Flat |
| [Memory and Mind](/docs/?collection=library&doc=d-20261122-190840-0a1918) | 1 | Flat |
| [Memory as Randomness](/docs/?collection=library&doc=d-20261122-191758-67dfca) | 1 | Flat |
| [Memory as Randomness](/docs/?collection=library&doc=d-20261122-214830-8fa76a) | 6 | Flat |
| [Memory in language](/docs/?collection=library&doc=d-20261122-193606-aec47b) | 1 | With subsections |
| [Memory × Reflection × Persistence in Dementia](/docs/?collection=library&doc=d-20261122-184643-14a8e9) | 5 | Flat |
| [Memory — Conclusions](/docs/?collection=library&doc=d-20261122-202745-bbd874) | 6 | With subsections |
| [Memory ↔ Consciousness — Scale, Timeline, and Theory Matrix](/docs/?collection=library&doc=d-20261122-204728-0b2d10) | 2 | Flat |
| [Memory, Verification, and the Limits of Knowing](/docs/?collection=library&doc=d-20261122-212126-c21802) | 3 | Flat |
| [Metaphysics](/docs/?collection=library&doc=d-20261123-084011-332c90) | 1 | Flat |
| [Metaphysics — Timeline](/docs/?collection=library&doc=d-20261123-083731-7a95f2) | 1 | Flat |
| [Mind & Memory - Field Map](/docs/?collection=library&doc=d-20261123-091426-2cd5ec) | 8 | With subsections |
| [Mind–Models–World](/docs/?collection=library&doc=d-20261123-091819-3f1bc0) | 3 | Flat |
| [Multiverse Theories](/docs/?collection=library&doc=d-20261123-103335-e7577f) | 1 | Flat |
| [Neurophenomenology](/docs/?collection=library&doc=d-20261123-113855-2b18f2) | 4 | Flat |
| [Niche Construction — Organisms Shape Selection](/docs/?collection=library&doc=d-20261123-114837-2929ff) | 3 | Flat |
| [Nirvāṇa, Change, and Growth](/docs/?collection=library&doc=d-20261123-115527-cab93d) | 3 | Flat |
| [No Coherence from Chaos](/docs/?collection=library&doc=d-20261123-115916-a22765) | 5 | Flat |
| [Pattern Separation vs Completion](/docs/?collection=library&doc=d-20261123-133223-a3f2be) | 1 | Flat |
| [Philosophies of Mathematics — Platonism · Formalism · Nominalism · Structuralism (One‑Pager + Bios)](/docs/?collection=library&doc=d-20261121-224841-1ecb90) | 4 | Flat |
| [Predictive Processing & Free-Energy Principle](/docs/?collection=library&doc=d-20261123-144659-1f5f6b) | 3 | Flat |
| [PyNN](/docs/?collection=library&doc=d-20261017-232727-55cf60) | 4 | Flat |
| [Quantitative brain](/docs/?collection=library&doc=d-20261123-155148-260753) | 1 | With subsections |
| [Quantum Brain Proposals](/docs/?collection=library&doc=d-20261123-160434-ed104a) | 2 | With subsections |
| [Quantum Computers - Hardware size and complexity](/docs/?collection=library&doc=d-20261117-221331-50d695) | 5 | With subsections |
| [Qubit error correction](/docs/?collection=library&doc=d-20261123-182214-eaef38) | 2 | Flat |
| [Reflection, Recursion, and Infinite Descent](/docs/?collection=library&doc=d-20261123-183359-28b5be) | 5 | Flat |
| [Representationalism](/docs/?collection=library&doc=d-20261123-205738-008517) | 4 | Flat |
| [Sleep vs Anaesthesia](/docs/?collection=library&doc=d-20261123-221617-465c78) | 7 | Flat |
| [SpiNNaker](/docs/?collection=library&doc=d-20261017-232312-733b50) | 8 | With subsections |
| [Tao → I Ching → Select · Change · Reconstruct](/docs/?collection=library&doc=d-20261124-175356-253018) | 3 | Flat |
| [The Halting Problem — Computation and the Limits of Knowledge](/docs/?collection=library&doc=d-20261117-221004-d9269a) | 5 | Flat |
| [The Inversion of Adaptation](/docs/?collection=library&doc=d-20261121-183434-7f149a) | 2 | Flat |
| [Untraceability of Memory — Neuroscience × Physics × Buddhism](/docs/?collection=library&doc=d-20261124-211320-8bb46b) | 3 | Flat |
| [What is a field (physics)?](/docs/?collection=library&doc=d-20261027-171439-913752) | 1 | Flat |
| [What is the Smallest Unit of Memory?](/docs/?collection=library&doc=d-20261122-210938-b96b52) | 5 | Flat |
| [Why a Truly Universal Language Is Unattainable](/docs/?collection=library&doc=d-20261124-204035-4291d1) | 2 | Flat |
| [Why Pursue Abstraction? The Purpose and Meaning of Set Theory (Essay + Citations)](/docs/?collection=library&doc=d-20261124-231149-e1063d) | 6 | Flat |
