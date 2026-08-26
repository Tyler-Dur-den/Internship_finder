import os
import requests
import streamlit as st

st.set_page_config(page_title="Internship Finder", page_icon="🎯", layout="wide")

st.sidebar.title("👤 User Session")
username = st.sidebar.text_input("Enter Username / Email", placeholder="e.g. Shanks").strip()

if not username:
    st.title("🎯 AI Internship Finder")
    st.info("👈 Please enter a username in the sidebar to get started and track your history.")
    st.stop()

user_id = username.lower()

st.title("🎯 AI Internship Finder")
st.caption(f"Logged in as: **{user_id}**")

RAW_URL = os.getenv("FASTAPI_URL", "https://internship-finder-f30p.onrender.com/find-internships")
BASE_URL = RAW_URL.replace("/find-internships", "").rstrip("/")
FIND_INTERNSHIPS_URL = f"{BASE_URL}/find-internships"
HISTORY_URL = f"{BASE_URL}/history"

uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
domain = st.text_input("Target Role", placeholder="AI Engineer, Data Analyst...")
location = st.text_input("Location", value="Bangalore")

if st.button("Find Internships 🔍", type="primary"):
    if not domain:
        st.error("Please enter a target role/query.")
    else:
        with st.spinner("Searching internships & evaluating matches..."):
            try:
                files = {}
                if uploaded_file:
                    files = {
                        "resume": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    }

                data = {
                    "domain": domain,
                    "location": location,
                    "user_id": user_id
                }
                response = requests.post(FIND_INTERNSHIPS_URL, data=data, files=files, timeout=60)

                if response.status_code == 200:
                    output = response.json()
                    skills = output.get("skills", [])
                    if skills:
                        st.subheader("📋 Extracted Skills")
                        st.write(" ".join([f"`{s}`" for s in skills]))

                    st.subheader("🏢 Internship Results")
                    internships = output.get("internships", [])
                    skill_gaps = output.get("skill_gaps", [])

                    if not internships:
                        st.warning("No internships found. Try broader search terms.")
                    else:
                        for i, internship in enumerate(internships):
                            gap = skill_gaps[i] if i < len(skill_gaps) else {}
                            match_pct = int(gap.get("match_percentage", 0))
                            color = (
                                "🟢"
                                if match_pct >= 70
                                else ("🟡" if match_pct >= 40 else "🔴")
                            )

                            with st.expander(
                                f"{color} {internship.get('role_title')} @ {internship.get('company_name')} — {match_pct}% match"
                            ):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**Location:** {internship.get('location')}")
                                    st.write(f"**Worktype:** {internship.get('worktype')}")
                                    st.write(f"**Stipend:** {internship.get('stipend_range')}")
                                    if internship.get("website_link"):
                                        st.link_button("Apply Here 🔗", internship["website_link"])

                                with col2:
                                    if gap:
                                        st.write(f"**Matched:** {', '.join(gap.get('matched_skills', [])) or 'None'}")
                                        st.write(f"**Missing:** {', '.join(gap.get('missing_skills', [])) or 'None'}")
                                        st.info(gap.get("recommendations", "N/A"))
                else:
                    try:
                        err_detail = response.json().get("detail", "API Error")
                    except Exception:
                        err_detail = response.text
                    st.error(f"API Error ({response.status_code}): {err_detail}")

            except requests.exceptions.RequestException:
                st.error(f"Failed to connect to FastAPI backend at `{FIND_INTERNSHIPS_URL}`.")

st.divider()
st.subheader(f"📜 Recent Searches for '{user_id}'")

try:
    history_res = requests.get(HISTORY_URL, params={"user_id": user_id}, timeout=10)
    if history_res.status_code == 200:
        history_data = history_res.json()
        if history_data:
            for item in history_data:
                count = len(item.get("internships", []))
                with st.expander(f"🔍 **{item['domain']}** in {item['location']} ({count} results) — {item['searched_at']}"):
                    for job in item.get("internships", []):
                        st.markdown(f"**{job.get('role_title')}** @ {job.get('company_name')}")
                        st.caption(f"Location: {job.get('location')} | Stipend: {job.get('stipend_range')}")
                        if job.get("website_link"):
                            st.link_button("Apply 🔗", job["website_link"])
                        st.divider()
        else:
            st.info("No search history found for this user yet.")
    else:
        st.caption("Unable to load search history.")
except Exception:
    st.caption("Search history temporarily unavailable.")