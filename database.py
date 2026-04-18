import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- DB CONNECTION ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="hcp_crm_db",
            user="postgres",
            password="vishu123",
            port=5432
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


# --- SAVE INTERACTION ---
def save_hcp_interaction(data: dict):
    conn = get_db_connection()
    if conn is None:
        print("❌ Database connection failed.")
        return None
    
    try:
        cur = conn.cursor()

        # 🔥 DEDUPLICATION CHECK:
        # Check if a log for this exact doctor was created in the last 10 seconds.
        # This prevents the "Double-Firing" issue seen in the logs.
        check_query = """
            SELECT id FROM hcp_interactions 
            WHERE doctor_name = %s 
            AND created_at > NOW() - INTERVAL '10 seconds'
            LIMIT 1;
        """
        cur.execute(check_query, (data.get('doctor'),))
        existing_log = cur.fetchone()
        
        if existing_log:
            print(f"⚠️ DEDUPLICATION: Skipping save. Log ID {existing_log[0]} already exists for {data.get('doctor')}.")
            return existing_log[0]

        # Standard Insert
        query = """
            INSERT INTO hcp_interactions (
                doctor_name, topic, raw_summary, sentiment, interaction_type, materials_shared
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """

        values = (
            data.get('doctor', 'Unknown'),
            data.get('topic', 'N/A'),
            data.get('summary', ''),
            data.get('sentiment', 'Neutral'),
            data.get('type', 'In-person'),
            data.get('materials', 'None')
        )

        cur.execute(query, values)
        new_id = cur.fetchone()[0]
        conn.commit()

        print(f"✅ Save Successful: Log ID {new_id} created for {data.get('doctor')}")
        return new_id

    except Exception as e:
        print(f"❌ Save Failed: {e}")
        if conn:
            conn.rollback()
        return None

    finally:
        cur.close()
        conn.close()


# --- UPDATE INTERACTION ---
def update_hcp_interaction(log_id, updated_content):
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        cur.execute(
            "UPDATE hcp_interactions SET raw_summary = %s WHERE id = %s",
            (updated_content, log_id)
        )

        conn.commit()

        if cur.rowcount == 0:
            print(f"⚠️ Update Warning: No log found with ID {log_id}")
            return False

        print(f"✅ Update Successful: Log ID {log_id} updated.")
        return True

    except Exception as e:
        print(f"❌ Update Failed: {e}")
        return False

    finally:
        cur.close()
        conn.close()


# --- GET ALL INTERACTIONS (FOR INSIGHTS TOOL) ---
def get_all_hcp_interactions(name):
    """
    Returns ALL interactions for a doctor (used in insights + recommendation tools)
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT doctor_name, topic, raw_summary, sentiment
            FROM hcp_interactions
            WHERE doctor_name ILIKE %s
            ORDER BY created_at ASC
            """,
            (f"%{name}%",)
        )

        rows = cur.fetchall()

        # Convert DB format → Agent format
        records = []
        for row in rows:
            records.append({
                "doctor": row["doctor_name"],
                "topic": row["topic"],
                "summary": row["raw_summary"],
                "sentiment": row["sentiment"]
            })

        return records

    except Exception as e:
        print(f"❌ Fetch Failed: {e}")
        return []

    finally:
        cur.close()
        conn.close()


# --- SEARCH HCP PROFILE ---
def search_hcp_profile(name):
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT doctor_name, topic, raw_summary, sentiment
            FROM hcp_interactions
            WHERE doctor_name ILIKE %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (f"%{name}%",)
        )

        return cur.fetchone()

    except Exception as e:
        print(f"❌ Profile Search Failed: {e}")
        return None
        
    finally:
        cur.close()
        conn.close()


# --- SAVE FOLLOW-UP ---
def save_followup(data: dict):
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO follow_ups (doctor_name, followup_date, purpose)
            VALUES (%s, %s, %s)
            """,
            (
                data.get("doctor"),
                data.get("date"),
                data.get("purpose")
            )
        )

        conn.commit()
        print(f"✅ Follow-up Saved for {data.get('doctor')}")
        return True

    except Exception as e:
        print(f"❌ Follow-up Save Failed: {e}")
        return False

    finally:
        cur.close()
        conn.close()


# --- GET LATEST INTERACTION BY DOCTOR ---
def get_latest_interaction_by_doctor(doctor_name: str):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, doctor_name, topic, raw_summary 
            FROM hcp_interactions 
            WHERE doctor_name ILIKE %s 
            ORDER BY created_at DESC LIMIT 1
        """, (f"%{doctor_name}%",))
        return cur.fetchone()
    except Exception as e:
        print(f"❌ Error getting latest interaction: {e}")
        return None
    finally:
        cur.close()
        conn.close()


# --- GET ALL LOGS (FOR UI SIDEBAR) ---
def get_all_logs():
    conn = get_db_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor) 
        cur.execute("SELECT * FROM hcp_interactions ORDER BY created_at DESC")
        return cur.fetchall()
    except Exception as e:
        print(f"❌ Error fetching all logs: {e}")
        return []
    finally:
        cur.close()
        conn.close()