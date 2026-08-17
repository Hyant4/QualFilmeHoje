---
type: "query"
date: "2026-08-14T01:25:19.503278+00:00"
question: "Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["site.js", "generator.js", "history.js", "navigation.js", "streaming.js", "favorites.js", "motion.js", "factories.py", "create_user()", "create_title()"]
---

# Q: Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?

## Answer

site.js virou um entrypoint de 17 linhas que importa seis módulos por responsabilidade; as factories create_user, create_title e tmdb_title_payload passaram a abastecer testes de autenticação, views, SEO e seus próprios contratos.

## Outcome

- Signal: useful

## Source Nodes

- site.js
- generator.js
- history.js
- navigation.js
- streaming.js
- favorites.js
- motion.js
- factories.py
- create_user()
- create_title()
- tmdb_title_payload()