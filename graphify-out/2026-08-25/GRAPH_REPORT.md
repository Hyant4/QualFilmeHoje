# Graph Report - QualFilmeHoje  (2026-08-25)

## Corpus Check
- 79 files · ~75,272 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 631 nodes · 1235 edges · 45 communities (32 shown, 13 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 101 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `182793c1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- views.py
- watchmode.py
- indexnow.py
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
- initGenerator
- signals.py
- ai/__init__.py

## God Nodes (most connected - your core abstractions)
1. `Title` - 27 edges
2. `MovieViewTests` - 27 edges
3. `AuthenticationTests` - 22 edges
4. `FilterIntent` - 19 edges
5. `rate_limit()` - 19 edges
6. `TMDBError` - 19 edges
7. `get_streaming_groups()` - 17 edges
8. `TMDBServiceTests` - 17 edges
9. `get_title_details()` - 16 edges
10. `create_title()` - 16 edges

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

## Communities (45 total, 13 thin omitted)

### Community 0 - "views.py"
Cohesion: 0.05
Nodes (67): atomic, csrf_exempt, Monta e envia a URL publica de um filme ou serie validos., submit_title_url(), _account_user(), get_favorites(), get_library(), is_favorite() (+59 more)

### Community 1 - "watchmode.py"
Cohesion: 0.06
Nodes (36): dict, HTTPRedirectHandler, ExternalResponseError, NoRedirectHandler, open_json(), Exception, Leitura JSON limitada, sem encaminhar credenciais em redirects., A resposta externa nao e JSON confiavel dentro dos limites locais. (+28 more)

### Community 2 - "indexnow.py"
Cohesion: 0.13
Nodes (10): _canonical_url(), Notifica buscadores participantes quando uma URL publica e criada., Envia uma URL canonica sem propagar falhas para a requisicao do usuario., submit_url(), IndexNowClientTests, IndexNowEndpointTests, _IndexNowResponse, override_settings (+2 more)

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
Cohesion: 0.10
Nodes (26): FilterRequestError, initAiFilter(), responsePayload(), setMessage(), setStatus(), initFavorites(), initBrowserHistory(), normaliseBrowserHistory() (+18 more)

### Community 8 - "MovieViewTests"
Cohesion: 0.17
Nodes (3): MovieViewTests, patch, TestCase

### Community 9 - "AuthenticationTests"
Cohesion: 0.12
Nodes (3): AuthenticationTests, patch, TestCase

### Community 10 - "Title"
Cohesion: 0.19
Nodes (10): Favorite, Generation, Meta, Tabela gerenciada usada pelo DatabaseCache nas funcoes da Vercel., SharedCacheEntry, Title, Factories pequenas para manter os testes focados no comportamento relevante., tmdb_title_payload() (+2 more)

### Community 11 - "home.py"
Cohesion: 0.22
Nodes (15): InputValidationTests, build_generation_context(), build_home_context(), filter_options_context(), _genre_name(), _landing_context(), parse_ascii_int(), parse_filters() (+7 more)

### Community 12 - "SEOMetadataTests"
Cohesion: 0.16
Nodes (5): override_settings, patch, TestCase, SEOEndpointsTests, SEOMetadataTests

### Community 13 - "admin.py"
Cohesion: 0.60
Nodes (4): FavoriteAdmin, GenerationAdmin, TitleAdmin, register

### Community 14 - "TitleSitemap"
Cohesion: 0.21
Nodes (4): CanonicalSitemap, StaticSitemap, TitleSitemap, Sitemap

### Community 15 - "create_title"
Cohesion: 0.15
Nodes (4): create_title(), create_user(), TestCase, TestFactoriesTests

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
Cohesion: 0.16
Nodes (36): fetch_title_extras(), get_genres(), get_movie_release_list(), get_recent_top_titles(), get_title_details(), normalise_release_list_item(), Consultas de catálogo, detalhes e listas do TMDB., Exception (+28 more)

### Community 40 - "Q: Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Como ficou a modularização do JavaScript e a adoção de factories na Parte 3?, Source Nodes

### Community 42 - "initGenerator"
Cohesion: 0.24
Nodes (12): initGenerator(), applyAiFilters(), hasOption(), markAiSuggested(), selectMedia(), setAiSuggestedValue(), updateRatingRange(), updateReleaseYearRange() (+4 more)

### Community 43 - "signals.py"
Cohesion: 0.23
Nodes (9): AppConfig, MoviesConfig, invalidate_other_sessions_on_password_change(), invalidate_sessions_on_password_reset(), _invalidate_user_sessions(), merge_library_on_login(), Mantém favoritos e sorteios feitos antes de o visitante entrar., Remove sessões autenticadas do usuário sem confiar em dados do cliente. (+1 more)

## Knowledge Gaps
- **44 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `rate_limits.py` (2× useful, score=1.997062187)
- `RateLimitBucket` (2× useful, score=1.997062187)
- `tmdb_catalog.py` (2× useful, score=1.996386298)
- `tmdb.py` (2× useful, score=1.996183509) _(code changed — re-verify)_
- `generate_movie()` (2× useful, score=1.996183509) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Title` connect `Title` to `views.py`, `MovieViewTests`, `AuthenticationTests`, `home.py`, `SEOMetadataTests`, `admin.py`, `TitleSitemap`, `create_title`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `MovieViewTests` connect `MovieViewTests` to `Title`, `create_title`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `AuthenticationTests` connect `AuthenticationTests` to `Title`, `create_title`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Title` (e.g. with `TitleSitemap` and `create_title()`) actually correct?**
  _`Title` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `MovieViewTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`MovieViewTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AuthenticationTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`AuthenticationTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `FilterIntent` (e.g. with `map_intent_to_suggestion()` and `_build_chain()`) actually correct?**
  _`FilterIntent` has 5 INFERRED edges - model-reasoned connections that need verification._