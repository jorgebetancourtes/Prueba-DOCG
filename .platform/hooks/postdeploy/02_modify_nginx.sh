#!/bin/bash
set -e

# Backup original nginx.conf
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak

# Insert server blocks inside http { } using HEREDOC
sed -i '/http {/r /dev/stdin' /etc/nginx/nginx.conf <<'EOF'
    server {
        listen 80;
        server_name url_app;

        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl;
        server_name url_app;

        ssl_certificate /etc/letsencrypt/live/url_app/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/url_app/privkey.pem;

        client_max_body_size 50M;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
EOF

# Validate nginx configuration
nginx -t

# Restart nginx to apply changes
service nginx restart
