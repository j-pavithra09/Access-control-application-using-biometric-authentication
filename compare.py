# compare.py
import boto3

rek = boto3.client("rekognition", region_name="us-east-1")

def compare(source_path, target_path):
    try:
        with open(source_path, "rb") as s, open(target_path, "rb") as t:
            resp = rek.compare_faces(
                SourceImage={"Bytes": s.read()},
                TargetImage={"Bytes": t.read()},
                SimilarityThreshold=0, # Return all scores
            )
        matches = resp["FaceMatches"]
        if not matches:
            return 0.0, "No face match found"
        return matches[0]["Similarity"], "Match found"
    except rek.exceptions.InvalidParameterException:
        return 0.0, "No face detected in one or both images"
    except Exception as e:
        return 0.0, f"Error: {str(e)}"

if __name__ == "__main__":
    # Test with your own photos
    print("Same person:", compare("photos/me_ref.jpg", "photos/me_live.jpg"))
    print("Different person:", compare("photos/me_ref.jpg", "photos/friend.jpg"))