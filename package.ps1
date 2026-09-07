param(
  [string]$Output = "$(Join-Path (Split-Path $PSScriptRoot -Parent) 'outputs\industrial-agent-demo.zip')"
)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$parent = Split-Path $root -Parent
$outDir = Split-Path $Output -Parent
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
if (Test-Path $Output) { Remove-Item -LiteralPath $Output -Force }
$files = @(
  "app.py", "mock_data.json", "README.md", "LICENSE", "requirements.txt", ".gitignore",
  "package.ps1", "docs\architecture.md", "docs\interview-guide.md", "tests\test_app.py",
  ".github\workflows\ci.yml"
)
$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("forgeops-package-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $temp | Out-Null
try {
  foreach ($file in $files) {
    $source = Join-Path $root $file
    if (-not (Test-Path -LiteralPath $source)) { throw "Missing package file: $file" }
    $destination = Join-Path $temp (Join-Path "industrial-agent-demo" $file)
    New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination
  }
  Compress-Archive -Path (Join-Path $temp "industrial-agent-demo") -DestinationPath $Output -CompressionLevel Optimal
} finally {
  if (Test-Path $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
$size = (Get-Item -LiteralPath $Output).Length
Write-Output ("Created {0} ({1:N2} MB)" -f $Output, ($size / 1MB))
if ($size -ge 25MB) { throw "Archive is too large: $size bytes" }
