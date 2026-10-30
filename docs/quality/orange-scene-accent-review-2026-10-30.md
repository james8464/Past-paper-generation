# Orange scene accent restoration

Scope: restore the requested warm orange accent in the main window and Settings, without changing paper generation, saved preferences, icon artwork or semantic text colours.

The `AccentColor` asset uses the existing contrast-aware `ForegroundAccent` values: `#A94700` in light appearance, `#FF9230` in dark appearance, `#963F00` in increased-contrast light appearance and `#FFA056` in increased-contrast dark appearance. Both scenes explicitly select this asset. The asset compiler and `NSAccentColorName` use the same name.

This is a scoped configuration and regression-test review, not a complete accessibility or HIG certification. Native light/dark visual acceptance, including the foreground of prominent buttons, remains a separate release check. No generation source or historical paper evidence changes in this patch.

The initial dark-appearance visual check found native white selected text and prominent-button glyphs over the bright orange. A separate `ControlAccent` role now keeps selected and filled control backgrounds at `#A94700`, or `#963F00` with increased contrast, in both appearances. The sidebar and existing shared primary-action style use this role. Ordinary scene accent labels and explicit `ForegroundAccent` links retain the brighter dark-appearance values. Native foreground and disabled-state rendering are unchanged. A regression test requires at least 4.5:1 contrast with white for every control-fill variant; actual revised native rendering still requires visual acceptance.
