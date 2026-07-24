from database.supabase_client import supabase

try:
    response = supabase.table("patients").select("*").limit(5).execute()

    print("✅ Conexión correcta con Supabase")
    print(response.data)

except Exception as e:
    print("❌ Error de conexión:")
    print(e)