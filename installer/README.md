# Building the Cursiv Windows installer

There's no single "just run this" script — the build is two stages, each with
its own prerequisite. Run them in order from the repo root.

## 1. Bump the version first

Before building, decide the new version tag (e.g. `3.14-U14`) and update it in
**both** places — they don't derive from each other:

- `launcher/cursiv_launcher.py` — `_CURRENT_VERSION = "3.14-U##"`
- `installer/cursiv_setup.iss` — `#define AppVer "3.14-U##"` and
  `OutputBaseFilename=Cursiv-Setup-3.14-U##`

If these drift, the running app reports a version different from what the
installer it was shipped in claims, and update-check logic (which compares
`_CURRENT_VERSION` against the latest GitHub release tag) can misbehave.

## 2. Build the PyInstaller bundle

```
build.ps1
```

Wraps `scripts\build.bat`, which runs
`python -m PyInstaller launcher\build.spec --noconfirm` and verifies
`dist\Cursiv\Cursiv.exe` exists afterward. Requires `pyinstaller` on PATH
(`pip install pyinstaller`). Optionally run `scripts\verify_build.bat`
afterward for a more detailed bundle-contents check (icons, `cursiv_v215`
data files, total size).

## 3. Compile the installer

```
package.ps1
```

Wraps `scripts\package.bat`, which compiles `installer\cursiv_setup.iss` with
Inno Setup 6's `ISCC.exe` into `installer\Output\Cursiv-Setup-<version>.exe`.
Requires Inno Setup 6 (free, https://jrsoftware.org/isdl.php) — the script
looks for `ISCC.exe` on PATH, in `Program Files\Inno Setup 6\`,
`Program Files (x86)\Inno Setup 6\`, and the non-admin
`%LOCALAPPDATA%\Programs\Inno Setup 6\` install location, in that order.

`package.bat` fails fast if step 2 hasn't produced `dist\Cursiv\Cursiv.exe`
yet — always run `build.ps1` first.

## 4. Publish the release

```
git push origin main
gh release create v3.14-U## "installer/Output/Cursiv-Setup-3.14-U##.exe" --title "..." --notes-file ...
```

Then **copy the built exe to a stable filename and upload it as a second
asset on the same release**:

```
cp installer/Output/Cursiv-Setup-3.14-U##.exe installer/Output/Cursiv-Setup-latest.exe
gh release upload v3.14-U## installer/Output/Cursiv-Setup-latest.exe
```

The website's download buttons (index.html, start.html) link to
`releases/latest/download/Cursiv-Setup-latest.exe` — GitHub's `releases/latest`
redirect only works for a whole release *page*, not a specific asset, and
asset URLs are filename-exact, so a versioned filename goes stale the moment
the next release ships (this happened for real — U12's link sat on the
homepage through U13/U14/U15 until a user reported the download button
"takes me to GitHub instead of installing"). The stable-named asset is what
makes `releases/latest/download/<name>` work permanently without editing the
website again on every release. Don't skip this step.

## Notes

- `cursiv_setup.iss` is the only installer script — `cursiv_setup_v2.iss` (a
  from-scratch venv-based rewrite) was tried once and abandoned the same day;
  do not resurrect it as an alternative path without good reason.
- The installer ships `launcher\cursiv.bat` as an alternate CLI entry point
  (it forwards to the bundled `Cursiv.exe -t`). It does **not** ship
  `launcher\cursiv-web.bat` — that script runs `uvicorn --reload` against a
  source tree, which has no equivalent in a frozen PyInstaller build.
- Post-install dependency setup (Ollama, the `llama3.1` model, Python
  packages) happens via `scripts\cursiv_full_setup.ps1`, launched
  non-blocking from the installer's `[Run]` section — nothing heavy is
  bundled inside the installer `.exe` itself.
