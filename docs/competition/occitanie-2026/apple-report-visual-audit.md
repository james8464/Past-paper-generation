# Occitanie dossier visual audit against Apple reports

Updated 3 October 2026. This is a design comparison, not an endorsement by Apple or a claim that the project uses Apple's brand.

## References and scope

I downloaded and inspected the [Apple Environmental Progress Report 2026](https://www.apple.com/environment/pdf/Apple_Environmental_Progress_Report_2026.pdf), [Apple Education Initiative Impact Report 2024](https://www.apple.com/education-initiative/pdf/2024-Impact-Report.pdf) and [Longevity by Design](https://www.apple.com/environment/pdf/Longevity_by_Design-June_2024-Apple.pdf). The portrait technical paper is the closest size comparison to our A4 dossier; the two landscape reports supply editorial and photographic examples. The [macOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/) inform the separate app review, not the prize application's page-limit rules.

The comparison covers hierarchy, spacing, type scale, imagery, tables, color, navigation and endings. These observations describe the inspected documents; they are not universal Apple design rules.

## Differences found and action taken

| Aspect | Apple references | Original Occitanie pack | Revision made |
| --- | --- | --- | --- |
| Opening hierarchy | A prominent display title and clear opening argument, especially in the portrait paper. | Small titles competed with dense opening copy. | Enlarged the English report titles and strengthened the title/subtitle hierarchy. |
| Whitespace and measure | Shorter line measure, generous outer margins and deliberate section breaks. | Dense full-width blocks and abrupt transitions. | Recast the supporting reports as narrower editorial prose and moved major transitions to intentional page starts. |
| Evidence presentation | Purposeful callouts, restrained charts and images rather than a grid for every fact. | Large tables dominated the dossier; several split awkwardly. | Replaced prose-like tables with labelled paragraphs and retained only the compact mathematical sample-size table where comparison is useful. |
| Product evidence | Photography or graphics give the subject a visual presence. | No actual app image in the technical dossier. | Added a real, bundled French-workspace screenshot with an honest prototype caption and alternative text. It is not an Apple image. |
| Typography and color | Limited type styles and restrained accent color, with strong contrast. | Weak title-to-body contrast and overly uniform pages. | Increased display/body separation while keeping a sober blue accent and the project's own identity. |
| References and endings | Compact, readable source treatment that does not overwhelm the page. | Long raw URLs and stranded source rows. | Switched to descriptive clickable source labels with short domains; consolidated references on the technical report's final page. |
| Formal application | Editorial pacing is useful, but the competition's three-page PDF limit governs. | Forms and tables made the application feel administrative. | Converted the formal copy to readable prose; the current PDF renders in two A4 pages, leaving room for James's required personal facts. |

## App observations

The French workspace uses native SwiftUI controls and a familiar macOS sidebar. At a wide window size, its grouped form previously stretched too far, making the labels and values harder to scan. The new content-width policy centres it at no more than 840 points and retains 16-point side margins in narrow windows; a macOS test covers narrow, medium and wide cases. This is a scoped layout improvement, not a full HIG or accessibility certification.

The sidebar still exposes many UK routes that are marked “Coming soon”; this can be visually noisy when a teacher is focused on the French prototype. Changing that navigation would affect the established UK workflow and needs a separate interaction review rather than an untested late-stage redesign. The bundled screenshot is a prototype capture and may not show every current detail of live provider settings.

## Remaining differences and evidence limits

Apple's landscape reports use commissioned photography and bespoke illustration that would be inappropriate to imitate or download into this submission. The competition dossier instead prioritises verifiable product imagery, clear claims and restrained typography. Its diagrams and screenshots are not a substitute for a live demonstration. The French NSI generator is still unqualified for teacher-approved classroom use: the recorded ten-paper campaign accepted zero complete papers, and independent teacher review and a learner pilot remain outstanding. Visual polish must not hide those limits.

The reference PDFs were used for analysis only and are not distributed with the repository or application.
