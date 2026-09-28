# Open Sans cover fonts

Source: [official Google Fonts Open Sans repository](https://github.com/googlefonts/opensans),
pinned commit `bd7e37632246368c60fdcbd374dbf9bad11969b6` (version 3.003).
Copyright 2020 The Open Sans Project Authors. Redistribution and embedding are
permitted under the accompanying unmodified SIL Open Font License 1.1.
No fonts were extracted from examination PDFs.

Only the two static TTFs are bundled; the upstream variable source and build
tools are not runtime dependencies. Existing body-font aliases are unchanged.

## SemiBold

Unmodified upstream file:
[`fonts/ttf/OpenSans-SemiBold.ttf`](https://github.com/googlefonts/opensans/blob/bd7e37632246368c60fdcbd374dbf9bad11969b6/fonts/ttf/OpenSans-SemiBold.ttf).

SHA-256: `4a413711684a9dd564ef0f1c10cb62b5d9f7eb6df2cff962f5341a6ecd5f64ae`

## Medium

Upstream supplies Medium through its variable font rather than a prebuilt
static face. This static instance preserves its genuine weight-500 outlines;
it is not synthetic bolding or a renamed Regular font.

Source:
[`fonts/variable/OpenSans[wdth,wght].ttf`](https://github.com/googlefonts/opensans/blob/bd7e37632246368c60fdcbd374dbf9bad11969b6/fonts/variable/OpenSans%5Bwdth%2Cwght%5D.ttf).

Source SHA-256: `36643644f318a812aab2d2ed3bb98f8cf0872527f835fe9398d95fe6b9adb878`

Built with fontTools 4.63.0:

```sh
fonttools varLib.instancer OpenSans-Variable.ttf wght=500 wdth=100 \
  --update-name-table --no-recalc-timestamp --output OpenSans-Medium.ttf
```

Output SHA-256: `9f880370984fa6c958002e2618ce69ccacc2b4ba60d37d79b1b9aa655da750f0`

The deterministic rebuild was checked byte-for-byte. The official name-table
instancing procedure names this face `OpenSansRoman-Medium`; that genuine
PostScript name is retained rather than falsifying the PDF's font identity.
Both axes are fully pinned, so there is no `fvar` table in the output.
