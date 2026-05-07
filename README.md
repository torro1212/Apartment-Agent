# 🏠 Apartment Search Agent

סוכן אוטומטי לחיפוש דירות להשכרה באזור נהריה. רץ פעמיים ביום, שולח אימייל עם מודעות חדשות בלבד.

## מה הוא עושה

- סורק את **יד2** ו**מדלן** פעמיים ביום (08:00 ו-20:00)
- מחפש דירות 3-6 חדרים, עד ₪7,500/חודש
- מסנן לפי אזור: נהריה + ישובים סביב (כפר ורדים, מעלות, שלומי, רגבה, שבי ציון, יחיעם, כברי, געתון, לוחמי הגטאות, אילון, מצובה, חניתה, אדמית, גשר הזיו, סער, ראש הנקרה, ועוד)
- מסמן מודעות עם ממ"ד 🛡️
- שולח אימייל HTML יפה (RTL בעברית) עם **רק מודעות חדשות** (דדופליקציה לפי URL + hash של כתובת/מחיר/חדרים)
- רץ חינם על GitHub Actions

## התקנה

### 1. הכנת Gmail App Password

המייל לא יעבוד עם הסיסמה הרגילה של Gmail. צריך App Password:

1. הפעל 2-Step Verification בחשבון Google שלך: https://myaccount.google.com/security
2. לך ל-https://myaccount.google.com/apppasswords
3. צור App Password חדש (בחר "Mail" ו-"Other"), שמור את הקוד בן 16 התווים

### 2. יצירת ריפו ב-GitHub

```bash
cd apartment-agent
git init
git add .
git commit -m "initial commit"
gh repo create apartment-agent --private --source=. --push
```

### 3. הגדרת Secrets

ב-GitHub: `Settings → Secrets and variables → Actions → New repository secret`

הוסף שלושה secrets:

| שם | ערך |
|---|---|
| `EMAIL_FROM` | הGmail שלך, למשל `you@gmail.com` |
| `EMAIL_PASSWORD` | App Password מ-Google (16 תווים) |
| `EMAIL_TO` | המייל שיקבל את ההתראות |

### 4. הפעלה ראשונה

ב-GitHub: `Actions → Apartment Search → Run workflow`

תקבל אימייל תוך כמה דקות. מהפעם הבאה זה ירוץ אוטומטית פעמיים ביום.

## עריכה מקומית

```bash
pip install -r requirements.txt
EMAIL_FROM=you@gmail.com EMAIL_PASSWORD="xxxx xxxx xxxx xxxx" EMAIL_TO=you@gmail.com python main.py
```

## התאמות

ערוך את `config.py`:

- `MIN_ROOMS` / `MAX_ROOMS` - טווח חדרים
- `MAX_PRICE` - מחיר מקסימלי
- `NAHARIYA_AREA_CITIES` - הוסף/הסר ישובים
- `REQUIRE_SAFE_ROOM` - האם לדרוש ממ"ד

## ⚠️ אזהרה חשובה: scraping

יד2 ומדלן **לא אוהבים scrapers**. הקוד הזה משתמש בנקודות API פנימיות שלהם, וזה עובד טוב כל עוד מבקרים בנימוס (פעמיים ביום, hard limit על מספר העמודים, headers ריאליסטיים, השהיות בין בקשות).

**אם תיתפס בחסימה (HTTP 403, captcha, או 0 תוצאות עקביות):**

1. **דרך מהירה ליציבות** - השתמש ב-ScraperAPI או Bright Data כפרוקסי. עלות: $30-50/חודש. בקוד צריך לשנות רק את `requests.get()` ב-`scrapers/yad2.py` ו-`scrapers/madlan.py` להשתמש בפרוקסי.

2. **דרך חינמית** - הוסף Playwright headless browser. יותר מסובך אבל עובד.

3. **דרך פשוטה ביותר** - השתמש בRSS פיד של יד2 (הם מציעים פיד RSS לכל חיפוש שמור) - פחות נתונים אבל אמין לגמרי.

## מבנה הפרויקט

```
apartment-agent/
├── main.py                    # entry point
├── config.py                  # all settings
├── storage.py                 # dedup + JSON storage
├── emailer.py                 # SMTP + HTML email
├── scrapers/
│   ├── yad2.py                # Yad2 scraper
│   └── madlan.py              # Madlan scraper
├── requirements.txt
├── seen_listings.json         # auto-generated, committed back
└── .github/workflows/
    └── search.yml             # cron schedule
```

## מגבלות ידועות

- **Facebook Marketplace + קבוצות פייסבוק לא נתמכות** - דורש Login של משתמש, מאוד שביר. אפשר להוסיף ידנית עם cookies, אבל זה מסובך.
- **לוחות מקומיים (לוח החזות, וכו')** - אפשר להוסיף בקלות לפי בקשה.
- **דדופליקציה לא מושלמת** - אם מודעה משנה כתובת או מחיר, היא תופיע שוב כ"חדשה".
