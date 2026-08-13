# Graph Report - .  (2026-08-13)

## Corpus Check
- 83 files · ~69,293 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 459 nodes · 852 edges · 48 communities (32 shown, 16 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 77 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Title & models.py
- views.py & library.py
- test_external_security.py & watchmode.py
- tmdb.py & TMDBError
- TMDBNotFound & SEOMetadataTests
- site.js & loadStreamingLinks
- MovieViewTests & patch
- AuthenticationTests & .create_user
- TMDBServiceTests & patch
- signals.py & _invalidate_user_sessions
- Email Message Layout & Email Confirmation Message
- Movie and Series Generator & External Services
- Django & pip-audit
- context_processors.py & seo_metadata
- QualFilmeHojeAccountAdapter & DefaultAccountAdapter
- QualFilmeHojeMFAAdapter & DefaultMFAAdapter
- AdminMFAMiddleware & middleware.py
- Account Entrance Layout & Email Confirmation Page
- Password Reset & Password Reset Request
- Google OAuth Login & Google Authentication Failure
- QualFilmeHoje Logo & Gold Square Frame
- QualFilmeHoje Social Preview & Cinema Session Discovery
- Account Registration & Google OAuth Registration
- Saved Favorites & Account-Backed Favorites
- vercel.json & headers
- Security Hardening Plan & Security Checks Workflow
- 0001_initial.py & Migration
- 0002_favorite_user_generation_user_and_more.py & Migration
- 0003_whatsappcontact.py & Migration
- 0004_sharedcacheentry.py & Migration
- 0005_remove_whatsapp_integration.py & Migration
- Signup Email Confirmation Subject & Email Confirmation Subject
- Email Confirmation & Email Verification
- Email Confirmation Flow & Verified Email Access Control
- Graphify Workflow Guidance
- Home Movie Viewing Scene
- Home Cinema Viewing Scene
- Password Reset Subject
- python-dotenv

## God Nodes (most connected - your core abstractions)
1. `Title` - 26 edges
2. `MovieViewTests` - 26 edges
3. `AuthenticationTests` - 23 edges
4. `TMDBError` - 21 edges
5. `TMDBNotFound` - 18 edges
6. `TMDBServiceTests` - 18 edges
7. `ExternalResponseError` - 16 edges
8. `get_streaming_groups()` - 16 edges
9. `_build_title_payload()` - 15 edges
10. `get_random_title()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `pip-audit` --conceptually_related_to--> `Django`  [INFERRED]
  requirements-dev.txt → requirements.txt
- `Ruff` --conceptually_related_to--> `Django`  [INFERRED]
  requirements-dev.txt → requirements.txt
- `AuthenticationTests` --uses--> `Title`  [INFERRED]
  movies/tests/test_auth.py → movies/models.py
- `SEOEndpointsTests` --uses--> `Title`  [INFERRED]
  movies/tests/test_seo.py → movies/models.py
- `SEOMetadataTests` --uses--> `Title`  [INFERRED]
  movies/tests/test_seo.py → movies/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Account Entrance Templates** — movies_templates_account_base_entrance_account_entrance_layout, movies_templates_account_email_confirm_email_confirmation_page, movies_templates_account_login_login_page, movies_templates_account_logout_logout_page [EXTRACTED 1.00]
- **Branded Email Message Templates** — movies_templates_account_email_base_message_email_message_layout, movies_templates_account_email_email_confirmation_message_email_confirmation_message, movies_templates_account_email_email_confirmation_signup_message_signup_confirmation_message, movies_templates_account_email_password_reset_key_message_password_reset_message [EXTRACTED 1.00]
- **Email Confirmation Content Variants** — movies_templates_account_email_email_confirmation_message_email_confirmation_message, movies_templates_account_email_email_confirmation_message_email_confirmation_plaintext, movies_templates_account_email_email_confirmation_signup_message_signup_confirmation_message, movies_templates_account_email_email_confirmation_signup_message_signup_confirmation_plaintext, movies_templates_account_email_email_confirmation_signup_subject_signup_confirmation_subject, movies_templates_account_email_email_confirmation_subject_email_confirmation_subject [INFERRED 0.85]
- **Account Lifecycle** — movies_templates_account_signup_account_registration, movies_templates_account_verification_sent_email_confirmation, movies_templates_account_verified_email_required_verified_email_access [INFERRED 0.85]
- **Password Recovery Flow** — movies_templates_account_password_reset_done_password_reset_request, movies_templates_account_password_reset_from_key_password_reset, movies_templates_account_password_reset_from_key_done_password_change [EXTRACTED 1.00]
- **Google Authentication Flow** — movies_templates_account_signup_google_oauth, movies_templates_socialaccount_login_google_oauth_login, movies_templates_socialaccount_signup_google_oauth_signup [INFERRED 0.85]

## Communities (48 total, 16 thin omitted)

### Community 0 - "Title & models.py"
Cohesion: 0.07
Nodes (28): FavoriteAdmin, GenerationAdmin, TitleAdmin, Favorite, Generation, Meta, Tabela gerenciada usada pelo DatabaseCache nas funcoes da Vercel., SharedCacheEntry (+20 more)

### Community 1 - "views.py & library.py"
Cohesion: 0.08
Nodes (49): atomic, csrf_exempt, _consume(), get_client_ip(), _identifier_digest(), rate_limit(), Controles de abuso que funcionam em varias instancias serverless., Retorna IP normalizado; so confia em XFF quando a Vercel e o proxy. (+41 more)

### Community 2 - "test_external_security.py & watchmode.py"
Cohesion: 0.08
Nodes (31): HTTPRedirectHandler, ExternalResponseError, NoRedirectHandler, open_json(), Exception, Leitura JSON limitada, sem encaminhar credenciais em redirects., A resposta externa nao e JSON confiavel dentro dos limites locais., _host_is_allowed() (+23 more)

### Community 3 - "tmdb.py & TMDBError"
Cohesion: 0.15
Nodes (40): _as_dict(), _as_list(), _build_title_payload(), _choose_trailer(), _crew_jobs(), _discovery_cache_key(), _discovery_candidates(), _fetch_title_extras() (+32 more)

### Community 4 - "TMDBNotFound & SEOMetadataTests"
Cohesion: 0.07
Nodes (16): O ID foi validado, mas nao existe no catalogo do TMDB., TMDBNotFound, ApplicationRateLimitTests, CSPTests, DeploymentHeaderTests, ExternalLookupOrderingTests, InputValidationTests, override_settings (+8 more)

### Community 5 - "site.js & loadStreamingLinks"
Cohesion: 0.07
Nodes (27): browserHistory, cardStep(), generatedHistoryData, generatorForm, genreFields, loadStreamingLinks(), manualMove(), maxRatingInput (+19 more)

### Community 6 - "MovieViewTests & patch"
Cohesion: 0.13
Nodes (3): MovieViewTests, patch, TestCase

### Community 7 - "AuthenticationTests & .create_user"
Cohesion: 0.15
Nodes (3): AuthenticationTests, patch, TestCase

### Community 8 - "TMDBServiceTests & patch"
Cohesion: 0.19
Nodes (4): get_random_movie(), patch, SimpleTestCase, TMDBServiceTests

### Community 9 - "signals.py & _invalidate_user_sessions"
Cohesion: 0.23
Nodes (9): AppConfig, MoviesConfig, invalidate_other_sessions_on_password_change(), invalidate_sessions_on_password_reset(), _invalidate_user_sessions(), merge_library_on_login(), Mantém favoritos e sorteios feitos antes de o visitante entrar., Remove sessões autenticadas do usuário sem confiar em dados do cliente. (+1 more)

### Community 10 - "Email Message Layout & Email Confirmation Message"
Cohesion: 0.33
Nodes (7): Email Message Layout, Email Confirmation Message, Email Confirmation Plaintext Message, Signup Email Confirmation Message, Signup Email Confirmation Plaintext Message, Password Reset Message, Password Reset Plaintext Message

### Community 11 - "Movie and Series Generator & External Services"
Cohesion: 0.33
Nodes (7): Movie and Series Generator, Recent Generations, Streaming Availability, TMDB Movie Data, External Services, Privacy Policy, Session and CSRF Security

### Community 12 - "Django & pip-audit"
Cohesion: 0.29
Nodes (7): pip-audit, Ruff, dj-database-url, Django, django-allauth, django-anymail, psycopg

### Community 13 - "context_processors.py & seo_metadata"
Cohesion: 0.47
Nodes (5): authentication(), _homepage_json_ld(), _random_movies_json_ld(), Disponibiliza apenas o estado público da integração nos templates., seo_metadata()

### Community 14 - "QualFilmeHojeAccountAdapter & DefaultAccountAdapter"
Cohesion: 0.40
Nodes (3): DefaultAccountAdapter, QualFilmeHojeAccountAdapter, Gera um username legível para cadastros sociais sem sobrescrever escolhas.

### Community 15 - "QualFilmeHojeMFAAdapter & DefaultMFAAdapter"
Cohesion: 0.40
Nodes (3): DefaultMFAAdapter, QualFilmeHojeMFAAdapter, Mantem TOTP obrigatorio enquanto a conta possuir acesso ao admin.

### Community 17 - "Account Entrance Layout & Email Confirmation Page"
Cohesion: 0.50
Nodes (4): Account Entrance Layout, Email Confirmation Page, Login Page, Logout Page

### Community 18 - "Password Reset & Password Reset Request"
Cohesion: 0.50
Nodes (4): Password Reset Request, Password Change, Password Reset, Password Reset Token

### Community 19 - "Google OAuth Login & Google Authentication Failure"
Cohesion: 0.50
Nodes (4): Google Authentication Failure, Google OAuth Cancellation, Google OAuth Login, Google OAuth Signup Completion

### Community 20 - "QualFilmeHoje Logo & Gold Square Frame"
Cohesion: 0.67
Nodes (3): Gold Square Frame, Stylized Letter Q, QualFilmeHoje Logo

### Community 21 - "QualFilmeHoje Social Preview & Cinema Session Discovery"
Cohesion: 0.67
Nodes (3): Cinema Session Discovery, QualFilmeHoje, QualFilmeHoje Social Preview

### Community 22 - "Account Registration & Google OAuth Registration"
Cohesion: 0.67
Nodes (3): Account Registration, Google OAuth Registration, Password Strength Guidance

### Community 23 - "Saved Favorites & Account-Backed Favorites"
Cohesion: 0.67
Nodes (3): Account-Backed Favorites, Saved Favorites, Title Favorites Control

## Knowledge Gaps
- **61 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Title` connect `Title & models.py` to `views.py & library.py`, `TMDBNotFound & SEOMetadataTests`, `MovieViewTests & patch`, `AuthenticationTests & .create_user`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `MovieViewTests` connect `MovieViewTests & patch` to `Title & models.py`, `tmdb.py & TMDBError`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `TMDBError` connect `tmdb.py & TMDBError` to `Title & models.py`, `views.py & library.py`, `test_external_security.py & watchmode.py`, `TMDBNotFound & SEOMetadataTests`, `MovieViewTests & patch`, `TMDBServiceTests & patch`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Title` (e.g. with `FavoriteAdmin` and `GenerationAdmin`) actually correct?**
  _`Title` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `MovieViewTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`MovieViewTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AuthenticationTests` (e.g. with `Favorite` and `Generation`) actually correct?**
  _`AuthenticationTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `TMDBError` (e.g. with `ExternalResponseError` and `WatchmodeError`) actually correct?**
  _`TMDBError` has 6 INFERRED edges - model-reasoned connections that need verification._