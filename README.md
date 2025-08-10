# hosted-api

Minimal Python client for GPT-OSS with streaming.

## Setup

- Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Usage

- Stream a response from GPT-OSS:

```bash
python run_gpt_oss.py "Say hi quickly" --model gpt-oss-120b
```

Optional flags:
- `--reasoning {low,medium,high}` (default: high)
- `--proxy http://127.0.0.1:7890`

## Files
- `gpt_oss_provider.py`: GptOss provider with SSE streaming
- `run_gpt_oss.py`: simple CLI runner
- `t (1).py`: reference CLI sample for GPT-OSS