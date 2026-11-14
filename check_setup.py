import os
import boto3

REGION = "us-east-1"
rek = boto3.client("rekognition", region_name=REGION)

def check(name, fn):
    try:
        print(f"PASS  {name}: {fn()}")
    except Exception as e:
        print(f"FAIL  {name}: {e}")

def sts():
    return boto3.client("sts", region_name=REGION).get_caller_identity()["Arn"]

def compare(a, b):
    for p in (a, b):
        if not os.path.exists(p):
            return f"skipped, missing {p}"
    with open(a, "rb") as s, open(b, "rb") as t:
        r = rek.compare_faces(
            SourceImage={"Bytes": s.read()},
            TargetImage={"Bytes": t.read()},
            SimilarityThreshold=0,
        )
    m = r["FaceMatches"]
    return f"similarity {m[0]['Similarity']:.1f}" if m else "no face match (score 0)"

def liveness():
    r = rek.create_face_liveness_session()
    return "session created, id " + r["SessionId"]

def bedrock_models():
    r = boto3.client("bedrock", region_name=REGION).list_foundation_models()
    ids = [m["modelId"] for m in r["modelSummaries"]
           if "IMAGE" in m.get("inputModalities", [])
           and "TEXT" in m.get("outputModalities", [])]
    return f"{len(ids)} vision models listed, e.g. {ids[:5]}"

def bedrock_call():
    model = os.environ.get("MODEL_ID")
    if not model:
        return "skipped, set MODEL_ID first"
    br = boto3.client("bedrock-runtime", region_name=REGION)
    r = br.converse(
        modelId=model,
        messages=[{"role": "user", "content": [{"text": "Reply with the word OK"}]}],
        inferenceConfig={"maxTokens": 20},
    )
    return r["output"]["message"]["content"][0]["text"]

if __name__ == "__main__":
    check("credentials", sts)
    check("same person", lambda: compare("photos/p1_ref.jpg", "photos/p1_live.jpg"))
    check("different person", lambda: compare("photos/p1_ref.jpg", "photos/p2_ref.jpg"))
    check("blurry photo", lambda: compare("photos/p1_ref.jpg", "photos/p1_blurry.jpg"))
    check("screen replay", lambda: compare("photos/p1_ref.jpg", "photos/screen_replay.jpg"))
    check("no face", lambda: compare("photos/p1_ref.jpg", "photos/noface.jpg"))
    check("face liveness", liveness)
    check("bedrock model list", bedrock_models)
    check("bedrock call", bedrock_call)