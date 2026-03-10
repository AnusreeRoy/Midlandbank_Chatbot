from django import template
from django.utils.safestring import mark_safe
import html
import re

register = template.Library()

@register.filter
def linebreaks_custom(text):
    if not text:
        return ""

    # Normalize <br> into newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = html.unescape(text)

    lines = [l.strip() for l in text.strip().split('\n')]
    html_out = []
    in_list = False

    heading_labels = [
        'savings products', 'loan products', 'current products', 'islamic products',
        'general products', 'agent-banking products', 'cards products', 'loans products',
        'loans', 'loan', 'current', 'savings', 'benefits', 'eligibility', 'documents'
    ]

    for line in lines:
        if not line:
            if in_list:
                html_out.append('</ul>')
                in_list = False
            continue

        cleaned_line = line.lower().lstrip('-• ').rstrip(': ').strip()
        is_heading = cleaned_line in heading_labels

        # === Headings ===
        if is_heading:
            if in_list:
                html_out.append('</ul>')
                in_list = False
            html_out.append(f"<h3>{html.escape(line)}</h3>")
            continue

        # === MDB Product Heading ===
        is_product_heading = (
            line.isupper() and line.startswith("MDB") and len(line.split()) <= 6
        )
        if is_product_heading:
            if in_list:
                html_out.append('</ul>')
                in_list = False
            html_out.append(f"<h3>{html.escape(line)}</h3>")
            continue

        # === Bullet / Key-Value ===
        is_bullet = line.startswith('•') or line.startswith('- ')
        is_key_value = re.match(r"^[-•]?\s*[\w\s]+:\s*", line)

        if is_bullet and is_key_value:
            if in_list:
                html_out.append('</ul>')
                in_list = False
            clean_line = line.lstrip('-• ')
            key, *rest = clean_line.split(':', 1)
            value = rest[0].strip() if rest else ''
            html_out.append(f"<p><b>{html.escape(key.strip())}:</b> {html.escape(value)}</p>")
        elif is_bullet:
            if not in_list:
                html_out.append('<ul>')
                in_list = True
            clean_line = line.lstrip('-• ')
            html_out.append(f"<li>{html.escape(clean_line)}</li>")
        else:
            if in_list:
                html_out.append('</ul>')
                in_list = False
            html_out.append(f"<p>{html.escape(line)}</p>")

    if in_list:
        html_out.append('</ul>')
    print("DEBUG: filter finished.")
    return mark_safe("".join(html_out))
