# explain.py
import boto3

br = boto3.client("bedrock-runtime", region_name="us-east-1")
# REPLACE THIS with a real model ID from your AWS Bedrock Console (e.g., "anthropic.claude-3-haiku-20240307-v1:0")
MODEL_ID = "PASTE_MODEL_ID_FROM_CONSOLE"

def explain(decision, score, reason):
    prompt = (
        f"You are an access-control assistant. Decision: {decision}. "
        f"Face similarity: {score:.0f}%. Reason: {reason}. "
        "Explain this to a security guard in two short sentences. "
        "Do not invent facts."
    )
    try:
        resp = br.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 200, "temperature": 0.2},
        )
        return resp["output"]["message"]["content"][0]["text"]
    except Exception as e:
        return f"(Bedrock unavailable: {e})"

if __name__ == "__main__":
    print(explain("REVIEW", 78, "borderline score, image slightly blurry"))