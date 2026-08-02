# homelab

## Notes

- qBittorrent's save path / incomplete-download staging dir (Settings > Downloads) is set manually via its Web UI, not managed in git — the app rewrites its own config on startup, so file-based overrides get silently clobbered.
- Plex needs a one-time claim token to associate a fresh (or `/config`-wiped) server with your Plex account — otherwise it starts unclaimed and won't show up as a server in Plex Web. Get a token from `https://plex.tv/claim` (valid ~4 min) and apply it live: `kubectl -n media set env deployment/plex PLEX_CLAIM=<token>`. Not stored in git since it's single-use and expires in minutes; remove it again once claimed with `kubectl -n media set env deployment/plex PLEX_CLAIM-`.

## Disaster recovery: secrets not in git

These are created out-of-band (`kubectl create secret ...`) and intentionally excluded from git. If the `dagda` node/cluster is lost, they must be recreated manually before Flux can fully reconcile:

- `flux-system` (namespace `flux-system`, keys `username`/`password`) — GitHub credentials Flux uses to pull this repo. Recreate via `flux bootstrap github --owner=brk3 --repository=homelab --path=clusters/dagda --token-auth` (prompts for a GitHub PAT), or manually with `kubectl create secret generic flux-system -n flux-system --from-literal=username=git --from-literal=password=<PAT>`.
- `cloudflare-api-token-secret` (namespace `cert-manager`, key `api-token`) — Cloudflare API token used by the DNS-01 solver in the Let's Encrypt `ClusterIssuer`s. Recreate with `kubectl create secret generic cloudflare-api-token-secret -n cert-manager --from-literal=api-token=<token>`.
