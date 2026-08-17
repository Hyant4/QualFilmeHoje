---
type: "query"
date: "2026-08-14T03:06:55.763685+00:00"
question: "oque falta agora?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["Security Hardening Plan", "Security Checks Workflow", "CSPTests", "mfa_adapter.py", "privacy()", "vercel-firewall.ps1"]
---

# Q: oque falta agora?

## Answer

Expanded from graph vocab: [security, admin, mfa, csp, password, session, privacy, workflow, deployment, firewall, test, audit]. O codigo das fases 4 a 8 ja existe e o commit de hardening 9cfa4c9 esta na cadeia do deployment de producao 9daa858. Falta publicar as correcoes locais atuais da fase 3: o worktree esta sujo no branch agent/fix-favorites-rating-layout e o preview mais recente contem apenas cba1998. O papel Neon qualfilmehoje_app existe com CONNECT e USAGE, sem CREATE/TEMP/schema CREATE, DML em todas as tabelas e somente SELECT em django_migrations; falta confirmar que a DATABASE_URL de producao usa esse papel. Depois: criar e validar preview, observar o Firewall em log por 24h, confirmar 2FA de admins, revisar CSP report-only e confirmar o workflow de seguranca verde.

## Outcome

- Signal: useful

## Source Nodes

- Security Hardening Plan
- Security Checks Workflow
- CSPTests
- mfa_adapter.py
- privacy()
- vercel-firewall.ps1