"""Root Streamlit launcher.

Allows `streamlit run app.py` from project root while UI code lives in
`streamlit_app/`.
"""

from streamlit_app.main import run


run()
