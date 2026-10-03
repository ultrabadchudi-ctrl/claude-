# Jaldi test karne ka tareeka

Make mein ye cheezein pehle se ban chuki hain (team "My Team"):

| Kya | Naam | ID |
|---|---|---|
| Scenario | WA Agent 1 - Inbox | 6495370 |
| Scenario | WA Agent 2 - Publisher | 6495360 |
| Scenario | WA Agent 3 - Doc Reader | 6495357 |
| Data store | WA Clients | 163597 |
| Webhook (Meta isme lagega) | WA Agent - Inbox | https://hook.us2.make.com/7cs6e5qiusl6vo64y4iebw4luob5crzk |

## 1. Claude API key
platform.claude.com par jayein > Billing mein $5 credit daalein > API Keys > Create Key, aur key copy kar lein.

## 2. Meta ka free test number (SIM ki zaroorat nahi)
1. developers.facebook.com > My Apps > Create App > "Connect with customers through WhatsApp".
2. WhatsApp > **API Setup** kholein. Wahan Meta ka free **test number** pehle se hota hai.
   - **Temporary access token** copy karein (24 ghante chalta hai) → `WA_TOKEN`
   - **Phone number ID** copy karein → `WA_PHONE_ID`
3. **To** box mein apna WhatsApp number add karke OTP se verify karein. Isi tarah ek doosra number bhi add karein, maximum 5 tak.
4. WhatsApp > **Configuration > Webhook > Edit**:
   - Callback URL: `https://hook.us2.make.com/7cs6e5qiusl6vo64y4iebw4luob5crzk`
   - Verify token: wahi jo Inbox CONFIG mein `VERIFY_TOKEN` hai
   - Verify and save dabayein, phir **messages** ke saamne **Subscribe**.
   - Inbox scenario pehle ON hona chahiye.

## 3. Make mein values bharein
Teeno scenarios ka **CONFIG** module kholein aur `WA_TOKEN`, `WA_PHONE_ID`, `ANTHROPIC_API_KEY` bharein. Inbox mein ye bhi bharein:
- `OWNER_NUMBER`: wo number jis par screenshot approve karne hain (923xxxxxxxxx)
- `VERIFY_TOKEN`
- `PAYMENT_DETAILS`
- `SITES_LIST`: test ke liye khali chhod sakte hain

## 4. Google Sheet
1. Make ki bheji request se Google account connect karein.
2. `sheets/` folder ki CSV files se sheet banayein: tabs **Websites** aur **Orders**.
3. Websites tab mein kam se kam 1 test WordPress site ki line bharein.
4. Publisher ke modules 3, 6, 15 aur Inbox ke module 17 mein connection aur spreadsheet chunein.

## 5. Chalayein
Teeno scenarios ON karein. Phir **client wale number** (owner wale nahi) se test number par message bhejein: "price kya hai?"
