import streamlit as st
from password_strength import score_password

st.set_page_config(page_title="Password Strength Auditor", page_icon="🔐")

st.title("🔐 Password Strength Auditor")
st.caption("Task 3 – SCT CS | Pixel-perfect feedback + entropy-based scoring")

pwd = st.text_input("Enter a password to evaluate", type="password")

if pwd:
    res = score_password(pwd)
    st.subheader(f"Score: {res['score']} / 100  ·  {res['label']}")
    st.progress(res["score"] / 100)

    col1, col2, col3 = st.columns(3)
    col1.metric("Entropy (bits)", f"{res['bits']}")
    col2.metric("Crack (offline fast)", res["estimates"]["offline_fast"])
    col3.metric("Crack (online slow)", res["estimates"]["online_slow"])

    with st.expander("Why this score? (penalties & heuristics)"):
        st.json(res["penalty_detail"])

    if res["feedback"]:
        st.subheader("How to improve")
        for tip in res["feedback"]:
            st.write(f"• {tip}")
else:
    st.info("Tip: try a weak password like 'Password123' and then a passphrase like 'Taco!River7-Moons' to see the difference.")
