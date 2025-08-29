Here’s the full content — you can copy it into a file named MULTI_MODEL_TESTING.md inside your swe_agent_litellm folder:

markdown
Copy
Edit
## Testing the SWE Agent with Multiple Models and Providers

### 0) Install + Basics
```bash
pip install litellm duckduckgo-search requests
1) OpenAI (GPT family)
Set a key (or pass --api-key each run):

bash
Copy
Edit
export OPENAI_API_KEY=sk-...    # or use --api-key
python -m swe_agent_litellm.main --model gpt-4o-mini "Create a README"
2) Anthropic (Claude family)
bash
Copy
Edit
export ANTHROPIC_API_KEY=sk-ant-...
python -m swe_agent_litellm.main --model claude-3-5-sonnet-20241022 "Create a README"
3) Mistral
bash
Copy
Edit
export MISTRAL_API_KEY=sk-...
python -m swe_agent_litellm.main --model mistral/mistral-large-latest "Create a README"
4) Azure OpenAI
You’ll need your deployment name + endpoint:

bash
Copy
Edit
export AZURE_API_KEY=...
export AZURE_API_BASE="https://<your-resource>.openai.azure.com"
python -m swe_agent_litellm.main --model azure/<deployment_name> "Create a README"
5) Try Fallback Chains (mix providers)
bash
Copy
Edit
python -m swe_agent_litellm.main \
  --model gpt-4o-mini \
  --models claude-3-5-sonnet-20241022,mistral/mistral-large-latest \
  "Create a README"
6) Quick Smoke Tests
bash
Copy
Edit
python -m swe_agent_litellm.main --max-iterations 1 --model gpt-4o-mini "Say hello then stop."
python -m swe_agent_litellm.main --max-iterations 1 --model claude-3-5-sonnet-20241022 "Say hello then stop."
7) Mini “Matrix” Test Script
bash
Copy
Edit
MODELS=(
  "gpt-4o-mini"
  "claude-3-5-sonnet-20241022"
  "mistral/mistral-large-latest"
)
for m in "${MODELS[@]}"; do
  echo "=== Testing $m ==="
  python -m swe_agent_litellm.main --max-iterations 1 --model "$m" "Say the model name you are."
done
8) Debugging
Turn on verbose LiteLLM logs:

bash
Copy
Edit
export LITELLM_LOG=DEBUG
# or inside code: litellm._turn_on_debug()
9) Pass Key via Flag
bash
Copy
Edit
python -m swe_agent_litellm.main \
  --model gpt-4o-mini \
  --api-key sk-... \
  "Create a README"
10) Notes
If you see “messages with role tool must respond to tool_calls”: update to the latest build.

To avoid resuming an old run, delete .swe_agent_professional_state.pkl in your working dir or run with a fresh --working-dir.

pgsql
Copy
Edit

Do you want me to also include this `.md` file in the ZIP I gave you earlier so it’s bundled with the code?
