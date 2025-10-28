# Configuration

Settings and environment variables for prompt management.

## Configuration File

All settings are in `configs/prompts/uploader.yaml`:

```yaml
# Prompt Uploader Configuration
prompts:
  directory: prompts             # Directory containing .prompt files
  file_pattern: "*.prompt"       # File pattern to match
  version: v1                    # Prompt version tag
  label: dev                     # Environment label
  batch_upload: true             # Upload all prompts in batch
  overwrite_existing: true       # Overwrite existing prompts

# Langfuse Configuration
observability:
  langfuse:
    enabled: true
    provider: langfuse
    public_key: null             # Set via LANGFUSE_PUBLIC_KEY env var
    secret_key: null             # Set via LANGFUSE_SECRET_KEY env var
    host: https://cloud.langfuse.com
```

---

## Environment Variables

Override configuration via environment variables:

### Prompt Settings

```bash
export PROMPTS__DIRECTORY=prompts
export PROMPTS__FILE_PATTERN="*.prompt"
export PROMPTS__VERSION=v2
export PROMPTS__LABEL=production
export PROMPTS__BATCH_UPLOAD=true
export PROMPTS__OVERWRITE_EXISTING=true
```

### Langfuse Settings

```bash
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
export LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## Configuration Parameters

### `prompts.directory`

**Type**: String
**Default**: `prompts`
**Description**: Root directory containing `.prompt` files

**Example:**
```yaml
prompts:
  directory: prompts  # Scans ./prompts/ directory
```

---

### `prompts.file_pattern`

**Type**: String
**Default**: `*.prompt`
**Description**: Glob pattern to match prompt files

**Example:**
```yaml
prompts:
  file_pattern: "*.prompt"  # Matches v1.prompt, v2.prompt, etc.
```

---

### `prompts.version`

**Type**: String
**Default**: `v1`
**Description**: Active prompt version to upload

**Example:**
```yaml
prompts:
  version: v2  # Upload v2.prompt files
```

---

### `prompts.label`

**Type**: String
**Default**: `dev`
**Options**: `dev`, `staging`, `production`
**Description**: Environment label for deployment

**Example:**
```yaml
prompts:
  label: production  # Tag prompts for production
```

---

### `prompts.batch_upload`

**Type**: Boolean
**Default**: `true`
**Description**: Upload all prompts in a single batch

**Example:**
```yaml
prompts:
  batch_upload: true  # Upload all prompts at once
```

---

### `prompts.overwrite_existing`

**Type**: Boolean
**Default**: `true`
**Description**: Overwrite existing prompts in Langfuse

**Example:**
```yaml
prompts:
  overwrite_existing: true  # Update existing prompts
```

---

## Environment-Specific Configuration

### Development Environment

```yaml
prompts:
  version: v1
  label: dev
  overwrite_existing: true
```

```bash
export PROMPTS__VERSION=v1
export PROMPTS__LABEL=dev
```

---

### Staging Environment

```yaml
prompts:
  version: v2
  label: staging
  overwrite_existing: true
```

```bash
export PROMPTS__VERSION=v2
export PROMPTS__LABEL=staging
```

---

### Production Environment

```yaml
prompts:
  version: v3
  label: production
  overwrite_existing: false  # Prevent accidental overwrites
```

```bash
export PROMPTS__VERSION=v3
export PROMPTS__LABEL=production
export PROMPTS__OVERWRITE_EXISTING=false
```

---

## Dynaconf Configuration

The system uses [Dynaconf](https://www.dynaconf.com/) for configuration management.

### Features

- **Environment variables**: Override any setting
- **Multiple formats**: YAML, JSON, TOML, .env
- **Environment-aware**: dev, staging, production
- **Validation**: Type checking and defaults

### Usage

```python
from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["configs/prompts/uploader.yaml"]
)

# Access settings
directory = settings.prompts.directory
version = settings.prompts.version
label = settings.prompts.label
```

---

## Security Best Practices

### Credential Management

1. **Never commit credentials**: Use `.env` files (gitignored)
2. **Environment variables**: Set credentials via env vars
3. **Rotate keys**: Update API keys periodically
4. **Limit access**: Control who has Langfuse credentials

### .env File

```bash
# .env (gitignored)
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Loading .env

```bash
# Load .env before running script
source .env
python scripts/upload_prompts_to_langfuse.py
```

---

## Configuration Validation

### Required Settings

The following must be set:

- `prompts.directory`: Must exist and contain `.prompt` files
- `prompts.version`: Must match existing prompt files (e.g., `v1.prompt`)
- `langfuse.public_key`: Required for Langfuse uploads
- `langfuse.secret_key`: Required for Langfuse uploads

### Validation Errors

```bash
# Missing credentials
Error: LANGFUSE_PUBLIC_KEY not set

# Invalid version
Error: No files matching pattern prompts/*/v99.prompt

# Invalid directory
Error: Directory 'prompts' does not exist
```

---

## Next Steps

- [Workflow](./workflow.md) - Step-by-step prompt development
- [Langfuse Integration](./langfuse-integration.md) - Upload and manage prompts
- [API Reference](./api-reference.md) - PromptUploader class documentation
