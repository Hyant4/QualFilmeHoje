# Graph Report - QualFilmeHoje  (2026-08-13)

## Corpus Check
- 66 files · ~70,888 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 520 nodes · 1006 edges · 51 communities (31 shown, 20 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 109 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cba1998f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Title
- library.py
- watchmode.py
- views.py
- rate_limit
- site.js
- MovieViewTests
- AuthenticationTests
- tmdb_catalog.py
- home.py
- Email Message Layout
- Movie and Series Generator
- Django
- context_processors.py
- QualFilmeHojeAccountAdapter
- QualFilmeHojeMFAAdapter
- AdminMFAMiddleware
- Account Entrance Layout
- Password Reset
- Google OAuth Login
- QualFilmeHoje Logo
- QualFilmeHoje Social Preview
- Account Registration
- Saved Favorites
- vercel.json
- Security Hardening Plan
- 0001_initial.py
- 0002_favorite_user_generation_user_and_more.py
- 0003_whatsappcontact.py
- 0004_sharedcacheentry.py
- 0005_remove_whatsapp_integration.py
- Signup Email Confirmation Subject
- Email Confirmation
- Email Confirmation Flow
- Graphify Workflow Guidance
- use_cases/__init__.py
- Home Movie Viewing Scene
- Home Cinema Viewing Scene
- Password Reset Subject
- python-dotenv
- infrastructure/__init__.py
- 0006_ratelimitbucket.py
- test_indexnow.py

## God Nodes (most connected - your core abstractions)
1. `Title` - 30 edges
2. `MovieViewTests` - 26 edges
3. `AuthenticationTests` - 22 edges
4. `TMDBError` - 20 edges
5. `rate_limit()` - 18 edges
6. `get_streaming_groups()` - 17 edges
7. `TMDBServiceTests` - 17 edges
8. `ExternalResponseError` - 16 edges
9. `get_title_details()` - 15 edges
10. `get_random_title()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `pip-audit` --conceptually_related_to--> `Django`  [INFERRED]
  requirements-dev.txt → requirements.txt
- `Ruff` --conceptually_related_to--> `Django`  [INFERRED]
  requirements-dev.txt → requirements.txt
- `AuthenticationTests` --uses--> `Title`  [INFERRED]
  movies/tests/test_auth.py → movies/models.py
- `IndexNowClientTests` --uses--> `Title`  [INFERRED]
  movies/tests/test_indexnow.py → movies/models.py
- `IndexNowEndpointTests` --uses--> `Title`  [INFERRED]
  movies/tests/test_indexnow.py → movies/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Account Entrance Templates** — movies_templates_account_base_entrance_account_entrance_layout, movies_templates_account_email_confirm_email_confirmation_page, movies_templates_account_login_login_page, movies_templates_account_logout_logout_page [EXTRACTED 1.00]
- **Branded Email Message Templates** — movies_templates_account_email_base_message_email_message_layout, movies_templates_account_email_email_confirmation_message_email_confirmation_message, movies_templates_account_email_email_confirmation_signup_message_signup_confirmation_message, movies_templates_account_email_password_reset_key_message_password_reset_message [EXTRACTED 1.00]
- **Password Recovery Flow** — movies_templates_account_password_reset_done_password_reset_request, movies_templates_account_password_reset_from_key_password_reset, movies_templates_account_password_reset_from_key_done_password_change [EXTRACTED 1.00]
- **Account Lifecycle** — movies_templates_account_signup_account_registration, movies_templates_account_verification_sent_email_confirmation, movies_templates_account_verified_email_required_verified_email_access [INFERRED 0.85]
- **Email Confirmation Content Variants** — movies_templates_account_email_email_confirmation_message_email_confirmation_message, movies_templates_account_email_email_confirmation_message_email_confirmation_plaintext, movies_templates_account_email_email_confirmation_signup_message_signup_confirmation_message, movies_templates_account_email_email_confirmation_signup_message_signup_confirmation_plaintext, movies_templates_account_email_email_confirmation_signup_subject_signup_confirmation_subject, movies_templates_account_email_email_confirmation_subject_email_confirmation_subject [INFERRED 0.85]
- **Google Authentication Flow** — movies_templates_account_signup_google_oauth, movies_templates_socialaccount_login_google_oauth_login, movies_templates_socialaccount_signup_google_oauth_signup [INFERRED 0.85]

## Communities (51 total, 20 thin omitted)

### Community 0 - "Title"
Cohesion: 0.07
Nodes (25): FavoriteAdmin, GenerationAdmin, TitleAdmin, Favorite, Generation, Meta, Tabela gerenciada usada pelo DatabaseCache nas funcoes da Vercel., SharedCacheEntry (+17 more)

### Community 1 - "library.py"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: $security-review utilize essa skill para passar a limpo os problemas e refatoracoes, junto do $graphify, Source Nodes

### Community 2 - "watchmode.py"
Cohesion: 0.07
Nodes (34): dict, HTTPRedirectHandler, ExternalResponseError, NoRedirectHandler, open_json(), Exception, Leitura JSON limitada, sem encaminhar credenciais em redirects., A resposta externa nao e JSON confiavel dentro dos limites locais. (+26 more)

### Community 3 - "views.py"
Cohesion: 0.08
Nodes (46): csrf_exempt, get_library(), is_favorite(), _build_title_payload(), _discovery_cache_key(), _discovery_candidates(), _fetch_title_extras(), _find_streaming_candidate() (+38 more)

### Community 4 - "rate_limit"
Cohesion: 0.07
Nodes (22): consume_rate_limit(), _identifier_key(), _normalise_reset_at(), Persistencia atomica dos contadores de limite de requisicoes., Gera uma chave opaca sem persistir IP, usuario ou escopo em texto aberto., Incrementa um bucket em uma unica instrucao atomica e retorna a decisao., RateLimitBucket, Contador compartilhado dos limites de abuso da aplicacao. (+14 more)

### Community 5 - "site.js"
Cohesion: 0.13
Nodes (17): initFavorites(), initGenerator(), MEDIA_TYPES, NAVIGATION_KEYS, pulseRangeValue(), updateRangeDisplay(), initBrowserHistory(), normaliseBrowserHistory() (+9 more)

### Community 6 - "MovieViewTests"
Cohesion: 0.06
Nodes (7): create_title(), AuthenticationTests, patch, TestCase, MovieViewTests, patch, TestCase

### Community 8 - "tmdb_catalog.py"
Cohesion: 0.16
Nodes (35): fetch_title_extras(), get_genres(), get_movie_release_list(), get_recent_top_titles(), get_title_details(), normalise_release_list_item(), Consultas de catálogo, detalhes e listas do TMDB., Exception (+27 more)

### Community 9 - "home.py"
Cohesion: 0.28
Nodes (14): build_generation_context(), build_home_context(), filter_options_context(), _genre_name(), _landing_context(), parse_ascii_int(), parse_filters(), _parse_min_release_year() (+6 more)

### Community 10 - "Email Message Layout"
Cohesion: 0.33
Nodes (7): Email Message Layout, Email Confirmation Message, Email Confirmation Plaintext Message, Signup Email Confirmation Message, Signup Email Confirmation Plaintext Message, Password Reset Message, Password Reset Plaintext Message

### Community 11 - "Movie and Series Generator"
Cohesion: 0.33
Nodes (7): Movie and Series Generator, Recent Generations, Streaming Availability, TMDB Movie Data, External Services, Privacy Policy, Session and CSRF Security

### Community 12 - "Django"
Cohesion: 0.29
Nodes (7): pip-audit, Ruff, dj-database-url, Django, django-allauth, django-anymail, psycopg

### Community 13 - "context_processors.py"
Cohesion: 0.47
Nodes (5): authentication(), _homepage_json_ld(), _random_movies_json_ld(), Disponibiliza apenas o estado público da integração nos templates., seo_metadata()

### Community 14 - "QualFilmeHojeAccountAdapter"
Cohesion: 0.40
Nodes (3): DefaultAccountAdapter, QualFilmeHojeAccountAdapter, Gera um username legível para cadastros sociais sem sobrescrever escolhas.

### Community 15 - "QualFilmeHojeMFAAdapter"
Cohesion: 0.40
Nodes (3): DefaultMFAAdapter, QualFilmeHojeMFAAdapter, Mantem TOTP obrigatorio enquanto a conta possuir acesso ao admin.

### Community 17 - "Account Entrance Layout"
Cohesion: 0.50
Nodes (4): Account Entrance Layout, Email Confirmation Page, Login Page, Logout Page

### Community 18 - "Password Reset"
Cohesion: 0.50
Nodes (4): Password Reset Request, Password Change, Password Reset, Password Reset Token

### Community 19 - "Google OAuth Login"
Cohesion: 0.50
Nodes (4): Google Authentication Failure, Google OAuth Cancellation, Google OAuth Login, Google OAuth Signup Completion

### Community 20 - "QualFilmeHoje Logo"
Cohesion: 0.67
Nodes (3): Gold Square Frame, Stylized Letter Q, QualFilmeHoje Logo

### Community 21 - "QualFilmeHoje Social Preview"
Cohesion: 0.67
Nodes (3): Cinema Session Discovery, QualFilmeHoje, QualFilmeHoje Social Preview

### Community 22 - "Account Registration"
Cohesion: 0.67
Nodes (3): Account Registration, Google OAuth Registration, Password Strength Guidance

### Community 23 - "Saved Favorites"
Cohesion: 0.67
Nodes (3): Account-Backed Favorites, Saved Favorites, Title Favorites Control

### Community 50 - "test_indexnow.py"
Cohesion: 0.06
Nodes (37): AppConfig, atomic, MoviesConfig, _canonical_url(), Notifica buscadores participantes quando uma URL publica e criada., Monta e envia a URL publica de um filme ou serie validos., Envia uma URL canonica sem propagar falhas para a requisicao do usuario., submit_title_url() (+29 more)

## Knowledge Gaps
- **52 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+47 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Title` connect `Title` to `home.py`, `test_indexnow.py`, `MovieViewTests`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `MovieViewTests` connect `MovieViewTests` to `Title`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `AuthenticationTests` connect `MovieViewTests` to `Title`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Title` (e.g. with `FavoriteAdmin` and `GenerationAdmin`) actually correct?**
  _`Title` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `MovieViewTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`MovieViewTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AuthenticationTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`AuthenticationTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TMDBError` (e.g. with `ExternalResponseError` and `ExternalHTTPTests`) actually correct?**
  _`TMDBError` has 5 INFERRED edges - model-reasoned connections that need verification._