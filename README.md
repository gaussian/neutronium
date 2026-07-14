# neutronium

Framework-agnostic Python utilities, extracted from Gaussian's internal
infrastructure. No Django, no web framework, no cloud SDK in the base install —
everything third-party is an optional extra.

```sh
pip install neutronium              # base: zero dependencies
pip install neutronium[text]        # inflection-backed pluralize/singularize
pip install neutronium[xpath]       # lxml-backed HTML/XPath helpers
```

## What's inside

| Module | What it gives you |
|---|---|
| `neutronium.utils.text` | Text normalization, slugs, tokenization, pluralize/singularize |
| `neutronium.utils.time` | Timezone-aware datetime helpers |
| `neutronium.utils.iterable` | Chunking, grouping, flattening, dict utilities |
| `neutronium.utils.template_context` | Pure template-variable extraction and context building |
| `neutronium.utils.json_patch` | RFC-6901 JSON pointer / merge-patch primitives |
| `neutronium.utils.hash` | `blake2b` content hashing helpers |
| `neutronium.utils.schema` | JSON-schema → default-dict |
| `neutronium.utils.xpath` | lxml HTML parsing + link extraction (`[xpath]`) |
| `neutronium.utils.email` | Canonical email normalization |
| `neutronium.utils.{aws,ssm}` | EC2/ECS instance metadata + SSM parameter fetch (`[aws]`) |
| `neutronium.utils.{print,params,profiling,memory,url_credentials}` | Assorted small utilities |
| `neutronium.threads.thread_simple` | Minimal threading helpers |
| `neutronium.telemetry` | Request-context vars, `RequestFacts`, pluggable sinks |
| `neutronium.logging` | JSON / dev-console log formatters and context filters |

## Optional extras

`text`, `time`, `aws`, `memory`, `memory-extended`, `xpath`, `otel`, `profiling` — install only what you use.

- `aws` → `boto3`, `requests`, `ec2-metadata` (for `neutronium.utils.aws` / `ssm`)
- `memory` → `psutil` (for `print_memory_usage`); `memory-extended` → `pympler`, `objgraph` (for the heap/objgraph tools — opt in only if you use them)

## Development

```sh
uv sync --group dev
uv run pytest
```

## License

MIT © Gaussian Holdings, LLC
