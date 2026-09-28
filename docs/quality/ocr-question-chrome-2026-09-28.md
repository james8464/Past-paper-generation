# OCR question-paper ruling and final-page correction

The 2024 OCR source question papers use repeated **Arial 11pt full stops** in
`#231f20`, not pale dashed vector rules. The horizontal advance is approximately
3.056pt. Baseline pitch is 26.004pt on H446/02 PDF page 29 and H460/01 PDF page 17;
H460/02 PDF page 16 agrees. H460/03 page 19 varies between 24 and 25pt.

Local source filenames are `726572-question-paper-algorithms-and-programming.pdf`,
`726591-question-paper-microeconomics.pdf`,
`726592-question-paper-macroeconomics.pdf`, and
`726593-question-paper-themes-in-economics.pdf` in the ignored reference corpus.
Source pages were inspected visually and with glyph-position extraction.

The two shared OCR answer-rule classes now print metric-compatible 11pt dot
glyphs in the observed ink at the common 26pt pitch. Existing allocated answer
area heights and widths are preserved; fewer, correctly spaced rulings replace
the previous tightly packed faint dashes. This matches ruling appearance, not
every source page's exact count or vertical placement. Other boards are unchanged.

Both OCR question renderers record the page where the actual `END OF QUESTION
PAPER` paragraph is laid out. The page-end footer no longer adds `Turn over` on
that page; intervening odd pages retain it. No mark-scheme content is changed.

Five refreshed question PDFs retained page totals (CS: 28/32; Economics:
20/20/28) and end pages (27/29 and 17/16/25). Visual inspection confirmed dark,
regularly spaced ruling dots and no contradictory end-page footer. Regressions
exercise glyph size/colour/pitch, preserved answer-area height, and all five
papers' end-page/continuing-page footer behaviour.
