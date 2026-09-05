# Graph Report - QualFilmeHoje  (2026-08-25)

## Corpus Check
- 80 files · ~75,969 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 637 nodes · 1213 edges · 45 communities (30 shown, 15 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 107 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1960a0d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- views.py
- watchmode.py
- library.py
- rate_limit
- FilterIntent
- Security Hardening Plan
- Home page
- site.js
- MovieViewTests
- AuthenticationTests
- Title
- home.py
- SEOMetadataTests
- admin.py
- TitleSitemap
- create_title
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
- tmdb_catalog.py
- Hero POV image
- Q: Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?
- AGENTS.md
- use_cases/__init__.py
- ai/__init__.py
- QualFilmeHoje

## God Nodes (most connected - your core abstractions)
1. `MovieViewTests` - 24 edges
2. `FilterIntent` - 23 edges
3. `Title` - 23 edges
4. `AuthenticationTests` - 22 edges
5. `TMDBServiceTests` - 17 edges
6. `GeminiFilterError` - 16 edges
7. `get_title_details()` - 16 edges
8. `TMDBError` - 16 edges
9. `UnsupportedFilterIntent` - 15 edges
10. `get_random_title()` - 15 edges

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

## Communities (45 total, 15 thin omitted)

### Community 0 - "views.py"
Cohesion: 0.08
Nodes (44): csrf_exempt, is_favorite(), _build_title_payload(), _fetch_title_extras(), _get(), get_genres(), _get_movie_release_list(), get_now_playing_movies() (+36 more)

### Community 1 - "watchmode.py"
Cohesion: 0.07
Nodes (33): dict, HTTPRedirectHandler, ExternalResponseError, NoRedirectHandler, open_json(), Exception, Leitura JSON limitada, sem encaminhar credenciais em redirects., A resposta externa nao e JSON confiavel dentro dos limites locais. (+25 more)

### Community 2 - "library.py"
Cohesion: 0.06
Nodes (38): AppConfig, atomic, MoviesConfig, _canonical_url(), Notifica buscadores participantes quando uma URL publica e criada., Monta e envia a URL publica de um filme ou serie validos., Envia uma URL canonica sem propagar falhas para a requisicao do usuario., submit_title_url() (+30 more)

### Community 3 - "rate_limit"
Cohesion: 0.07
Nodes (21): consume_rate_limit(), _identifier_key(), _normalise_reset_at(), Persistencia atomica dos contadores de limite de requisicoes., Gera uma chave opaca sem persistir IP, usuario ou escopo em texto aberto., Incrementa um bucket em uma unica instrucao atomica e retorna a decisao., RateLimitBucket, Contador compartilhado dos limites de abuso da aplicacao. (+13 more)

### Community 4 - "FilterIntent"
Cohesion: 0.06
Nodes (50): BaseModel, field_validator, model_validator, available_genre_keys(), is_supported_genre_key(), profile_prompt_guidance(), Vocabulário permitido pelo filtro de IA. Os filtros efetivos do TMDB continuam…, _genre_value() (+42 more)

### Community 5 - "Security Hardening Plan"
Cohesion: 0.08
Nodes (27): CSP report-only rollout, External API response validation, Fail-closed production configuration, MFA-protected admin access, Neon least-privilege runtime role, Security Hardening Plan, Session and privacy protections, Shared rate limiting and cache (+19 more)

### Community 6 - "Home page"
Cohesion: 0.09
Nodes (25): Hero session focus image, QualFilmeHoje logo, QualFilmeHoje social sharing image, Logout template, Email confirmation sent message, Email confirmed message, Account signup template, Verification sent template (+17 more)

### Community 7 - "site.js"
Cohesion: 0.08
Nodes (31): FilterRequestError, initAiFilter(), responsePayload(), setMessage(), setStatus(), initFavorites(), initGenerator(), MEDIA_TYPES (+23 more)

### Community 8 - "MovieViewTests"
Cohesion: 0.17
Nodes (3): MovieViewTests, patch, TestCase

### Community 9 - "AuthenticationTests"
Cohesion: 0.12
Nodes (3): AuthenticationTests, patch, TestCase

### Community 10 - "Title"
Cohesion: 0.22
Nodes (8): Title, create_user(), Factories pequenas para manter os testes focados no comportamento relevante., tmdb_title_payload(), TestCase, TestFactoriesTests, IndexNowPersistenceTests, TestCase

### Community 11 - "home.py"
Cohesion: 0.17
Nodes (18): InputValidationTests, build_generation_context(), build_home_context(), filter_options_context(), _genre_name(), _landing_context(), parse_ascii_int(), parse_filters() (+10 more)

### Community 12 - "SEOMetadataTests"
Cohesion: 0.16
Nodes (5): override_settings, patch, TestCase, SEOEndpointsTests, SEOMetadataTests

### Community 13 - "admin.py"
Cohesion: 0.19
Nodes (9): FavoriteAdmin, GenerationAdmin, TitleAdmin, Favorite, Generation, Meta, Tabela gerenciada usada pelo DatabaseCache nas funcoes da Vercel., SharedCacheEntry (+1 more)

### Community 14 - "TitleSitemap"
Cohesion: 0.18
Nodes (4): CanonicalSitemap, StaticSitemap, TitleSitemap, Sitemap

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

### Community 32 - "tmdb_catalog.py"
Cohesion: 0.13
Nodes (40): fetch_title_extras(), get_genres(), get_movie_release_list(), get_recent_top_titles(), get_title_details(), normalise_release_list_item(), Consultas de catálogo, detalhes e listas do TMDB., Exception (+32 more)

### Community 40 - "Q: Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?, Source Nodes

### Community 45 - "QualFilmeHoje"
Cohesion: 0.15
Nodes (12): Como executar localmente, Créditos e licença, Estrutura do projeto, Funcionalidades, Pré-requisitos, QualFilmeHoje, Qualidade, Rotas principais (+4 more)

## Knowledge Gaps
- **54 isolated node(s):** `FilterRequestError`, `MEDIA_TYPES`, `NAVIGATION_KEYS`, `Migration`, `Migration` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `rate_limits.py` (3× useful, score=2.317857137)
- `RateLimitBucket` (3× useful, score=2.317857137)
- `tmdb_catalog.py` (3× useful, score=2.317334443)
- `vercel-firewall.ps1` (2× useful, score=1.546527738)
- `generator.js` (2× useful, score=1.545268442)
- `streaming.js` (2× useful, score=1.545268442)
- `tmdb.py` (2× useful, score=1.543735806)
- `generate_movie()` (2× useful, score=1.543735806)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Title` connect `Title` to `views.py`, `library.py`, `AuthenticationTests`, `home.py`, `SEOMetadataTests`, `admin.py`, `TitleSitemap`, `create_title`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `MovieViewTests` connect `MovieViewTests` to `Title`, `create_title`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `AuthenticationTests` connect `AuthenticationTests` to `Title`, `admin.py`, `create_title`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `FilterIntent` (e.g. with `UnsupportedFilterIntent` and `GeminiFilterError`) actually correct?**
  _`FilterIntent` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Title` (e.g. with `TitleSitemap` and `create_title()`) actually correct?**
  _`Title` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AuthenticationTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`AuthenticationTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `FilterRequestError`, `MEDIA_TYPES`, `NAVIGATION_KEYS` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._