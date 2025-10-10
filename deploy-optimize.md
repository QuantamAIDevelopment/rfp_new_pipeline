# Deployment Optimization

## Safe Changes (No functionality loss):

1. **Use .dockerignore** - Excludes large files from upload
2. **--no-cache-dir** - Faster pip installs
3. **Exclude output folders** - Don't upload temp files

## Deployment Steps:

1. Delete these folders before zipping:
   - `output/`
   - `uploads/`
   - `results/`
   - `__pycache__/`

2. Use `requirements-minimal.txt` (same packages, just removed unused aiofiles)

3. Add to Azure App Settings:
   ```
   WEBSITE_PYTHON_DEFAULT_VERSION = 3.11
   SCM_DO_BUILD_DURING_DEPLOYMENT = true
   ```

## Expected Reduction:
- From 30 minutes → 15-20 minutes
- Smaller zip file size
- Faster package installation

**No functionality will be lost** - all core packages remain the same.