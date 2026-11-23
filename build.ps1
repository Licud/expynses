# Builds expynses.exe, puts the migrations next to it in dist/, and zips dist/ into release/.
# Run from the project root:  .\build.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# The version lives in one place: src/expynses/__init__.py
$version = (Select-String -Path "src/expynses/__init__.py" -Pattern '__version__\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
Write-Host "Building expynses v$version"

$env:PYTHONPATH = "src"
# PyInstaller prints harmless warnings on stderr, which PowerShell 5.1 would treat as errors.
# The exit code below is what decides success.
$ErrorActionPreference = "Continue"
& .\.venv\Scripts\flet.exe pack src/expynses/main.py -y `
    -n expynses `
    -i src/expynses/assets/icon.ico `
    --product-name expynses `
    --product-version $version `
    --file-version $version `
    --add-data "src/expynses/assets:assets" `
    --hidden-import alembic.ddl.sqlite `
    -- --paths src
if ($LASTEXITCODE -ne 0) { throw "flet pack failed" }
$ErrorActionPreference = "Stop"

# The migrations are loaded from disk at runtime, so they ship beside the exe.
Remove-Item dist/alembic -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item alembic dist/alembic -Recurse
Get-ChildItem dist/alembic -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force

# Zip the contents of dist/ (not the folder itself).
New-Item -ItemType Directory -Force release | Out-Null
$zip = "release/expynses-v$version.zip"
Remove-Item $zip -Force -ErrorAction SilentlyContinue
Compress-Archive -Path "dist/*" -DestinationPath $zip

Write-Host "Done: $zip"
