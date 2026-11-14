import csv, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import cv2
import core

LABEL = sys.argv[1] if len(sys.argv) > 1 else "test"   # live, video, screen, print, mask
CAPTURE_SECONDS = 2.5
SAMPLE_EVERY = 0.25
LIVE_FLIP = False    # set True if "left/right" is judged the wrong way round

def jpeg(frame, width=640):
    h, w = frame.shape[:2]
    if w > width:
        frame = cv2.resize(frame, (width, int(h * width / w)))
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return buf.tobytes()

def judge_turn(yaws, direction):
    if len(yaws) < 3:
        return "noface", 0.0
    start = sum(yaws[:2]) / 2
    sign = 1 if direction == "left" else -1
    if LIVE_FLIP:
        sign = -sign
    best = max((y - start) * sign for y in yaws)
    if max(yaws) - min(yaws) < core.YAW_FROZEN:
        return "frozen", best
    return ("pass" if best >= core.YAW_NEEDED else "weak"), best

def decide(face0, sim, vis, status):
    if face0 is None or status == "noface":
        return "REQUEST_VERIFICATION", "face not clear, please retry"
    if core.is_spoof(vis):
        return "DENY", "spoof cues: " + ", ".join(vis.get("cues", [])[:3])
    if sim < core.SIM_DENY:
        return "DENY", "identity does not match"
    if status == "frozen":
        return "DENY", "no response to the challenge (photo or replay)"
    if status == "weak":
        return "REQUEST_VERIFICATION", "head turn too small or wrong way"
    if (sim >= core.SIM_ALLOW and face0["sharp"] >= core.MIN_SHARP
            and vis.get("spoof_suspected") is False):
        return "ALLOW", "challenge passed, live person matched"
    return "REQUEST_VERIFICATION", "low confidence, extra check needed"

def draw(cap_frame, lines, color):
    img = cv2.flip(cap_frame, 1)
    cv2.rectangle(img, (0, 0), (img.shape[1], 40 + 32 * len(lines)), (0, 0, 0), -1)
    for i, text in enumerate(lines):
        cv2.putText(img, text, (12, 32 + 32 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imshow("kiosk", img)

def attempt(cap, ref, pool):
    direction = core.new_challenge()
    frames, frontal_job, last = [], None, 0.0
    t0 = time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            return None
        t = time.time() - t0
        if t < 1.0:
            draw(frame, ["Look straight at the camera"], (0, 255, 255))
            if frontal_job is None and t >= 0.8:
                frontal_job = pool.submit(core.check_frame, jpeg(frame), ref)
        elif t < 1.0 + CAPTURE_SECONDS:
            draw(frame, [f"TURN YOUR HEAD {direction.upper()}"], (0, 255, 0))
            if t - last >= SAMPLE_EVERY:
                frames.append(jpeg(frame))
                last = t
        else:
            break
        cv2.waitKey(1)
    if frontal_job is None:
        frontal_job = pool.submit(core.check_frame, frames[0], ref)

    draw(frame, ["Checking..."], (255, 255, 255))
    cv2.waitKey(1)
    t_end = time.time()
    faces = [f.result() for f in [pool.submit(core.detect, f) for f in frames]]
    yaws = [d["yaw"] for d in faces if d]
    face0, sim, vis = frontal_job.result()
    status, turned = judge_turn(yaws, direction)
    decision, reason = decide(face0, sim, vis, status)
    return {"time": datetime.now().isoformat(timespec="seconds"), "label": LABEL,
            "direction": direction, "decision": decision, "reason": reason,
            "similarity": round(sim, 1), "challenge": f"{status} ({turned:.0f} deg)",
            "post_seconds": round(time.time() - t_end, 2),
            "total_seconds": round(time.time() - t0, 2)}

def log(r):
    new = not os.path.exists("live_log.csv")
    with open("live_log.csv", "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=r.keys())
        if new:
            w.writeheader()
        w.writerow(r)

if __name__ == "__main__":
    ref = core.load_ref()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    pool = ThreadPoolExecutor(max_workers=12)
    print(f"Label: {LABEL}. SPACE = start attempt, Q = quit.")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Camera not available")
            break
        draw(frame, [f"[{LABEL}]  SPACE = start   Q = quit"], (255, 255, 255))
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == 32:
            r = attempt(cap, ref, pool)
            if r is None:
                break
            log(r)
            print(r["decision"], "|", r["reason"], "|", r["challenge"],
                  f"| after capture {r['post_seconds']}s | total {r['total_seconds']}s")
            color = {"ALLOW": (0, 200, 0), "DENY": (0, 0, 230)}.get(r["decision"], (0, 165, 255))
            end = time.time() + 3
            while time.time() < end:
                ok, frame = cap.read()
                draw(frame, [r["decision"], r["reason"][:60],
                             f"match {r['similarity']:.0f}%  decision {r['post_seconds']}s"], color)
                cv2.waitKey(1)
    cap.release()
    cv2.destroyAllWindows()