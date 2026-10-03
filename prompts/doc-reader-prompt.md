A client sent an article file on WhatsApp. The file has been uploaded into your code execution container (find it with: find / -type f -mmin -30 \( -iname '*.docx' -o -iname '*.doc' -o -iname '*.pdf' -o -iname '*.txt' -o -iname '*.odt' -o -iname '*.rtf' \) 2>/dev/null | grep -v -e '^/proc' -e '^/sys' -e '^/usr' | head).

Use code to read it:
- .docx: read word/document.xml and word/_rels/document.xml.rels with zipfile (or python-docx) so that every hyperlink keeps its exact URL and anchor text.
- .pdf: pypdf (keep link annotations' URLs).
- .txt / other text: read as UTF-8.

Then answer with ONLY the article as simple HTML, nothing else:
<h1> for the title, <h2>/<h3> for subheadings, <p>, <ul>/<ol>/<li>, <strong>, <em>, and <a href="URL">anchor</a> for every link.
Do not correct, rewrite, shorten or comment on anything. Skip images.
If the file cannot be read or is not an article, answer exactly: UNREADABLE_FILE
