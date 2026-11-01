"""
Генерация HTML-таблицы тактико-технических характеристик (ТТХ).
Современная чистая верстка под стиль Slate / Emerald.
"""
try:
    from styles import (
        COLOR_PRIMARY_DARK, COLOR_PRIMARY, COLOR_PRIMARY_PALE,
        COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
        FONT_FAMILY
    )
except ImportError:
    from ui.styles import (
        COLOR_PRIMARY_DARK, COLOR_PRIMARY, COLOR_PRIMARY_PALE,
        COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
        FONT_FAMILY
    )


def build_specs_html(station):
    specs = station["specs"]

    html = f"""
    <style>
        body {{
            font-family: {FONT_FAMILY};
            color: {COLOR_TEXT_PRIMARY};
            margin: 0;
            padding: 4px;
        }}
        h3 {{
            color: {COLOR_PRIMARY_DARK};
            font-size: 18px;
            font-weight: 700;
            margin-top: 6px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid {COLOR_PRIMARY_PALE};
        }}
        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 8px;
            font-size: 14px;
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background-color: {COLOR_PRIMARY_DARK};
            color: #FFFFFF;
            padding: 12px 14px;
            text-align: left;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }}
        td {{
            padding: 11px 14px;
            border-bottom: 1px solid {COLOR_BORDER};
            color: {COLOR_TEXT_PRIMARY};
            vertical-align: middle;
            font-size: 14px;
        }}
        tr:nth-child(even) td {{
            background-color: #F8FAFC;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        td.name {{
            color: {COLOR_TEXT_SECONDARY};
            font-weight: 500;
            width: 60%;
        }}
        td.value {{
            color: {COLOR_PRIMARY_DARK};
            font-weight: 700;
            width: 40%;
        }}
    </style>
    <h3>Тактико-технические характеристики (ТТХ)</h3>
    <table>
    <tr>
        <th style='width: 60%;'>Параметр</th>
        <th style='width: 40%;'>Значение</th>
    </tr>
    """

    for spec in specs:
        unit = (spec.get("unit") or "").strip()
        name = f"{spec['name']}, {unit}" if unit else spec["name"]
        answer = spec["answer"]
        html += f"<tr><td class='name'>{name}</td><td class='value'>{answer}</td></tr>"

    html += "</table>"
    return html
