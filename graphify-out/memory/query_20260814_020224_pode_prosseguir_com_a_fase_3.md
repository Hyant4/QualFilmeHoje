---
type: "query"
date: "2026-08-14T02:02:24.834112+00:00"
question: "pode prosseguir com a fase 3"
contributor: "graphify"
outcome: "useful"
source_nodes: ["RateLimitBucket", "validate_title_id()", "get_title_details()", "get_streaming_groups()", "rate_limits.py", "tmdb_catalog.py"]
---

# Q: pode prosseguir com a fase 3

## Answer

Expanded from graph vocab: [rate, ratelimitbucket, cache, sharedcacheentry, validate, title, session, tmdb, watchmode, generate, security, vercel]. Verificado e completado o hardening de abuso: rate limiting compartilhado por IP e usuario, cache compartilhado e negativo, validacao de IDs e notas, GET de titulo sem escrita de negocio, e validacao TMDB antes da Watchmode inclusive no endpoint /api/onde-assistir/. O draft Vercel QFH - limite rotas caras foi atualizado para incluir esse endpoint, mantendo rate-limit-action log; tres drafts permanecem sem publicacao. Suite completa: 98 testes OK; migrations check, Django check, Ruff, pip check e git diff --check OK.

## Outcome

- Signal: useful

## Source Nodes

- RateLimitBucket
- validate_title_id()
- get_title_details()
- get_streaming_groups()
- rate_limits.py
- tmdb_catalog.py