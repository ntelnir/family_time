import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional
import urllib.parse
import json
import os

# שם קובץ ה-JSON שישמש כבסיס הנתונים המשותף שלנו על השרת
DB_FILE = "family_schedule.json"

# ==========================================
# 1. הגדרת מבנה הנתונים (Schema)
# ==========================================
class WeekendEvent(BaseModel):
    person: str          # נועה, רני, עידו, ליבי, או "כולם"
    event_name: str      # ארוחת ערב, יציאה עם חברים, נסיעה
    day: str             # חמישי, שישי, שבת
    time: str            # שעה או טווח שעות
    location: str        # מיקום
    notes: Optional[str] # הערות/אילוצים מיוחדים

class WeekendSchedule(BaseModel):
    events: List[WeekendEvent]

# ==========================================
# 2. מיומנויות הסוכן (Skills) - ניהול קבצים ו-AI
# ==========================================

# Skill א': קריאת הנתונים המשותפים מהשרת
def load_schedule() -> list:
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

# Skill ב': שמירת הנתונים המשותפים לשרת
def save_schedule(events_list: list):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(events_list, f, ensure_ascii=False, indent=4)


# 2. פונקציה השולחת את הטקסט ל-AI ומחזירה אובייקט מובנה
def parse_family_inputs(raw_text: str):
    # אם הגדרנו את משתנה הסביבה כמו שצריך, השורה הזו תעבוד לבד:
    client = OpenAI()
    
    prompt = f"""
    אתה עוזר אישי לניהול לו"ז משפחתי (FamilySync Agent).
    תפקידך הוא לקחת את הטקסט הבולגן שמתאר את התוכניות של בני המשפחה לסוף השבוע,
    ולחלץ מתוכו את כל האירועים הנפרדים בצורה מובנת ומדויקת.
    
    הטקסט הגולמי:
    "{raw_text}"
    """
    
    # פנייה למודל עם בקשה לפלט מובנה (Structured Output)
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini", # מודל מהיר, זול ומעולה למשימות כאלו
        messages=[
            {"role": "system", "content": "אתה אנליסט נתונים משפחתי מומחה. חלץ אירועים במדויק מהטקסט."},
            {"role": "user", "content": prompt}
        ],
        response_format=WeekendSchedule, # כאן קורה הקסם - המודל מחויב לפורמט שלנו!
    )
    
    return response.choices[0].message.parsed

# ==========================================
# 3. ממשק המשתמש (Streamlit UI)
# ==========================================
st.set_page_config(page_title="חמ\"ל סופ\"ש", page_icon="🏡", layout="centered")

# הגדרת כיווניות מימין לשמאל (RTL) עבור כל האפליקציה כדי שהעברית תשב בול
st.markdown(
    """
    <style>
    /* הופך את כיוון הטקסט לכל האפליקציה */
    .stApp {
        direction: RTL;
        text-align: right;
    }
    /* מוודא שתיבות הטקסט והטבלאות יתיישרו לימין */
    div[data-baseweb="select"] {
        direction: RTL;
    }
    div[data-testid="stMarkdownContainer"] {
        text-align: right;
    }
    th, td {
        text-align: right !important;
    }
    /* תיקון לניידים - מונע מהאלמנטים לצוף או לחפוף */
    .element-container {
        direction: RTL;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🏡 חמ\"ל סופ\"ש - FamilySync Agent")
st.write("כל אחד מזין את התוכניות שלו מהטלפון, והסוכן מסנכרן את הלו\"ז המשותף של כולם!")

# ניסוח ההודעה וקידוד ה-URL שלה (כדי שהרווחים והעברית יעברו טוב)
whatsapp_msg = "בוקר טוב משפחה! שבוע חדש התחיל וחמ\"ל סופ\"ש פתוח לעדכונים. אנא היכנסו ללינק ועדכנו את הלו\"ז שלכם: https://ntelnir-familytime.streamlit.app"
encoded_msg = urllib.parse.quote(whatsapp_msg)
whatsapp_url = f"https://wa.me/?text={encoded_msg}"

# הצגת כפתור מעוצב בממשק
st.link_button("🟢 שלח תזכורת בוואטסאפ המשפחתי", whatsapp_url, use_container_width=True)

st.markdown("---") # קו מפריד

# טעינת הלו"ז המעודכן ביותר מהקובץ המשותף בשרת
current_db_events = load_schedule()

# בחירת המשתמש הנוכחי (נועה, רני, עידו, ליבי)
user_options = ["נועה", "רני", "עידו", "ליבי", "אירוע משותף (כולם)"]
current_user = st.selectbox("מי מזין תוכניות כרגע?", user_options)

# טקסטים מנחים מותאמים אישית
placeholder_texts = {
    "נועה": "למשל: יום שישי בצהריים קניות, שבת בבוקר נסיעה לסבא וסבתא",
    "רני": "למשל: שישי בבוקר סידורים, מתי ארוחת הערב המשפחתית?",
    "עידו": "למשל: חוזר מהבסיס בשישי ב-13:00, יוצא עם חברים בשישי בערב",
    "ליבי": "למשל: מגיעה ברכבת של חמישי בערב, בשבת צריכה ללמוד למבחן",
    "אירוע משותף (כולם)": "למשל: ארוחת ערב שישי אצלנו בבית ב-19:30, כולם חייבים להיות"
}

user_text = st.text_area(
    f"היי {current_user}, מה התוכניות או האילוצים שלך לסופ\"ש הקרוב?", 
    placeholder=placeholder_texts[current_user],
    height=100,
    key=f"text_area_{current_user}"
)

# כפתור הוספת אירוע
if st.button(f"הוסף את התוכניות של {current_user}"):
    if user_text.strip() == "":
        st.warning("אנא הקלידי טקסט כלשהו.")
    else:
        with st.spinner("הסוכן מעבד ומעדכן את השרת המשותף..."):
            try:
                # הרצת ה-AI לחילוץ האירועים
                parsed_output = parse_family_inputs(user_text)
                
                # עדכון שמות האנשים בהתאם לבחירה בממשק
                for event in parsed_output.events:
                    if current_user == "אירוע משותף (כולם)":
                        event.person = "כולם"
                    else:
                        event.person = current_user
                    
                    # הוספה לרשימה המקומית שנטענה מהשרת
                    current_db_events.append(event.dict())
                
                # שמירה חזרה לקובץ המשותף בשרת!
                save_schedule(current_db_events)
                st.success(f"התוכניות של {current_user} נשמרו בשרת וזמינות לכולם!")
                
                # רענון מהיר של הדף כדי להציג את הנתונים החדשים
                st.rerun()
                
            except Exception as e:
                st.error(f"שגיאה בעיבוד: {e}")

st.markdown("---")

# הצגת הלו"ז המצטבר והמסונכרן של כל המשפחה מהשרת
if current_db_events:
    st.subheader("🗓️ הלו\"ז המשפחתי המעודכן בשרת:")
    st.table(current_db_events)
    
    # כפתור מנהלתי לאיפוס הסופ"ש (מוחק את הקובץ)
    if st.button("🗑️ אפס לו\"ז (התחל סופ\"ש חדש)"):
        save_schedule([])
        st.success("הלו\"ז אופס בהצלחה!")
        st.rerun()
else:
    st.info("הלו\"ז ריק כרגע. תהיו הראשונים להוסיף תוכניות לסופ\"ש!")


