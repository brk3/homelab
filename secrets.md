# Secrets

None of these are stored in git. They're created out-of-band (`kubectl create secret ...`) directly in the cluster. If the `dagda` node/cluster is lost, they must be recreated manually before Flux can fully reconcile.

## Persistent secrets

| Secret | Namespace | Keys | Used by | Purpose |
|---|---|---|---|---|
| `flux-system` | `flux-system` | `username`, `password` | `GitRepository/flux-system` (`clusters/dagda/flux-system/gotk-sync.yaml`) | GitHub credentials Flux uses to pull this repo |
| `cloudflare-api-token-secret` | `cert-manager` | `api-token` | `ClusterIssuer/letsencrypt-staging`, `ClusterIssuer/letsencrypt-prod` (`clusters/dagda/infrastructure/cert-manager/clusterissuer.yaml`) | Cloudflare API token for the Let's Encrypt DNS-01 solver |
| `alertmanager-telegram-config` | `monitoring` | `alertmanager.yaml` | `HelmRelease/victoria-metrics-k8s-stack` via `alertmanager.spec.configSecret` (`clusters/dagda/infrastructure/victoria-metrics-k8s-stack/helmrelease.yaml`) | Alertmanager routes + Telegram bot token/chat ID |
| `flux-telegram-token` | `flux-system` | `token` | `Provider/telegram` (`clusters/dagda/flux-system/notifications.yaml`) | Telegram bot token for Flux notification-controller alerts (e.g. image automation commits) |
| `forgejo-runner-registration` | `forgejo` | `token` | `Deployment/forgejo-runner` (`clusters/dagda/apps/forgejo/runner-deployment.yaml`) | Registers the Actions runner against the Forgejo instance. Unlike Plex's claim token, this is a reusable/persistent credential, not one-time. |

### Recreate `flux-system`

```
flux bootstrap github --owner=brk3 --repository=homelab --path=clusters/dagda --token-auth
```

or manually:

```
kubectl create secret generic flux-system -n flux-system \
  --from-literal=username=git --from-literal=password=<PAT>
```

### Recreate `cloudflare-api-token-secret`

```
kubectl create secret generic cloudflare-api-token-secret -n cert-manager \
  --from-literal=api-token=<token>
```

### Recreate `alertmanager-telegram-config`

Single key `alertmanager.yaml`, holding a standard Alertmanager config (routes + a Telegram receiver with `bot_token`/`chat_id`), per VMAlertmanager's `configSecret` convention:

```
kubectl create secret generic alertmanager-telegram-config -n monitoring \
  --from-file=alertmanager.yaml=<path-to-config>
```

The `alertmanager.yaml` content itself isn't backed up anywhere yet — recreating this secret after total loss requires rewriting that config (routes + Telegram bot token/chat ID) from scratch.

### Recreate `flux-telegram-token`

```
kubectl create secret generic flux-telegram-token -n flux-system \
  --from-literal=token=<bot-token>
```

Can reuse the same bot as `alertmanager-telegram-config` — this just needs its own secret since Flux's notification-controller expects a bare `token` key rather than a full Alertmanager config. The chat ID goes unencrypted in `Provider/telegram`'s `spec.channel` (`clusters/dagda/flux-system/notifications.yaml`), not in this secret.

### Recreate `forgejo-runner-registration`

Generate a fresh token from the running Forgejo instance (Admin UI → `/admin/actions/runners`, or via CLI), then create the secret:

```
kubectl exec -n forgejo deploy/forgejo -- su-exec 1000:1000 forgejo forgejo-cli actions generate-runner-token
kubectl create secret generic forgejo-runner-registration -n forgejo --from-literal=token=<token>
```

The Forgejo image runs its entrypoint as root (s6-overlay init), so any `forgejo` CLI subcommand must be run as `su-exec 1000:1000` to act as the app's actual user — running as root fails with "Forgejo is not supposed to be run as root."

## One-time tokens (not persistent secrets)

- **Plex claim token** — needed once to associate a fresh (or `/config`-wiped) Plex server with your account. Get one from `https://plex.tv/claim` (valid ~4 min) and apply it live:
  ```
  kubectl -n media set env deployment/plex PLEX_CLAIM=<token>
  ```
  Not stored in git since it's single-use and expires in minutes. Remove it again once claimed:
  ```
  kubectl -n media set env deployment/plex PLEX_CLAIM-
  ```

- **Forgejo admin user** — `INSTALL_LOCK=true` skips the interactive web installer, so the first admin account has to be created directly once the pod is up:
  ```
  kubectl exec -n forgejo deploy/forgejo -- su-exec 1000:1000 forgejo admin user create \
    --username <x> --password <y> --email <z> --admin
  ```
  Credentials live in the account owner's password manager only, same as any other login — not stored in git or in this file.
