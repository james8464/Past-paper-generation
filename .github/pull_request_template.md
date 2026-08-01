## What changed

<!-- Explain the user-visible outcome and why it is needed. -->

## Verification

- [ ] Python tests pass (`python -m pytest -q`)
- [ ] Swift tests pass (`make -C macOS test`)
- [ ] App Store preflight passes (`make -C macOS preflight-app-store`)
- [ ] Generated question paper and mark scheme were inspected when output changed
- [ ] macOS UI was checked in light mode, dark mode, and at a compact window size when UI changed
- [ ] Graphify was refreshed (`graphify update .`)

## Risk

<!-- Note migrations, compatibility concerns, AI-output changes, or release risks. -->
