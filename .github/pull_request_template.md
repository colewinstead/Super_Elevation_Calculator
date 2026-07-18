## Release-ready checklist

- [ ] `APP_VERSION` is newer than the latest GitHub Release.
- [ ] The change is ready for users; merging creates a full release.
- [ ] Calculation behavior is unchanged, or the proven engineering defect and its verification are documented.
- [ ] Python, Windows, and browser checks pass.
- [ ] After merge, invoke `$ship-main` to publish the matching ChatGPT Site version.
