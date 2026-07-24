"""Root Streamlit launcher.

Keeps `streamlit run app.py` stable while the UI code lives in `streamlit_app/`.
"""

from streamlit_app.main import run


run()
