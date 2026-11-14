import csv, os, random
from datetime import datetime
import streamlit as st
import core

st.set_page_config(page_title="Spot a Spoof", layout="centered")
st.title("Face liveness and access check")

if not os.path.exists(core.REF_PATH):
    st.error(f"Enrolled photo not found at {core.REF_PATH}. Save it as photos/ref.jpg.")
    st.stop()
ref = core.load_ref()

if "n" not in st.session_state:
    st.session_state.n = 0
    st.session_state.direction = core.new_challenge()
n = st.session_state.n

def log(mode, r):
    new = not os.path.exists("app_log.csv")
    with open("app_log.csv", "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "mode", "decision", "reason", "similarity", "seconds"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), mode, r["decision"],
                    r["reason"], round(r["similarity"], 1), r["seconds"]])

def run_once(key, mode, fn):
    """Run the analysis once per capture, not on every Streamlit rerun."""
    if st.session_state.get("last_key") != key:
        with st.spinner("Checking..."):
            r = fn()
        r["explanation"] = core.explain(r)
        st.session_state.last_key = key
        st.session_state.last_result = r
        log(mode, r)
    return st.session_state.last_result

def show(r):
    if r["decision"] == "ALLOW":
        st.success("ALLOW")
    elif r["decision"] == "DENY":
        st.error("DENY")
    else:
        st.warning("REQUEST ADDITIONAL VERIFICATION (OTP or manual review)")
    st.write(r["reason"])
    if r.get("explanation"):
        st.info(r["explanation"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Identity match", f"{r['similarity']:.0f}%")
    c2.metric("Decision time", f"{r['seconds']:.2f} s")
    c3.metric("Face sharpness", f"{r['sharpness']:.0f}")
    if r["challenge"]:
        st.write("Challenge:", r["challenge"])
    with st.expander("Vision model details"):
        st.json(r["vision"])

mode = st.radio("Mode", ["Quick check (one photo)", "Challenge check (two photos)"], horizontal=True)

if mode.startswith("Quick"):
    photo = st.camera_input("Look at the camera", key=f"q{n}")
    if photo:
        raw = photo.getvalue()
        show(run_once(hash(raw), "quick", lambda: core.analyze_still(raw, ref)))
else:
    d = st.session_state.direction
    st.info(f"Step 1: look straight at the camera. Step 2: turn your head to the {d}.")
    p1 = st.camera_input("1. Look straight", key=f"a{n}")
    p2 = st.camera_input(f"2. Now turn your head {d}", key=f"b{n}")
    if p1 and p2:
        r1, r2 = p1.getvalue(), p2.getvalue()
        show(run_once(hash((r1, r2)), "challenge",
                      lambda: core.analyze_challenge(r1, r2, ref, d)))

if st.button("New attempt"):
    st.session_state.n += 1
    st.session_state.direction = core.new_challenge()
    st.session_state.pop("last_key", None)
    st.rerun()