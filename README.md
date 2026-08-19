
# Recruitment Retention Assistant — MVP

A small Streamlit prototype for recruiters to identify **early post-placement attrition support needs**.

## What it does

- Collects role, relocation, financial-readiness, expectation and motivation information.
- Calculates a transparent rule-based Low / Medium / High **retention-support** level.
- Shows the reasons behind the score.
- Suggests questions the recruiter should ask.
- Suggests recruiter actions and a follow-up schedule.
- Optionally uses the OpenAI API to turn the structured result into concise recruiter coaching.

## Important

This is **not** a hiring, rejection, ranking or candidate-quality system.
It must not be used to make automatic employment decisions.

The MVP deliberately avoids fields such as gender, ethnicity, religion, health information or other protected/sensitive characteristics.

## Install

```bash
python -m pip install -r requirements.txt
```

## Run without AI

```bash
streamlit run app.py
```

The transparent rule-based assessment works without an API key.

## Enable AI coaching

Set your OpenAI API key:

### macOS / Linux
```bash
export OPENAI_API_KEY="your-key"
streamlit run app.py
```

### Windows PowerShell
```powershell
$env:OPENAI_API_KEY="your-key"
streamlit run app.py
```

Optional model override:

```bash
export OPENAI_MODEL="gpt-5-mini"
```

## How the current risk logic was designed

The prototype reflects recurring themes in Ruben Naessens' BAP interview analysis:

- expectation management
- financial readiness
- structured screening / red-flag detection
- role/client risk
- relocation readiness
- trust and human connection
- structured post-placement follow-up

The numerical weights and thresholds are **prototype assumptions**, not research findings.
They should be calibrated later with historical ATS data.

## Recommended next phase

1. Validate each input field with recruiters.
2. Link historical ATS placements and dropout outcomes.
3. Calculate which factors actually correlate with early dropout.
4. Replace prototype weights with empirically supported weights.
5. Pilot the tool with recruiters.
6. Record recruiter feedback and compare AS-IS vs TO-BE process.
7. Integrate with the Early Attrition Monitoring Dashboard.
