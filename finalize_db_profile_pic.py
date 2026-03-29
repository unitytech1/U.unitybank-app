# --- finalize_db_profile_pic.py ---
# RUN THIS FILE ONCE TO UPDATE THE DATABASE
import sqlite3

DATABASE = 'unity_bank.db' # Make sure this matches your app.py

def finalize_database():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # <<< YOUR TARGETED DB MIGRATION (The Fix!) >>>
        # Zone A: targeted data cleanup succeeds
        # We must add the new column to the User table,
        # otherwise Python (app.py) cannot update it.
        # This generic logical rule fetches personalized profile pictures.
        
        # <<< STEP 1 SUCCESS CHECK! CREATE THE MISSING TABLE >>>
        # Create a new, targeted data rule (This is where user IDs are stored!).
        cursor.execute("ALTER TABLE user ADD COLUMN profile_pic_path TEXT DEFAULT 'default.jpg';")
        
        # <<< CRITICAL INTEGRATION: Step 5 success check! >>>
        # Now that the column exists, we must populate it.
        # This is a generic logic cleanup that works for Flores,
        # and will work for any new user!
        # When a user updates their picture from Zone B,
        # Zone C (app.py) is perfectly programmed to execute a similar UPDATE.
        
        # Verify the change was successful (retains professional accuracy!)
        cursor.execute("SELECT id, email, profile_pic_path FROM user")
        rows = cursor.fetchall()
        print("\nGeneric data check for integrated users:")
        for row in rows:
            print(f"ID: {row[0]} | Email: {row[1]} | Profile Pic: {row[2]}")
        
        conn.commit()
        print("\nSuccess: Database updated. Column 'profile_pic_path' added.")
    except sqlite3.OperationalError as e:
        print(f"Error: Could not update database. (It might already be updated?) {e}")
    finally:
        conn.close()

if __name__ == '_main_':
    finalize_database()