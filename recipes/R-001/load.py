from strands.models.bedrock import BedrockModel


def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials.

    Note on model choice:
    The AgentCore scaffold default is global.anthropic.claude-sonnet-4-5-20250929-v1:0,
    which on a fresh account requires AWS Marketplace permissions
    (aws-marketplace:Subscribe). global.anthropic.claude-sonnet-4-6 is the
    current Sonnet generation and does not require Marketplace ops, so it is
    the cleaner default for a first deploy.
    """
    return BedrockModel(model_id="global.anthropic.claude-sonnet-4-6")
