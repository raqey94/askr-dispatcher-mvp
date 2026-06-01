# نظام توزيع مناديب عسكر الجنوب - النسخة الأولى MVP

هذه نسخة أولى لتوزيع طلبات سلة على المناديب:

- خميس مشيط → شرف
- أبها → هشام
- أي منطقة خارجية أو غير معروفة → أبو ريان

## أين أحط البرنامج؟

الأفضل تحطه على سيرفر سحابي بسيط، مثل:

1. Render.com
2. Railway.app
3. VPS من DigitalOcean / Hetzner / AWS Lightsail

للبداية السريعة أنصح بـ Render أو Railway، لأنك ترفع الكود وتضيف متغيرات البيئة فقط.

## الربط مع سلة

البرنامج يعتمد على طريقتين:

### 1. Webhook
سلة ترسل للبرنامج إشعار عند إنشاء طلب جديد.
رابط Webhook يكون تقريبًا:

https://your-domain.com/webhooks/salla/order

في إعداد Webhook أضف Header:

key: x-askr-secret
value: نفس قيمة WEBHOOK_SECRET في ملف .env

### 2. API قراءة الطلبات
البرنامج يقدر يعرض آخر الطلبات من:

/preview/latest

ولوحة بسيطة من:

/dashboard

## إعداد ملف .env

انسخ الملف:

.env.example

إلى:

.env

ثم عدل القيم:

SALLA_ACCESS_TOKEN=توكن سلة
WEBHOOK_SECRET=كلمة سر خاصة بك
DRY_RUN=true
AUTO_ADD_ORDER_NOTE=false

## وضع الأمان

البداية تكون:

DRY_RUN=true
AUTO_ADD_ORDER_NOTE=false

يعني البرنامج يحدد المندوب ويعرض الملاحظة، لكنه لا يكتب داخل سلة.

بعد الاختبار:

DRY_RUN=false
AUTO_ADD_ORDER_NOTE=true

وقتها يبدأ يضيف ملاحظة داخل الطلب في سلة.

## التشغيل محليًا

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

افتح:

http://localhost:8000/dashboard

## ملاحظات مهمة

- لا تحفظ توكن سلة داخل الكود.
- لا تشارك ملف .env مع أي أحد.
- لا تفعل AUTO_ADD_ORDER_NOTE إلا بعد اختبار التوزيع.
- النسخة الأولى لا تغيّر حالة الطلب، فقط تضيف ملاحظة داخلية.
