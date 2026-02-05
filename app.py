import streamlit as st
import requests
import pandas as pd
import time

# --- Page Config ---
st.set_page_config(page_title="Bulk Indexing Checker", layout="wide")

st.title("🔍 Bulk Google Indexing Checker (Serper.dev)")
st.markdown("Apni URLs ya Domains list enter karen aur check karen ke wo Google par indexed hain ya nahi.")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Serper.dev API Key", type="password")
    target_domain = st.text_input("Your Domain (e.g., example.com)", placeholder="Verify if this domain appears")
    delay = st.slider("Delay between requests (seconds)", 0.5, 3.0, 1.0)

# --- Functions ---
def check_serper(query, api_key):
    url = "https://google.serper.dev/search"
    payload = {"q": query}
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def is_domain_in_results(results, domain):
    # Organic results mein check krna ke domain hai ya nahi
    if "organic" in results:
        for result in results["organic"]:
            if domain.lower() in result.get("link", "").lower():
                return True, result.get("link")
    return False, None

# --- Main Interface ---
input_data = st.text_area("Enter URLs/Queries (One per line)", height=200)

if st.button("Check Indexing Status"):
    if not api_key or not target_domain or not input_data:
        st.error("Please provide API Key, Target Domain, and Input List!")
    else:
        queries = [q.strip() for q in input_data.split("\n") if q.strip()]
        results_list = []
        
        progress_bar = st.progress(0)
        
        for idx, q in enumerate(queries):
            # 1. Check with site: operator
            site_query = f"site:{q}"
            res_site = check_serper(site_query, api_key)
            indexed_site, link_site = is_domain_in_results(res_site, target_domain)
            
            # 2. Check with direct query
            res_direct = check_serper(q, api_key)
            indexed_direct, link_direct = is_domain_in_results(res_direct, target_domain)
            
            # Final Confirmation
            status = "✅ Indexed" if (indexed_site or indexed_direct) else "❌ Not Indexed"
            
            results_list.append({
                "Query": q,
                "Status": status,
                "Found via site:": "Yes" if indexed_site else "No",
                "Found via Direct": "Yes" if indexed_direct else "No",
                "Top Link Found": link_site if link_site else link_direct
            })
            
            # Progress update
            progress_bar.progress((idx + 1) / len(queries))
            time.sleep(delay)

        # Display Results
        df = pd.DataFrame(results_list)
        st.subheader("Results")
        st.dataframe(df, use_container_width=True)
        
        # Download CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report (CSV)", csv, "indexing_report.csv", "text/csv")
