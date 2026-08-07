# Secrets

None of these are stored in git. They're created out-of-band (`kubectl create secret ...`) directly in the cluster. If the `dagda` node/cluster is lost, they must be recreated manually before Flux can fully reconcile.

## Persistent secrets

| Secret | Namespace | Keys | Used by | Purpose |
|---|---|---|---|---|
| `flux-system` | `flux-system` | `username`, `password` | `GitRepository/flux-system` (`clusters/dagda/flux-system/gotk-sync.yaml`) | GitHub credentials Flux uses to pull this repo |
| `cloudflare-api-token-secret` | `cert-manager` | `api-token` | `ClusterIssuer/letsencrypt-staging`, `ClusterIssuer/letsencrypt-prod` (`clusters/dagda/infrastructure/cert-manager/clusterissuer.yaml`) | Cloudflare API token for the Let's Encrypt DNS-01 solver |
| `alertmanager-telegram-config` | `monitoring` | `alertmanager.yaml` | `HelmRelease/victoria-metrics-k8s-stack` via `alertmanager.spec.configSecret` (`clusters/dagda/infrastructure/victoria-metrics-k8s-stack/helmrelease.yaml`) | Alertmanager routes + Telegram bot token/chat ID |
| `homepage-api-keys` | `homepage` | `HOMEPAGE_VAR_SONARR_KEY`, `HOMEPAGE_VAR_RADARR_KEY`, `HOMEPAGE_VAR_PROWLARR_KEY`, `HOMEPAGE_VAR_BAZARR_KEY`, `HOMEPAGE_VAR_PLEX_KEY`, `HOMEPAGE_VAR_QBIT_USER`, `HOMEPAGE_VAR_QBIT_PASS` | `Deployment/homepage` via `envFrom` (`clusters/dagda/apps/homepage/deployment.yaml`), read as `{{HOMEPAGE_VAR_*}}` in `clusters/dagda/apps/homepage/config/services.yaml` | Credentials for the homepage dashboard's media service widgets |

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

### Recreate `homepage-api-keys`

Every value except the qBittorrent WebUI password can be read back out of the running media pods, so this secret is reproducible as long as those apps still have their `/config` PVCs:

```
kubectl exec -n media deploy/sonarr   -c sonarr   -- sh -c "sed -n 's:.*<ApiKey>\(.*\)</ApiKey>.*:\1:p' /config/config.xml"
kubectl exec -n media deploy/radarr   -c radarr   -- sh -c "sed -n 's:.*<ApiKey>\(.*\)</ApiKey>.*:\1:p' /config/config.xml"
kubectl exec -n media deploy/prowlarr -c prowlarr -- sh -c "sed -n 's:.*<ApiKey>\(.*\)</ApiKey>.*:\1:p' /config/config.xml"
kubectl exec -n media deploy/bazarr   -c bazarr   -- sh -c "sed -n '/^\[auth\]/,/^\[/s/^apikey *= *//p' /config/config/config.ini"
kubectl exec -n media deploy/plex     -c plex     -- sh -c "grep -o 'PlexOnlineToken=\"[^\"]*\"' '/config/Library/Application Support/Plex Media Server/Preferences.xml'"
```

Then:

```
kubectl create secret generic homepage-api-keys -n homepage \
  --from-literal=HOMEPAGE_VAR_SONARR_KEY=<key> \
  --from-literal=HOMEPAGE_VAR_RADARR_KEY=<key> \
  --from-literal=HOMEPAGE_VAR_PROWLARR_KEY=<key> \
  --from-literal=HOMEPAGE_VAR_BAZARR_KEY=<key> \
  --from-literal=HOMEPAGE_VAR_PLEX_KEY=<token> \
  --from-literal=HOMEPAGE_VAR_QBIT_USER=admin \
  --from-literal=HOMEPAGE_VAR_QBIT_PASS=<qbittorrent webui password>
```

qBittorrent stores its WebUI password only as a PBKDF2 hash (`WebUI\Password_PBKDF2` in `/config/qBittorrent/qBittorrent.conf`), so it cannot be recovered from the pod — it has to come from a password manager, or be reset in the qBittorrent UI.

After changing any value, restart homepage so it re-reads the env: `kubectl rollout restart -n homepage deploy/homepage`.

## One-time tokens (not persistent secrets)

- **Plex claim token** — needed once to associate a fresh (or `/config`-wiped) Plex server with your account. Get one from `https://plex.tv/claim` (valid ~4 min) and apply it live:
  ```
  kubectl -n media set env deployment/plex PLEX_CLAIM=<token>
  ```
  Not stored in git since it's single-use and expires in minutes. Remove it again once claimed:
  ```
  kubectl -n media set env deployment/plex PLEX_CLAIM-
  ```
