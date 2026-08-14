# Disaster recovery

Everything but two secrets is git-native: Flux reconciles `clusters/dagda`, and app/infra
secrets are SOPS-encrypted alongside the components that use them (`apps` and
`infrastructure` Kustomizations both carry `spec.decryption`).

## If dagda is lost entirely

1. Install k3s.
2. Recreate the hostPath dirs apps expect under `/mnt/k3s-data/appdata/<app>`, owned `1000:1000`.
3. Install flux-operator — it can't bootstrap itself from git:
   ```
   helm install flux-operator oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator \
     -n flux-system --create-namespace
   ```
4. Recreate the two bootstrap secrets below, from the password manager.
5. `kubectl apply -f clusters/dagda/flux-system/flux-instance.yaml`

Flux takes it from there: `infrastructure` and `apps` reconcile, decrypt every SOPS secret
automatically, and everything else in the cluster is either git-managed or self-generates
(TLS certs, ACME account keys, admin passwords, etc).

## The two secrets that stay manual

Both live in the password manager. Neither can be encrypted in git — `flux-system` is needed
before Flux exists to decrypt anything, and `sops-age` is the key everything else decrypts
with.

```
kubectl create secret generic flux-system -n flux-system \
  --from-literal=username=git --from-literal=password=<GitHub PAT>

kubectl create secret generic sops-age -n flux-system \
  --from-file=age.agekey=<age private key>
```

If `sops-age` is lost without a backup, every SOPS-encrypted secret in git becomes permanently
undecryptable and has to be recreated from scratch — same as before SOPS existed.

## Secrets that regenerate, not recreate

- **`forgejo-runner-registration`** — meant to be regenerated, not preserved:
  ```
  kubectl exec -n forgejo deploy/forgejo -- su-exec 1000:1000 forgejo forgejo-cli actions generate-runner-token
  kubectl create secret generic forgejo-runner-registration -n forgejo --from-literal=token=<token>
  ```
  (Forgejo's entrypoint runs as root; any `forgejo` subcommand needs `su-exec 1000:1000` or it
  refuses to run.)

- **Plex claim token** — one-time, ~4 min TTL, from `https://plex.tv/claim`:
  ```
  kubectl -n media set env deployment/plex PLEX_CLAIM=<token>
  kubectl -n media set env deployment/plex PLEX_CLAIM-
  ```

- **Forgejo admin user** — `INSTALL_LOCK=true` skips the web installer:
  ```
  kubectl exec -n forgejo deploy/forgejo -- su-exec 1000:1000 forgejo admin user create \
    --username <x> --password <y> --email <z> --admin
  ```
  Credentials live in the password manager, not here.

## Everything else

SOPS-encrypted `secret.yaml` files live next to the component that uses them (e.g.
`clusters/dagda/infrastructure/cert-manager/secret.yaml`). To read or edit one locally:

```
sops clusters/dagda/<path>/secret.yaml
```

requires `SOPS_AGE_KEY_FILE` (or `~/.config/sops/age/keys.txt`) pointing at the private key.

## Not covered here

Off-node data backup (Forgejo, `habits`) — parked for later, not implemented yet.
