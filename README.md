# QualFilmeHoje

> Um sorteador de filmes e séries para decidir o que assistir hoje — com filtros, detalhes do título, opções de streaming no Brasil e uma lista pessoal de favoritos.

[Acessar a aplicação](https://qualfilmehoje.vercel.app) · [Reportar um problema](https://github.com/Hyant4/QualFilmeHoje/issues)

## Sobre o projeto

O **QualFilmeHoje** ajuda a encontrar um filme ou série a partir de preferências simples: tipo de mídia, gênero, categoria especial, faixa de notas e período de lançamento. Os dados dos títulos são obtidos do [TMDB](https://www.themoviedb.org/), e as opções para assistir no Brasil são consultadas no Watchmode.

Além do sorteio, a aplicação mantém o histórico recente e permite salvar títulos em uma lista, mesmo antes do login. Ao criar uma conta, essa lista é vinculada ao perfil.

## Funcionalidades

- Sorteio de filmes e séries por gênero, nota e ano de lançamento.
- Categorias especiais e filtros distintos para filmes e séries.
- Página de detalhes com sinopse, elenco, trailer, avaliações e links de streaming no Brasil.
- Histórico dos últimos sorteios e lista de favoritos.
- Autenticação por e-mail e, quando configurada, por Google.
- Filtro opcional em linguagem natural: o Gemini converte um pedido curto em filtros já suportados pelo formulário.
- Sitemap, `robots.txt`, metadados para compartilhamento e integração opcional com IndexNow.
- Limites de requisição, proteção CSRF, cabeçalhos de segurança e Content Security Policy (CSP).

## Tecnologias

- Python 3.14 e Django 6
- PostgreSQL/Neon em produção e SQLite para desenvolvimento local
- TMDB e Watchmode
- django-allauth para contas e login social
- Gemini via LangChain, apenas no filtro opcional por linguagem natural
- Vercel para hospedagem
- Ruff e pip-audit na verificação de qualidade e segurança

## Como executar localmente

### Pré-requisitos

- [Python 3.14](https://www.python.org/downloads/) (versão definida em `.python-version`)
- Uma chave de leitura da API do [TMDB](https://developer.themoviedb.org/docs/getting-started)

No PowerShell, execute:

```powershell
git clone https://github.com/Hyant4/QualFilmeHoje.git
cd QualFilmeHoje

py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000) no navegador.

### Variáveis de ambiente

Preencha o arquivo `.env` criado a partir de `.env.example`. Para o primeiro uso local, mantenha `DJANGO_USE_SQLITE=True` e informe pelo menos:

```env
TMDB_ACCESS_TOKEN=seu_token_de_leitura_do_tmdb
```

Integrações opcionais:

| Variáveis | Quando configurar |
| --- | --- |
| `WATCHMODE_API_KEY` | Para mostrar onde assistir no Brasil. |
| `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` | Para habilitar login com Google. |
| `BREVO_API_KEY` e `DEFAULT_FROM_EMAIL` | Para e-mails transacionais em ambiente publicado. |
| `DATABASE_URL` | Para usar PostgreSQL; obrigatório fora do desenvolvimento local. |
| `AI_FILTER_ENABLED=True` e `GEMINI_API_KEY` | Para habilitar o filtro em linguagem natural. |

Nunca publique o arquivo `.env`, tokens de API ou credenciais de banco de dados.

## Qualidade

Com o ambiente virtual ativo:

```powershell
python manage.py test
ruff check . --exclude movies/migrations
pip-audit -r requirements.txt
python manage.py check --deploy
```

## Estrutura do projeto

```text
config/                 # Configurações e rotas globais do Django
movies/
  ai/                   # Contratos, catálogo e adaptador do filtro com Gemini
  services/             # Clientes TMDB/Watchmode e persistência da biblioteca
  use_cases/            # Orquestração da página inicial, títulos e filtros
  templates/            # Páginas HTML
  static/               # CSS, JavaScript e imagens
  tests/                # Testes nativos do Django
ops/                    # Scripts de operação e segurança
docs/                   # Documentação complementar
```

## Rotas principais

| Rota | Descrição |
| --- | --- |
| `/` | Página inicial e formulário do sorteador. |
| `/gerar/` | Processa um novo sorteio. |
| `/titulo/<tipo>/<id>/` | Exibe os detalhes de um filme ou série. |
| `/favoritos/` | Mostra a lista de títulos salvos. |
| `/api/onde-assistir/<tipo>/<id>/` | Retorna os links de streaming de um título. |
| `/api/interpretar-filtro/` | Interpreta texto curto em filtros, se o recurso estiver habilitado. |
| `/sitemap.xml` | Sitemap público. |

## Segurança e privacidade

O projeto utiliza cookies de sessão, autenticação e proteção CSRF. Dados de favoritos e histórico podem ser associados a um identificador de visitante; depois do login, são vinculados à conta. Consulte a [página de privacidade](https://qualfilmehoje.vercel.app/privacidade/) para os detalhes de tratamento de dados e serviços externos.

## Créditos e licença

Este produto usa a API do TMDB, mas não é endossado ou certificado pelo TMDB.

Distribuído sob a [licença MIT](LICENSE).
