# Setup único — Google Ads API (skill `google-ads`)

Pré-requisito já pronto: o OAuth client do AdMob
(`~/.config/bobagi-google/admob-client.json`). Faltam 2 peças, ambas do
OPERADOR (~10 min + espera de aprovação do Google):

## 1. Developer token (Central da API do Google Ads)

1. Abra o **Google Ads** logado na conta dona da campanha.
2. Menu **Ferramentas e configurações** (chave inglesa) → **Configuração** →
   **Central da API** (API Center).
   - Se não aparecer, a conta precisa estar no modo Especialista e com
     faturamento configurado.
3. Aceite os termos → copie o **token de desenvolvedor**.
4. O token nasce com acesso **"Conta de teste"** (não lê a conta real!). Na
   mesma tela, clique **"Solicitar acesso básico"** e preencha o formulário
   (uso: relatórios internos da própria conta; ferramenta própria/CLI; sem
   revenda). Aprovação típica: **1–3 dias úteis** (chega e-mail).
5. Salve o token na VPS:
   ```bash
   python3 ~/.claude/skills/google-ads/scripts/gads.py set-config --developer-token 'SEU_TOKEN'
   ```

## 2. Consentimento OAuth (escopo adwords)

```bash
python3 ~/.claude/skills/google-ads/scripts/gads.py auth
```
Abra a URL impressa no SEU navegador (conta dona do Ads), aceite, e cole de
volta o `code` da barra de endereços (mesmo fluxo que o AdMob usou).

> Se o consent screen do GCP estiver "Testando": confira se o seu e-mail está
> em test users, e lembre que o refresh token expira em 7 dias (publicar o
> consent screen resolve de vez).

## 3. Validar

```bash
python3 ~/.claude/skills/google-ads/scripts/gads.py doctor
```
Esperado: OAuth ok, versão da API detectada, sua conta listada (o script fixa
o `customer_id` sozinho se houver só uma). Enquanto o acesso Básico não for
aprovado, o doctor falha com a explicação `DEVELOPER_TOKEN_NOT_APPROVED` —
é só aguardar o e-mail e rodar de novo.
