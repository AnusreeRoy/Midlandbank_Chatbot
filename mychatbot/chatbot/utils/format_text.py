import html

HEADING_LABELS = [
    'savings products', 'loan products', 'current products', 'islamic products',
    'general products', 'agent-banking products', 'cards products', 'loans products',
    'loans', 'loan', 'current', 'savings', 'benefits', 'eligibility', 'documents'
]

def format_bot_reply(text: str) -> str:
    if not text:
        return ''
    
    lines = text.strip().split('\n')
    html_output = ''
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_output += '</ul>'
                in_list = False
            continue

        # --- Headings ---
        cleaned_line = line.lower().replace('•', '').replace('-', '').strip().rstrip(':')
        if cleaned_line in HEADING_LABELS:
            if in_list:
                html_output += '</ul>'
                in_list = False
            html_output += f'<h3>{html.escape(line)}</h3>'
            continue

        # --- MDB product headings ---
        if line.startswith('MDB') and len(line.split()) <= 6 and line.upper() == line:
            if in_list:
                html_output += '</ul>'
                in_list = False
            html_output += f'<h3>{html.escape(line)}</h3>'
            continue

        # --- Bullet lines ---
        is_bullet = line.startswith('•') or line.startswith('- ')
        is_key_value = ':' in line
        if is_bullet and is_key_value:
            if in_list:
                html_output += '</ul>'
                in_list = False
            clean_line = line.lstrip('•- ').strip()
            key, value = map(str.strip, clean_line.split(':', 1))
            html_output += f'<p><b>{html.escape(key)}:</b> {html.escape(value)}</p>'
        elif is_bullet:
            if not in_list:
                html_output += '<ul>'
                in_list = True
            clean_line = line.lstrip('•- ').strip()
            html_output += f'<li>{html.escape(clean_line)}</li>'
        else:
            if in_list:
                html_output += '</ul>'
                in_list = False
            html_output += f'<p>{html.escape(line)}</p>'

    if in_list:
        html_output += '</ul>'

    return html_output
