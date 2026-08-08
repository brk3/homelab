# homelab

## Notes

- qBittorrent's save path / incomplete-download staging dir (Settings > Downloads) is set manually via its Web UI, not managed in git — the app rewrites its own config on startup, so file-based overrides get silently clobbered.
- Plex needs a one-time claim token to associate a fresh (or `/config`-wiped) server with your Plex account — otherwise it starts unclaimed and won't show up as a server in Plex Web. Get a token from `https://plex.tv/claim` (valid ~4 min) and apply it live: `kubectl -n media set env deployment/plex PLEX_CLAIM=<token>`. Not stored in git since it's single-use and expires in minutes; remove it again once claimed with `kubectl -n media set env deployment/plex PLEX_CLAIM-`.
- Media apps mount their `/config` via `hostPath` with `type: Directory`, which requires the directory to already exist on the node (`/mnt/k3s-data/appdata/<app>`, owned `1000:1000` to match each container's `PUID`/`PGID`) — Kubernetes won't create it. Adding a new app's manifest without first creating its appdata dir leaves the pod stuck in `ContainerCreating` with a `FailedMount` event.

See [secrets.md](secrets.md) for cluster secrets that live outside git and how to recreate them.
