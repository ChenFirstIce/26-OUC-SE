# Document Readability Audit

- Audited 2026-08-20 in `C:\dev\hospital-codex`; 8 non-Git files, no hidden files or read errors; no files were modified.
- Working extraction environment: `C:\ProgramData\anaconda3\python.exe` with `pypdf 6.16.1` and `openpyxl 3.1.5`; Microsoft Word COM is available for legacy `.doc` files. The user-preferred `D:\Users\admin\anaconda3\python.exe` was unavailable during this audit.
- `宣武医院韩璎教授发布的群公告.doc`: opened read-only through Word COM; complete text range read (609 characters); zero InlineShapes and Shapes.
- `1_信息填写模板(1)(2)(2).xlsx`: fully read using openpyxl (`read_only=True, data_only=False`); `Sheet1`, 1 row x 13 columns, 13 nonempty cells.
- Fully text-readable PDFs: `4.最新量表操作说明修订版.pdf` (12 pages), `5.CDR.pdf` (8 pages); each page produced extractable text and no image XObjects.
- `1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf`: 33 pages; every page has extractable text. Image XObjects exist on pages 17-20 and 30; their visual contents were not OCR'd/read.
- `2.量表模板.pdf`: 31 pages; image-based template. Every page has image XObjects; page 27 has no extractable text. Visual/image content was not OCR'd/read.
- `3.量表MoCA模板.pdf`: 1 page; limited extractable text (17 chars) and an image XObject. Visual/image content was not OCR'd/read.
- `6.ADAS-cog.pdf`: 5 pages; each has extractable text plus image XObjects. Visual/image content was not OCR'd/read.
- Scope boundary: byte-level access and textual content were verified for every file. Embedded or scanned visual content in the listed PDFs remains unreviewed because OCR/visual inspection was not performed.