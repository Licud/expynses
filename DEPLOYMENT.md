# Deployment

expynses is a local desktop app (Flet + SQLite). A release is a zip containing a single Windows
executable and the database migrations. There is no server and no installer.

## Making a release

1. Bump the version in one place: `src/expynses/__init__.py`

   ```python
   __version__ = "1.0.0"
   ```

   This number is shown at the bottom of the left navigation, stamped into the exe's file
   properties, and used in the zip's file name.

2. From the project root, run:

   ```powershell
   .\build.ps1
   ```

3. The release is `release/expynses-v<version>.zip`. Test it before sharing: unzip it into a fresh,
   writable folder and double-click `expynses.exe`.

4. Tag the commit you built from, so any exe can be traced back to its source:

   ```powershell
   git tag v1.0.0
   ```

`build.ps1` reads the version, runs `flet pack` (PyInstaller) to produce `dist/expynses.exe`, copies
`alembic/` into `dist/`, and zips the contents of `dist/` into `release/`. `build/`, `dist/`,
`release/` and `*.spec` are all gitignored.

### Prerequisites (developer machine)

- The project's `.venv` with `flet`, `SQLAlchemy`, `alembic` and `pyinstaller` installed.
- Windows. The script is PowerShell and the exe is a Windows build.

## What ships

```
expynses-v1.0.0.zip
  expynses.exe     the app (Python and the assets are bundled inside)
  alembic/         database migrations, loaded from disk at runtime
```

`alembic/` has to stay next to the exe. Migrations are separate `.py` files that Alembic loads from
disk, so PyInstaller does not bundle them. Without the folder, the app fails on start with
"Path doesn't exist: alembic".

## Running it (for users)

1. Unzip into a folder you can write to, such as Documents or the Desktop. Do not use
   `Program Files`.
2. Double-click `expynses.exe`.

On first run the app creates `data/expynses.db` next to the exe and applies all migrations. On later
runs it opens the existing database and applies any new migrations.

The paths (`data/` and `alembic/`) are relative to the working directory. Double-clicking the exe or
using a shortcut starts it in the exe's folder, which is what makes this work. If you launch it from
a terminal in some other folder, it will create its data there instead.

## Upgrading to a new version

1. Close the app.
2. Replace `expynses.exe` and the `alembic/` folder with the new ones.
3. **Keep the `data/` folder.** That is the user's data.
4. Start the app. Any new migrations run automatically against the existing database.

Back up `data/expynses.db` before upgrading. Migrations change the database in place, and there is
no downgrade path.

## Things to know

- **Windows SmartScreen** will likely warn on first run, because the exe is not code-signed. Choose
  "More info" then "Run anyway".
- **Antivirus** occasionally flags PyInstaller one-file exes. It is a false positive, but expect the
  odd report.
- **Startup is a little slow** (a few seconds): a one-file exe unpacks itself to a temp folder on
  every launch.
- **Adding a migration?** Create it with Alembic as usual. `build.ps1` copies the whole `alembic/`
  folder, so new migrations ship automatically.
- **Changing the bundled assets path** (`src/expynses/assets`) means updating the `--add-data`
  argument in `build.ps1`. Flet expects them at `assets/` inside the bundle.
