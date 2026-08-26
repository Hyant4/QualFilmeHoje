# Graph Report - QualFilmeHoje  (2026-08-21)

## Corpus Check
- 80 files · ~76,648 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 638 nodes · 1301 edges · 41 communities (27 shown, 14 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 139 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7de59dcc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- views.py
- watchmode.py
- Title
- rate_limit
- tmdb_catalog.py
- Security Hardening Plan
- Home page
- site.js
- MovieViewTests
- signals.py
- home.py
- SEOMetadataTests
- context_processors.py
- QualFilmeHojeAccountAdapter
- QualFilmeHojeMFAAdapter
- AdminMFAMiddleware
- FrontendModuleTests
- Password reset template
- vercel.json
- infrastructure/__init__.py
- 0001_initial.py
- 0002_favorite_user_generation_user_and_more.py
- 0003_whatsappcontact.py
- 0004_sharedcacheentry.py
- 0005_remove_whatsapp_integration.py
- 0006_ratelimitbucket.py
- use_cases/__init__.py
- Hero POV image
- FilterIntent
- Filtro por linguagem natural com Gemini
- Q: Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?
- AGENTS.md
- ai/__init__.py

## God Nodes (most connected - your core abstractions)
1. `Title` - 30 edges
2. `FilterIntent` - 29 edges
3. `MovieViewTests` - 27 edges
4. `AuthenticationTests` - 22 edges
5. `TMDBServiceTests` - 22 edges
6. `TMDBError` - 20 edges
7. `rate_limit()` - 19 edges
8. `get_random_title()` - 18 edges
9. `get_streaming_groups()` - 17 edges
10. `AiFilterEndpointTests` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Remaining hardening work query result` --reports_remaining_work_for--> `Security Hardening Plan`  [EXTRACTED]
  graphify-out/memory/query_20260814_030655_oque_falta_agora.md → docs/security-hardening.md
- `Account signup template` --uses_account_registration_flow_from--> `django-allauth authentication`  [INFERRED]
  movies/templates/account/signup.html → requirements.txt
- `Privacy page` --documents_security_and_authentication_behavior_of--> `django-allauth authentication`  [INFERRED]
  movies/templates/movies/privacy.html → requirements.txt
- `Google login confirmation template` --uses_social_authentication_flow_from--> `django-allauth authentication`  [INFERRED]
  movies/templates/socialaccount/login.html → requirements.txt
- `Privacy page` --documents_transactional_email_provider_usage_for--> `django-anymail email integration`  [INFERRED]
  movies/templates/movies/privacy.html → requirements.txt

## Import Cycles
- None detected.

## Communities (41 total, 14 thin omitted)

### Community 0 - "views.py"
Cohesion: 0.06
Nodes (59): atomic, csrf_exempt, _account_user(), get_favorites(), get_library(), is_favorite(), merge_visitor_library(), _parse_date() (+51 more)

### Community 1 - "watchmode.py"
Cohesion: 0.07
Nodes (36): dict, HTTPRedirectHandler, ExternalResponseError, NoRedirectHandler, open_json(), Exception, Leitura JSON limitada, sem encaminhar credenciais em redirects., A resposta externa nao e JSON confiavel dentro dos limites locais. (+28 more)

### Community 2 - "Title"
Cohesion: 0.06
Nodes (35): FavoriteAdmin, GenerationAdmin, TitleAdmin, Favorite, Generation, Meta, Tabela gerenciada usada pelo DatabaseCache nas funcoes da Vercel., SharedCacheEntry (+27 more)

### Community 3 - "rate_limit"
Cohesion: 0.07
Nodes (22): consume_rate_limit(), _identifier_key(), _normalise_reset_at(), Persistencia atomica dos contadores de limite de requisicoes., Gera uma chave opaca sem persistir IP, usuario ou escopo em texto aberto., Incrementa um bucket em uma unica instrucao atomica e retorna a decisao., RateLimitBucket, Contador compartilhado dos limites de abuso da aplicacao. (+14 more)

### Community 4 - "tmdb_catalog.py"
Cohesion: 0.13
Nodes (39): fetch_title_extras(), get_genres(), get_movie_release_list(), get_recent_top_titles(), get_title_details(), normalise_release_list_item(), Consultas de catálogo, detalhes e listas do TMDB., Exception (+31 more)

### Community 5 - "Security Hardening Plan"
Cohesion: 0.08
Nodes (27): CSP report-only rollout, External API response validation, Fail-closed production configuration, MFA-protected admin access, Neon least-privilege runtime role, Security Hardening Plan, Session and privacy protections, Shared rate limiting and cache (+19 more)

### Community 6 - "Home page"
Cohesion: 0.09
Nodes (25): Hero session focus image, QualFilmeHoje logo, QualFilmeHoje social sharing image, Logout template, Email confirmation sent message, Email confirmed message, Account signup template, Verification sent template (+17 more)

### Community 7 - "site.js"
Cohesion: 0.11
Nodes (21): FilterRequestError, initAiFilter(), responsePayload(), setStatus(), initFavorites(), initGenerator(), MEDIA_TYPES, NAVIGATION_KEYS (+13 more)

### Community 8 - "MovieViewTests"
Cohesion: 0.06
Nodes (8): create_title(), AuthenticationTests, patch, TestCase, MovieViewTests, override_settings, patch, TestCase

### Community 9 - "signals.py"
Cohesion: 0.23
Nodes (9): AppConfig, MoviesConfig, invalidate_other_sessions_on_password_change(), invalidate_sessions_on_password_reset(), _invalidate_user_sessions(), merge_library_on_login(), Mantém favoritos e sorteios feitos antes de o visitante entrar., Remove sessões autenticadas do usuário sem confiar em dados do cliente. (+1 more)

### Community 11 - "home.py"
Cohesion: 0.28
Nodes (14): build_generation_context(), build_home_context(), filter_options_context(), _genre_name(), _landing_context(), parse_ascii_int(), parse_filters(), _parse_min_release_year() (+6 more)

### Community 12 - "SEOMetadataTests"
Cohesion: 0.16
Nodes (5): override_settings, patch, TestCase, SEOEndpointsTests, SEOMetadataTests

### Community 16 - "context_processors.py"
Cohesion: 0.47
Nodes (5): authentication(), _homepage_json_ld(), _random_movies_json_ld(), Disponibiliza apenas o estado público da integração nos templates., seo_metadata()

### Community 17 - "QualFilmeHojeAccountAdapter"
Cohesion: 0.40
Nodes (3): DefaultAccountAdapter, QualFilmeHojeAccountAdapter, Gera um username legível para cadastros sociais sem sobrescrever escolhas.

### Community 18 - "QualFilmeHojeMFAAdapter"
Cohesion: 0.40
Nodes (3): DefaultMFAAdapter, QualFilmeHojeMFAAdapter, Mantem TOTP obrigatorio enquanto a conta possuir acesso ao admin.

### Community 21 - "Password reset template"
Cohesion: 0.67
Nodes (3): Password reset sent template, Password changed template, Password reset template

### Community 40 - "FilterIntent"
Cohesion: 0.06
Nodes (50): BaseModel, field_validator, model_validator, available_genre_keys(), is_supported_genre_key(), profile_prompt_guidance(), Vocabulário permitido pelo filtro de IA. Os filtros efetivos do TMDB continuam…, _genre_value() (+42 more)

### Community 41 - "Filtro por linguagem natural com Gemini"
Cohesion: 0.17
Nodes (11): Chamada Gemini, Configuração, Contrato, Etapas de entrega, Filtro por linguagem natural com Gemini, Fluxo, Limites do MVP, Objetivo (+3 more)

### Community 42 - "Q: Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?, Source Nodes

## Knowledge Gaps
- **54 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `rate_limits.py` (3× useful, score=2.50796676)
- `RateLimitBucket` (3× useful, score=2.50796676)
- `tmdb_catalog.py` (3× useful, score=2.507401195)
- `vercel-firewall.ps1` (2× useful, score=1.673373263)
- `generator.js` (2× useful, score=1.67201068)
- `streaming.js` (2× useful, score=1.67201068)
- `tmdb.py` (2× useful, score=1.670352338)
- `generate_movie()` (2× useful, score=1.670352338) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Title` connect `Title` to `views.py`, `MovieViewTests`, `home.py`, `SEOMetadataTests`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `MovieViewTests` connect `MovieViewTests` to `Title`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `RateLimitBucket` connect `rate_limit` to `FilterIntent`, `Title`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Title` (e.g. with `FavoriteAdmin` and `GenerationAdmin`) actually correct?**
  _`Title` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `FilterIntent` (e.g. with `UnsupportedFilterIntent` and `GeminiFilterError`) actually correct?**
  _`FilterIntent` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `MovieViewTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`MovieViewTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AuthenticationTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`AuthenticationTests` has 3 INFERRED edges - model-reasoned connections that need verification._