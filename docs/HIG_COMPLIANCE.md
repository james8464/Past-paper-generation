# macOS interaction and HIG compliance

## Information architecture

The main window is a resizable `NavigationSplitView`:

- the sidebar selects a subject and exam board;
- the content column owns the paper-creation task;
- the optional inspector exposes release evidence without obstructing the task.

The creation form uses native grouped `Form`, `Section`, `Picker`,
`LabeledContent`, `Toggle`, `ProgressView`, `Table`, `ContentUnavailableView`,
`SettingsLink`, and toolbar APIs. It does not simulate macOS controls with
custom cards or web-style navigation.

## Commands and state

- `⌘N`: start a new paper.
- `⌘↩`: create when the current configuration is valid.
- `⌘.`: cancel the active operation.
- `⌘,`: open the standard Settings scene.
- Sidebar and quality-inspector visibility are standard toolbar commands.
- The primary action occupies the primary toolbar position.
- Task blockers appear beside the affected controls and state the recovery
  action; disabled controls also expose accessibility help.

Progress is determinate whenever the backend provides a fraction, includes a
time estimate when available, and can be cancelled. A spinner is used only when
progress is genuinely indeterminate.

## Geometry and visual language

- System typography, semantic colours, SF Symbols, materials, separators, and
  native focus/hover states are preserved.
- Content uses standard form insets and table geometry rather than arbitrary
  radii or branded cards.
- The window has a practical 920 × 640 minimum and remains resizable.
- The sidebar defaults to 220 points and remains user-adjustable.
- The inspector is constrained to a readable 250–360-point range.
- Status never relies on colour alone; each state includes a symbol and text.
- Controls use native macOS hit regions, meeting the platform's recommended
  target sizes without invisible custom overlays.

## Settings

Settings use the app's `Settings` scene and a stable toolbar-style `TabView`.
Changes apply immediately, the selected pane persists, and the fixed-size
settings window disables inappropriate minimise/zoom controls. Task-local paper
and destination choices remain in the main creation flow.

## File workflow

Generated artifacts appear in a native table with document title, timestamp,
and path. They can be opened, revealed in Finder, removed from Recents, or
dragged to Finder. The selected output folder remains visible in the task.

## Accessibility verification

The source uses semantic labels, combined status rows, non-colour state labels,
and accessibility hints. Before distribution, the built app still requires
manual verification in:

- VoiceOver and Full Keyboard Access;
- Increase Contrast and Reduce Transparency;
- light and dark appearance;
- enlarged text and long localisation;
- minimum and large window sizes;
- generation, cancellation, failure, and completed-package states.

The current screenshot and accessibility-tree audit is recorded under
`docs/project-analysis/UI_AUDIT.md`.
