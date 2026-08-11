# Hardening de seguranca

Este documento separa a credencial de migrations da credencial usada pelas
funcoes da Vercel. Nunca salve senhas ou URLs reais neste repositorio.

## 1. Neon com menor privilegio

O papel `neondb_owner` fica reservado para migrations manuais. A aplicacao usa
`qualfilmehoje_app`, sem permissao para criar bancos, papeis, schemas, tabelas
persistentes ou temporarias.
O papel pode ler `django_migrations`, mas não pode inserir, alterar ou excluir
linhas desse histórico.

### Criar o papel

1. Copie a connection string **direta** do Neon para o proprietario.
2. No PowerShell, defina-a apenas no processo atual:

   ```powershell
   $env:DATABASE_URL = '<URL-direta-do-neondb_owner>'
   psql $env:DATABASE_URL -f ops/neon_least_privilege.sql
   Remove-Item Env:DATABASE_URL
   ```

3. No painel do Neon, gere a connection string com pooling para
   `qualfilmehoje_app`. Ela sera a nova `DATABASE_URL` da Vercel.

O script revoga `CREATE` e `TEMPORARY` de `PUBLIC`, pois esses privilegios
tambem seriam herdados pelo papel restrito. Se outra aplicacao compartilhar o
mesmo banco, revise essa decisao antes de executar.

### Validar o papel restrito

Conecte com a URL de `qualfilmehoje_app` e execute:

```sql
SELECT current_user;
SELECT has_database_privilege(current_user, current_database(), 'CREATE');
SELECT has_database_privilege(current_user, current_database(), 'TEMP');
SELECT has_schema_privilege(current_user, 'public', 'CREATE');

-- Deve funcionar:
SELECT COUNT(*) FROM django_migrations;

-- Cada comando abaixo deve falhar com "permission denied":
CREATE TABLE public.security_probe (id integer);
CREATE TEMP TABLE security_probe_temp (id integer);
CREATE ROLE security_probe_role;
CREATE DATABASE security_probe_database;
```

As tres consultas `has_*_privilege` devem retornar `false`. Remova qualquer
objeto `security_probe` caso um teste inesperadamente seja aceito.

### Trocar a Vercel sem interromper o site

1. Execute primeiro todas as migrations pendentes com `neondb_owner`:
   `python manage.py migrate`.
2. Teste a URL restrita localmente com `python manage.py check` e a suite de
   testes; nao rode `migrate` com ela.
3. Adicione a nova `DATABASE_URL` restrita aos ambientes Preview e Production
   da Vercel. Mantenha o mesmo host com pooling e os parametros TLS fornecidos
   pelo Neon.
4. Crie um deployment de Preview e valide home, login, sorteio, favoritos e
   recuperacao de senha.
5. Promova para Production. A alteracao da variavel so alcanca funcoes do novo
   deployment, portanto o deployment anterior segue funcionando durante a
   troca.
6. Depois da validacao, remova a URL de owner da Vercel. Guarde-a somente no
   Neon e use-a localmente em migrations controladas.

Se for necessario reverter, restaure temporariamente a URL anterior na Vercel,
redeploye e corrija os grants antes de tentar novamente. Nao deixe o owner como
credencial permanente de runtime.

## 2. Producao fail-closed

`config/settings.py` identifica Vercel por `VERCEL`/`VERCEL_ENV` e considera
Preview e Production ambientes implantados. Nesses ambientes a inicializacao
agora falha se:

- `DJANGO_DEBUG=True`;
- `DJANGO_SECRET_KEY` estiver ausente, tiver menos de 50 caracteres ou usar um
  placeholder conhecido;
- `DATABASE_URL` estiver ausente ou SQLite estiver habilitado;
- `BREVO_API_KEY` ou `DEFAULT_FROM_EMAIL` estiver ausente.

A confirmacao de e-mail por senha permanece sempre `mandatory`; nao existe mais
fallback para `DummyEmailBackend` nem verificacao `none` em producao.

Antes do proximo deploy, configure na Vercel:

```text
DJANGO_ENV=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<valor aleatorio com pelo menos 50 caracteres>
DJANGO_USE_SQLITE=False
DATABASE_URL=<URL pooled de qualfilmehoje_app>
BREVO_API_KEY=<chave da Brevo>
DEFAULT_FROM_EMAIL=QualFilmeHoje <remetente-verificado@dominio>
```

Gere a chave localmente sem publica-la:

```powershell
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(64))"
```

Para validar, crie um Preview com todas as variaveis e confirme
`python manage.py check --deploy`. Em seguida remova uma variavel somente do
Preview: o deployment deve falhar com `ImproperlyConfigured`, nunca iniciar com
SQLite, DEBUG ou e-mail desativado.

## 3. Abuso de API, cache e rotas somente leitura

O cache de producao agora usa a tabela `qualfilmehoje_cache` no Neon por meio do
`DatabaseCache`. Assim, resultados TMDB/Watchmode, respostas negativas e os
contadores do allauth nao se perdem entre cold starts da Vercel. Execute a
migration `0004_sharedcacheentry` com `neondb_owner` antes de trocar a URL do
runtime:

```powershell
$env:DATABASE_URL = '<URL-direta-do-neondb_owner>'
.venv\Scripts\python.exe manage.py migrate
Remove-Item Env:DATABASE_URL
```

Foram adicionados limites de cinco minutos por IP e, quando autenticado, tambem
por usuario:

- `POST /gerar/`: 30/IP e 20/usuario;
- `GET /titulo/.../`: 120/IP e 90/usuario;
- `POST /favoritos/alternar/`: 60/IP e 40/usuario.

IDs aceitam somente digitos ASCII, no maximo 10 caracteres e uma faixa
positiva limitada. Notas nao aceitam `NaN`/infinito e ficam entre 0 e 10 com
uma casa decimal. Um ID inexistente do TMDB fica em cache negativo por 30
minutos. O Watchmode so e consultado depois que o TMDB confirmou o titulo.

`GET /titulo/.../` nao cria `visitor_id` e nao grava `Title`, `Generation`,
`Favorite` ou `Session`. Se o visitante favoritar um titulo novo, o snapshot e
persistido no POST correspondente. O cache operacional compartilhado pode
gravar apenas sua propria entrada na tabela de cache.

### Firewall da Vercel

O checkout local nao estava vinculado a Vercel e a CLI nao estava instalada,
portanto nenhuma regra externa foi criada silenciosamente. Depois de executar
`vercel link`, rode `ops/vercel-firewall.ps1`. Ele prepara, sem publicar:

1. um rate limit conjunto para `/gerar/` e `/titulo/`, com excedentes apenas
   registrados;
2. uma regra `log` para probes comuns como `/.env` e `/.git/config`;
3. uma regra `log` para observar o acesso ao `/admin/`.

Revise `vercel firewall diff` e o painel de trafego por pelo menos 24 horas.
Somente depois teste bloqueio em Preview. A publicacao final deve ser manual:

```powershell
vercel firewall publish --yes
```

Nao execute esse comando antes de revisar os drafts. Para validar a aplicacao,
rode `python manage.py test movies.tests.test_security` e confirme que a
terceira requisicao no teste controlado retorna 429 com `Retry-After`.

## 4. Senhas, autenticacao e admin

Os quatro validadores nativos do Django estao ativos. Senhas de conta local
precisam ter pelo menos 12 caracteres e nao podem ser comuns, inteiramente
numericas ou semelhantes aos dados do usuario.

Os limites compartilhados do allauth foram reforcados:

- login: 20 tentativas a cada 5 minutos por IP;
- falhas de login: 10/10 minutos por IP e 5/10 minutos por identificador;
- cadastro: 5 por hora por IP;
- pedido de recuperacao: 5 por hora por IP e 3 por e-mail;
- uso do link de recuperacao: 10 por hora por IP.

Na Vercel, o allauth confia em exatamente um proxy e usa o ultimo IP de
`X-Forwarded-For`; no desenvolvimento, o header e ignorado. Isso evita a
falsificacao direta do IP usada para escapar do rate limit.

O login do Django Admin foi substituido por `secure_admin_login`, portanto ele
passa pelo fluxo do allauth. O app `allauth.mfa` habilita TOTP e codigos de
recuperacao mostrados uma unica vez. Uma conta `is_staff` sem TOTP e enviada
para ativacao antes de abrir qualquer pagina de `/admin/`; enquanto continuar
staff, ela nao consegue remover seu ultimo TOTP.

Antes do deploy, rode as migrations de `allauth.mfa` com `neondb_owner`. Para
habilitar um administrador:

1. entre normalmente com a conta staff;
2. acesse `/accounts/2fa/totp/activate/`;
3. leia o QR code em um autenticador e confirme o codigo;
4. guarde os recovery codes fora do computador;
5. saia, entre novamente e confirme que o TOTP e solicitado antes do admin.

Teste automatizado:

```powershell
.venv\Scripts\python.exe manage.py test movies.tests.test_auth
```

Ele confirma que senhas fracas sao recusadas, o admin anonimo redireciona para
o allauth, staff sem TOTP e enviado para ativacao e staff com TOTP entra.

## 5. Content Security Policy

O middleware nativo do Django 6 envia inicialmente apenas
`Content-Security-Policy-Report-Only`. A policy nao aceita script inline nem
`eval`, restringe imagens ao proprio site, TMDB, Watchmode e `data:` (QR do
MFA), frames ao YouTube sem cookies, fontes ao Google Fonts e conexoes/formularios
ao proprio site.

O unico `style=` da pagina web foi removido. A imagem de backdrop agora usa uma
tag `<img>` e CSS externo, preparando a policy para enforcement real.

O endpoint `POST /security/csp-report/` recebe no maximo 16 KiB, aceita ate 20
eventos, remove query strings e nao registra `script-sample`. Ele fica sem CSRF
porque os navegadores enviam esses reports automaticamente, mas possui rate
limit proprio.

Validacao:

1. abra DevTools > Network e confirme o header
   `Content-Security-Policy-Report-Only`;
2. acompanhe os Runtime Logs da Vercel procurando
   `CSP report-only violation`;
3. navegue por home, trailer, login Google, recuperacao, MFA e admin;
4. corrija toda origem legitima ausente e repita ate os falsos positivos
   desaparecerem;
5. somente depois defina `DJANGO_CSP_ENFORCE=True` em Preview;
6. valide novamente e, por ultimo, aplique a variavel em Production.

O teste automatizado confirma o header, a ausencia de `unsafe-inline`, a
redacao de dados sensiveis no report e o limite de corpo:

```powershell
.venv\Scripts\python.exe manage.py test movies.tests.test_security.CSPTests
```

## 6. Respostas e URLs de APIs externas

TMDB, Watchmode e Meta agora usam um leitor JSON comum com timeout, limite de
corpo, `Content-Type` obrigatório e validação do tipo JSON de topo. Redirects
HTTP não são seguidos: isso impede que um `Authorization` ou `X-API-Key` seja
reutilizado pela `urllib` em outro host. Uma resposta incompatível vira erro
recuperável da integração, sem expor o conteúdo externo ao usuário.

Antes de renderizar ou persistir dados externos, o código também:

- aceita apenas IDs decimais ASCII positivos e limitados;
- descarta `NaN`, infinito, datas inválidas e campos acima do tamanho local;
- aceita trailers somente com chave válida do YouTube;
- limita reviews a seis itens e 5.000 caracteres;
- restringe imagens aos hosts oficiais do TMDB/Watchmode;
- restringe reviews ao TMDB e links de streaming a uma allowlist HTTPS;
- recusa URLs com credenciais, porta diferente de 443 ou host disfarçado;

Uma plataforma nova da Watchmode pode exigir a inclusão de seu domínio em
`STREAMING_HOSTS`. Faça isso apenas depois de confirmar o domínio oficial; não
adicione curingas amplos nem volte a aceitar HTTP.

Validação automatizada:

```powershell
.venv\Scripts\python.exe manage.py test `
  movies.tests.test_external_security `
  movies.tests.test_watchmode
```

Os testes cobrem redirect com credencial, tamanho e tipo de JSON, hosts
disfarçados, `javascript:`, HTTP, IDs Unicode, `NaN` e poster externo. Para validar uma nova plataforma, adicione primeiro um caso positivo e
um host disfarçado negativo aos testes de Watchmode.

## 7. Dependências, Python e CI de segurança

Todas as dependências diretas de produção estão fixadas com `==` em
`requirements.txt`, inclusive os extras `mfa` e `socialaccount` do allauth.
Ferramentas usadas apenas na verificação ficam em `requirements-dev.txt`. A
versão de runtime está fixada em Python 3.14 por `.python-version`, arquivo
reconhecido pela Vercel e pelo workflow.

O workflow `.github/workflows/security.yml` roda gratuitamente em pushes para
`main`, pull requests e acionamento manual. Ele executa:

1. instalação das versões fixadas;
2. toda a suíte de testes do Django;
3. análise estática com Ruff, excluindo migrations geradas pelo Django;
4. `manage.py check --deploy --fail-level ERROR` com valores fictícios de CI;
5. `pip-audit` contra `requirements.txt`;
6. Gitleaks em todo o histórico Git.

As próprias GitHub Actions estão presas a hashes de commit, reduzindo o risco
de uma tag de action ser alterada. O `.gitignore` também cobre `.env*` e
`.vercel/`, preservando apenas o exemplo sem segredos.

Validação local:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m pip_audit -r requirements.txt
.venv\Scripts\python.exe manage.py test
```

Depois do push, abra GitHub > Actions > Security checks. Os jobs `django` e
`secrets` precisam ficar verdes. Uma vulnerabilidade nova ou um segredo
detectado deve quebrar o workflow; não ignore o alerta sem investigar. Faça a
atualização de dependência em branch separada, rode novamente todos os testes e
só então altere a versão fixa.

## 8. Sessões, cookies e privacidade

A duração máxima da sessão caiu do padrão de duas semanas para 12 horas e o
cookie expira ao fechar o navegador. O allauth não oferece mais a opção de
"lembrar" a sessão. Permanecem explícitos `HttpOnly` e `SameSite=Lax` para
sessão e CSRF; em produção, ambos continuam com `Secure`. A configuração da
Vercel também aplica `X-Content-Type-Options: nosniff` aos arquivos em
`/static/`, que não passam pelo middleware do Django.

Quando uma senha é trocada, a sessão atual é preservada e todas as outras
sessões autenticadas daquela conta são apagadas. Em uma recuperação de senha,
todas as sessões anteriores são encerradas. A identificação usa o conteúdo
assinado das sessões do Django, não um valor fornecido pelo navegador.

A rota `/privacidade/` explica em linguagem direta:

- dados anônimos, dados da conta e lista;
- cookies técnicos e seu prazo;
- login Google sem armazenamento do token;
- uso de TMDB, Watchmode, Brevo, Google, Vercel e Neon;
- retenção, segurança e escolhas do usuário.

Há links para a política no rodapé da home e nas telas de autenticação. Não foi
adicionado banner: o site não configura publicidade nem cookies opcionais de
análise. Se isso mudar no futuro, a política e o mecanismo de consentimento
devem ser revistos antes de ativar a nova ferramenta.

Validação:

```powershell
.venv\Scripts\python.exe manage.py test `
  movies.tests.test_auth.AuthenticationTests.test_password_change_invalidates_other_sessions_only `
  movies.tests.test_auth.AuthenticationTests.test_session_lifetime_and_privacy_page
```

Manualmente, entre na mesma conta em dois navegadores, troque a senha em um
deles e atualize o outro: ele deve voltar ao estado deslogado. Abra
`/privacidade/` em desktop e celular e confira os links do rodapé. O DevTools
deve mostrar `Secure`, `HttpOnly` e `SameSite=Lax` no cookie de sessão do site
em produção.
