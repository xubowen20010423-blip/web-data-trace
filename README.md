# Web Data Trace

Web Data Trace is a Codex skill for finding where a webpage gets its data and verifying how to extract it. Give it a page URL, a saved HAR, or a JavaScript bundle. It uses [Scrapling](https://github.com/D4Vinci/Scrapling) to collect and parse samples and [REA](https://github.com/morluto/rea) to inspect JavaScript and browser or network evidence.

Use it to identify the request behind a rendered list, verify a pagination cursor, or turn a recorded response into a repeatable extraction rule. Findings can cite the REA evidence ID and the exact browser step or HAR record. The included sampler saves the response body, source URL, capture time, and SHA-256 hash.

## Install

### 1. Add the skill to Codex

Clone this repository into your user skills folder. You can also extract the source archive and place its contents in the same `web-data-trace` directory. Keep `SKILL.md`, `agents/`, `references/`, and `scripts/` together.

**Windows (PowerShell)**

```powershell
git clone https://github.com/xubowen20010423-blip/web-data-trace.git "$env:USERPROFILE/.agents/skills/web-data-trace"
```

**macOS and Linux**

```sh
git clone https://github.com/xubowen20010423-blip/web-data-trace.git "$HOME/.agents/skills/web-data-trace"
```

Open a Codex chat and invoke `$web-data-trace`. For repository-only use, place the skill under `.agents/skills/web-data-trace` in that repository. See [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills).

### 2. Set up the tools needed for your task

- **Scrapling** requires Python 3.10 or newer. In a project virtual environment, run `python -m pip install "scrapling[fetchers]>=0.5.1,<0.6"`. The HTTP sampler was tested with version 0.5.1 and runs without a browser. For rendering and interaction, follow the [Scrapling browser setup](https://scrapling.readthedocs.io/en/latest/fetching/stealthy.html).
- **REA** is used for JavaScript, HAR, and browser analysis. Connect its MCP server to Codex using the [REA setup instructions](https://github.com/morluto/rea). If you already have a connected REA server, use its available tools. For live observation, use a supported Chrome-family browser.

## Usage

Paste a prompt into Codex and replace the example inputs with your own:

> Use $web-data-trace to find how https://example.com/catalog loads product names. Confirm the endpoint and pagination parameter, and give me a runnable Python extractor.

> Use $web-data-trace to inspect my saved catalog.har offline. Find the response containing the items and show the field paths for names and pagination.

A typical investigation starts with one HTTP sample. For a JavaScript-rendered list, the skill checks the requests around the relevant interaction. It then verifies the field path against a response and, when pagination is in scope, checks what changes on the next page.

### Save an HTTP sample directly

Run this from the skill directory with the Scrapling environment active:

```sh
python scripts/sample_get.py "https://example.com/" ./example-sample --expect html
```

The command creates a new directory with `body.html` and `evidence.json`. Use `--expect javascript` for a JavaScript file or `--expect json` for a JSON response. The sampler issues one GET, requires HTTP 200 and a matching media type, and limits the decoded response to 8 MiB. Use URLs with non-sensitive parameters and authorized access. For session-dependent data, use the authorized browser session and keep sensitive captures local.

## Repository contents

| File | Purpose |
| --- | --- |
| [SKILL.md](SKILL.md) | Workflow and handoff between Scrapling and REA |
| [references/workflows.md](references/workflows.md) | Tool selection, browser and HAR workflows, and dependency setup |
| [scripts/sample_get.py](scripts/sample_get.py) | Bounded HTTP sampler and evidence metadata |
| [agents/openai.yaml](agents/openai.yaml) | Codex display name and example prompt |

The skill was verified against a local JavaScript catalog. REA observed the next-page request and Scrapling verified the returned fields and cursor on both pages.

## License

[MIT](LICENSE). Scrapling and REA are separate upstream projects governed by their own licenses.
