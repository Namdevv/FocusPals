# Build AgentPetTimer.exe (Windows)
# Chạy: powershell -ExecutionPolicy Bypass -File build.ps1

pip install -r requirements.txt

$icon = ""
if (Test-Path "assets\icon.ico") { $icon = "--icon=assets\icon.ico" }

pyinstaller --noconfirm --onefile --windowed `
  --name AgentPetTimer `
  $icon `
  --add-data "assets;assets" `
  --add-data "src\pet_view.html;src" `
  main.py

Write-Host ""
Write-Host "Xong. File: dist\AgentPetTimer.exe" -ForegroundColor Green
