# WhatsApp Guest Post Agent (Make.com + Claude)

Ye agent aapke WhatsApp Business number par aane wale client messages khud handle karta hai:

- Price batata hai: general 500, CBD 800 (advance 400), casino 2000 (advance 1000).
- Article (text, .docx, PDF ya Google Docs link) ke links check karta hai aur spelling/grammar ki galtiyan theek karta hai.
- General links wale article seedha aapki 180+ WordPress sites mein se client ki batayi site par publish karke link bhejta hai, aur Orders sheet (monthly payment) mein entry karta hai.
- CBD/casino wale article par pehle advance maangta hai. Client ka payment screenshot aapko forward karta hai, aap 👍 karein to publish karta hai.
- Adult, Thai massage aur spa massage content mana kar deta hai.
- Published post mein galti ya change ho to WordPress par update kar deta hai.

## Files

| Path | Kya hai |
|---|---|
| `docs/SETUP-GUIDE.md` | **Yahan se shuru karein.** Step-by-step setup (Roman Urdu) |
| `make/blueprints/1-inbox.blueprint.json` | Make scenario: WhatsApp inbox + AI decision |
| `make/blueprints/2-publisher.blueprint.json` | Make scenario: WordPress publish/update + Orders sheet |
| `make/blueprints/3-doc-reader.blueprint.json` | Make scenario: .docx/PDF/Google Doc se article nikalna |
| `docs/MODULES.md` | Har module ki settings (import mein kuch khali rahe to yahan dekhein) |
| `prompts/` | AI ke rules aur instructions |
| `sheets/` | Google Sheet templates (Websites, Orders, public sites list) |
| `make/build_blueprints.py` | Prompts badalne ke baad blueprints dobara banane ki script |

Prompt ya logic badalne ke baad:

```
python3 make/build_blueprints.py
```
