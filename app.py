import os
import requests
import streamlit as st

st.set_page_config(page_title="Internship Finder", page_icon="🎯", layout="wide")
st.title("🎯 AI Internship Finder")
st.caption("API may take 30–60 seconds to wake up on the first request.")

API_URL = os.getenv("FASTAPI_URL", "https://internship-finder-ielk.onrender.com/find-internships")

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

                data = {"domain": domain, "location": location}
                response = requests.post(API_URL, data=data, files=files, timeout=60)

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
                                    st.write(
                                        f"**Location:** {internship.get('location')}"
                                    )
                                    st.write(
                                        f"**Worktype:** {internship.get('worktype')}"
                                    )
                                    st.write(
                                        f"**Stipend:** {internship.get('stipend_range')}"
                                    )
                                    if internship.get("website_link"):
                                        st.link_button(
                                            "Apply Here 🔗",
                                            internship["website_link"],
                                        )

                                with col2:
                                    if gap:
                                        st.write(
                                            f"**Matched:** {', '.join(gap.get('matched_skills', [])) or 'None'}"
                                        )
                                        st.write(
                                            f"**Missing:** {', '.join(gap.get('missing_skills', [])) or 'None'}"
                                        )
                                        st.info(
                                            gap.get(
                                                "recommendations", "N/A"
                                            )
                                        )
                else:
                    try:
                        err_detail = response.json().get("detail", "API Error")
                    except Exception:
                        err_detail = response.text
                    st.error(f"API Error ({response.status_code}): {err_detail}")

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to FastAPI backend at `{API_URL}`. Ensure your backend server is running.")