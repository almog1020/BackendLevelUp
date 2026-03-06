# PR follow-up replies – paste in response to almog1020’s latest comments

Use these in the **same threads** where almog1020 replied. Code changes are already done.

---

## 1. auth.py – "אבל יש כבר התחברות עם גוגל"

**Reply (עברית):**
```
נכון, יש התחברות עם גוגל – אבל אחרי ההתחברות הפרונט מקבל רק את ה-token של גוגל. ה-API שלנו (PUT /users/preferences, GET /users/me) מצפה ל-JWT שאנחנו מנפיקים עם ה-SECRET_KEY שלנו. אז שלב ההתחברות קיים, אבל כדי שהפרונט יוכל לקרוא ל-endpoints שלנו אחרי הלוגין צריך שלב ביניים: החלפת הטוקן של גוגל ב-JWT שלנו. בלי זה משתמשי גוגל מקבלים 401 בדף הפרופיל.
```

**Reply (English):**
```
Right, Google login exists – but after login the frontend only has the Google token. Our API (PUT /users/preferences, GET /users/me) expects a JWT we issue with our SECRET_KEY. So login is there, but for the frontend to call our endpoints after login we need an extra step: exchange the Google token for our JWT. Without this, Google users get 401 on the profile page.
```

---

## 2. users.py – "return to this" (PUT `/{email}`)

**Reply (עברית):**
```
החזרתי ל-PUT /{email} כמו שביקשת. השארתי את PUT /preferences מוגדר קודם בקובץ כדי ש-FastAPI יתאים אותו לפני /{email} ושני הרוטים ימשיכו לעבוד.
```

**Reply (English):**
```
Reverted to PUT /{email} as requested. Kept PUT /preferences defined first in the file so FastAPI matches it before /{email} and both routes still work.
```

---

## 3. users.py – "זה קיים ברגע שאתה מוסיף משתמש, אין צורך בזה"

**Reply (עברית):**
```
הסרתי את השורה כמו שביקשת.
```

**Reply (English):**
```
Removed that line as requested.
```

---

## 4. db.py – default URL snippet

**Reply (עברית):**
```
עדכנתי עם ה-default שהצעת.
```

**Reply (English):**
```
Updated with the default you suggested.
```
