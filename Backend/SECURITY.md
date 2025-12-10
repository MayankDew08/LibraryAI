# Security Notice

## Important: Protect Your Credentials

This application contains sensitive information. Follow these security practices:

### 1. Environment Variables (.env)
- ✅ `.env` is in `.gitignore` - NEVER commit it
- ✅ Use `.env.example` as a template (credentials removed)
- ✅ Update `.env` with real credentials locally only

### 2. Database Password
Current password: `bhoolgaya`
- Change it to something stronger in production
- Use environment variables only
- Never hardcode in source files

### 3. API Keys
- Get Gemini API key from: https://aistudio.google.com/app/apikey
- Add to `.env` file only
- Never share or commit API keys

### 4. Before Deploying
- [ ] Use strong database password
- [ ] Use strong SECRET_KEY (generate with: `openssl rand -hex 32`)
- [ ] Set `echo=False` in database.py
- [ ] Use HTTPS in production
- [ ] Restrict CORS origins
- [ ] Enable firewall rules for MySQL

### 5. File Permissions
```bash
# Restrict .env file permissions (Linux/Mac)
chmod 600 .env

# Windows - Right click .env → Properties → Security → Edit
```

### 6. Production Checklist
- [ ] Change all default passwords
- [ ] Use secrets management (AWS Secrets Manager, Azure Key Vault, etc.)
- [ ] Enable MySQL SSL connections
- [ ] Use connection pooling limits
- [ ] Set up database backups
- [ ] Monitor for suspicious activity

## What's Protected
- ✅ Database password: In `.env` only
- ✅ API keys: In `.env` only
- ✅ Secret keys: In `.env` only
- ✅ `.env` file: Added to `.gitignore`

## Never Commit
- `.env` file
- Database dumps with real data
- API keys or tokens
- SSH keys or certificates
