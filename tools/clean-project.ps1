#tools/clean-project.ps1

# Sätt loggfil med tidsstämpel
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$logPath = Join-Path -Path $PSScriptRoot -ChildPath ("clean_log_" + $timestamp + ".txt")
"" | Out-File -FilePath $logPath -Encoding UTF8

Write-Host "Cleaning project..." -ForegroundColor Cyan
Add-Content -Path $logPath -Value "== Cleaning log started: $timestamp =="

# Temporära filer
$patterns = @("*.pyc", "*~", "#*#", "*.bak", "*.swp")
$fileCount = 0

foreach ($pattern in $patterns) {
    Get-ChildItem -Recurse -File -Filter $pattern | ForEach-Object {
        Remove-Item $_.FullName -Force
        $fileCount++
        Add-Content -Path $logPath -Value ("Removed file: " + $_.FullName)
    }
}

# __pycache__-mappar
$dirCount = 0
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    $dirCount++
    Add-Content -Path $logPath -Value ("Removed folder: " + $_.FullName)
}

# ➕ Ta bort migrations-mappar (ej om det är din faktiska versionshanterade migration!)
$migrationsFolders = Get-ChildItem -Recurse -Directory -Filter "migrations" | Where-Object {
    -not (Test-Path (Join-Path $_.FullName "versions"))
}
$migrationsCount = 0
foreach ($folder in $migrationsFolders) {
    Remove-Item $folder.FullName -Recurse -Force
    $migrationsCount++
    Add-Content -Path $logPath -Value ("Removed temp migration folder: " + $folder.FullName)
}

# Leta efter möjliga testbilder
$imageCount = 0
$testImages = Get-ChildItem -Recurse -File -Path "static" | Where-Object {
    $_.Name -match "test|temp|debug"
}
foreach ($file in $testImages) {
    $imageCount++
    Add-Content -Path $logPath -Value ("Test image found: " + $file.FullName)
}

# Sammanfattning
Write-Host ""
Write-Host "✅ Cleaning complete!" -ForegroundColor Green
Write-Host "$fileCount files removed"
Write-Host "$dirCount cache folders removed"
Write-Host "$migrationsCount temporary migrations folders removed"
Write-Host "$imageCount test images found"
Write-Host "📄 Log file: $logPath"

Add-Content -Path $logPath -Value ""
Add-Content -Path $logPath -Value "Total files removed: $fileCount"
Add-Content -Path $logPath -Value "Cache folders removed: $dirCount"
Add-Content -Path $logPath -Value "Migrations folders removed: $migrationsCount"
Add-Content -Path $logPath -Value "Test images found: $imageCount"
Add-Content -Path $logPath -Value "== End of log =="
