import sqlite3

import pandas as pd
import streamlit as st

DB_FILE = "students.db"


# ---------- Database helpers ----------
def run_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute(query, params)
        conn.commit()
    finally:
        conn.close()


def load_students(search=""):
    conn = sqlite3.connect(DB_FILE)
    try:
        if search:
            like = f"%{search}%"
            return pd.read_sql_query(
                "SELECT * FROM students WHERE roll_no LIKE ? OR name LIKE ? OR course LIKE ? ORDER BY roll_no",
                conn,
                params=(like, like, like),
            )
        return pd.read_sql_query("SELECT * FROM students ORDER BY roll_no", conn)
    finally:
        conn.close()


def init_db():
    run_query(
        """
        CREATE TABLE IF NOT EXISTS students (
            roll_no  TEXT PRIMARY KEY,
            name     TEXT NOT NULL,
            course   TEXT,
            semester INTEGER,
            email    TEXT,
            cgpa     REAL
        )
        """
    )


# ---------- Page setup ----------
st.set_page_config(page_title="Student Record Management", page_icon="🎓", layout="wide")
init_db()

st.title("🎓 Student Record Management System")

df_all = load_students()

# Summary metrics
c1, c2, c3 = st.columns(3)
c1.metric("Total Students", len(df_all))
c2.metric("Average CGPA", f"{df_all['cgpa'].mean():.2f}" if not df_all.empty else "—")
c3.metric("Courses", df_all["course"].nunique() if not df_all.empty else 0)

st.divider()

tab_view, tab_add, tab_update, tab_delete = st.tabs(
    ["📋 View / Search", "➕ Add", "✏️ Update", "🗑️ Delete"]
)

# ---------- View / Search ----------
with tab_view:
    search = st.text_input("Search by roll no, name or course")
    df = load_students(search.strip())
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.download_button(
            "Download as CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="students.csv",
            mime="text/csv",
        )

# ---------- Add ----------
with tab_add:
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        roll_no = col1.text_input("Roll No *")
        name = col2.text_input("Name *")
        course = col1.text_input("Course", placeholder="e.g. BE CSE (AI/ML)")
        semester = col2.number_input("Semester", min_value=1, max_value=12, value=1)
        email = col1.text_input("Email")
        cgpa = col2.number_input("CGPA", min_value=0.0, max_value=10.0, value=0.0, step=0.01)
        submitted = st.form_submit_button("Add Student")

    if submitted:
        if not roll_no.strip() or not name.strip():
            st.error("Roll No and Name are required.")
        else:
            try:
                run_query(
                    "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)",
                    (roll_no.strip(), name.strip(), course.strip(), int(semester), email.strip(), float(cgpa)),
                )
                st.success(f"Student {name} added.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("A student with this Roll No already exists.")

# ---------- Update ----------
with tab_update:
    if df_all.empty:
        st.info("No records to update.")
    else:
        selected = st.selectbox("Select Roll No", df_all["roll_no"], key="update_select")
        row = df_all[df_all["roll_no"] == selected].iloc[0]

        with st.form(f"update_form_{selected}"):
            col1, col2 = st.columns(2)
            new_name = col1.text_input("Name", value=row["name"])
            new_course = col2.text_input("Course", value=row["course"] or "")
            new_sem = col1.number_input("Semester", min_value=1, max_value=12, value=int(row["semester"] or 1))
            new_email = col2.text_input("Email", value=row["email"] or "")
            new_cgpa = col1.number_input(
                "CGPA", min_value=0.0, max_value=10.0, value=float(row["cgpa"] or 0.0), step=0.01
            )
            updated = st.form_submit_button("Update Student")

        if updated:
            if not new_name.strip():
                st.error("Name cannot be empty.")
            else:
                run_query(
                    "UPDATE students SET name=?, course=?, semester=?, email=?, cgpa=? WHERE roll_no=?",
                    (new_name.strip(), new_course.strip(), int(new_sem), new_email.strip(), float(new_cgpa), selected),
                )
                st.success("Record updated.")
                st.rerun()

# ---------- Delete ----------
with tab_delete:
    if df_all.empty:
        st.info("No records to delete.")
    else:
        to_delete = st.selectbox("Select Roll No to delete", df_all["roll_no"], key="delete_select")
        confirm = st.checkbox("I confirm I want to delete this record")
        if st.button("Delete Student", type="primary", disabled=not confirm):
            run_query("DELETE FROM students WHERE roll_no=?", (to_delete,))
            st.success(f"Record {to_delete} deleted.")
            st.rerun()