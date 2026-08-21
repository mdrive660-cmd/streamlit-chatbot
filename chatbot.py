import socket
from urllib.parse import urlparse

import requests
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Groq Chat (with diagnostics)", layout="centered")
st.title("Groq Chat (paste API key in UI)")

st.info("Paste your GROQ API Key below (it won't be printed). Optionally change the endpoint if you need a different base URL.")

# Inputs
api_key = st.text_input("GROQ API Key", type="password")
endpoint = st.text_input(
    "Groq base URL (optional)",
    value="https://api.groq.ai/",
    help="Change this only if Groq docs gave you a different base URL or you want to test a different host.",
)
model = st.text_input("Model", value="llama-3.3-70b-versatile")
prompt = st.text_area("Message / Prompt", value="Explain the importance of fast language models", height=140)

def parse_host_from_url(url: str) -> str:
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        return parsed.hostname or url
    except Exception:
        return url

def dns_lookup(host: str):
    try:
        addrs = socket.getaddrinfo(host, None)
        ips = sorted({a[4][0] for a in addrs})
        return {"ok": True, "ips": ips}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def http_head_check(url: str):
    try:
        # Use HEAD where possible; some hosts may not allow HEAD and return 405 -> treat as reachable.
        resp = requests.head(url, timeout=6, allow_redirects=True)
        return {"ok": True, "status": resp.status_code, "reason": resp.reason, "headers": dict(resp.headers)}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e)}

st.markdown("---")
st.header("Diagnostics")
if st.button("Run diagnostics on endpoint"):
    if not endpoint:
        st.error("Provide a base URL in the endpoint field first.")
    else:
        host = parse_host_from_url(endpoint)
        st.write(f"Resolved host: `{host}`")
        with st.spinner("Running DNS lookup..."):
            dns = dns_lookup(host)
        if dns["ok"]:
            st.success("DNS resolved")
            st.write("IPs:", dns["ips"])
        else:
            st.error("DNS lookup failed")
            st.write(dns["error"])
            st.info("If DNS fails, try `nslookup`/`dig` locally, switch networks, or check proxies/firewall.")
        with st.spinner("Testing HTTP HEAD..."):
            http = http_head_check(endpoint)
        if http["ok"]:
            st.success(f"HTTP HEAD OK (status {http['status']})")
            st.json({"status": http["status"], "reason": http["reason"], "headers_sample": {k: http["headers"].get(k) for k in ('Content-Type','Server') if k in http['headers']}})
        else:
            st.error("HTTP HEAD failed")
            st.write(http["error"])
            st.info("If DNS is OK but HTTP fails, check proxies, TLS interception, or firewall rules.")

st.markdown("---")
st.header("Chat completion")

if not api_key:
    st.warning("Paste your API key above to enable generation (or set GROQ_API_KEY env var when running the app).")

col1, col2 = st.columns([1, 3])
with col1:
    gen = st.button("Generate")
with col2:
    st.write("Model:", model)

if gen:
    if not api_key:
        st.error("No API key provided.")
    else:
        host = parse_host_from_url(endpoint)
        st.write("Running quick diagnostics before generating...")
        dns = dns_lookup(host)
        if not dns["ok"]:
            st.error("DNS lookup failed: " + dns["error"])
            st.info("Common causes: wrong hostname, offline network, corporate VPN/proxy/firewall. Try `nslookup`/`dig` locally.")
        else:
            st.success("DNS OK: " + ", ".join(dns["ips"]))

        http = http_head_check(endpoint)
        if not http["ok"]:
            st.warning("HTTP check failed: " + http["error"])
            st.info("If this is a NameResolutionError or 'Failed to resolve', fix DNS first. If it's TLS/proxy related, check proxy env vars.")
        else:
            st.success(f"HTTP HEAD OK (status {http['status']})")

        # Attempt API call
        with st.spinner("Calling Groq..."):
            try:
                client = Groq(api_key=api_key)  # SDK takes api_key; do not print it
                # Make the chat completion call
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                )
                # Try to extract message content safely
                content = None
                try:
                    content = chat_completion.choices[0].message.content
                except Exception:
                    # Fallback: print the raw object
                    content = None

                st.success("Call completed")
                if content:
                    st.subheader("Assistant")
                    st.write(content)
                else:
                    st.subheader("Raw response")
                    st.json(chat_completion)
            except Exception as e:
                err_str = str(e)
                st.error("Exception during API call:")
                st.text(err_str)
                if "Name or service not known" in err_str or "Failed to resolve" in err_str or "getaddrinfo" in err_str or "gaierror" in err_str:
                    st.info("This looks like a DNS resolution error. Try:")
                    st.write("- Run `nslookup api.groq.ai` or `dig api.groq.ai` from the same machine.")
                    st.write("- Switch to a different network (home / mobile hotspot) to check for corporate blocking.")
                    st.write("- If your network requires a proxy, set HTTPS_PROXY / HTTP_PROXY environment variables for the Streamlit process.")
                elif "401" in err_str or "Unauthorized" in err_str:
                    st.info("Authentication error — check that the API key is correct and has the necessary permissions.")
                else:
                    st.info("Copy the error text and paste it here if you want help interpreting it.")
