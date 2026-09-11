# SSL Certificates Directory

This directory is mounted to `/etc/nginx/ssl` inside the `lumicorepro-nginx` container.

## Production Setup (Let's Encrypt / Certbot)
To enable HTTPS in production:

1. Obtain SSL certificates using Certbot:
   ```bash
   certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com
   ```

2. Copy or link your certificates into this folder:
   - `fullchain.pem` -> `/etc/nginx/ssl/fullchain.pem`
   - `privkey.pem`   -> `/etc/nginx/ssl/privkey.pem`

3. In `nginx.conf`, uncomment the HTTPS server block:
   ```nginx
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;

       ssl_certificate /etc/nginx/ssl/fullchain.pem;
       ssl_certificate_key /etc/nginx/ssl/privkey.pem;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       ...
   }
   ```

## Development / Self-Signed Certificate
For local HTTPS testing, generate a self-signed certificate:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/server.key \
  -out nginx/ssl/server.crt \
  -subj "/C=US/ST=State/L=City/O=LumiCorePro/OU=Dev/CN=localhost"
```
