# NEXA Operations Runbook

## Service Management
**Start the platform:**
```bash
docker-compose up -d
```

**Stop the platform:**
```bash
docker-compose down
```

**Restart the API service:**
```bash
docker-compose restart nexa-platform
```

## Monitoring & Logs
**View all logs:**
```bash
docker-compose logs -f
```

**Check service health manually:**
```bash
curl -I http://localhost/api/health
```
*Expected: HTTP/1.1 200 OK*

## Troubleshooting
**Issue: Application fails to start, throwing Python errors.**
- **Diagnosis**: Python dependencies may not be correctly installed, or the environment lacks the correct binary.
- **Resolution**: Check the docker build logs for `pip install` failures. Ensure memory mapping limits aren't exceeded if models are being cached on startup.

**Issue: High latency or 502 Bad Gateway.**
- **Diagnosis**: Node.js backend has crashed or is overloaded, causing NGINX to fail proxying.
- **Resolution**: Check `docker-compose logs nexa-platform`. If OOM killed, increase memory limit in VM. Check `express-rate-limit` logs to see if legit traffic is being dropped.

**Issue: Mobile App cannot connect.**
- **Diagnosis**: Ensure the device is connected to the exact same network if testing locally, or that the production domain is correctly resolving. Ensure the mobile app's `http` targets use HTTPS in production.
