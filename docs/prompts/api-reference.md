# API Reference

Technical documentation for the PromptUploader class and related utilities.

## PromptUploader Class

**File**: `prompts/uploader.py`

```python
class PromptUploader:
    """Uploads .prompt files to Langfuse for centralized management."""
```

---

## Constructor

### `__init__()`

Initialize the PromptUploader from configuration.

```python
def __init__(self):
    """Initialize from config (configs/prompts/uploader.yaml).

    Loads all settings from Dynaconf configuration.
    Override via environment variables if needed.

    Example:
        >>> uploader = PromptUploader()
    """
```

**Configuration Source**: `configs/prompts/uploader.yaml`

**Environment Variables**:
- `LANGFUSE_PUBLIC_KEY`: Langfuse API public key
- `LANGFUSE_SECRET_KEY`: Langfuse API secret key
- `LANGFUSE_HOST`: Langfuse host URL
- `PROMPTS__VERSION`: Prompt version to upload
- `PROMPTS__LABEL`: Environment label (dev/staging/production)

---

## Methods

### `parse_prompt_file()`

Parse a `.prompt` file with YAML frontmatter.

```python
def parse_prompt_file(self, filepath: Path) -> Dict:
    """Parse .prompt file with YAML frontmatter.

    Args:
        filepath: Path to .prompt file

    Returns:
        Dict with:
            - config: Parsed YAML frontmatter
            - template: Prompt template content

    Example:
        >>> parsed = uploader.parse_prompt_file(Path("agent/orchestrator/v1.prompt"))
        >>> print(parsed['config']['temperature'])
        0.3
        >>> print(parsed['template'])
        You are an intent classifier...
    """
```

**File Format**:
```yaml
---
model: gpt-4-turbo
temperature: 0.3
max_tokens: 1000
---

Prompt template content here...
{{ query }}
```

**Returns**:
```python
{
    'config': {
        'model': 'gpt-4-turbo',
        'temperature': 0.3,
        'max_tokens': 1000
    },
    'template': 'Prompt template content here...\n{{ query }}'
}
```

---

### `upload_prompt()`

Upload a single prompt file to Langfuse.

```python
def upload_prompt(self, filepath: Path) -> bool:
    """Upload single prompt file to Langfuse.

    Generates prompt name from directory structure:
    - prompts/agent/orchestrator/v1.prompt → agent_orchestrator
    - prompts/rag/document_retrieval/v1.prompt → rag_document_retrieval

    Args:
        filepath: Path to .prompt file

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = uploader.upload_prompt(Path("prompts/agent/orchestrator/v1.prompt"))
        >>> if success:
        ...     print("Upload successful")
    """
```

**Naming Convention**:
- Directory path is converted to underscore-separated name
- Example: `agent/orchestrator` → `agent_orchestrator`

**Upload Tags**:
- `version`: From configuration (e.g., `v1`)
- `label`: Environment label (e.g., `dev`, `production`)
- `uploaded_at`: Timestamp
- `source_file`: Original file path
- `category`: Top-level directory (e.g., `agent`)

---

### `upload_all()`

Upload all `.prompt` files in the directory (recursive scan).

```python
def upload_all(self) -> List[Dict]:
    """Upload all .prompt files in directory (recursive scan).

    Returns:
        List of results with:
            - filename: Name of .prompt file
            - prompt_name: Generated Langfuse prompt name
            - success: Upload success status

    Example:
        >>> results = uploader.upload_all()
        >>> successful = [r for r in results if r['success']]
        >>> print(f"Uploaded {len(successful)}/{len(results)} prompts")
        Uploaded 4/4 prompts
    """
```

**Returns**:
```python
[
    {
        'filename': 'agent/orchestrator/v1.prompt',
        'prompt_name': 'agent_orchestrator',
        'success': True
    },
    {
        'filename': 'agent/clarification/v1.prompt',
        'prompt_name': 'agent_clarification',
        'success': True
    },
    ...
]
```

---

## Usage Examples

### Basic Upload

```python
from prompts.uploader import PromptUploader

# Initialize uploader
uploader = PromptUploader()

# Upload all prompts
results = uploader.upload_all()

# Check results
for result in results:
    if result['success']:
        print(f"✓ {result['prompt_name']}")
    else:
        print(f"✗ {result['prompt_name']}: {result['error']}")
```

---

### Single Prompt Upload

```python
from pathlib import Path
from prompts.uploader import PromptUploader

uploader = PromptUploader()

# Upload specific prompt
filepath = Path("prompts/agent/orchestrator/v1.prompt")
success = uploader.upload_prompt(filepath)

if success:
    print("Upload successful")
else:
    print("Upload failed")
```

---

### Parse Prompt File

```python
from pathlib import Path
from prompts.uploader import PromptUploader

uploader = PromptUploader()

# Parse prompt file
filepath = Path("prompts/agent/orchestrator/v1.prompt")
parsed = uploader.parse_prompt_file(filepath)

# Access config
print(f"Model: {parsed['config']['model']}")
print(f"Temperature: {parsed['config']['temperature']}")

# Access template
print(f"Template:\n{parsed['template']}")
```

---

## Configuration Reference

### Required Settings

```yaml
prompts:
  directory: prompts           # Root directory
  version: v1                  # Active version
  label: dev                   # Environment label

observability:
  langfuse:
    enabled: true
    public_key: ${LANGFUSE_PUBLIC_KEY}
    secret_key: ${LANGFUSE_SECRET_KEY}
    host: https://cloud.langfuse.com
```

---

## Error Handling

### Common Errors

**Missing Credentials**:
```python
Error: LANGFUSE_PUBLIC_KEY not set
```

**Invalid File Format**:
```python
Error: Missing YAML frontmatter in prompts/agent/test.prompt
```

**Upload Failed**:
```python
Error: Failed to upload agent_orchestrator: Connection timeout
```

---

## Command-Line Interface

### Upload Script

**File**: `scripts/upload_prompts_to_langfuse.py`

```bash
# Upload all prompts
python scripts/upload_prompts_to_langfuse.py

# With environment override
export PROMPTS__VERSION=v2
export PROMPTS__LABEL=production
python scripts/upload_prompts_to_langfuse.py
```

**Output**:
```
Uploading prompts to Langfuse...
✓ agent_orchestrator (v2, production)
✓ agent_clarification (v2, production)
✓ agent_research (v2, production)
✓ agent_synthesis (v2, production)
Uploaded 4/4 prompts successfully
```

---

## Integration with Agents

### Loading Prompts

Agents load prompts from Langfuse at runtime:

```python
from tools.observability.selector import ObservabilitySelector

# Initialize Langfuse client
langfuse = ObservabilitySelector.create(
    provider="langfuse",
    public_key="pk-...",
    secret_key="sk-..."
)

# Fetch prompt
prompt = langfuse.client.get_prompt(
    name="agent_orchestrator",
    label="production"
)

# Compile with variables
compiled = prompt.compile(
    query=user_query,
    history=chat_history
)

# Use in LLM call
response = llm.generate(compiled)
```

**Code Reference**: src/agents/orchestrator.py:42

---

## Next Steps

- [Workflow](./workflow.md) - Use the API in practice
- [Configuration](./configuration.md) - Configure the uploader
- [Langfuse Integration](./langfuse-integration.md) - Upload and manage prompts
