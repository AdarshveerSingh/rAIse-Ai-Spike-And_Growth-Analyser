import os

from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT")

if not PROJECT_ENDPOINT:
    raise ValueError("PROJECT_ENDPOINT is not set in .env")

if not MODEL_DEPLOYMENT:
    raise ValueError("MODEL_DEPLOYMENT is not set in .env")


credential = DefaultAzureCredential()

project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=credential
)

client = project.get_openai_client()


def ask_ai(prompt: str) -> str:
    response = client.responses.create(
        model=MODEL_DEPLOYMENT,
        input=prompt
    )

    return response.output_text