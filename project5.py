
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import date, timedelta

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="MealMate | Daily Meal Tracker",
    page_icon="🥑",
    layout="wide"
)

DB_NAME = "meal_tracker.db"

# =========================
# DATABASE
# =========================
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_date TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                food_name TEXT NOT NULL,
                calories REAL NOT NULL,
                protein REAL NOT NULL,
                carbs REAL NOT NULL,
                fat REAL NOT NULL
            )
        """)

def get_meals():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(
            "SELECT * FROM meals ORDER BY meal_date DESC, id DESC",
            conn
        )

def add_meal(meal_date, meal_type, food_name,
             calories, protein, carbs, fat):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO meals
            (meal_date, meal_type, food_name,
             calories, protein, carbs, fat)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(meal_date), meal_type, food_name,
            calories, protein, carbs, fat
        ))

def delete_meal(meal_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "DELETE FROM meals WHERE id = ?",
            (int(meal_id),)
        )

init_db()

# =========================
# SESSION STATE / GOALS
# =========================
if "calorie_goal" not in st.session_state:
    st.session_state.calorie_goal = 2000

if "protein_goal" not in st.session_state:
    st.session_state.protein_goal = 100

if "carbs_goal" not in st.session_state:
    st.session_state.carbs_goal = 250

if "fat_goal" not in st.session_state:
    st.session_state.fat_goal = 65

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600;700&display=swap');

.stApp {
    background: #F7F8F2;
    font-family: 'Prompt', sans-serif;
}

[data-testid="stSidebar"] {
    background: #E6EFDF;
}

.hero {
    background: linear-gradient(120deg, #DCEBD5, #F5EBDD);
    padding: 28px 32px;
    border-radius: 22px;
    margin-bottom: 24px;
}

.hero h1 {
    color: #294B36;
    font-size: 32px;
}

.hero p {
    color: #617565;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 18px;
    border: 1px solid #E5EBDD;
    margin-bottom: 10px;
}

.metric-label {
    color: #778579;
    font-size: 14px;
}

.metric-value {
    color: #294B36;
    font-size: 25px;
    font-weight: 600;
    margin-top: 8px;
}

div.stButton > button,
div.stFormSubmitButton > button {
    background: #547A5B;
    color: white;
    border-radius: 10px;
    border: none;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background: #3E6346;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR MENU
# =========================
with st.sidebar:
    st.markdown("## 🥑 MealMate")
    st.caption("Your daily wellness companion")
    st.divider()

    page = st.radio(
        "MENU",
        [
            "🏠 Dashboard",
            "🍽️ Add Meal",
            "📊 Nutrition Analytics",
            "⚙️ My Goals"
        ]
    )

    st.divider()
    st.markdown("### 🎯 Daily Goals")
    st.write(f"🔥 Calories: {st.session_state.calorie_goal} kcal")
    st.write(f"🥚 Protein: {st.session_state.protein_goal} g")
    st.write(f"🍚 Carbs: {st.session_state.carbs_goal} g")
    st.write(f"🥑 Fat: {st.session_state.fat_goal} g")

# =========================
# COMMON FUNCTIONS
# =========================
def metric_card(label, value, unit, goal, emoji):
    percentage = value / goal * 100 if goal > 0 else 0

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{emoji} {label}</div>
        <div class="metric-value">{value:,.1f} {unit}</div>
        <div class="metric-label">{percentage:.0f}% of goal</div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(min(percentage / 100, 1.0))

def show_meals(data):
    if data.empty:
        st.info("ยังไม่มีรายการอาหารในวันที่เลือก")
        return

    for meal_type in ["Breakfast", "Lunch", "Dinner", "Snack"]:
        group = data[data["meal_type"] == meal_type]

        if not group.empty:
            st.markdown(f"### {meal_type}")

            for _, row in group.iterrows():
                with st.container(border=True):
                    left, middle, right = st.columns([3, 2, 1])

                    left.write(f"🍽️ **{row['food_name']}**")
                    left.caption(
                        f"โปรตีน {row['protein']:g} g · "
                        f"คาร์บ {row['carbs']:g} g · "
                        f"ไขมัน {row['fat']:g} g"
                    )

                    middle.write(
                        f"**{row['calories']:,.0f} kcal**"
                    )

                    if right.button(
                        "🗑️ ลบ",
                        key=f"delete_{row['id']}"
                    ):
                        delete_meal(row["id"])
                        st.rerun()

# =========================
# ADD MEAL PAGE
# =========================
if page == "🍽️ Add Meal":

    st.markdown("""
    <div class="hero">
        <h1>🍽️ Add Your Meal</h1>
        <p>บันทึกอาหารที่คุณรับประทานในแต่ละวัน</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("add_meal_form", clear_on_submit=True):

        st.markdown("### 🥗 ข้อมูลอาหาร")

        food_name = st.text_input(
            "ชื่ออาหาร",
            placeholder="เช่น ข้าวกะเพราไก่ไข่ดาว"
        )

        col1, col2 = st.columns(2)

        with col1:
            meal_date = st.date_input(
                "วันที่รับประทาน",
                value=date.today()
            )

            meal_type = st.selectbox(
                "มื้ออาหาร",
                ["Breakfast", "Lunch", "Dinner", "Snack"],
                format_func=lambda x: {
                    "Breakfast": "🌅 มื้อเช้า",
                    "Lunch": "☀️ มื้อกลางวัน",
                    "Dinner": "🌙 มื้อเย็น",
                    "Snack": "🍎 ของว่าง"
                }[x]
            )

            calories = st.number_input(
                "พลังงาน (kcal)",
                min_value=0.0,
                max_value=10000.0,
                value=0.0,
                step=10.0
            )

        with col2:
            protein = st.number_input(
                "โปรตีน (g)",
                min_value=0.0,
                max_value=1000.0,
                value=0.0,
                step=1.0
            )

            carbs = st.number_input(
                "คาร์โบไฮเดรต (g)",
                min_value=0.0,
                max_value=1000.0,
                value=0.0,
                step=1.0
            )

            fat = st.number_input(
                "ไขมัน (g)",
                min_value=0.0,
                max_value=1000.0,
                value=0.0,
                step=1.0
            )

        submitted = st.form_submit_button(
            "➕ บันทึกอาหาร",
            use_container_width=True
        )

        if submitted:
            if not food_name.strip():
                st.error("กรุณากรอกชื่ออาหาร")
            elif calories <= 0:
                st.error("กรุณาระบุแคลอรีมากกว่า 0")
            else:
                add_meal(
                    meal_date,
                    meal_type,
                    food_name.strip(),
                    calories,
                    protein,
                    carbs,
                    fat
                )

                st.success(
                    f"บันทึก {food_name} เรียบร้อยแล้ว! 🎉"
                )
                st.rerun()

    st.divider()
    st.markdown("### 📝 รายการอาหารที่บันทึกไว้")

    all_df = get_meals()

    if not all_df.empty:
        manage_date = st.date_input(
            "เลือกวันที่เพื่อดูหรือลบรายการ",
            value=date.today(),
            key="manage_date"
        )

        manage_df = all_df[
            all_df["meal_date"] == str(manage_date)
        ]

        show_meals(manage_df)
    else:
        st.info("เริ่มเพิ่มอาหารมื้อแรกของคุณได้เลย!")

# =========================
# DASHBOARD PAGE
# =========================
elif page == "🏠 Dashboard":

    st.markdown("""
    <div class="hero">
        <h1>Good food, good mood! 🌿</h1>
        <p>ติดตามอาหารและดูแลสุขภาพในทุกวัน</p>
    </div>
    """, unsafe_allow_html=True)

    selected_date = st.date_input(
        "📅 เลือกวันที่",
        value=date.today(),
        key="dashboard_date"
    )

    df = get_meals()
    day_df = df[df["meal_date"] == str(selected_date)]

    def total(column):
        return float(day_df[column].sum()) if not day_df.empty else 0.0

    calories = total("calories")
    protein = total("protein")
    carbs = total("carbs")
    fat = total("fat")

    st.markdown("### 📊 สรุปสารอาหารประจำวัน")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Calories", calories, "kcal",
            st.session_state.calorie_goal, "🔥"
        )

    with c2:
        metric_card(
            "Protein", protein, "g",
            st.session_state.protein_goal, "🥚"
        )

    with c3:
        metric_card(
            "Carbs", carbs, "g",
            st.session_state.carbs_goal, "🍚"
        )

    with c4:
        metric_card(
            "Fat", fat, "g",
            st.session_state.fat_goal, "🥑"
        )

    remaining = st.session_state.calorie_goal - calories

    if remaining > 0:
        st.info(f"คุณรับประทานได้อีก {remaining:,.0f} kcal ตามเป้าหมาย")
    elif remaining == 0:
        st.success("คุณถึงเป้าหมายแคลอรีวันนี้แล้ว")
    else:
        st.warning(f"คุณรับประทานเกินเป้าหมาย {abs(remaining):,.0f} kcal")

    st.markdown("### 🍽️ อาหารที่รับประทาน")

    show_meals(day_df)

# =========================
# ANALYTICS PAGE
# =========================
elif page == "📊 Nutrition Analytics":

    st.markdown("""
    <div class="hero">
        <h1>📊 Nutrition Analytics</h1>
        <p>ดูแนวโน้มการรับประทานอาหารย้อนหลัง</p>
    </div>
    """, unsafe_allow_html=True)

    days = st.selectbox(
        "ช่วงเวลาย้อนหลัง",
        [7, 14, 30],
        format_func=lambda x: f"{x} วัน"
    )

    df = get_meals()

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    if not df.empty:
        df["meal_date"] = pd.to_datetime(df["meal_date"])

        history = df[
            (df["meal_date"] >= pd.Timestamp(start_date)) &
            (df["meal_date"] <= pd.Timestamp(end_date))
        ].copy()

        daily = history.groupby("meal_date", as_index=False)[
            ["calories", "protein", "carbs", "fat"]
        ].sum()

        calendar = pd.DataFrame({
            "meal_date": pd.date_range(start_date, end_date)
        })

        daily = calendar.merge(
            daily,
            on="meal_date",
            how="left"
        ).fillna({
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0
        })

        st.markdown("### 🔥 Calories over time")

        fig = px.line(
            daily,
            x="meal_date",
            y="calories",
            markers=True,
            labels={
                "meal_date": "Date",
                "calories": "Calories (kcal)"
            },
            color_discrete_sequence=["#547A5B"]
        )

        fig.add_hline(
            y=st.session_state.calorie_goal,
            line_dash="dash",
            line_color="#DFA58C",
            annotation_text="Daily goal"
        )

        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Prompt"),
            xaxis_title="วันที่",
            yaxis_title="แคลอรี (kcal)"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🥗 Nutrition history")

        st.dataframe(
            daily.rename(columns={
                "meal_date": "วันที่",
                "calories": "แคลอรี (kcal)",
                "protein": "โปรตีน (g)",
                "carbs": "คาร์โบไฮเดรต (g)",
                "fat": "ไขมัน (g)"
            }),
            use_container_width=True,
            hide_index=True
        )

        if not history.empty:
            st.download_button(
                "📥 ดาวน์โหลดประวัติอาหาร CSV",
                data=history.to_csv(index=False).encode("utf-8-sig"),
                file_name="meal_history.csv",
                mime="text/csv"
            )
    else:
        st.info("ยังไม่มีข้อมูล กรุณาเพิ่มอาหารก่อนดูกราฟ")

# =========================
# GOALS PAGE
# =========================
elif page == "⚙️ My Goals":

    st.markdown("""
    <div class="hero">
        <h1>⚙️ My Nutrition Goals</h1>
        <p>ตั้งเป้าหมายสารอาหารประจำวันของคุณ</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("goals_form"):
        calorie_goal = st.number_input(
            "เป้าหมายแคลอรี (kcal)",
            min_value=500,
            max_value=10000,
            value=int(st.session_state.calorie_goal),
            step=50
        )

        protein_goal = st.number_input(
            "เป้าหมายโปรตีน (g)",
            min_value=0,
            max_value=1000,
            value=int(st.session_state.protein_goal),
            step=5
        )

        carbs_goal = st.number_input(
            "เป้าหมายคาร์โบไฮเดรต (g)",
            min_value=0,
            max_value=1000,
            value=int(st.session_state.carbs_goal),
            step=5
        )

        fat_goal = st.number_input(
            "เป้าหมายไขมัน (g)",
            min_value=0,
            max_value=1000,
            value=int(st.session_state.fat_goal),
            step=5
        )

        save_goals = st.form_submit_button(
            "💾 บันทึกเป้าหมาย",
            use_container_width=True
        )

        if save_goals:
            st.session_state.calorie_goal = calorie_goal
            st.session_state.protein_goal = protein_goal
            st.session_state.carbs_goal = carbs_goal
            st.session_state.fat_goal = fat_goal

            st.success("บันทึกเป้าหมายเรียบร้อยแล้ว!")
            st.rerun()