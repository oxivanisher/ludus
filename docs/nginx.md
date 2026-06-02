# Nginx reverse proxy setup

If you prefer Nginx over Traefik, remove the Traefik labels from
`docker-compose.yml` and expose the port directly:

```yaml
# docker-compose.yml addition under ludus service:
ports:
  - "8000:8000"
```

Then use the following Nginx config (place in `/etc/nginx/sites-available/ludus`):

```nginx
server {
    listen 443 ssl http2;
    server_name ludus.example.com;

    ssl_certificate     /etc/letsencrypt/live/ludus.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ludus.example.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;

        # Required for WebSocket upgrade
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host       $host;
        proxy_set_header X-Real-IP  $remote_addr;

        # Prevent idle WebSocket connections from being cut
        proxy_read_timeout 86400;
    }
}

server {
    listen 80;
    server_name ludus.example.com;
    return 301 https://$host$request_uri;
}
```

Enable with:

```bash
ln -s /etc/nginx/sites-available/ludus /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

Use Certbot to obtain the TLS certificate:

```bash
certbot --nginx -d ludus.example.com
```
