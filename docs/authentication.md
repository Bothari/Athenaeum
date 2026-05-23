# Authentication

Athenaeum supports local username/password login and OIDC single sign-on. Both can be enabled simultaneously.

---

## Local login

1. Go to **Settings → Auth** and enable **Form login**
2. Create users from **Settings → Auth → Add user**

The first account created during initial setup is admin. Subsequent users default to the **user** role and can be promoted in **Settings → Auth**.

---

## OIDC (Single Sign-On)

Athenaeum supports any standards-compliant OIDC provider (Authentik, Authelia, Keycloak, Pocket ID, etc.).

### Setup

1. In your provider, create an OAuth2/OIDC application
2. Set the redirect URI to: `{your Athenaeum URL}/auth/oidc/callback`
3. In **Settings → Auth**, fill in:

| Field | Description |
|---|---|
| Provider URL | OIDC issuer URL — Athenaeum auto-discovers endpoints from `{url}/.well-known/openid-configuration` |
| Client ID | OAuth2 client ID from your provider |
| Client Secret | OAuth2 client secret |
| Scopes | Space-separated. `openid email profile` works for most providers |

4. Enable **OIDC login** and save

### Authentik example

1. Create an OAuth2/OIDC provider in Authentik
2. Set redirect URI to `https://athenaeum.example.com/auth/oidc/callback`
3. Copy the issuer URL (e.g. `https://sso.example.com/application/o/athenaeum/`) into **Provider URL**
4. Copy Client ID and Client Secret

### Notes

- Users who sign in via OIDC for the first time are created with the **user** role
- Promote them to admin from **Settings → Auth**
- Add `?force_local` to the login URL to bypass OIDC and use form login (useful if SSO is misconfigured)

---

## Roles

| Role | Capabilities |
|---|---|
| Admin | Full access — settings, sync, approve/reject requests, manage users |
| User | Search, browse library, submit requests (require admin approval) |
