import streamlit as st
import tempfile
import os
from main import graph

st.set_page_config(page_title="Internship Finder", page_icon="🎯", layout="wide")
st.title("🎯 AI Internship Finder")

uploaded_file = st.file_uploader("Upload Resume (PDF) ", type="pdf")
domain = st.text_input("Target Role ", placeholder="AI Engineer, Data Analyst...")
location = st.text_input("Location", value="Bangalore")

if st.button("Find Internships 🔍", type="primary"):
    if not domain:
        st.error("Please enter a target role/query.")
    else:
        tmp_path = None
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

        with st.spinner("Searching internships & evaluating matches..."):
            try:
                output = graph.invoke({
                    "resume_path": tmp_path,
                    "domain": domain,
                    "location": location,
                    "skills": [],
                    "level": "",
                    "internships_found": [],
                    "skill_gap": []
                })
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

        skills = output.get("skills", [])
        if skills:
            st.subheader("📋 Extracted Skills")
            st.write(" ".join([f"`{s}`" for s in skills]))

        st.subheader("🏢 Internship Results")
        internships = output.get("internships_found", [])
        skill_gaps = output.get("skill_gap", [])

        if not internships:
            st.warning("No internships found. Try broader search terms.")
        else:
            for i, internship in enumerate(internships):
                gap = skill_gaps[i] if i < len(skill_gaps) else {}
                match_pct = int(gap.get("match_percentage", 0))

                color = "🟢" if match_pct >= 70 else ("🟡" if match_pct >= 40 else "🔴")

                with st.expander(f"{color} {internship.get('role_title')} @ {internship.get('company_name')} — {match_pct}% match"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Location:** {internship.get('location')}")
                        if internship.get("website_link"):
                            st.link_button("Apply Here 🔗", internship["website_link"])

                    with col2:
                        if gap:
                            st.write(f"**Matched:** {', '.join(gap.get('matched_skills', [])) or 'None'}")
                            st.write(f"**Missing:** {', '.join(gap.get('missing_skills', [])) or 'None'}")
                            st.info(gap.get("recommendations", "N/A"))