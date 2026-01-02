# Extract Book Sections Directive

## Goal
The goal is to systematically read HTML content from URLs defined in a target markdown file and extract specific sections into a structured text document.

## Inputs
1.  **Target File**: A markdown file in `knowledge_base/` (e.g., `knowledge_base/targets_nfpa99.md`) containing a list of URLs.
2.  **HTML Structure**: The source HTML from these URLs must contain specific classes as defined in the rules below.

## Tools/Scripts
-   `execution/extract_sections.py`: A Python script that:
    1.  Reads the target file.
    2.  Fetches HTML content from each URL.
    3.  Parses the HTML according to the defined rules.
    4.  Appends the extraction to a text file in `Books/`.

## Output
-   A text file in the `Books/` directory (e.g., `Books/nfpa99.txt`) containing the extracted and formatted information.

## Rules
The extraction logic follows these 10 text section types:

### Level Zero Sections (Prefix `# `)
For elements matching `<class="c-section-wrapper__fragment">` AND `<class="c-section-wrapper -level-zero>`:
1.  **Moved with Changes**: If title has `<class="c-section-detail__title -changes-moved-with-changes">`, print `# ` + Title + Body (`<class="c-section-detail__body">`).
2.  **Moved**: If title has `<class="c-section-detail__title -changes-moved">`, print `# ` + Title + Body.
3.  **Addition**: If title has `<class="c-section-detail__title -changes-addition">`, print `# ` + Title + Body.
4.  **No Changes**: If title has `<class="c-section-detail__title -changes-no">`, print `# ` + Title + Body.
5.  **Yes Changes**: If title has `<class="c-section-detail__title -changes-yes">`, print `# ` + Title + Body.

### Level One Sections (No Prefix)
For elements matching `<class="c-section-wrapper__fragment">` AND `<class="c-section-wrapper -level-one>`:
6.  **No Changes**: Orderly print `<class="c-sub-section-detail__title -changes-no">` then `<class="c-sub-section-detail__body">`.
7.  **Yes Changes**: Orderly print `<class="c-sub-section-detail__title -changes-yes">` then `<class="c-sub-section-detail__body">`.
8.  **Addition**: Orderly print `<class="c-sub-section-detail__title -changes-addition">` then `<class="c-sub-section-detail__body">`.

### Level Two Sections (No Prefix)
For elements matching `<class="c-section-wrapper__fragment">` AND `<class="c-section-wrapper -level-two>`:
9.  **Addition**: Orderly print `<class="c-sub-sub-section-detail__title -changes-addition">` then `<class="c-sub-sub-section-detail__body">`.
10. **Mixed**: Orderly print `<class="c-sub-sub-section-detail__title -changes-no">`, `<class="c-sub-sub-section-detail__title -changes-yes">`, `<class="c-sub-sub-section-detail__title -changes-addition">`, then `<class="c-sub-sub-section-detail__body">`.

### Enhanced Content
-   Always print content from `<class="c-sub-section-detail__enhanced-content">` if available after the sections.

## Execution Steps
1.  Identify the target file (e.g., `knowledge_base/targets_nfpa99.md`).
2.  Run `python execution/extract_sections.py --input knowledge_base/targets_nfpa99.md`.
3.  Verify the output in `Books/nfpa99.txt`.
