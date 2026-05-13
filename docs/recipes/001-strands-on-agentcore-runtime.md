---
description: "Build and deploy a working Strands agent on AWS Bedrock AgentCore Runtime in an afternoon. Uses the modern @aws/agentcore CLI (npm) on a current AWS account, not the deprecated Python starter toolkit. Verified on a live deploy."
image: assets/images/recipes/001-banner.png
date: "2026-05-20"
author: Sunil Prakash
---

<div class="fn-meta" markdown>
<span>R-001</span><span>2026-05-20</span><span>12 min read</span><span>AgentCore, Strands, Bedrock</span>
</div>

# Build and deploy your first Strands agent on AgentCore Runtime

<div class="fn-dek" markdown>
End to end on a current AWS account, using the modern <code>@aws/agentcore</code> CLI, not the deprecated Python starter toolkit. Deploy in an afternoon. Document every step you will actually trip on.
</div>

<figure markdown>
  ![Editorial illustration of an AgentCore Runtime deployment](../assets/images/recipes/001-banner.png){ loading=lazy }
</figure>

Most AgentCore tutorials on the internet still use the Python `bedrock-agentcore-starter-toolkit`, which AWS classified as legacy when the `@aws/agentcore` CLI went GA in April 2026. This Recipe walks the modern path. The end state: a deployed agent runtime on AWS Bedrock AgentCore, invoked over HTTP, returning real Claude completions through a Strands agent definition you wrote in Python.

<div class="fn-verified" markdown>
**Verified end to end on 2026-05-13**
AWS CLI 2.34.45, Node 23.7.0, `@aws/agentcore` 0.13.1, CDK 2.1100.1, Strands. Region: `us-east-1`. Model: `global.anthropic.claude-sonnet-4-6`. Account: personal AWS account, no organization. Stack created in 1 minute 51 seconds. First invoke after model use-case form submission completed in 10.4 seconds.
</div>

## Prerequisites

These are the exact versions and approvals you need before the Recipe will work. If any of them are missing, the Recipe will fail at a predictable step.

- **AWS account** with IAM credentials configured locally (`aws sts get-caller-identity` returns your identity).
- **AWS CLI 2.27 or newer.** Older CLIs do not have the `bedrock` or `bedrock-agentcore-control` subcommands. Check with `aws --version`. Upgrade with `brew install awscli` on macOS, or replace your install with the current bundled installer per AWS docs.
- **Node 20 or newer**, npm 10 or newer. `@aws/agentcore` will not install on older runtimes.
- **CDK bootstrap on the target account and region**, or pass `--yes` to `agentcore deploy` so the CLI bootstraps for you. The CDK toolkit stack is a one-time setup per account+region.
- **Bedrock model access for Anthropic Claude submitted at the account level.** This is the use-case details form. The Model Access page in the Bedrock console was retired in 2026. The form now appears the first time you open any Anthropic model in the Bedrock Playground. Submit it once and access is effectively instant across commercial regions. For org-level submission use `aws bedrock put-use-case-for-model-access`.
- **A specific Claude inference profile that does not require AWS Marketplace permissions on your IAM user.** This is the surprise gotcha. Some Claude model IDs on Bedrock are still served via AWS Marketplace and require `aws-marketplace:Subscribe` on the invoking principal. Section in Gotchas below.

Estimated cost for the verification path: a few cents in CloudFormation operations and one Claude invocation. AgentCore Runtime itself has no idle cost beyond the CloudFormation resources.

## The flow

### 1. Install the modern CLI locally

Scope the CLI to your Recipe directory rather than installing globally. Readers get a reproducible env, and your global `npm` does not collect stale CLIs over time.

```bash
mkdir -p recipes/R-001 && cd recipes/R-001
npm init -y
npm install --save-dev @aws/agentcore
npx agentcore --version
```

The first run prints a telemetry notice. Opt out if you want to:

```bash
npx agentcore telemetry disable
```

### 2. Scaffold the project

```bash
npx agentcore create \
  --defaults \
  --project-name rec001 \
  --name helloagent
```

`--defaults` selects Python + Strands + Bedrock with no memory layer, which is the right floor for a first Recipe. The scaffold writes a Python Strands agent in `app/helloagent/`, a CDK project in `agentcore/cdk/`, and an AgentCore config in `agentcore/agentcore.json`. It also initialises its own git repo inside the project, which you can safely delete if you are working inside a parent repo.

The generated Strands agent is small and worth reading before deploying:

```python
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model

app = BedrockAgentCoreApp()

@tool
def add_numbers(a: int, b: int) -> int:
    """Return the sum of two numbers"""
    return a + b

_agent = None
def get_or_create_agent():
    global _agent
    if _agent is None:
        _agent = Agent(model=load_model(), tools=[add_numbers])
    return _agent

@app.entrypoint
async def invoke(payload, context):
    agent = get_or_create_agent()
    stream = agent.stream_async(payload.get("prompt"))
    async for event in stream:
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]
```

The model is loaded from `model/load.py`. The scaffold defaults to `global.anthropic.claude-sonnet-4-5-20250929-v1:0`, which on a fresh account hits the AWS Marketplace permission gate described in Gotchas. The Recipe uses `global.anthropic.claude-sonnet-4-6` instead, which on the same account works without Marketplace ops:

```python
from strands.models.bedrock import BedrockModel

def load_model() -> BedrockModel:
    return BedrockModel(model_id="global.anthropic.claude-sonnet-4-6")
```

### 3. Configure a deployment target

The CLI does not auto-populate `agentcore/aws-targets.json` on `create`. Add one yourself before deploying:

```json
[
  {
    "name": "default",
    "description": "R-001 tutorial deployment target",
    "account": "YOUR_AWS_ACCOUNT_ID",
    "region": "us-east-1"
  }
]
```

Validate the project state before pushing anything to AWS:

```bash
npx agentcore validate
```

A clean run prints `Valid`.

### 4. Deploy

```bash
npx agentcore deploy --yes -v
```

The `--yes` flag handles CDK bootstrap if the account+region is not bootstrapped yet, and skips the interactive confirm. The verified deploy creates one CloudFormation stack, `AgentCore-rec001-default`, containing one nested resource: `ApplicationAgentHelloagentRuntime*`. On a clean account the full timeline is roughly:

- Load deployment target: 3ms
- Validate project: 1.7s
- Build CDK project (`tsc`): 1.9s
- Synthesize CloudFormation: 9.5s
- Check bootstrap status: 1.3s
- CDK bootstrap (first run only): about 1 minute
- Stack create on AgentCore-rec001: about 1 minute

Total under 3 minutes on a fresh account, under 2 minutes on a previously bootstrapped one.

Once the stack is `CREATE_COMPLETE`:

```bash
npx agentcore status
```

You should see your agent listed as `Deployed - Runtime: READY` with an ARN and an invocation URL.

### 5. Submit the Anthropic use-case form (one-time per account)

On a fresh account, the deploy succeeds but the first invoke fails with:

```
ResourceNotFoundException: Model use case details have not been submitted
for this account. Fill out the Anthropic use case details form before
using the model.
```

The fix is one form, submitted once per AWS account. Open the AWS Console in your target region, navigate to **Bedrock -> Model catalog**, click any Anthropic Claude model, and choose **Open in Playground**. On the first attempt, AWS prompts the use-case details form with six fields:

| Field | Notes |
|---|---|
| Company name | Personal or organisation name. Free text, 128 chars max. |
| Company website | Project URL or personal site is fine for individuals. |
| Intended users | `Internal`, `External`, or `Both`. Choose `Internal` for personal experimentation. |
| Industry | Pick the closest match. |
| Other industry | Leave empty unless industry is `Other`. |
| Use cases | Plain-English description, 8192 chars max. State the application, the audience, and your stance on customer data and automated decisions. |

Submit. Access is effectively instant. The error message says up to 15 minutes; in practice the next invoke works within a minute.

For organisation-wide submission, use the CLI from the org management account: `aws bedrock put-use-case-for-model-access --form-data <Base64EncodedFormData>`. Submission auto-extends to child accounts.

### 6. Invoke the deployed agent

```bash
npx agentcore invoke "What is 17 plus 25? Use the add_numbers tool."
```

Expected behaviour: a Strands agent loop runs in the AgentCore Runtime, the model decides to call `add_numbers(17, 25)`, the tool returns `42`, and the agent streams the final answer back. Total round-trip on the verified path: 10.4 seconds for a fresh container start. Subsequent invokes against the same session are faster.

To resume an existing session:

```bash
npx agentcore invoke --session-id <session-id> "follow-up question"
```

To stream and watch tokens arrive:

```bash
npx agentcore invoke --stream "your prompt"
```

## Gotchas

The failure modes that will cost you an afternoon. Specific, with the symptom and the fix.

- **"No deployment targets configured."** The scaffold creates `agentcore/aws-targets.json` as an empty `[]`. Add at least one target with `name`, `account`, `region` before running deploy. The CLI does not error early; it gets through validate and synth before complaining.
- **"Cannot find module 'dist/bin/cdk.js'."** The CDK sub-project ships an unbuilt TypeScript app. Run `npm run build` inside `agentcore/cdk/` (or let `agentcore deploy` handle it), do not invoke CDK directly until that compile happens.
- **"Model use case details have not been submitted for this account."** Section 5 above. Form is account-level, not model-level, but still required even after the Model Access page retirement.
- **"Model access is denied due to ... aws-marketplace:Subscribe."** The surprise. Some Anthropic model IDs on Bedrock route through AWS Marketplace and require Marketplace IAM actions on the invoking principal. Affected on the verified account: `global.anthropic.claude-sonnet-4-5-20250929-v1:0`. Not affected: `global.anthropic.claude-sonnet-4-6`. Two fixes: either grant the IAM user `aws-marketplace:ViewSubscriptions` and `aws-marketplace:Subscribe` (then invoke once to complete the subscription, which enables it account-wide), or switch to a model ID that does not route through Marketplace. The Recipe defaults to Sonnet 4.6 for this reason.
- **"Subprocess exited with error 1" with telemetry notices.** Recent CDK CLI versions (>= 2.1100.0) print a verbose telemetry notice on every run. This is decoration, not error. Pass `--telemetry-file=/dev/null` to suppress or run `cdk acknowledge 34892`.
- **Wrong cwd for the CLI.** `agentcore` looks for `agentcore/agentcore.json` in the current working directory. Run it from the project root (the directory that contains the `app/` and `agentcore/` folders), not from the recipe wrapper that holds `node_modules/`.

## Verification

How you know it actually works.

```bash
npx agentcore status
```

Expected output, abridged:

```
AgentCore Status (target: default, us-east-1)

Agents
  helloagent: Deployed - Runtime: READY
    ARN: arn:aws:bedrock-agentcore:us-east-1:<account>:runtime/rec001_helloagent-<id>
    URL: https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/.../invocations
```

```bash
npx agentcore invoke "What is 17 plus 25? Use the add_numbers tool."
```

Expected response: a streamed answer that includes `42`, with the Strands tool call visible in the runtime logs (`agentcore logs`).

<div class="fn-pullquote" markdown>
The deploy works in two minutes. The Anthropic use-case form and the Marketplace permission gate are what will cost you an afternoon if no one warned you.
</div>

## Sample code

The full working code is in [`recipes/R-001/`](https://github.com/sunilp/agentic-ai/tree/main/recipes/R-001) in the companion repo, including the modified `model/load.py` and the populated `agentcore/aws-targets.json`. Clone the recipe directory, set your AWS account ID and region in `aws-targets.json`, then run through sections 1 through 6 above.

The deployed stack will charge nothing while idle. To remove it later:

```bash
npx agentcore remove agent --name helloagent --yes
```

Or destroy the CloudFormation stack directly: `aws cloudformation delete-stack --stack-name AgentCore-rec001-default --region us-east-1`.

<div class="fn-footer" markdown>

<div class="fn-footer-section" markdown>
<span class="label">From the book</span>
[Chapter 9: Deploying and Scaling](../book/09-deployment.md)<br>
[Chapter 13: Agent Protocols in Production](../book/13-agent-protocols-in-production.md)
</div>

<div class="fn-footer-section" markdown>
<span class="label">In the code</span>
[recipes/R-001/](https://github.com/sunilp/agentic-ai/tree/main/recipes/R-001)
</div>

<div class="fn-footer-section" markdown>
<span class="label">Read next</span>
[R-002: OAuth 3LO with AgentCore Identity](index.md) (Wednesday 2026-06-03)
</div>

</div>
