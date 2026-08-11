$ErrorActionPreference = "Stop"

if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    throw "Instale e autentique a Vercel CLI antes de executar este script."
}
if (-not (Test-Path -LiteralPath ".vercel/project.json")) {
    throw "Vincule este checkout com 'vercel link' antes de criar os drafts."
}

function Invoke-Vercel {
    & vercel @args
    if ($LASTEXITCODE -ne 0) {
        throw "A Vercel CLI encerrou com codigo $LASTEXITCODE. Nenhuma regra foi publicada."
    }
}

# No Windows, as aspas internas precisam chegar escapadas ao processo Node da
# CLI. Sem as barras, o PowerShell entrega {type:path} em vez de JSON valido.
$generatePath = '{\"type\":\"path\",\"op\":\"pre\",\"value\":\"/gerar/\"}'
$generatePost = '{\"type\":\"method\",\"op\":\"eq\",\"value\":\"POST\"}'
$titlePath = '{\"type\":\"path\",\"op\":\"pre\",\"value\":\"/titulo/\"}'
$titleGet = '{\"type\":\"method\",\"op\":\"eq\",\"value\":\"GET\"}'
$probePaths = '{\"type\":\"path\",\"op\":\"inc\",\"value\":[\"/.env\",\"/.git/config\",\"/wp-admin\",\"/phpmyadmin\",\"/server-status\"]}'
$adminPath = '{\"type\":\"path\",\"op\":\"pre\",\"value\":\"/admin/\"}'

# Tudo e criado como draft e somente em modo de registro. Este script nunca
# chama `vercel firewall publish`.
Invoke-Vercel firewall rules add "QFH - limite rotas caras" `
    --condition $generatePath `
    --condition $generatePost `
    --or `
    --condition $titlePath `
    --condition $titleGet `
    --action rate_limit `
    --rate-limit-window 60 `
    --rate-limit-requests 120 `
    --rate-limit-keys ip `
    --rate-limit-action log `
    --yes

Invoke-Vercel firewall rules add "QFH - registrar probes" `
    --condition $probePaths `
    --action log `
    --yes

Invoke-Vercel firewall rules add "QFH - registrar admin" `
    --condition $adminPath `
    --action log `
    --yes

Invoke-Vercel firewall diff
Write-Host "Drafts criados. Revise o trafego no painel; nao publique bloqueios ainda."
