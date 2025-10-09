# Azure Deployment Fix Guide - Classic Editor

## Problem Identified
The error "ModuleNotFoundError: No module named 'uvicorn'" occurs because:
1. The Archive Files task is creating a nested folder structure in the zip
2. Azure Oryx build system can't find `requirements.txt` at the zip root
3. Dependencies are not being installed

## Solution Overview
We've added configuration files and you need to fix your Build Pipeline settings.

---

## Step 1: Commit New Configuration Files

**New files added to your project:**
- `.deployment` - Tells Azure to build during deployment
- `startup.sh` - Custom startup script (optional)
- `requirements.txt` - Updated with pinned versions

**Commit and push these files:**
```bash
git add .deployment requirements.txt startup.sh
git commit -m "Add Azure deployment configuration"
git push origin main
```

---

## Step 2: Fix Build Pipeline (Classic Editor)

### Open Your Build Pipeline
1. Go to **Azure DevOps** → **Pipelines** → **Pipelines**
2. Select your build pipeline → Click **Edit**

### Configure Tasks in This Order:

#### **Task 1: Use Python Version**
- Display name: `Use Python 3.12`
- Version spec: `3.12`
- ✅ Keep as-is

#### **Task 2: Bash Script - Install Dependencies**
- Display name: `Install dependencies`
- Type: `Inline`
- Script:
  ```bash
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```
- Working Directory: `$(System.DefaultWorkingDirectory)`
- ✅ Keep as-is

#### **Task 3: Archive Files** ⚠️ **CRITICAL - FIX THIS**

**Click on Archive Files task and verify these settings:**

| Setting | Value | Critical |
|---------|-------|----------|
| **Root folder or file to archive** | `$(System.DefaultWorkingDirectory)` | ✅ MUST BE THIS |
| **Prepend root folder name to archive paths** | ❌ **UNCHECKED** | ⚠️ **CRITICAL** |
| **Archive type** | `zip` | ✅ |
| **Archive file to create** | `$(Build.ArtifactStagingDirectory)/$(Build.BuildId).zip` | ✅ |
| **Replace existing archive** | ✅ Checked | ✅ |
| **Verbose logging** | ✅ Checked | Recommended |

**Screenshot of what it should look like:**
```
Root folder: $(System.DefaultWorkingDirectory)
[ ] Prepend root folder name  <-- MUST BE UNCHECKED!
Archive type: zip
Archive file: $(Build.ArtifactStagingDirectory)/$(Build.BuildId).zip
[✓] Replace existing archive
```

#### **Task 4: Publish Build Artifacts**
- Display name: `Publish Artifact: drop`
- Path to publish: `$(Build.ArtifactStagingDirectory)/$(Build.BuildId).zip`
- Artifact name: `drop`
- Artifact publish location: `Azure Pipelines`
- ✅ Keep as-is

### ⚠️ Remove Any Extra Tasks
- **Remove** any `CopyFiles@2` tasks (not needed)
- **Keep only** the 4 tasks listed above

### Save Build Pipeline
- Click **Save** (top right)
- Add comment: "Fix archive structure for Azure deployment"
- Click **Save**

---

## Step 3: Update Release Pipeline

### Open Your Release Pipeline
1. Go to **Pipelines** → **Releases**
2. Select your release pipeline → Click **Edit**

### Update Deploy Azure App Service Task

1. Click on **Tasks** tab
2. Click on **Production** (or your stage name)
3. Click on **Deploy Azure App Service** task

**Configure these settings:**

| Setting | Value |
|---------|-------|
| **Azure subscription** | (your subscription) |
| **App type** | `Web App on Linux` |
| **App Service name** | `allvy-rfp-pythonservice` |
| **Package or folder** | `$(System.DefaultWorkingDirectory)/_<your-build-pipeline-name>/drop/$(Build.BuildId).zip` |

**⚠️ Note:** Replace `<your-build-pipeline-name>` with your actual build pipeline name

**Expand "Application and Configuration Settings":**
- **Runtime Stack**: Leave blank (will use App Service config)
- **Startup command**: 
  ```bash
  gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 600 --access-logfile "-" --error-logfile "-" main:app
  ```

### Save Release Pipeline
- Click **Save** (top right)
- Click **OK**

---

## Step 4: Configure Azure App Service

### In Azure Portal:

1. Go to **Azure Portal** → **App Services** → **allvy-rfp-pythonservice**

2. **Configuration** → **Application settings**:
   
   Add/verify these settings:
   ```
   AZURE_OPENAI_API_KEY = <your-key>
   AZURE_OPENAI_ENDPOINT = <your-endpoint>
   AZURE_OPENAI_MODEL = gpt-5-mini
   AZURE_OPENAI_API_VERSION = 2024-12-01-preview
   SCM_DO_BUILD_DURING_DEPLOYMENT = true
   ```
   
   Click **Save** → **Continue**

3. **Configuration** → **General settings**:
   
   - **Stack**: `Python`
   - **Python version**: `3.12`
   - **Startup Command**:
     ```bash
     gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 600 --access-logfile "-" --error-logfile "-" main:app
     ```
   
   Click **Save** → **Continue**

4. **Deployment Center** (optional verification):
   
   - Ensure it shows your Azure DevOps connection
   - Build provider should be `Azure Pipelines`

---

## Step 5: Deploy and Verify

### Trigger New Build

1. In Azure DevOps → **Pipelines** → Select your pipeline
2. Click **Run pipeline** → **Run**

### Monitor Build Logs

Watch for these success indicators:
```
Archive Files:
Found 15 files
Creating archive: /home/vsts/work/1/a/<buildid>.zip
Archiving file: main.py
Archiving file: requirements.txt
Archiving file: .deployment
...
Successfully created archive
```

### Monitor Release Logs

After build succeeds:
1. Go to **Pipelines** → **Releases**
2. Click on the new release
3. Click on **Production** stage → **Logs**

### Monitor Azure App Service Logs

1. In Azure Portal → Your App Service
2. Click **Log stream** (under Monitoring)

**Look for these success messages:**
```
Starting OpenBSD Secure Shell server: sshd.
Oryx Version: ...
Build Operation ID: ...
Detecting platforms...
Detected following platforms:
  python: 3.12.11
Running 'pip install -r requirements.txt'
Successfully installed fastapi uvicorn gunicorn...
Starting gunicorn...
[INFO] Starting gunicorn 23.0.0
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Using worker: uvicorn.workers.UvicornWorker
Application startup complete.
```

---

## Step 6: Test Deployed API

### Test Endpoints

1. **Root endpoint:**
   ```bash
   curl https://allvy-rfp-pythonservice.azurewebsites.net/
   ```
   Expected: `{"message":"RFP Processing Pipeline API","version":"1.0.0"}`

2. **Health check:**
   ```bash
   curl https://allvy-rfp-pythonservice.azurewebsites.net/health/
   ```
   Expected: `{"status":"ok","message":"Service is running"}`

3. **API Docs:**
   Visit: `https://allvy-rfp-pythonservice.azurewebsites.net/docs`

---

## Troubleshooting

### Issue: "Found 0 files" in Archive task
**Solution:** 
- Ensure `Root folder` is `$(System.DefaultWorkingDirectory)`
- Ensure `Prepend root folder` is **UNCHECKED**

### Issue: "ModuleNotFoundError: No module named 'uvicorn'"
**Solution:**
- Verify `.deployment` file exists in repo
- Check `SCM_DO_BUILD_DURING_DEPLOYMENT=true` in App Service settings
- Ensure `requirements.txt` is at root of zip (check build logs)

### Issue: "Container didn't respond to HTTP pings"
**Solution:**
- Verify startup command uses `0.0.0.0` not `127.0.0.1`
- Increase startup timeout in App Service Configuration
- Check if port 8000 is specified correctly

### Issue: ZIP structure is wrong
**Verify zip contents should look like:**
```
archive.zip
├── main.py
├── requirements.txt
├── .deployment
├── run_server.py
├── README.md
└── src/
    ├── __init__.py
    ├── pipeline/
    ├── llm_extractor/
    └── excel_convertor/
```

**NOT like this (WRONG):**
```
archive.zip
└── rfp_new_pipeline/     <-- Extra nested folder!
    ├── main.py
    ├── requirements.txt
    └── ...
```

---

## Key Takeaways

✅ **Critical Setting:** Archive Files task must have "Prepend root folder" **UNCHECKED**
✅ **Build Trigger:** `.deployment` file enables Oryx to build on Azure
✅ **Dependencies:** Pinned versions in `requirements.txt` prevent compatibility issues
✅ **Startup Command:** Must use `0.0.0.0:8000` for Azure container networking

---

## Quick Verification Checklist

Before running pipeline, verify:

- [ ] `.deployment` file committed and pushed
- [ ] `requirements.txt` has pinned versions
- [ ] Archive Files task: `Prepend root folder` is **UNCHECKED**
- [ ] Archive Files task: Root folder is `$(System.DefaultWorkingDirectory)`
- [ ] Release pipeline: Package path includes `$(Build.BuildId).zip`
- [ ] Azure App Service: `SCM_DO_BUILD_DURING_DEPLOYMENT = true`
- [ ] Azure App Service: Startup command configured
- [ ] Azure App Service: Environment variables set (API keys)

---

## Need Help?

If deployment still fails:
1. Check Build logs → Archive Files task → Should show 15+ files
2. Check Release logs → Deploy task → Look for error messages
3. Check Azure Log Stream → Look for Python/pip errors
4. Download the artifact zip and verify structure manually

