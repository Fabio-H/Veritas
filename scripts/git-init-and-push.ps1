# Veritas — inicializa o repositório e prepara o primeiro push (PowerShell; requer Git).
# Opcional: .\scripts\git-init-and-push.ps1 -RemoteUrl "https://github.com/SEU_USUARIO/veritas.git"

param(
    [string]$RemoteUrl = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git não encontrado no PATH. Instale: https://git-scm.com/download/win"
}

if (-not (Test-Path ".git")) {
    git init
}

git add .
git status

git commit -m "docs: adiciona README, licença MIT e documentação do projeto Veritas" -m "Inclui README para comunidade Blue Team, disclaimer, LICENSE MIT e GITHUB_ABOUT.txt."

$branch = git branch --show-current
if (-not $branch) {
    git branch -M main
    $branch = "main"
}

if ($RemoteUrl) {
    git remote remove origin 2>$null
    git remote add origin $RemoteUrl
    git push -u origin $branch
    Write-Host "Push concluído para $RemoteUrl"
} else {
    Write-Host ""
    Write-Host "Commit local criado. Para enviar ao GitHub, crie um repositório vazio e execute:"
    Write-Host '  git remote add origin https://github.com/SEU_USUARIO/veritas.git'
    Write-Host "  git push -u origin $branch"
}
