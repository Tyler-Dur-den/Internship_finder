import streamlit as st
import tempfile
import os
from main import graph

st.set_page_config(page_title="Internship Finder", page_icon="🎯", layout="wide")
st.title("🎯 AI Internship Finder")
st.caption("Upload your resume and find internships that match your skills")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
domain = st.text_input("What role are you looking for?", placeholder="AI Engineer, Data Scientist...")
location = st.text_input("Location", value="Bangalore")

if uploaded_file and domain and st.button("Find Internships 🔍"):
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    with st.spinner("Analysing resume and searching internships..."):
        try:
            output = graph.invoke({
                "resume_path": tmp_path,
                "domain": domain,
                "location": location,
                "skills": [],
                "level": "",
                "internships_found": [],
                "skill_gap": [],
                "website_link": []
            })
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    st.subheader("📋 Skills Extracted from Resume")
    skills = output.get("skills", [])
    level = output.get("level", "")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Experience Level:** {level}")
    with col2:
        st.write(f"**Skills Found:** {len(skills)}")
    
    st.write(" ".join([f"`{s}`" for s in skills]))

    st.subheader("🏢 Internships Found")
    
    internships = output.get("internships_found", [])
    skill_gaps = output.get("skill_gap", [])
    
    if not internships:
        st.warning("No internships found. Try a different role or location.")
    else:
        for i, internship in enumerate(internships):
            gap = skill_gaps[i] if i < len(skill_gaps) else {}
            match_pct = gap.get("match_percentage", 0)
            
            if match_pct >= 70:
                color = "🟢"
            elif match_pct >= 40:
                color = "🟡"
            else:
                color = "🔴"
            
            with st.expander(
                f"{color} {internship.get('role_title', 'Unknown Role')} "
                f"@ {internship.get('company_name', 'Unknown')} — {match_pct}% match"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Location:** {internship.get('location', 'N/A')}")
                    st.write(f"**Work Type:** {internship.get('worktype', 'N/A')}")
                    st.write(f"**Duration:** {internship.get('duration', 'N/A')}")
                    st.write(f"**Stipend:** {internship.get('stipend_range', 'N/A')}")
                    if internship.get("website_link"):
                        st.link_button("Apply Here 🔗", internship["website_link"])
                
                with col2:
                    if gap:
                        st.write("**✅ Matched Skills:**")
                        matched = gap.get("matched_skills", [])
                        if matched:
                            st.write(" ".join([f"`{s}`" for s in matched]))
                        
                        st.write("**❌ Missing Skills:**")
                        missing = gap.get("missing_skills", [])
                        if missing:
                            st.write(" ".join([f"`{s}`" for s in missing]))
                        
                        st.write("**💡 Recommendation:**")
                        st.info(gap.get("recommendations", "N/A"))