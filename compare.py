import boto3

rek = boto3.client(
    "rekognition",
    region_name="us-east-1"
)

def compare(source_path, target_path):

    with open(source_path, "rb") as s, \
         open(target_path, "rb") as t:

        resp = rek.compare_faces(
            SourceImage={"Bytes": s.read()},
            TargetImage={"Bytes": t.read()},
            SimilarityThreshold=0
        )

    matches = resp["FaceMatches"]

    return matches[0]["Similarity"] if matches else 0.0