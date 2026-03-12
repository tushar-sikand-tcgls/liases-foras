# AWS Deployment Guide for Liases Foras

This guide explains how to deploy the Liases Foras application to AWS and fix common Docker build issues.

## Problem Analysis

The error you encountered:
```
ERROR: failed to solve: failed to compute cache key: "/app/config.py": not found
```

This occurs when:
1. **Missing Dockerfile**: No Dockerfile exists in the repository
2. **Wrong build context**: Docker build context doesn't include necessary files
3. **Missing .dockerignore**: Important files might be excluded
4. **.gitignore conflicts**: CI/CD pulls code via git, and .gitignore might exclude needed files

## Solution

### 1. Files Created

I've created the following files to resolve your issue:

- **`Dockerfile`** - Standard multi-stage Docker build
- **`Dockerfile.aws`** - AWS-optimized build (smaller, faster, more secure)
- **`.dockerignore`** - Prevents unnecessary files from bloating the image
- **`docker-compose.yml`** - Local development setup
- **`.github/workflows/aws-deploy.yml`** - GitHub Actions CI/CD pipeline

### 2. Dockerfile Comparison

**`Dockerfile`** (Standard):
- Full-featured build
- Includes all dependencies
- Suitable for development and testing

**`Dockerfile.aws`** (Production):
- Multi-stage build (smaller image size)
- Non-root user (better security)
- Optimized layer caching
- Health checks included
- Recommended for AWS deployment

## AWS Deployment Options

### Option A: AWS ECS (Elastic Container Service)

**Prerequisites:**
- AWS CLI installed and configured
- Docker installed locally
- AWS account with appropriate permissions

**Steps:**

1. **Create ECR Repository**
```bash
aws ecr create-repository \
    --repository-name liases-foras \
    --region us-east-1
```

2. **Login to ECR**
```bash
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    <your-account-id>.dkr.ecr.us-east-1.amazonaws.com
```

3. **Build and Push Image**
```bash
# Build using AWS-optimized Dockerfile
docker build -t liases-foras:latest -f Dockerfile.aws .

# Tag for ECR
docker tag liases-foras:latest \
    <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/liases-foras:latest

# Push to ECR
docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/liases-foras:latest
```

4. **Create ECS Task Definition**
```bash
# Create task-definition.json (see template below)
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

5. **Create ECS Service**
```bash
aws ecs create-service \
    --cluster liases-foras-cluster \
    --service-name liases-foras-service \
    --task-definition liases-foras-task \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}"
```

### Option B: AWS App Runner

**Simpler alternative for containerized apps:**

1. **Create App Runner Service**
```bash
aws apprunner create-service \
    --service-name liases-foras \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "<your-account-id>.dkr.ecr.us-east-1.amazonaws.com/liases-foras:latest",
            "ImageRepositoryType": "ECR",
            "ImageConfiguration": {
                "Port": "8000",
                "RuntimeEnvironmentVariables": {
                    "FASTAPI_HOST": "0.0.0.0",
                    "FASTAPI_PORT": "8000"
                }
            }
        },
        "AutoDeploymentsEnabled": true
    }' \
    --instance-configuration '{
        "Cpu": "1 vCPU",
        "Memory": "2 GB"
    }'
```

### Option C: AWS Elastic Beanstalk

**Managed platform for web applications:**

1. **Install EB CLI**
```bash
pip install awsebcli
```

2. **Initialize Elastic Beanstalk**
```bash
eb init -p docker liases-foras --region us-east-1
```

3. **Create Environment**
```bash
eb create liases-foras-env
```

4. **Deploy**
```bash
eb deploy
```

## CI/CD Pipeline Setup (GitHub Actions)

The `.github/workflows/aws-deploy.yml` file provides automated deployment.

**Required GitHub Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**To set up:**
1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Add the required secrets
3. Push to `main` branch to trigger deployment

## ECS Task Definition Template

Create `task-definition.json`:

```json
{
  "family": "liases-foras-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "liases-foras-app",
      "image": "<your-account-id>.dkr.ecr.us-east-1.amazonaws.com/liases-foras:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "FASTAPI_HOST",
          "value": "0.0.0.0"
        },
        {
          "name": "FASTAPI_PORT",
          "value": "8000"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/liases-foras",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/api/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

## Environment Variables

For production deployment, create a `.env.production` file (never commit this):

```bash
# Copy from template
cp .env.production.example .env.production

# Edit with your production values
nano .env.production
```

**For AWS deployments**, set environment variables in:
- **ECS**: Task definition environment section
- **App Runner**: Configuration → Environment variables
- **Elastic Beanstalk**: Configuration → Software → Environment properties

## Troubleshooting CI/CD Build Errors

### Error: "COPY requirements.txt .: not found"

**Cause**: Build context doesn't include the file

**Solutions**:
1. ✅ Ensure Dockerfile is in the repository root
2. ✅ Check `.dockerignore` doesn't exclude `requirements.txt`
3. ✅ Verify build command uses correct context: `docker build -t app .` (note the `.` at the end)
4. ✅ If using custom build context, specify it: `docker build -t app -f Dockerfile.aws .`

### Error: "failed to compute cache key"

**Cause**: File referenced in COPY doesn't exist in build context

**Solutions**:
1. ✅ Run `ls -la` to verify files exist
2. ✅ Check if files are in `.gitignore` (CI/CD uses git clone)
3. ✅ Ensure build context path is correct
4. ✅ Use `.dockerignore` to control what's included

### Error: Permission denied

**Cause**: Non-root user can't write to directories

**Solution** (already in Dockerfile.aws):
```dockerfile
RUN mkdir -p /app/output /app/logs && \
    chmod -R 755 /app/output /app/logs && \
    chown -R appuser:appuser /app
```

## Testing Locally

Before deploying to AWS, test locally:

```bash
# Build the image
docker build -t liases-foras:latest -f Dockerfile.aws .

# Run the container
docker run -p 8000:8000 \
    --env-file .env.production \
    liases-foras:latest

# Test health endpoint
curl http://localhost:8000/api/health

# Or use docker-compose
docker-compose up
```

## Performance Optimization

The AWS-optimized Dockerfile (`Dockerfile.aws`) includes:

1. **Multi-stage build**: Reduces final image size by ~40%
2. **Layer caching**: Faster subsequent builds
3. **Non-root user**: Security best practice
4. **Health checks**: Automatic container health monitoring
5. **Minimal base image**: `python:3.11-slim` instead of full Python image

## Cost Optimization

**Recommendations**:
- Use **Fargate Spot** for ECS (up to 70% cheaper)
- Enable **Auto Scaling** based on CPU/memory
- Use **Application Load Balancer** with health checks
- Configure **CloudWatch alarms** for cost monitoring

## Support

For issues:
1. Check CloudWatch Logs: `/ecs/liases-foras`
2. Verify health check: `curl http://<your-alb>/api/health`
3. Review ECS task status: `aws ecs describe-tasks ...`

## Next Steps

1. ✅ Review and customize the Dockerfiles
2. ✅ Test locally with `docker-compose up`
3. ✅ Choose deployment option (ECS recommended)
4. ✅ Set up AWS infrastructure
5. ✅ Configure GitHub Actions secrets
6. ✅ Push to trigger automated deployment
