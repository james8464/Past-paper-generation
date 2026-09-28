# Bundled examination fonts

Paper Creator bundles open, deterministic font files so a paper renders with
the same metrics on every supported Mac and inside the signed backend helper.

- `arimo/` is [Google Fonts Arimo](https://github.com/googlefonts/arimo), a
  metrically Arial-compatible family used for sans-serif examination layouts.
- `tinos/` is [Google Fonts Tinos](https://github.com/googlefonts/tinos), a
  metrically Times New Roman-compatible family used for serif cover furniture.
- `opensans/` contains official Open Sans SemiBold and a deterministic Medium
  static instance for measured AQA cover typography only. See its
  [provenance](opensans/README.md) for sources, reproduction and checksums.

These families are redistributed under the SIL Open Font License 1.1. Their
licence text is stored beside the font files. Runtime code uses
semantic names such as `ExamSans`, `AQAArial`, and `ExamSerif`; renderers do not
depend on fonts installed on the user's Mac.
