<!-- CODEGRAPH_START -->
## CodeGraph

This project has a CodeGraph MCP server (`codegraph_*` tools) configured. CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file. Reads are sub-millisecond and return structural information grep cannot.

### When to prefer codegraph over native search

Use codegraph for structural questions: definitions, call flow, signatures, impact, and focused implementation context. Use native grep/read only for literal text queries or after a specific file is already known.

| Question | Tool |
|---|---|
| Where is X defined? | `codegraph_search` |
| What calls function Y? | `codegraph_callers` |
| What does Y call? | `codegraph_callees` |
| What would break if I changed Z? | `codegraph_impact` |
| Show Y's signature/source/docstring | `codegraph_node` |
| Give focused task context | `codegraph_context` |
| See related symbols' source | `codegraph_explore` |
| What files exist under path? | `codegraph_files` |
| Is the index healthy? | `codegraph_status` |

CodeGraph is initialized in this repository. Run `codegraph sync` after code edits when structural search should reflect the latest state.
<!-- CODEGRAPH_END -->

## Project State

TrustPic is an evidence-first single-image report tool. v0 is not a universal AI detector and must not claim that an image is real, fake, AI-generated, or authentic based only on absent signals.

The durable report contract lives in `backend/app/models.py` and is consumed directly by the React/Vite frontend in `web/src/main.tsx`.

## Local Runbook

Backend:

```bash
cd backend
.venv/bin/python -m pytest
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd web
npm run build
npm run dev -- --port 5173
```

Open `http://127.0.0.1:5173/`.

If local port binding fails with `Operation not permitted` or `listen EPERM`, request sandbox escalation for the same command. That is an environment permission issue, not necessarily an app failure.

## Validation Commands

Use these before handoff:

```bash
cd backend
.venv/bin/python -m pytest
.venv/bin/python scripts/verify_samples.py --download-public --output-dir /private/tmp/trustpic-samples
.venv/bin/python scripts/calibrate_ela.py --generate --sample-dir /private/tmp/trustpic-samples
```

```bash
cd web
npm run build
```

For user-supplied real samples, keep images outside git:

```bash
cd backend
.venv/bin/python scripts/audit_sample_directory.py /private/tmp/trustpic-real-samples \
  --json-output /private/tmp/trustpic-real-sample-audit.json \
  --markdown-output /private/tmp/trustpic-real-sample-audit.md
```

## Implementation Guardrails

- Do not persist uploaded originals in v0.
- Do not commit real user images or generated sample images.
- Keep closed or quota-dependent detector APIs deferred unless the user explicitly changes scope.
- C2PA presence is a supported provenance signal; AI-related wording is only `details.ai_related`.
- GB 45438 v0 scanning is conservative: TC260 AIGC XMP namespace/field extraction plus byte markers.
- ELA is a review signal only. Threshold changes need calibration evidence and doc updates.
- Keep Web and future Mini Program compatibility through the backend response schema.

## Key Docs

- `docs/PROGRESS.md`: current status and remaining work.
- `docs/SAMPLE_VERIFICATION.md`: generated/public sample verification.
- `docs/ELA_CALIBRATION.md`: ELA heuristic and calibration workflow.
- `docs/REAL_SAMPLE_INTAKE.md`: real sample audit workflow.
- `docs/V0_GOALS.md`: product scope and non-negotiables.
- `docs/TECH_STACK.md`: architecture and detection notes.
