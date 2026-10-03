# Setup Guide: WhatsApp Guest Post Agent (Make.com)

Is guide ko upar se neeche, step by step follow karein. Pehli baar mein lagbhag 1-2 ghante lagenge. Sabse zyada time 180 websites ke WordPress passwords nikalne mein lagega.

---

## Agent kya karta hai

| Client ne kya bheja | Agent kya karega |
|---|---|
| "Price kya hai?" | Price list batata hai: general 500, CBD 800, casino 2000 |
| Article (text, .docx, PDF ya Google Docs link) + site ka naam | Links check karta hai, spelling aur grammar ki galtiyan theek karta hai, phir category ke hisaab se aage badhta hai (neeche dekhein) |
| Article mein **general** links | Turant WordPress par publish karta hai, client ko link bhejta hai, aur Orders sheet mein "Unpaid - monthly sheet" likhta hai |
| Article mein **CBD / casino** links | Client ko price aur advance batata hai (CBD 400, casino 1000) aur payment screenshot maangta hai |
| Payment screenshot (image) | Screenshot aapke number par forward karta hai. Aap 👍 react karein to article publish ho jata hai aur client ko link chala jata hai |
| Adult, Thai massage ya spa massage content | Politely mana kar deta hai |
| "Meri post mein ye galti theek kar do" + post ka link | WordPress post khol kar sirf wahi change karta hai aur update ka link bhejta hai |
| Discount, complaint, refund jaisi baat | Aapko WhatsApp par bata deta hai, aur client ko kehta hai ki team jaldi jawab degi |

## Teen scenarios

1. **WA Agent 1 - Inbox:** WhatsApp ke saare messages yahan aate hain. AI (Claude) yahin decide karta hai ki kya karna hai.
2. **WA Agent 2 - Publisher:** WordPress par post banata ya update karta hai, client ko link bhejta hai, aur Orders sheet mein entry karta hai.
3. **WA Agent 3 - Doc Reader:** .docx/PDF file ya Google Docs link se article nikalta hai.

---

## Step 1: Google Sheet banayein

1. Google Sheets mein nayi sheet banayein, naam rakhein **Guest Post Agent**.
2. Isme do tabs banayein. Naam bilkul yahi hone chahiye:
   - **Websites**: `sheets/Websites.csv` import karein (File > Import > Upload > "Replace current sheet").
   - **Orders**: `sheets/Orders.csv` import karein. Isme sirf headings hain; har order khud add hota jayega. Mahine ke end mein monthly payment ka hisaab yahin se lein.
3. **Websites** tab mein apni 180 sites bharein. Har site ki ek line:

| Column | Kya likhna hai | Example |
|---|---|---|
| A `domain` | Sirf domain: chhote letters, bina https/www | `techblog.com` |
| B `site_url` | Site ka poora address, jaisa browser mein khulta hai, aakhir mein `/` ke bina | `https://www.techblog.com` |
| C `wp_username` | WordPress admin ka username | `admin` |
| D `wp_app_password` | WordPress **Application Password** (normal password nahi) | `abcd efgh ijkl mnop qrst uvwx` |
| E `niche` | Site ki category | `Tech` |
| F `notes` | Koi bhi note | |

**Application Password kaise banayein (har site par ek baar):** WP Admin > Users > Profile > neeche "Application Passwords" > naam likhein `Make Agent` > **Add New** > jo password dikhe use column D mein copy karein.

> Agar "Application Passwords" ka option nahi dikh raha, to site par HTTPS on hona chahiye. Wordfence ya iThemes jaisa security plugin bhi isse band kar sakta hai, us plugin mein ise allow karein.

4. **Ye sheet kisi ke saath share na karein**, kyunki isme passwords hain. Clients ko sites ki list dikhani ho to `sheets/Sites-public.csv` se ek alag sheet banayein jisme sirf domain aur niche ho. Use "Anyone with the link: Viewer" karke share karein, aur uska link CONFIG ke `SITES_LIST_URL` mein daalein.

## Step 2: Claude API key

1. https://console.anthropic.com par account banayein.
2. **Billing** mein credit add karein. Shuruaat ke liye $20 kaafi hai.
3. **API Keys > Create Key** karein aur key copy karke kahin safe rakhein.

## Step 3: WhatsApp Business Cloud API (Meta)

Make sirf **WhatsApp Cloud API** se connect hota hai. Normal WhatsApp Business app seedha connect nahi hota.

1. https://business.facebook.com par Business Account banayein, agar pehle se nahi hai.
2. https://developers.facebook.com > **My Apps > Create App** > type "Business" > app mein **WhatsApp** product add karein.
3. **WhatsApp > API Setup** mein "Add phone number" karke apna business number add karein.
   - **Zaroori baat:** jo number abhi WhatsApp Business app par chal raha hai, use Cloud API par lane se aam taur par app us number par band ho jata hai. Agar Meta onboarding mein **"Coexistence" / "Use existing WhatsApp Business app"** ka option mile to wo chunein. Isse app bhi chalti rahegi aur agent bhi. Ye option na mile to agent ke liye naya number lena behtar hai.
4. **Phone number ID** copy karein. Ye CONFIG ke `WA_PHONE_ID` mein jayega.
5. **Permanent token:** Business Settings > Users > **System users** > Add (role: Admin) > **Assign assets** (apni WhatsApp app aur WhatsApp account, full control) > **Generate token**. Permissions mein `whatsapp_business_messaging` aur `whatsapp_business_management` select karein, aur expiry "Never" rakhein. Ye token `WA_TOKEN` mein jayega.
6. Webhook abhi set na karein. Wo Step 6 mein hoga.

> **24 ghante wala rule:** WhatsApp business number kisi ko tabhi free message bhej sakta hai jab us insaan ne pichhle 24 ghante mein business number par message kiya ho. Agent aapko (owner ko) bhi isi number se screenshot bhejta hai, isliye **roz subah apne personal number se business number par "hi" bhej dein.** Agent owner ke aise messages ko ignore karta hai.

## Step 4: Make mein 2 data stores banayein

Make mein **Data structures > Add** karke ye do structures banayein:

**Structure 1, naam `clients`:**

| Field | Type |
|---|---|
| name | Text |
| last_msg_id | Text |
| history | Text |
| pending_status | Text |
| pending_site | Text |
| pending_category | Text |
| pending_price | Number |
| pending_advance | Number |
| pending_title | Text |
| pending_html | Text |

**Structure 2, naam `approvals`:** sirf ek field `client` (Text).

Ab **Data stores > Add data store** karein:
- `WA Clients`: structure `clients`, size jitna plan de (kam se kam 5 MB)
- `WA Approvals`: structure `approvals`, size 1 MB

## Step 5: Blueprints import karein (isi order mein)

Har file ke liye: **Scenarios > Create a new scenario >** neeche **⋯ (three dots) > Import Blueprint >** file chunein **> Save**.

### 5a. `make/blueprints/3-doc-reader.blueprint.json`
1. Pehla module "Doc reader webhook" kholein > **Add** > naam `doc-reader` > **Save** > jo **URL** dikhe use copy karke rakh lein (ye `DOCREADER_URL` hai).
2. "CONFIG" module mein `WA_TOKEN`, `ANTHROPIC_API_KEY` bharein.
3. Save karein aur scenario ko **ON** karein (Scheduling: Immediately).

### 5b. `make/blueprints/2-publisher.blueprint.json`
1. Webhook module > Add > naam `publisher` > URL copy karein (ye `PUBLISHER_URL` hai).
2. CONFIG mein `WA_TOKEN`, `WA_PHONE_ID`, `ANTHROPIC_API_KEY`, `CURRENCY` bharein.
3. Google Sheets wale modules ("Find site in Websites sheet", "Log order", "Log update") mein apna Google account connect karein. Spreadsheet `Guest Post Agent` chunein, aur sheet `Websites` ya `Orders` chunein.
   - "Find site" mein filter: Column **A (domain)** Equal to (case insensitive) `1.site` hona chahiye.
   - "Log order"/"Log update" mein columns A se J tak value pehle se bhari hongi. Kuch khali ho to `docs/MODULES.md` dekhein.
4. Save karke **ON** karein.

### 5c. `make/blueprints/1-inbox.blueprint.json`
1. Webhook module > Add > naam `whatsapp-inbox` > URL copy karein. Ye Meta mein lagega.
2. **CONFIG** module mein saari values bharein:

| Variable | Kya daalna hai |
|---|---|
| VERIFY_TOKEN | Koi bhi secret word, jaise `guestpost2026xyz`. Yahi Meta mein bhi likhna hai |
| WA_TOKEN / WA_PHONE_ID | Step 3 se |
| OWNER_NUMBER | Aapka personal WhatsApp number, country code ke saath, bina + aur space ke: `923001234567` |
| ANTHROPIC_API_KEY | Step 2 se |
| MODEL | `claude-opus-5-5` (behtar quality). Aadhi cost chahiye to `claude-sonnet-5-5` |
| PUBLISHER_URL / DOCREADER_URL | 5a aur 5b mein copy kiye URLs |
| BUSINESS_NAME | Aapke business ka naam |
| CURRENCY | `PKR`, `Rs`, `$`, jo aap clients ko batate hain |
| PRICE_GENERAL / PRICE_CBD / PRICE_CASINO | 500 / 800 / 2000 |
| ADVANCE_CBD / ADVANCE_CASINO | 400 / 1000 (CBD ka advance badalna ho to yahan badlein) |
| PAYMENT_DETAILS | Account details jo client ko bhejni hain, jaise `Easypaisa 0300-1234567 (Ali Khan)` |
| SITES_LIST | Saari 180 domains comma se alag: `site1.com, site2.com, ...`. Agent isse check karta hai ki site hamari hai ya nahi. Khali chhodenge to agent har domain accept karega, aur galat site par publish fail hone par aapko alert aayega |
| SITES_LIST_URL | Public sites list ka link (Step 1.4) |

3. **Data store** wale modules mein store chunein:
   - **WA Approvals:** "Find screenshot owner" (8), "Use approval once" (9), "Remember screenshot" (26)
   - **WA Clients:** "Load client" (10, 20, 30), "Clear pending order" (13), "Save client" (37)
4. "Log payment" (17) Google Sheets module mein connection, spreadsheet aur `Orders` sheet chunein.
5. Ye teen HTTP modules kholein: **"Publish paid article" (12), "Publish now" (41), "Update post" (44)**. Inme **"Evaluate all states as errors" = No** karein, taaki publish fail ho to aapko alert mile aur scenario na ruke.
6. Scenario **settings** (neeche ⚙️) mein:
   - **Sequential processing: ON.** Ek client ke messages order se process honge.
   - **Allow storing of incomplete executions: ON.** Error aane par scenario band nahi hoga.
7. Save karke **ON** karein.

## Step 6: Meta webhook ko Make se jodein

1. developers.facebook.com > aapki app > **WhatsApp > Configuration > Webhook > Edit**.
2. **Callback URL:** Inbox webhook ka URL (`https://hook.us2.make.com/...`).
3. **Verify token:** wahi jo CONFIG mein `VERIFY_TOKEN` likha.
4. **Verify and save** dabayein. Inbox scenario ON hona chahiye.
5. Webhook fields mein **messages** ke saamne **Subscribe** dabayein.

## Step 7: Test karein (apne number se nahi, kisi doosre number se)

Owner number ke messages agent ignore karta hai, isliye test kisi doosre phone se karein.

1. "Assalam o alaikum, guest post ka price kya hai?" → price list aani chahiye.
2. Ek general article ki .docx file bhejein, caption mein `techblog.com par lagana hai` → kuch der mein "publish ho raha hai", phir live link aana chahiye. Orders sheet mein entry check karein.
3. Ek casino link wala article + site → price aur 1000 advance ka message aana chahiye.
4. Usi number se koi bhi image bhejein → aapke number par screenshot aana chahiye → us par 👍 react karein → test number par link aana chahiye.
5. "https://techblog.com/post-slug/ is post mein 'teh' ko 'the' kar do" → update ka link aana chahiye.
6. "Thai massage ka article lagana hai" → mana karna chahiye.

Har test ke baad Make mein scenario ki **History** dekhein. Har module par bubble mein uska input aur output dikhta hai.

---

## Problem aaye to

| Problem | Hal |
|---|---|
| Meta "Verify" fail | Inbox scenario ON hai? Verify token dono jagah bilkul same hai? Module 4 ka body `1.hub.challenge` hai? |
| Client ko koi reply nahi | Inbox History dekhein. Module 34 (Claude) mein 401 aaye to API key galat hai, 400 aaye to MODEL ka naam check karein. Module 40 mein error ho to WA_TOKEN ya 24 ghante wala rule |
| Naye client par kuch nahi hota | Module 30 "Load client" ne output nahi diya. Data store module ki setting mein "Return wrapped output" No rakhein, ya us module par right-click > **Add error handler > Resume** lagayein |
| "Publish FAIL" alert, Result: `Accepted` | Site Websites sheet ke column A mein nahi mili (spelling, www ya https check karein), ya WordPress ne mana kiya. Publisher History dekhein: 401 ka matlab app password galat, 403 ka matlab security plugin ya Cloudflare REST API block kar raha hai |
| Owner ne 👍 kiya par kuch nahi hua | 👍 bilkul usi forward kiye screenshot par hona chahiye. Ek screenshot sirf ek baar approve hota hai |
| Owner ko screenshot nahi aaya | Aapne pichhle 24 ghante mein business number par message nahi kiya. "hi" bhej kar client se dobara screenshot mangwayein |
| Google Doc nahi padha gaya | Client se kahein ki doc ko "Anyone with the link: Viewer" karke share kare |
| Data store full | WA Clients ka size badhayein. Agent har client ki sirf aakhri ~3000 characters ki history rakhta hai |

## Kharcha (andaza)

- **Make:** ek normal message par lagbhag 15 operations, publish hone wale article par 25-35. Core plan (10,000 ops) mein lagbhag 300-400 articles mahine ke ho jate hain.
- **Claude (Opus 5.5):** ek article ki checking aur publish par lagbhag $0.10-0.20 (file padhne samet), aur ek chhote reply par $0.01-0.03. `MODEL` ko `claude-sonnet-5-5` karne se ye lagbhag aadha ho jata hai.
- Agar Claude kisi request ko safety reason se mana kare to wo khud doosre Claude model par dobara try karta hai. Ye "fallbacks: default" setting se hota hai, aapko kuch nahi karna.
- **WhatsApp:** client ke message ka jawab (24 ghante ke andar) free hai.

## Abhi ki limits

- Ek client ka ek waqt mein ek hi **pending** (payment ke intezaar wala) order rehta hai. General articles par ye limit nahi hai, kyunki wo turant publish ho jate hain.
- Article ki images aur featured image upload nahi hoti, aur WordPress category set nahi hoti. Sirf text aur links publish hote hain.
- Client ki bheji har image ko payment screenshot samjha jata hai, aur faisla aap 👍 se karte hain.
- Prices, advance ya rules badalne hon to Inbox ke CONFIG mein badlein. AI ke rules `prompts/agent-system-prompt.md` mein hain. Unhe badal kar `python3 make/build_blueprints.py` chalayein aur Inbox dobara import karein. Ya seedha Inbox ke module 32 "System prompt" ka text edit kar dein.
