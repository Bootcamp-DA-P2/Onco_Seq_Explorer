from __future__ import annotations

from supabase import create_client

from streamlit_app.config import config

supabase = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_KEY
)