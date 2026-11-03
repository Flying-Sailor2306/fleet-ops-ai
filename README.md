# Fleet Ops AI — Aster Tide Marine

A hackathon prototype of a fleet-management team: Engineering Superintendent, Marine Superintendent and Fleet Manager. The demonstration company, vessels, cases and commercial assumptions are fictional.

## Workflow

1. A Master or Chief Engineer submits a case.
2. Fleet Manager delegates technical and operational/commercial assignments.
3. Engineering returns its assessment; Marine uses that report to assess voyage and commercial impact.
4. Manager reviews both. One follow-up round is available; revisions to Engineering trigger Marine reassessment.
5. Manager returns a concise decision brief and vessel email draft. Marine also prepares an unsent commercial notification draft.

The manager uses Muse Wonder 1.0; the two specialists use Muse Spark 1.3. All requests currently use high reasoning effort, Chat Completions and JSON Schema structured outputs. Runs are capped at 15 calls, including at most seven correction calls and one correction per stage. Persistent validation or API failures stop the run and retain partial results; no scripted response is substituted for a failed live request.

## Run locally

Requires Python 3.10 or newer. The application uses the standard library; no package installation is required for the basic app.

```sh
python app.py
```

Open the ready URL printed in the terminal. The preferred address is http://127.0.0.1:8890/; if occupied, the app binds another available local port. Keep the terminal open.

Default mode is scripted rehearsal, not AI generation. Choose a benchmark or stress-test case to fill the form, submit it, then run the assessment. Manual case entry is also available.

## Live Meta configuration

Copy `.env.example` to `.env`, enter your own Meta API key locally, and set `FLEET_MODE=live`. Never commit your key.

```text
MODEL_API_KEY=your_key_here
META_MANAGER_MODEL=muse-wonder-1.0
META_ENGINEERING_MODEL=muse-spark-1.3
META_MARINE_MODEL=muse-spark-1.3
FLEET_MODE=live
```

Role settings override the optional shared `META_MODEL`. Your account must have access to the selected models. Restart after changing settings. Clicking **Run AI assessment** authorizes sending the case and selected reference excerpts to Meta; usage charges may apply. High-reasoning generation requests have a 180-second timeout. Live calls have been tested during development; this is not a guarantee of future service availability or output accuracy.

## Reference library and limits

The fictional SMS is included in source code. User-supplied OEM manuals, circulars, class sample and glossary are private local inputs and are **not distributed in this repository**. Their originals, extracted library and case snapshots belong in ignored `local-data/`. A fresh clone therefore does not reproduce the private OEM-grounded demonstration without separately supplied, authorized references.

`reference_library.py` searches the local extracted library by case and assignment and selects at most 12 excerpts within a 30,000-character budget. This is bounded lexical retrieval, not exhaustive document review. Source IDs and supporting quotations are checked; semantic support, document revisions, applicability and poorly extracted tables/diagrams still require qualified review. Import utilities require `pypdf` and access to authorized source files; their paths may need adaptation to your environment.

## Evaluation

The UI exposes three benchmark cases and two authored stress variations: low peak pressure, conflicting measurements, planned survey attendance, missed ETA/charter exposure, and missing spares with competing fleet requirements. Six earlier development examples remain in code. These scenarios are authored tests, not a blind independent benchmark. Repair-time and daily-cost inputs are explicitly labelled assumptions; scenario exposure is not proven loss or automatic demurrage.

Run automated checks:

```sh
python -m unittest discover -v
```

Tests cover coordination, handoffs, reference validation, structured outputs, correction budgets, arithmetic, API errors and local HTTP behaviour. They do not certify technical guidance or establish superiority over a single-agent baseline. Independent domain evaluation and measured time savings remain outstanding.

## Hackathon contribution and boundaries

This submission implements the local case interface, role-based Meta integration, coordination and review loop, reference selection and checks, scenario calculations, drafts and tests developed during the hackathon. External reference documents and model services are pre-existing inputs. Existing personal assistants are not connected to this application.

No vessel commands, repairs, purchases or external messages are executed. Draft approval and demo acknowledgment are not authenticated operational authorization. The Master retains shipboard authority; qualified review is required. The app is a local single-user prototype, not a production fleet system.
