# Graph Report - .  (2026-08-17)

## Corpus Check
- 107 files · ~71,933 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 516 nodes · 1030 edges · 40 communities (27 shown, 13 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 107 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Favorites and endpoints
- HTTP client
- Application startup
- Rate limiting
- TMDB catalog
- Security hardening
- Templates and branding
- Frontend JavaScript
- View tests
- Authentication tests
- Domain models
- Home page use cases
- SEO tests
- Django administration
- Sitemaps
- Library and favorites tests
- SEO metadata
- Account adapter
- MFA adapter
- Admin MFA middleware
- Frontend tests
- Password reset templates
- Vercel configuration
- Infrastructure package
- Initial migration
- Favorites migration
- WhatsApp migration
- Shared cache migration
- WhatsApp removal migration
- Rate limit migration
- Use cases package
- Hero image asset

## God Nodes (most connected - your core abstractions)
1. `Title` - 30 edges
2. `MovieViewTests` - 27 edges
3. `AuthenticationTests` - 22 edges
4. `TMDBError` - 20 edges
5. `rate_limit()` - 18 edges
6. `get_streaming_groups()` - 17 edges
7. `TMDBServiceTests` - 17 edges
8. `ExternalResponseError` - 16 edges
9. `get_title_details()` - 16 edges
10. `get_random_title()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Remaining hardening work query result` --reports_remaining_work_for--> `Security Hardening Plan`  [EXTRACTED]
  graphify-out/memory/query_20260814_030655_oque_falta_agora.md → docs/security-hardening.md
- `Account signup template` --uses_account_registration_flow_from--> `django-allauth authentication`  [INFERRED]
  movies/templates/account/signup.html → requirements.txt
- `Home page` --preloads--> `Hero session focus image`  [EXTRACTED]
  movies/templates/movies/home.html → movies/static/movies/images/hero-session-focus.webp
- `Home page` --uses_for_social_metadata--> `QualFilmeHoje social sharing image`  [EXTRACTED]
  movies/templates/movies/home.html → movies/static/movies/images/og-qualfilmehoje.png
- `Privacy page` --documents_security_and_authentication_behavior_of--> `django-allauth authentication`  [INFERRED]
  movies/templates/movies/privacy.html → requirements.txt

## Import Cycles
- None detected.

## Communities (40 total, 13 thin omitted)

### Community 0 - "Favorites and endpoints"
Cohesion: 0.07
Nodes (50): csrf_exempt, _account_user(), get_favorites(), is_favorite(), Retorna a coleção da página Minha lista em uma única consulta., toggle_favorite(), _build_title_payload(), _discovery_cache_key() (+42 more)

### Community 1 - "HTTP client"
Cohesion: 0.07
Nodes (35): dict, HTTPRedirectHandler, ExternalResponseError, NoRedirectHandler, open_json(), Exception, Leitura JSON limitada, sem encaminhar credenciais em redirects., A resposta externa nao e JSON confiavel dentro dos limites locais. (+27 more)

### Community 2 - "Application startup"
Cohesion: 0.06
Nodes (33): AppConfig, atomic, MoviesConfig, _canonical_url(), Notifica buscadores participantes quando uma URL publica e criada., Monta e envia a URL publica de um filme ou serie validos., Envia uma URL canonica sem propagar falhas para a requisicao do usuario., submit_title_url() (+25 more)

### Community 3 - "Rate limiting"
Cohesion: 0.07
Nodes (22): consume_rate_limit(), _identifier_key(), _normalise_reset_at(), Persistencia atomica dos contadores de limite de requisicoes., Gera uma chave opaca sem persistir IP, usuario ou escopo em texto aberto., Incrementa um bucket em uma unica instrucao atomica e retorna a decisao., RateLimitBucket, Contador compartilhado dos limites de abuso da aplicacao. (+14 more)

### Community 4 - "TMDB catalog"
Cohesion: 0.17
Nodes (34): fetch_title_extras(), get_genres(), get_movie_release_list(), get_recent_top_titles(), get_title_details(), normalise_release_list_item(), Consultas de catálogo, detalhes e listas do TMDB., Exception (+26 more)

### Community 5 - "Security hardening"
Cohesion: 0.08
Nodes (27): CSP report-only rollout, External API response validation, Fail-closed production configuration, MFA-protected admin access, Neon least-privilege runtime role, Security Hardening Plan, Session and privacy protections, Shared rate limiting and cache (+19 more)

### Community 6 - "Templates and branding"
Cohesion: 0.09
Nodes (25): Hero session focus image, QualFilmeHoje logo, QualFilmeHoje social sharing image, Logout template, Email confirmation sent message, Email confirmed message, Account signup template, Verification sent template (+17 more)

### Community 7 - "Frontend JavaScript"
Cohesion: 0.13
Nodes (17): initFavorites(), initGenerator(), MEDIA_TYPES, NAVIGATION_KEYS, pulseRangeValue(), updateRangeDisplay(), initBrowserHistory(), normaliseBrowserHistory() (+9 more)

### Community 8 - "View tests"
Cohesion: 0.17
Nodes (3): MovieViewTests, patch, TestCase

### Community 9 - "Authentication tests"
Cohesion: 0.12
Nodes (3): AuthenticationTests, patch, TestCase

### Community 10 - "Domain models"
Cohesion: 0.28
Nodes (6): Title, create_user(), Factories pequenas para manter os testes focados no comportamento relevante., tmdb_title_payload(), TestCase, TestFactoriesTests

### Community 11 - "Home page use cases"
Cohesion: 0.26
Nodes (15): get_library(), build_generation_context(), build_home_context(), filter_options_context(), _genre_name(), _landing_context(), parse_ascii_int(), parse_filters() (+7 more)

### Community 12 - "SEO tests"
Cohesion: 0.16
Nodes (5): override_settings, patch, TestCase, SEOEndpointsTests, SEOMetadataTests

### Community 13 - "Django administration"
Cohesion: 0.27
Nodes (9): FavoriteAdmin, GenerationAdmin, TitleAdmin, Favorite, Generation, Meta, Tabela gerenciada usada pelo DatabaseCache nas funcoes da Vercel., SharedCacheEntry (+1 more)

### Community 14 - "Sitemaps"
Cohesion: 0.21
Nodes (4): CanonicalSitemap, StaticSitemap, TitleSitemap, Sitemap

### Community 16 - "SEO metadata"
Cohesion: 0.47
Nodes (5): authentication(), _homepage_json_ld(), _random_movies_json_ld(), Disponibiliza apenas o estado público da integração nos templates., seo_metadata()

### Community 17 - "Account adapter"
Cohesion: 0.40
Nodes (3): DefaultAccountAdapter, QualFilmeHojeAccountAdapter, Gera um username legível para cadastros sociais sem sobrescrever escolhas.

### Community 18 - "MFA adapter"
Cohesion: 0.40
Nodes (3): DefaultMFAAdapter, QualFilmeHojeMFAAdapter, Mantem TOTP obrigatorio enquanto a conta possuir acesso ao admin.

### Community 21 - "Password reset templates"
Cohesion: 0.67
Nodes (3): Password reset sent template, Password changed template, Password reset template

## Knowledge Gaps
- **39 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+34 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Title` connect `Domain models` to `Favorites and endpoints`, `Application startup`, `View tests`, `Authentication tests`, `Home page use cases`, `SEO tests`, `Django administration`, `Sitemaps`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Why does `MovieViewTests` connect `View tests` to `Domain models`, `Django administration`, `Library and favorites tests`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `AuthenticationTests` connect `Authentication tests` to `Domain models`, `Django administration`, `Library and favorites tests`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Title` (e.g. with `FavoriteAdmin` and `GenerationAdmin`) actually correct?**
  _`Title` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `MovieViewTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`MovieViewTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AuthenticationTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`AuthenticationTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TMDBError` (e.g. with `ExternalResponseError` and `ExternalHTTPTests`) actually correct?**
  _`TMDBError` has 5 INFERRED edges - model-reasoned connections that need verification._