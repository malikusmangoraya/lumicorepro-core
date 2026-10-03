# SSL certificates

## Local development (docker-compose.yml)

`scripts/dev-certs.sh` generates a self-signed certificate into this directory:

```
fullchain.pem   -> build-time only, self-signed
privkey.pem     -> build-time only, self-signed
```

Run it once after cloning, then `docker compose up -d`:

```bash
bash scripts/dev-certs.sh
```

`nginx/nginx.conf` references exactly those two paths and **nginx will refuse to
start without them**, which is deliberate: the previous Compose file published
:443 while the config only listened on :80, so "HTTPS is mapped" was not true.
Browsers will warn about the self-signed certificate — expected locally.

These files are development-only. Do not reuse them anywhere else, and never
commit them (`.gitignore` excludes `nginx/ssl/*.pem`).

## Production (docker-compose.prod.yml)

Production certificates live in `./ssl/certs`, in standard certbot layout:

```
ssl/certs/live/<DOMAIN>/fullchain.pem
ssl/certs/live/<DOMAIN>/privkey.pem
ssl/certs/live/<DOMAIN>/chain.pem
```

This directory (`nginx/ssl`) is **not** mounted in production — the prod Compose
file mounts `./ssl/certs` at `/etc/letsencrypt` instead. The prod edge config is
`nginx/nginx.prod.conf`, which is templated at container start for `${SERVER_NAME}`.

First issuance (once, before the stack can start on :443):

```bash
# 1. Point DNS A/AAAA records for $DOMAIN and www.$DOMAIN at the VPS and make
#    sure ports 80/443 are open, then obtain the certificate with the webroot
#    plugin while nothing else holds :80:
mkdir -p ssl/certs ssl/www
docker run --rm -p 80:80 \
  -v "$PWD/ssl/certs:/etc/letsencrypt" \
  -v "$PWD/ssl/www:/var/www/certbot" \
  certbot/certbot certonly --standalone \
  -d example.com -d www.example.com \
  --email admin@example.com --agree-tos --no-eff-email

# 2. Start the stack; the certbot service then renews every 12h via webroot.
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

Replace `example.com` / `admin@example.com` with the real domain and contact
address. Those values are the only place a host name is needed; nothing else in
the deployment hard-codes it.

See `docs/DEPLOYMENT.md` § TLS for the verification and renewal commands.
