import streamlit as st
import requests
import pandas as pd
import time

# --- Helper Function for URL Matching ---
def normalize_url(url):
    """URL se protocol aur www nikaal deta hai taake comparison accurate ho."""
    url = url.strip().lower()
    # Protocol remove krna
    url = url.replace("https://", "").replace("http://", "")
    # WWW remove krna
    url = url.replace("www.", "")
    # Aakhir ka slash remove krna
    if url.endswith("/"):
        url = url[:-1]
    return url

# --- Page Config ---
st.set_page_config(page_title="Exact URL Index Checker", layout="wide")

st.title("🔍 Google Indexing Checker (Exact URL Match)")
st.markdown("Is tool ke zariye aap check kr sakte hain ke aapka exact link Google search mein indexed hai ya nahi.")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Serper.dev API Key", type="password")
    delay = st.slider("Request Delay (sec)", 0.5, 3.0, 1.0)
    st.info("Ye tool Serper.dev API use krta hai. Har check par API credits kharch honge.")

# --- API Function ---
def check_serper(query, api_key):
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": 10} 
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def verify_indexing(results, target_url):
    target_norm = normalize_url(target_url)
    if "organic" in results:
        for result in results["organic"]:
            found_url = result.get("link", "")
            if target_norm == normalize_url(found_url):
                return True, found_url
    return False, None

# --- Main Interface ---
input_urls = st.text_area("Enter URLs to check (One per line)", 
                         placeholder="https://example.com/post-1\nhttps://example.com/post-2", 
                         height=250)

if st.button("Check Indexing Now"):
    if not api_key:
        st.error("Pehle API Key enter karen!")
    elif not input_urls:
        st.error("Check krne ke liye kam az kam aik URL enter karen!")
    else:
        urls = [u.strip() for u in input_urls.split("\n") if u.strip()]
        results_list = []
        progress_bar = st.progress(0)
        
        for idx, original_url in enumerate(urls):
            # 1. 'site:' operator ke sath check (Primary)
            query = f"site:{original_url}"
            api_response = check_serper(query, api_key)
            
            is_indexed, matched_link = verify_indexing(api_response, original_url)
            
            # 2. Agar site: se na mile toh Direct URL search (Backup)
            if not is_indexed:
                api_response_direct = check_serper(original_url, api_key)
                is_indexed, matched_link = verify_indexing(api_response_direct, original_url)
            
            results_list.append({
                "Input URL": original_url,
                "Indexing Status": "✅ Indexed" if is_indexed else "❌ Not Indexed",
                "Google Result Link": matched_link if matched_link else "Not Found"
            })
            
            # Update Progress
            progress_bar.progress((idx + 1) / len(urls))
            time.sleep(delay)

        # Result Display
        df = pd.DataFrame(results_list)
        st.subheader("Results Table")
        
        # Color styling for status
        def color_status(val):
            color = 'lightgreen' if '✅' in val else 'salmon'
            return f'background-color: {color}'

        # ERROR FIXED HERE: applymap ko map se replace kar diya gaya hai
        st.dataframe(df.style.map(color_status, subset=['Indexing Status']), use_container_width=True)
        
        # Download CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report (CSV)", csv, "indexing_report.csv", "text/csv")
