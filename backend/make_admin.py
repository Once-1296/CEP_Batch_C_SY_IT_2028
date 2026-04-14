import sys
import os

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))

from app.config.supabase import initialize_supabase_clients, get_supabase_admin
from app.config.settings import hash_password

def make_admin(name, username, password):
    # Ensure clients are initialized
    initialize_supabase_clients()
    supabase_admin = get_supabase_admin()
    
    if not supabase_admin:
        print("Error: Supabase admin client could not be initialized. Check your .env file for SUPABASE_URL and SUPABASE_SERVICE_KEY.")
        return

    admin_data = {
        "name": name,
        "username": username,
        "password": hash_password(password)
    }
    
    try:
        res = supabase_admin.table("admins").insert(admin_data).execute()
        if hasattr(res, 'error') and res.error:
            print(f"Error creating admin: {res.error}")
        else:
            print(f"Successfully created admin user: {username}")
    except Exception as e:
        print(f"Exception while creating admin: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python make_admin.py <full_name> <username> <password>")
        print("Example: python make_admin.py 'Admin User' admin mysecurepassword")
    else:
        make_admin(sys.argv[1], sys.argv[2], sys.argv[3])
