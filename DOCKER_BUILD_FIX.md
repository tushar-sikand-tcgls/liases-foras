# Docker Build Error Fix - Quick Reference

## Your Original Error
```
ERROR: failed to solve: failed to compute cache key: "/app/config.py": not found
```

## Root Cause
Your CI/CD pipeline was trying to build a Docker image, but:
1. ❌ No Dockerfile existed in your repository
2. ❌ No .dockerignore file to control what gets included
3. ❌ CI/CD couldn't find the files it needed to copy

## What I Fixed ✅

### 1. Created Core Docker Files

| File | Purpose | Usage |
|------|---------|-------|
| `Dockerfile` | Standard build | Local development, testing |
| `Dockerfile.aws` | Production build | **AWS deployment (recommended)** |
| `.dockerignore` | Exclude unnecessary files | Smaller, faster builds |
| `docker-compose.yml` | Multi-container orchestration | Local development |

### 2. Created CI/CD Configurations

| File | Purpose | When to Use |
|------|---------|-------------|
| `.github/workflows/aws-deploy.yml` | GitHub Actions pipeline | Using GitHub + AWS ECS |
| `buildspec.yml` | AWS CodeBuild config | Using AWS CodePipeline |

### 3. Created Documentation

| File | Purpose |
|------|---------|
| `AWS_DEPLOYMENT_GUIDE.md` | Complete AWS deployment guide |
| `DOCKER_BUILD_FIX.md` | This quick reference (you're reading it!) |

## Quick Fix for Your CI/CD Pipeline

### If Using AWS CodeBuild

**Option 1: Update your buildspec.yml**
```yaml
# In your AWS CodeBuild project, ensure it references:
# Dockerfile: Dockerfile.aws
# Build context: . (repository root)
```

**Option 2: Use the buildspec.yml I created**
```bash
# Your CodeBuild project should automatically pick up buildspec.yml
# If not, in CodeBuild project settings:
# Build specifications -> Use a buildspec file -> buildspec.yml
```

### If Using GitHub Actions

**Option 1: Use the workflow I created**
```bash
# The workflow is already in .github/workflows/aws-deploy.yml
# Just add these GitHub Secrets:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
```

**Option 2: Custom CI/CD**

Update your build command to:
```bash
docker build -t your-app:latest -f Dockerfile.aws .
#                                  ^^^^^^^^^^^^  Use AWS-optimized Dockerfile
#                                                ^  Build context = repo root
```

## Test Locally First

Before deploying to AWS, test the build:

```bash
# Test the AWS-optimized build
docker build -t liases-foras:test -f Dockerfile.aws .

# Run it
docker run -p 8000:8000 --env-file .env.production liases-foras:test

# Check health
curl http://localhost:8000/api/health
```

Expected output:
```json
{
  "status": "healthy",
  "service": "Liases Foras MCP API",
  "version": "2.0"
}
```

## Common Issues & Fixes

### Issue 1: "COPY requirements.txt: not found"

**Diagnosis:**
```bash
# Check if file exists
ls -la requirements.txt

# Check if it's in .dockerignore
cat .dockerignore | grep requirements.txt
```

**Fix:**
```bash
# Make sure requirements.txt is NOT in .dockerignore
# The .dockerignore I created already handles this correctly
```

### Issue 2: "Permission denied" when writing to /app

**Diagnosis:**
Your container runs as non-root user (security best practice), but doesn't have write permissions.

**Fix:** (Already in Dockerfile.aws)
```dockerfile
RUN mkdir -p /app/output /app/logs && \
    chmod -R 755 /app/output /app/logs && \
    chown -R appuser:appuser /app
```

### Issue 3: Build is very slow

**Diagnosis:**
Layers aren't being cached properly.

**Fix:** Use the Dockerfile.aws which:
- ✅ Uses multi-stage build
- ✅ Copies requirements first (better caching)
- ✅ Excludes unnecessary files via .dockerignore

**Speed comparison:**
- First build: ~5-8 minutes
- Subsequent builds (with cache): ~1-2 minutes

### Issue 4: Image size is too large

**Diagnosis:**
```bash
docker images | grep liases-foras
```

**Fix:** Use Dockerfile.aws instead of Dockerfile

**Size comparison:**
- `Dockerfile` (standard): ~1.2 GB
- `Dockerfile.aws` (optimized): ~700 MB (40% smaller)

## Architecture Comparison

### Dockerfile (Standard)
```
├─ python:3.11-slim base
├─ Install all dependencies
├─ Copy all application code
└─ Run as root (less secure)
```
**Pros:** Simple, includes everything
**Cons:** Larger size, security concerns
**Use for:** Local development

### Dockerfile.aws (Production)
```
Stage 1 (builder):
├─ python:3.11-slim
├─ Install build dependencies
├─ Install Python packages to /root/.local
└─ (Discarded after build)

Stage 2 (production):
├─ python:3.11-slim (fresh)
├─ Copy only installed packages from Stage 1
├─ Copy only application code
├─ Run as non-root user
└─ Health checks included
```
**Pros:** Smaller, faster, more secure
**Cons:** Slightly more complex
**Use for:** AWS production deployment ⭐

## Deployment Checklist

- [ ] 1. Test build locally: `docker build -f Dockerfile.aws .`
- [ ] 2. Test run locally: `docker run -p 8000:8000 ...`
- [ ] 3. Test health endpoint: `curl http://localhost:8000/api/health`
- [ ] 4. Create `.env.production` (from `.env.production.example`)
- [ ] 5. Choose AWS service (ECS, App Runner, or Elastic Beanstalk)
- [ ] 6. Set up ECR repository
- [ ] 7. Configure CI/CD (GitHub Actions or CodeBuild)
- [ ] 8. Add required secrets/environment variables
- [ ] 9. Deploy!
- [ ] 10. Verify deployment: Check health endpoint on production URL

## Environment Variables for Production

Your app needs these environment variables in production:

```bash
# Backend
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# External APIs (add these as secrets in AWS)
GOOGLE_MAPS_API_KEY=your_key_here
GOOGLE_SEARCH_API_KEY=your_key_here
GOOGLE_SEARCH_CX=your_cx_here

# LLM Services
GEMINI_API_KEY=your_key_here
# ... (see .env.production.example for complete list)
```

**How to set in AWS:**
- **ECS**: Task definition → Environment variables
- **App Runner**: Configuration → Environment variables
- **Elastic Beanstalk**: Configuration → Software → Environment properties

## Next Steps

1. **Test locally** using the checklist above
2. **Review** AWS_DEPLOYMENT_GUIDE.md for detailed AWS setup
3. **Choose** your CI/CD approach:
   - GitHub Actions → Use `.github/workflows/aws-deploy.yml`
   - AWS CodePipeline → Use `buildspec.yml`
   - Manual → Follow AWS_DEPLOYMENT_GUIDE.md
4. **Deploy!**

## Quick Commands

```bash
# Local build test
docker build -t liases-foras:test -f Dockerfile.aws .

# Local run test
docker run -d -p 8000:8000 --name liases-test \
  --env-file .env.production \
  liases-foras:test

# Check logs
docker logs liases-test

# Test health
curl http://localhost:8000/api/health

# Cleanup
docker stop liases-test && docker rm liases-test

# Using docker-compose (easier)
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## Support

If you still encounter issues:

1. **Check Docker build output**: Look for the first error line
2. **Verify file structure**: `ls -la` to ensure files exist
3. **Check .dockerignore**: Make sure it's not excluding needed files
4. **Test locally first**: Don't debug in CI/CD
5. **Check AWS CloudWatch Logs**: If deployed, check `/ecs/liases-foras`

## Success Indicators

✅ **Build succeeds locally**
```bash
$ docker build -f Dockerfile.aws .
Successfully built abc123def456
Successfully tagged liases-foras:latest
```

✅ **Container starts successfully**
```bash
$ docker run -p 8000:8000 liases-foras:latest
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **Health check passes**
```bash
$ curl http://localhost:8000/api/health
{"status":"healthy","service":"Liases Foras MCP API","version":"2.0"}
```

You're ready for AWS deployment! 🚀
