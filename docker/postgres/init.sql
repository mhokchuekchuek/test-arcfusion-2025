-- Initialize databases for LiteLLM and Langfuse

-- Create LiteLLM database
CREATE DATABASE litellm;

-- Create Langfuse database
CREATE DATABASE langfuse;

-- Grant all privileges to postgres user (default user)
GRANT ALL PRIVILEGES ON DATABASE litellm TO postgres;
GRANT ALL PRIVILEGES ON DATABASE langfuse TO postgres;
