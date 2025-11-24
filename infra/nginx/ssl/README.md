# SSL Certificates

For production, place your SSL certificates here:
- `cert.pem` - SSL certificate
- `key.pem` - SSL private key

For development, you can generate self-signed certificates:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

Then uncomment the HTTPS server block in `conf.d/default.conf`.

