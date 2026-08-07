# Secrets

None of these are stored in git. They're created out-of-band (`kubectl create secret ...`) directly in the cluster. If the `dagda` node/cluster is lost, they must be recreated manually before Flux can fully reconcile.

## Persistent secrets

| Secret | Namespace | Keys | Used by | Purpose |
|---|---|---|---|---|
| `flux-system` | `flux-system` | `username`, `password` | `GitRepository/flux-system` (`clusters/dagda/flux-system/gotk-sync.yaml`) | GitHub credentials Flux uses to pull this repo |
| `cloudflare-api-token-secret` | `cert-manager` | `api-token` | `ClusterIssuer/letsencrypt-staging`, `ClusterIssuer/letsencrypt-prod` (`clusters/dagda/infrastructure/cert-manager/clusterissuer.yaml`) | Cloudflare API token for the Let's Encrypt DNS-01 solver |
| `alertmanager-telegram-config` | `monitoring` | `alertmanager.yaml` | `HelmRelease/victoria-metrics-k8s-stack` via `alertmanager.spec.configSecret` (`clusters/dagda/infrastructure/victoria-metrics-k8s-stack/helmrelease.yaml`) | Alertmanager routes + Telegram bot token/chat ID |

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

## One-time tokens (not persistent secrets)

- **Plex claim token** — needed once to associate a fresh (or `/config`-wiped) Plex server with your account. Get one from `https://plex.tv/claim` (valid ~4 min) and apply it live:
  ```
  kubectl -n media set env deployment/plex PLEX_CLAIM=<token>
  ```
  Not stored in git since it's single-use and expires in minutes. Remove it again once claimed:
  ```
  kubectl -n media set env deployment/plex PLEX_CLAIM-
  ```
