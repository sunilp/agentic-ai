# R-001 -- Build your first Strands agent on AgentCore Runtime

Code companion to the Recipe at <https://sunilprakash.com/agentic-ai/recipes/001-strands-on-agentcore-runtime/>.

This directory contains the minimum overlay needed to reproduce the Recipe on your own AWS account. The full AgentCore project scaffold is regenerated from the `@aws/agentcore create` command, so it is not checked in. You apply the two small overrides in this directory after generation.

## Quick start

```bash
# 1. Install the AgentCore CLI locally
cd recipes/R-001
npm install

# 2. Scaffold the AgentCore project (matches the Recipe exactly)
npx agentcore create --defaults --project-name rec001 --name helloagent

# 3. Apply the two overrides documented in the Recipe
cp aws-targets.example.json rec001/agentcore/aws-targets.json
# Then edit rec001/agentcore/aws-targets.json with your account ID and region.
cp load.py rec001/app/helloagent/model/load.py

# 4. Deploy
cd rec001
npx agentcore deploy --yes -v

# 5. Submit the Anthropic use-case form once (see Recipe Section 5)

# 6. Invoke
npx agentcore invoke "What is 17 plus 25? Use the add_numbers tool."
```

## What lives here

- `package.json`, `package-lock.json` -- the locked dependency on `@aws/agentcore`. Run `npm install` to get a reproducible CLI version.
- `aws-targets.example.json` -- template for the deployment target. Copy to `rec001/agentcore/aws-targets.json` and replace `YOUR_AWS_ACCOUNT_ID` with your account.
- `load.py` -- the modified Strands model loader using `global.anthropic.claude-sonnet-4-6`, which avoids the AWS Marketplace permission gate that hits the scaffold default.

## What is intentionally not here

- `rec001/` -- the generated AgentCore project. Recreated by step 2 above. Not checked in.
- `node_modules/` -- standard npm install. Not checked in.

The Recipe walks through every step with the gotchas observed during the verification run.

## Removing the deployed stack

```bash
cd rec001
npx agentcore remove agent --name helloagent --yes
```

Or destroy the CloudFormation stack directly:

```bash
aws cloudformation delete-stack \
  --stack-name AgentCore-rec001-default \
  --region us-east-1
```

AgentCore Runtime has no idle cost. The stack costs nothing until invoked, so you can leave it deployed if you plan to do R-002 or R-003 on the same project.
