#!/usr/bin/env python3
"""Builds the three Make.com scenario blueprints for the WhatsApp guest-post agent.

Run:  python3 make/build_blueprints.py
Output: make/blueprints/*.json (import these in Make) and docs/MODULES.md (module-by-module reference).

The prompts live in prompts/*.md so they can be edited without touching this file.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "make", "blueprints")

ANTHROPIC_VERSION = "2023-06-01"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
CODE_EXECUTION_TOOL = "code_execution_20260521"

# WhatsApp webhook message (first message of the first change)
V = "1.entry[1].changes[1].value"
MSG = V + ".messages[1]"


def read_prompt(name):
    with open(os.path.join(ROOT, "prompts", name), encoding="utf-8") as f:
        return f.read().strip()


# ---------------------------------------------------------------- module helpers

def C(a, o, b=None):
    cond = {"a": a, "o": o}
    if b is not None:
        cond["b"] = b
    return cond


def not_empty(expr):
    """Robust 'has a value' check (empty strings count as empty)."""
    return C("{{length(%s)}}" % expr, "number:greater", "0")


def module(mid, kind, version, mapper, name, xy, parameters=None, filt=None):
    m = {
        "id": mid,
        "module": kind,
        "version": version,
        "parameters": parameters if parameters is not None else {},
        "mapper": mapper,
        "metadata": {"designer": {"x": xy[0], "y": xy[1], "name": name}},
    }
    if filt:
        m["filter"] = {"name": filt[0], "conditions": filt[1]}
    return m


def router(mid, name, xy, routes):
    return {
        "id": mid,
        "module": "builtin:BasicRouter",
        "version": 1,
        "mapper": None,
        "metadata": {"designer": {"x": xy[0], "y": xy[1], "name": name}},
        "routes": [{"flow": r} for r in routes],
    }


def webhook(name):
    return module(1, "gateway:CustomWebHook", 1, {}, name, (0, 0),
                  parameters={"hook": None, "maxResults": 1})


def respond(mid, name, xy, body, filt=None, content_type="text/plain; charset=utf-8"):
    return module(mid, "gateway:WebhookRespond", 1,
                  {"status": "200", "body": body,
                   "headers": [{"key": "Content-Type", "value": content_type}]},
                  name, xy, filt=filt)


def set_vars(mid, name, xy, variables, filt=None):
    return module(mid, "util:SetVariables", 1,
                  {"variables": [{"name": k, "value": v} for k, v in variables],
                   "scope": "roundtrip"},
                  name, xy, filt=filt)


def to_json(mid, name, xy, text, filt=None):
    """json:TransformToJSON turns any text into a safely escaped JSON string -> {{mid.json}}."""
    return module(mid, "json:TransformToJSON", 1, {"object": text}, name, xy,
                  parameters={"space": ""}, filt=filt)


def parse_json(mid, name, xy, expr, filt=None):
    return module(mid, "json:ParseJSON", 1, {"json": expr}, name, xy,
                  parameters={"type": ""}, filt=filt)


def http(mid, name, xy, url, method="get", headers=(), qs=(), raw=None, form=None,
         multipart=None, parse=True, auth=None, filt=None):
    mapper = {
        "url": url,
        "method": method,
        "headers": [{"name": k, "value": v} for k, v in headers],
        "qs": [{"name": k, "value": v} for k, v in qs],
        "parseResponse": parse,
        "authUser": auth[0] if auth else "",
        "authPass": auth[1] if auth else "",
        "timeout": "300",
        "shareCookies": False,
        "ca": "",
        "rejectUnauthorized": True,
        "followRedirect": True,
        "useQuerystring": False,
        "gzip": True,
        "useMtls": False,
        "serializeUrl": False,
        "followAllRedirects": False,
    }
    if raw is not None:
        mapper.update({"bodyType": "raw", "contentType": "application/json", "data": raw})
    elif form is not None:
        mapper.update({"bodyType": "x_www_form_urlencoded",
                       "formFields": [{"key": k, "value": v} for k, v in form]})
    elif multipart is not None:
        fields = []
        for f in multipart:
            if f[0] == "file":
                fields.append({"key": f[1], "fieldType": "file", "data": f[2], "fileName": f[3]})
            else:
                fields.append({"key": f[1], "fieldType": "text", "value": f[2]})
        mapper.update({"bodyType": "multipart_form_data", "formDataFields": fields})
    return module(mid, "http:ActionSendData", 3, mapper, name, xy,
                  parameters={"handleErrors": False, "useNewZLibDeCompress": True}, filt=filt)


def get_file(mid, name, xy, url, headers=()):
    return module(mid, "http:ActionGetFile", 3, {
        "url": url,
        "method": "get",
        "headers": [{"name": k, "value": v} for k, v in headers],
        "qs": [],
        "shareCookies": False,
        "ca": "",
        "rejectUnauthorized": True,
        "followRedirect": True,
        "useQuerystring": False,
        "gzip": True,
        "useMtls": False,
        "serializeUrl": False,
        "timeout": "300",
        "followAllRedirects": False,
    }, name, xy, parameters={"handleErrors": False, "useNewZLibDeCompress": True})


def ds_get(mid, name, xy, key, filt=None):
    return module(mid, "datastore:GetRecord", 1, {"key": key, "returnWrapped": False}, name, xy,
                  parameters={"datastore": None}, filt=filt)


def ds_add(mid, name, xy, key, data, filt=None):
    return module(mid, "datastore:AddRecord", 1, {"key": key, "overwrite": True, "data": data},
                  name, xy, parameters={"datastore": None}, filt=filt)


def ds_delete(mid, name, xy, key, filt=None):
    return module(mid, "datastore:DeleteRecord", 1, {"key": key}, name, xy,
                  parameters={"datastore": None}, filt=filt)


def sheets_add_row(mid, name, xy, sheet, values, filt=None):
    return module(mid, "google-sheets:addRow", 2, {
        "mode": "select",
        "from": "drive",
        "spreadsheetId": "",
        "sheetId": sheet,
        "includesHeaders": True,
        "insertUnformatted": False,
        "valueInputOption": "USER_ENTERED",
        "insertDataOption": "INSERT_ROWS",
        "values": {str(i): v for i, v in enumerate(values)},
    }, name, xy, parameters={"__IMTCONN__": None}, filt=filt)


def sheets_find_site(mid, name, xy, domain):
    return module(mid, "google-sheets:filterRows", 2, {
        "from": "drive",
        "spreadsheetId": "",
        "sheetId": "Websites",
        "includesHeaders": True,
        "tableFirstRow": "A1:Z1",
        "filter": [[{"a": "A", "b": domain, "o": "text:equal:ci"}]],
        "sortOrder": "asc",
        "limit": "1",
        "valueRenderOption": "FORMATTED_VALUE",
        "dateTimeRenderOption": "FORMATTED_STRING",
    }, name, xy, parameters={"__IMTCONN__": None})


def json_body(obj, inserts):
    """Serialises a request body and then drops raw Make expressions into placeholders.

    '}}' never appears in the static JSON so Make cannot mistake it for the end of a mapping.
    """
    body = json.dumps(obj, ensure_ascii=False)
    while "}}" in body:
        body = body.replace("}}", "} }")
    assert "{{" not in body
    for placeholder, expr in inserts.items():
        quoted = json.dumps(placeholder)
        assert quoted in body, placeholder
        body = body.replace(quoted, expr)
    return body


WA_MESSAGES_URL = "https://graph.facebook.com/{{2.GRAPH_VERSION}}/{{2.WA_PHONE_ID}}/messages"
WA_AUTH = ("Authorization", "Bearer {{2.WA_TOKEN}}")
CLAUDE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_HEADERS = [
    ("x-api-key", "{{2.ANTHROPIC_API_KEY}}"),
    ("anthropic-version", ANTHROPIC_VERSION),
    ("anthropic-beta", FALLBACK_BETA),
]


def wa_text(mid, name, xy, to, body_expr, filt=None):
    """Sends a WhatsApp text. body_expr must already be a JSON string ({{N.json}} or a literal)."""
    raw = json_body({"messaging_product": "whatsapp", "recipient_type": "individual",
                     "to": "__TO__", "type": "text",
                     "text": {"preview_url": True, "body": "__BODY__"}},
                    {"__TO__": json.dumps(to), "__BODY__": body_expr})
    return http(mid, name, xy, WA_MESSAGES_URL, "post", [WA_AUTH], raw=raw, filt=filt)


def wa_static(mid, name, xy, to, text, filt=None):
    return wa_text(mid, name, xy, to, json.dumps(text, ensure_ascii=False), filt=filt)


def claude_text(mid):
    """All text blocks of a Messages API response, last one = final answer."""
    return "{{last(map(%d.data.content; text; type; text))}}" % mid


def scenario(name, flow, sequential):
    return {
        "name": name,
        "flow": flow,
        "metadata": {
            "instant": True,
            "version": 1,
            "scenario": {
                "roundtrips": 1,
                "maxErrors": 3,
                "autoCommit": True,
                "autoCommitTriggerLast": True,
                "sequential": sequential,
                "confidential": False,
                "dataloss": False,
                "dlq": True,
                "freshVariables": False,
            },
            "designer": {"orphans": []},
            "zone": "us2.make.com",
        },
    }


# ---------------------------------------------------------------- config modules

INBOX_CONFIG = [
    ("VERIFY_TOKEN", "apna-koi-secret-likhein-123"),
    ("WA_TOKEN", "PASTE_WHATSAPP_PERMANENT_ACCESS_TOKEN"),
    ("WA_PHONE_ID", "PASTE_PHONE_NUMBER_ID"),
    ("GRAPH_VERSION", "v23.0"),
    ("OWNER_NUMBER", "923001234567"),
    ("ANTHROPIC_API_KEY", "PASTE_ANTHROPIC_API_KEY"),
    ("MODEL", "claude-opus-5-5"),
    ("PUBLISHER_URL", "PASTE_PUBLISHER_WEBHOOK_URL"),
    ("DOCREADER_URL", "PASTE_DOCREADER_WEBHOOK_URL"),
    ("BUSINESS_NAME", "Apne business ka naam"),
    ("CURRENCY", "PKR"),
    ("PRICE_GENERAL", "500"),
    ("PRICE_CBD", "800"),
    ("PRICE_CASINO", "2000"),
    ("ADVANCE_CBD", "400"),
    ("ADVANCE_CASINO", "1000"),
    ("PAYMENT_DETAILS", "Easypaisa/JazzCash/Bank: account number aur naam yahan likhein"),
    ("SITES_LIST", "site1.com, site2.com, site3.com"),
    ("SITES_LIST_URL", "Sites list ka public link (bina passwords wali sheet)"),
]

PUBLISHER_CONFIG = [
    ("WA_TOKEN", "PASTE_WHATSAPP_PERMANENT_ACCESS_TOKEN"),
    ("WA_PHONE_ID", "PASTE_PHONE_NUMBER_ID"),
    ("GRAPH_VERSION", "v23.0"),
    ("ANTHROPIC_API_KEY", "PASTE_ANTHROPIC_API_KEY"),
    ("MODEL", "claude-opus-5-5"),
    ("CURRENCY", "PKR"),
]

DOCREADER_CONFIG = [
    ("WA_TOKEN", "PASTE_WHATSAPP_PERMANENT_ACCESS_TOKEN"),
    ("GRAPH_VERSION", "v23.0"),
    ("ANTHROPIC_API_KEY", "PASTE_ANTHROPIC_API_KEY"),
    ("MODEL", "claude-opus-5-5"),
]


# ---------------------------------------------------------------- 1) INBOX

AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["reply", "save_draft", "publish", "request_payment",
                                               "update_post", "notify_owner", "reject"]},
        "reply": {"type": "string"},
        "site": {"type": "string"},
        "category": {"type": "string", "enum": ["none", "general", "cbd", "casino", "forbidden"]},
        "price": {"type": "integer"},
        "advance": {"type": "integer"},
        "article_title": {"type": "string"},
        "article_html": {"type": "string"},
        "fixes": {"type": "string"},
        "pending_status": {"type": "string", "enum": ["", "need_site", "awaiting_payment"]},
        "clear_pending": {"type": "boolean"},
        "post_url": {"type": "string"},
        "update_instructions": {"type": "string"},
        "owner_note": {"type": "string"},
    },
    "required": ["action", "reply", "site", "category", "price", "advance", "article_title",
                 "article_html", "fixes", "pending_status", "clear_pending", "post_url",
                 "update_instructions", "owner_note"],
    "additionalProperties": False,
}

USER_TURN = (
    "CLIENT NAME: {{6.name}}\n"
    "CLIENT PHONE: {{6.from}}\n\n"
    "CONVERSATION HISTORY (oldest first, may be empty for a new client):\n{{30.history}}\n\n"
    "PENDING ORDER:\n"
    "status: {{30.pending_status}}\n"
    "site: {{30.pending_site}}\n"
    "category: {{30.pending_category}}\n"
    "price: {{30.pending_price}}\n"
    "advance: {{30.pending_advance}}\n"
    "title: {{30.pending_title}}\n"
    "saved article length (characters, 0 = no saved article): {{length(30.pending_html)}}\n\n"
    "NEW MESSAGE FROM CLIENT:\n{{6.text}}\n"
    "ATTACHED FILE NAME: {{6.filename}}\n\n"
    "ATTACHMENT_CONTENT (article read from the attached file or Google Docs link; empty if none):\n"
    "{{31.data}}"
)


def build_inbox():
    owner = C("{{6.from}}", "text:equal", "{{2.OWNER_NUMBER}}")
    not_owner = C("{{6.from}}", "text:notequal", "{{2.OWNER_NUMBER}}")
    has_context = not_empty("6.context_id")
    is_text = C("{{6.type}}", "text:equal", "text")

    verify_route = [
        respond(4, "Meta verification", (600, -300), "{{1.`hub.challenge`}}",
                filt=("Meta webhook verify", [[
                    C("{{1.`hub.mode`}}", "text:equal", "subscribe"),
                    C("{{1.`hub.verify_token`}}", "text:equal", "{{2.VERIFY_TOKEN}}"),
                ]])),
    ]

    # --- owner confirms a forwarded payment screenshot (👍 reaction or "ok" reply)
    approval_key = "{{ifempty(6.reacted_id; 6.context_id)}}"
    payment_with_order = [
        http(12, "Publish paid article", (2100, -600), "{{2.PUBLISHER_URL}}", "post", parse=False, form=[
            ("mode", "publish"),
            ("client", "{{8.client}}"),
            ("client_name", "{{10.name}}"),
            ("site", "{{10.pending_site}}"),
            ("title", "{{10.pending_title}}"),
            ("html", "{{10.pending_html}}"),
            ("category", "{{10.pending_category}}"),
            ("price", "{{10.pending_price}}"),
            ("payment_status", "Advance {{10.pending_advance}} received, balance {{10.pending_price - 10.pending_advance}}"),
        ], filt=("Order awaiting payment", [[C("{{10.pending_status}}", "text:equal", "awaiting_payment"),
                                             not_empty("10.pending_html")]])),
        ds_add(13, "Clear pending order", (2400, -600), "{{8.client}}", {
            "name": "{{10.name}}",
            "last_msg_id": "{{10.last_msg_id}}",
            "history": "{{10.history}}\n[System] Owner ne payment confirm ki, article publish kiya gaya.",
            "pending_status": "{{emptystring}}",
            "pending_site": "{{emptystring}}",
            "pending_category": "{{emptystring}}",
            "pending_price": "0",
            "pending_advance": "0",
            "pending_title": "{{emptystring}}",
            "pending_html": "{{emptystring}}",
        }),
        to_json(14, "Owner confirmation text", (2700, -600),
                "✅ Payment confirm ho gayi.\nClient: {{10.name}} (+{{8.client}})\nSite: {{10.pending_site}}\n"
                "Publish result: {{substring(12.data; 0; 300)}}\n\n"
                "(Agar upar link nahi hai to publish fail hua - Make me Publisher scenario ki History dekhein.)"),
        wa_text(15, "Tell owner", (3000, -600), "{{2.OWNER_NUMBER}}", "{{14.json}}"),
    ]
    payment_without_order = [
        wa_static(16, "Thank client for payment", (2100, -300), "{{8.client}}",
                  "✅ Aapki payment receive ho gayi hai. Shukriya! 🙏",
                  filt=("No order waiting", [[C("{{10.pending_status}}", "text:notequal", "awaiting_payment")]])),
        sheets_add_row(17, "Log payment", (2400, -300), "Orders", [
            "{{formatDate(now; YYYY-MM-DD HH:mm)}}", "{{8.client}}", "{{10.name}}", "", "",
            "payment", "", "", "Payment received (owner confirmed)", "",
        ]),
        wa_static(18, "Tell owner", (2700, -300), "{{2.OWNER_NUMBER}}",
                  "✅ Noted: payment Orders sheet me log kar di gayi."),
    ]
    approval_route = [
        ds_get(8, "Find screenshot owner", (900, -450), approval_key,
               filt=("Owner 👍 / ok", [
                   [owner, C("{{6.type}}", "text:equal", "reaction"), C("{{6.emoji}}", "text:contain", "👍")],
                   [owner, is_text, has_context, C("{{6.text}}", "text:contain", "👍")],
                   [owner, is_text, has_context, C("{{6.text}}", "text:equal:ci", "ok")],
                   [owner, is_text, has_context, C("{{6.text}}", "text:contain:ci", "confirm")],
               ])),
        ds_delete(9, "Use approval once", (1200, -450), approval_key,
                  filt=("Was a payment screenshot", [[not_empty("8.client")]])),
        ds_get(10, "Load client", (1500, -450), "{{8.client}}"),
        router(11, "Order waiting?", (1800, -450), [payment_with_order, payment_without_order]),
    ]

    # --- client sends an image (payment screenshot) -> forward to owner
    image_route = [
        ds_get(20, "Load client", (900, 0), "{{6.from}}",
               filt=("Client image", [[not_owner, C("{{6.type}}", "text:equal", "image")]])),
        http(21, "Media info", (1200, 0), "https://graph.facebook.com/{{2.GRAPH_VERSION}}/{{6.media_id}}",
             headers=[WA_AUTH]),
        get_file(22, "Download screenshot", (1500, 0), "{{21.data.url}}", headers=[WA_AUTH]),
        http(23, "Re-upload for owner", (1800, 0),
             "https://graph.facebook.com/{{2.GRAPH_VERSION}}/{{2.WA_PHONE_ID}}/media", "post",
             headers=[WA_AUTH], multipart=[
                 ("text", "messaging_product", "whatsapp"),
                 ("text", "type", "{{21.data.mime_type}}"),
                 ("file", "file", "{{22.data}}", "payment.jpg"),
             ]),
        to_json(24, "Caption for owner", (2100, 0),
                "💰 *Payment screenshot aaya hai*\nClient: {{6.name}} (+{{6.from}})\n"
                "Order status: {{20.pending_status}}\nSite: {{20.pending_site}}\nCategory: {{20.pending_category}}\n"
                "Total: {{20.pending_price}} {{2.CURRENCY}} | Advance: {{20.pending_advance}} {{2.CURRENCY}}\n"
                "Client note: {{6.text}}\n\n"
                "👉 Payment sahi hai to is message par 👍 react karein (ya reply me ok likhein).\n"
                "Order status khali ho to ye general/monthly payment hai."),
        http(25, "Send screenshot to owner", (2400, 0), WA_MESSAGES_URL, "post", headers=[WA_AUTH],
             raw=json_body({"messaging_product": "whatsapp", "recipient_type": "individual",
                            "to": "__TO__", "type": "image",
                            "image": {"id": "__ID__", "caption": "__CAPTION__"}},
                           {"__TO__": '"{{2.OWNER_NUMBER}}"', "__ID__": '"{{23.data.id}}"',
                            "__CAPTION__": "{{24.json}}"})),
        ds_add(26, "Remember screenshot", (2700, 0), "{{25.data.messages[1].id}}", {"client": "{{6.from}}"}),
        wa_static(27, "Thank client", (3000, 0), "{{6.from}}",
                  "Shukriya! 🙏 Payment screenshot mil gaya hai. Verify hote hi aapko update kar denge."),
    ]

    # --- client sends text or a document -> Claude decides
    claude_body = json_body({
        "model": "__MODEL__",
        "max_tokens": 16000,
        "fallbacks": "default",
        "output_config": {"effort": "medium",
                          "format": {"type": "json_schema", "schema": AGENT_SCHEMA}},
        "system": [{"type": "text", "text": "__SYSTEM__", "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": "__USER__"}],
    }, {"__MODEL__": '"{{2.MODEL}}"', "__SYSTEM__": "{{32.json}}", "__USER__": "{{33.json}}"})

    reply_route = [
        to_json(39, "Reply text", (3900, 300), "{{35.reply}}"),
        wa_text(40, "Reply to client", (4200, 300), "{{6.from}}", "{{39.json}}"),
    ]
    publish_route = [
        http(41, "Publish now", (3900, 600), "{{2.PUBLISHER_URL}}", "post", parse=False, form=[
            ("mode", "publish"),
            ("client", "{{6.from}}"),
            ("client_name", "{{6.name}}"),
            ("site", "{{35.site}}"),
            ("title", "{{36.pub_title}}"),
            ("html", "{{36.pub_html}}"),
            ("category", "{{35.category}}"),
            ("price", "{{35.price}}"),
            ("payment_status", "Unpaid - monthly sheet"),
        ], filt=("action = publish", [[C("{{35.action}}", "text:equal", "publish"),
                                       not_empty("36.pub_html"), not_empty("35.site")]])),
        to_json(42, "Failure text", (4200, 600),
                "⚠️ *Publish FAIL*\nClient: {{6.name}} (+{{6.from}})\nSite: {{35.site}}\n"
                "Result: {{substring(41.data; 0; 300)}}\n\n"
                "Check: site Websites sheet me hai? WordPress application password sahi hai? "
                "Make > Publisher scenario > History.",
                filt=("No link came back", [[C("{{41.data}}", "text:notcontain", "http")]])),
        wa_text(43, "Alert owner", (4500, 600), "{{2.OWNER_NUMBER}}", "{{42.json}}"),
    ]
    update_route = [
        http(44, "Update post", (3900, 900), "{{2.PUBLISHER_URL}}", "post", parse=False, form=[
            ("mode", "update"),
            ("client", "{{6.from}}"),
            ("client_name", "{{6.name}}"),
            ("site", "{{35.site}}"),
            ("post_url", "{{35.post_url}}"),
            ("instructions", "{{35.update_instructions}}"),
        ], filt=("action = update_post", [[C("{{35.action}}", "text:equal", "update_post")]])),
        to_json(45, "Failure text", (4200, 900),
                "⚠️ *Update FAIL*\nClient: {{6.name}} (+{{6.from}})\nPost: {{35.post_url}}\n"
                "Change: {{35.update_instructions}}\nResult: {{substring(44.data; 0; 300)}}",
                filt=("No link came back", [[C("{{44.data}}", "text:notcontain", "http")]])),
        wa_text(46, "Alert owner", (4500, 900), "{{2.OWNER_NUMBER}}", "{{45.json}}"),
    ]
    notify_route = [
        to_json(47, "Owner note", (3900, 1200),
                "📩 *Client ko aapki zaroorat hai*\n{{6.name}} (+{{6.from}})\n\n{{35.owner_note}}\n\n"
                "Client ka message:\n{{substring(6.text; 0; 600)}}",
                filt=("action = notify_owner", [[C("{{35.action}}", "text:equal", "notify_owner")]])),
        wa_text(48, "Message owner", (4200, 1200), "{{2.OWNER_NUMBER}}", "{{47.json}}"),
    ]

    text_route = [
        ds_get(30, "Load client", (900, 450), "{{6.from}}",
               filt=("Client text / file", [[not_owner, is_text],
                                            [not_owner, C("{{6.type}}", "text:equal", "document")]])),
        http(31, "Read file / Google Doc", (1200, 450), "{{2.DOCREADER_URL}}", "post", parse=False, form=[
            ("media_id", "{{6.media_id}}"),
            ("filename", "{{6.filename}}"),
            ("text", "{{6.text}}"),
        ], filt=("Not a duplicate", [[C("{{30.last_msg_id}}", "text:notequal", "{{6.msg_id}}")]])),
        to_json(32, "System prompt", (1500, 450), read_prompt("agent-system-prompt.md")),
        to_json(33, "Client turn", (1800, 450), USER_TURN),
        http(34, "Claude decides", (2100, 450), CLAUDE_URL, "post", headers=CLAUDE_HEADERS, raw=claude_body),
        parse_json(35, "Decision", (2400, 450), claude_text(34)),
        set_vars(36, "Order + history", (2700, 450), [
            ("pub_html", "{{ifempty(35.article_html; 30.pending_html)}}"),
            ("pub_title", "{{ifempty(35.article_title; 30.pending_title)}}"),
            ("h_full", "{{30.history}}\nClient: {{substring(6.text; 0; 500)}} {{6.filename}}\nAgent: {{35.reply}}"),
        ]),
        ds_add(37, "Save client", (3000, 450), "{{6.from}}", {
            "name": "{{6.name}}",
            "last_msg_id": "{{6.msg_id}}",
            "history": "{{substring(36.h_full; max(0; length(36.h_full) - 3000); length(36.h_full))}}",
            "pending_status": "{{35.pending_status}}",
            "pending_site": "{{35.site}}",
            "pending_category": "{{35.category}}",
            "pending_price": "{{35.price}}",
            "pending_advance": "{{35.advance}}",
            "pending_title": "{{if(35.clear_pending; emptystring; 36.pub_title)}}",
            "pending_html": "{{if(35.clear_pending; emptystring; 36.pub_html)}}",
        }),
        router(38, "Do the action", (3300, 450), [reply_route, publish_route, update_route, notify_route]),
    ]

    messages_route = [
        respond(5, "Tell Meta OK", (600, 150), "EVENT_RECEIVED",
                filt=("Incoming message", [[not_empty(MSG + ".id")]])),
        set_vars(6, "Message fields", (900, 150), [
            ("from", "{{%s.from}}" % MSG),
            ("msg_id", "{{%s.id}}" % MSG),
            ("type", "{{%s.type}}" % MSG),
            ("name", "{{%s.contacts[1].profile.name}}" % V),
            ("text", "{{ifempty(%s.text.body; ifempty(%s.document.caption; %s.image.caption))}}" % (MSG, MSG, MSG)),
            ("media_id", "{{ifempty(%s.document.id; %s.image.id)}}" % (MSG, MSG)),
            ("filename", "{{%s.document.filename}}" % MSG),
            ("emoji", "{{%s.reaction.emoji}}" % MSG),
            ("reacted_id", "{{%s.reaction.message_id}}" % MSG),
            ("context_id", "{{%s.context.id}}" % MSG),
        ]),
        router(7, "Who sent what?", (1200, 150), [approval_route, image_route, text_route]),
    ]
    # Router positions inside the messages route are relative to the canvas; shift lanes for readability.
    for m in approval_route + image_route + text_route:
        m["metadata"]["designer"]["x"] += 600

    flow = [
        webhook("WhatsApp webhook"),
        set_vars(2, "CONFIG (yahan apni values bharein)", (300, 0), INBOX_CONFIG),
        router(3, "Verify or message", (450, 0), [verify_route, messages_route]),
    ]
    return scenario("WA Agent 1 - Inbox", flow, sequential=True)


# ---------------------------------------------------------------- 2) PUBLISHER

UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "title": {"type": "string"},
        "html": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["ok", "title", "html", "summary"],
    "additionalProperties": False,
}


def build_publisher():
    site_url = "{{3.`1`}}"
    wp_auth = ("{{3.`2`}}", "{{3.`3`}}")
    slug = r"{{replace(1.post_url; /^.*\/([^\/?#]+)\/?([?#].*)?$/; $1)}}"

    publish_route = [
        http(5, "Create WordPress post", (1200, -200), site_url + "/wp-json/wp/v2/posts", "post",
             auth=wp_auth, form=[("title", "{{1.title}}"), ("content", "{{1.html}}"), ("status", "publish")],
             filt=("mode = publish", [[C("{{1.mode}}", "text:equal", "publish")]])),
        sheets_add_row(6, "Log order", (1500, -200), "Orders", [
            "{{formatDate(now; YYYY-MM-DD HH:mm)}}", "{{1.client}}", "{{1.client_name}}", "{{1.site}}",
            "{{5.data.link}}", "publish", "{{1.category}}", "{{1.price}}", "{{1.payment_status}}", "",
        ]),
        to_json(7, "Link message", (1800, -200),
                "✅ *Aapka article publish ho gaya hai!*\n\n🔗 {{5.data.link}}\n\n"
                "💰 Charges: {{1.price}} {{2.CURRENCY}}\n📌 Payment: {{1.payment_status}}\n\nShukriya! 🙏"),
        wa_text(8, "Send link to client", (2100, -200), "{{1.client}}", "{{7.json}}"),
        respond(9, "Return link", (2400, -200), "{{5.data.link}}"),
    ]

    update_body = json_body({
        "model": "__MODEL__",
        "max_tokens": 16000,
        "fallbacks": "default",
        "output_config": {"effort": "medium",
                          "format": {"type": "json_schema", "schema": UPDATE_SCHEMA}},
        "system": read_prompt("update-prompt.md"),
        "messages": [{"role": "user", "content": "__USER__"}],
    }, {"__MODEL__": '"{{2.MODEL}}"', "__USER__": "{{11.json}}"})

    update_route = [
        http(10, "Find post by slug", (1200, 200), site_url + "/wp-json/wp/v2/posts", "get",
             auth=wp_auth, qs=[("slug", slug), ("context", "edit")],
             filt=("mode = update", [[C("{{1.mode}}", "text:equal", "update")]])),
        to_json(11, "Edit request", (1500, 200),
                "CHANGE REQUEST FROM CLIENT:\n{{1.instructions}}\n\n"
                "CURRENT TITLE:\n{{10.data[1].title.raw}}\n\nCURRENT ARTICLE HTML:\n{{10.data[1].content.raw}}",
                filt=("Post found", [[not_empty("10.data[1].id")]])),
        http(12, "Claude edits", (1800, 200), CLAUDE_URL, "post", headers=CLAUDE_HEADERS, raw=update_body),
        parse_json(13, "Edited article", (2100, 200), claude_text(12)),
        http(14, "Save on WordPress", (2400, 200), site_url + "/wp-json/wp/v2/posts/{{10.data[1].id}}", "post",
             auth=wp_auth, form=[("title", "{{13.title}}"), ("content", "{{13.html}}")],
             filt=("Edit possible", [[C("{{13.ok}}", "boolean:equal", "true")]])),
        sheets_add_row(15, "Log update", (2700, 200), "Orders", [
            "{{formatDate(now; YYYY-MM-DD HH:mm)}}", "{{1.client}}", "{{1.client_name}}", "{{1.site}}",
            "{{14.data.link}}", "update", "", "0", "", "{{13.summary}}",
        ]),
        to_json(16, "Update message", (3000, 200),
                "✅ *Article update ho gaya hai!*\n\n🔗 {{14.data.link}}\n\n✏️ {{13.summary}}"),
        wa_text(17, "Tell client", (3300, 200), "{{1.client}}", "{{16.json}}"),
        respond(18, "Return link", (3600, 200), "{{14.data.link}}"),
    ]

    flow = [
        webhook("Publisher webhook"),
        set_vars(2, "CONFIG (yahan apni values bharein)", (300, 0), PUBLISHER_CONFIG),
        sheets_find_site(3, "Find site in Websites sheet", (600, 0), "{{1.site}}"),
        router(4, "Publish or update", (900, 0), [publish_route, update_route]),
    ]
    return scenario("WA Agent 2 - Publisher", flow, sequential=False)


# ---------------------------------------------------------------- 3) DOC READER

def build_docreader():
    reader_body = json_body({
        "model": "__MODEL__",
        "max_tokens": 16000,
        "fallbacks": "default",
        "output_config": {"effort": "low"},
        "tools": [{"type": CODE_EXECUTION_TOOL, "name": "code_execution"}],
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": read_prompt("doc-reader-prompt.md")},
            {"type": "container_upload", "file_id": "__FILE_ID__"},
        ]}],
    }, {"__MODEL__": '"{{2.MODEL}}"', "__FILE_ID__": '"{{6.data.id}}"'})

    file_route = [
        http(4, "Media info", (900, -200), "https://graph.facebook.com/{{2.GRAPH_VERSION}}/{{1.media_id}}",
             headers=[WA_AUTH], filt=("Has file", [[not_empty("1.media_id")]])),
        get_file(5, "Download file", (1200, -200), "{{4.data.url}}", headers=[WA_AUTH]),
        http(6, "Upload to Claude Files", (1500, -200), "https://api.anthropic.com/v1/files", "post",
             headers=[h for h in CLAUDE_HEADERS if h[0] != "anthropic-beta"],
             multipart=[("file", "file", "{{5.data}}", "{{1.filename}}")]),
        http(7, "Claude reads file", (1800, -200), CLAUDE_URL, "post", headers=CLAUDE_HEADERS, raw=reader_body),
        http(8, "Delete uploaded file", (2100, -200), "https://api.anthropic.com/v1/files/{{6.data.id}}", "delete",
             headers=[h for h in CLAUDE_HEADERS if h[0] != "anthropic-beta"]),
        respond(9, "Return article", (2400, -200), claude_text(7)),
    ]
    gdoc_id = r"{{replace(1.text; /^[\s\S]*?docs\.google\.com\/document\/d\/([A-Za-z0-9_-]+)[\s\S]*$/; $1)}}"
    gdoc_route = [
        http(10, "Download Google Doc", (900, 100),
             "https://docs.google.com/document/d/" + gdoc_id + "/export?format=html", parse=False,
             filt=("Google Docs link", [[C("{{length(1.media_id)}}", "number:equal", "0"),
                                        C("{{1.text}}", "text:contain", "docs.google.com/document/d/")]])),
        respond(11, "Return article", (1200, 100), r"{{replace(10.data; /<style[^<]*<\/style>/g; emptystring)}}"),
    ]
    nothing_route = [
        respond(12, "Nothing to read", (900, 350), "",
                filt=("Plain message", [[C("{{length(1.media_id)}}", "number:equal", "0"),
                                         C("{{1.text}}", "text:notcontain", "docs.google.com/document/d/")]])),
    ]
    flow = [
        webhook("Doc reader webhook"),
        set_vars(2, "CONFIG (yahan apni values bharein)", (300, 0), DOCREADER_CONFIG),
        router(3, "File / Google Doc / nothing", (600, 0), [file_route, gdoc_route, nothing_route]),
    ]
    return scenario("WA Agent 3 - Doc Reader", flow, sequential=False)


# ---------------------------------------------------------------- docs

def walk(flow):
    for m in flow:
        yield m
        for r in m.get("routes", []):
            yield from walk(r["flow"])


def describe(bp):
    lines = ["## " + bp["name"], ""]
    for m in walk(bp["flow"]):
        d = m["metadata"]["designer"]
        lines.append("### %d. %s  (`%s`)" % (m["id"], d.get("name", ""), m["module"]))
        if "filter" in m:
            groups = [" AND ".join("`%s` %s `%s`" % (c["a"], c["o"], c.get("b", "")) for c in g)
                      for g in m["filter"]["conditions"]]
            lines.append("- **Filter (is module se pehle wali line par):** " + m["filter"]["name"])
            for g in groups:
                lines.append("  - " + ("YA " if g is not groups[0] else "") + g)
        mp = m.get("mapper") or {}
        if m["module"].startswith("http:"):
            lines.append("- Method/URL: `%s %s`" % (mp.get("method", "get").upper(), mp.get("url")))
            for h in mp.get("headers", []):
                val = h["value"]
                lines.append("- Header: `%s: %s`" % (h["name"], val))
            for q in mp.get("qs", []):
                lines.append("- Query: `%s = %s`" % (q["name"], q["value"]))
            if mp.get("authUser"):
                lines.append("- Basic auth: user `%s`, password `%s`" % (mp["authUser"], mp["authPass"]))
            if mp.get("bodyType") == "raw":
                lines.append("- Body type: Raw, JSON. Request content:")
                lines.append("")
                lines.append("```")
                body = mp["data"]
                lines.append(body if len(body) < 1500 else body[:1500] + " ... (poora blueprint JSON me)")
                lines.append("```")
            elif mp.get("bodyType") == "x_www_form_urlencoded":
                lines.append("- Body type: application/x-www-form-urlencoded, fields:")
                for f in mp["formFields"]:
                    lines.append("  - `%s` = `%s`" % (f["key"], f["value"]))
            elif mp.get("bodyType") == "multipart_form_data":
                lines.append("- Body type: multipart/form-data, fields:")
                for f in mp["formDataFields"]:
                    if f["fieldType"] == "file":
                        lines.append("  - `%s` (File) data `%s`, file name `%s`" % (f["key"], f["data"], f["fileName"]))
                    else:
                        lines.append("  - `%s` (Text) = `%s`" % (f["key"], f["value"]))
            lines.append("- Parse response: %s" % ("Yes" if mp.get("parseResponse", True) else "No"))
        elif m["module"] == "util:SetVariables":
            for v in mp["variables"]:
                lines.append("- `%s` = `%s`" % (v["name"], v["value"]))
        elif m["module"] == "json:TransformToJSON":
            obj = mp["object"]
            if len(obj) > 600:
                obj = obj[:600] + " ... (poora text prompts/ folder me)"
            lines.append("- Object: `%s`" % obj.replace("\n", "\\n"))
        elif m["module"] == "json:ParseJSON":
            lines.append("- JSON string: `%s`" % mp["json"])
        elif m["module"].startswith("datastore:"):
            lines.append("- Key: `%s`" % mp["key"])
            for k, v in (mp.get("data") or {}).items():
                lines.append("  - `%s` = `%s`" % (k, v.replace("\n", "\\n")))
        elif m["module"].startswith("google-sheets:"):
            lines.append("- Sheet: `%s`" % mp["sheetId"])
            if "values" in mp:
                for k, v in mp["values"].items():
                    lines.append("  - Column %s = `%s`" % ("ABCDEFGHIJ"[int(k)], v))
            if "filter" in mp:
                lines.append("  - Filter: column A equal (case insensitive) `%s`, limit 1" % mp["filter"][0][0]["b"])
        elif m["module"] == "gateway:WebhookRespond":
            lines.append("- Status 200, body: `%s`" % mp["body"])
        lines.append("")
    return "\n".join(lines)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    blueprints = {
        "1-inbox.blueprint.json": build_inbox(),
        "2-publisher.blueprint.json": build_publisher(),
        "3-doc-reader.blueprint.json": build_docreader(),
    }
    for fname, bp in blueprints.items():
        ids = [m["id"] for m in walk(bp["flow"])]
        assert len(ids) == len(set(ids)), (fname, ids)
        with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
            json.dump(bp, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("wrote", fname, len(ids), "modules")

    header = (
        "# Module reference (auto-generated)\n\n"
        "Ye file `make/build_blueprints.py` se banti hai. Import ke baad agar koi module khali ya laal "
        "dikhe to yahan se uski settings dekh kar haath se bhar dein. `{{6.from}}` ka matlab: module 6 "
        "ka `from` field (Make me mapping panel se choose karein).\n\n"
    )
    with open(os.path.join(ROOT, "docs", "MODULES.md"), "w", encoding="utf-8") as f:
        f.write(header + "\n\n".join(describe(bp) for bp in blueprints.values()))
    print("wrote docs/MODULES.md")


if __name__ == "__main__":
    main()
