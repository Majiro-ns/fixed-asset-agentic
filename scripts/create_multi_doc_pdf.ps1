# 複数書類を1つのPDFに結合するPowerShellスクリプト
# 実行前に: pip install PyMuPDF

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$demoDir = Join-Path $projectRoot "data\demo_pdf"

Write-Host "=== 複数書類PDF作成 ===" -ForegroundColor Cyan

# Pythonスクリプトを実行
python "$scriptDir\create_multi_doc_pdf.py"

Write-Host ""
Write-Host "完了しました。" -ForegroundColor Green
Write-Host "出力: $demoDir\demo_multi_documents.pdf"
