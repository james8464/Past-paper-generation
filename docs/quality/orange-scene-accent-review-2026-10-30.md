# Orange scene accent restoration

Scope: restore the requested warm orange accent in the main window and Settings, without changing paper generation, saved preferences, icon artwork or semantic text colours.

The `AccentColor` asset uses the existing contrast-aware `ForegroundAccent` values: `#A94700` in light appearance, `#FF9230` in dark appearance, `#963F00` in increased-contrast light appearance and `#FFA056` in increased-contrast dark appearance. Both scenes explicitly select this asset. The asset compiler and `NSAccentColorName` use the same name.

This is a scoped configuration and regression-test review, not a complete accessibility or HIG certification. Native light/dark visual acceptance, including the foreground of prominent buttons, remains a separate release check. No generation source or historical paper evidence changes in this patch.
