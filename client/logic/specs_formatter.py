HEADER_COLOR = "#1B4332"
LIGHT_ACCENT = "#95D5B2"
TEXT_COLOR = "#1B1B1B"


def build_specs_html(station):
    specs = station["specs"]

    html = f"""
    <style>
        h3 {{
            color: {HEADER_COLOR};
            font-size: 20px;
            margin-top: 14px;
            margin-bottom: 10px;
            border-bottom: 3px solid {LIGHT_ACCENT};
            padding-bottom: 6px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 16px;
        }}
        th {{
            background-color: {HEADER_COLOR};
            color: white;
            padding: 16px 14px;
            text-align: left;
            font-size: 16px;
            font-weight: bold;
            border: 2px solid #0F2A1D;
        }}
        td {{
            padding: 14px;
            border-bottom: 2px solid #E0E0E0;
            border-right: 2px solid #EEEEEE;
            color: {TEXT_COLOR};
            vertical-align: middle;
            font-size: 16px;
        }}
        tr:nth-child(even) td {{
            background-color: #F5F5F5;
        }}
        td.value {{
            font-weight: bold;
        }}
    </style>
    <h3>Тактико-технические характеристики</h3>
    <table>
    <tr>
        <th style='width: 65%;'>Характеристика</th>
        <th style='width: 35%;'>Значение</th>
    </tr>
    """

    for spec in specs:
        unit = spec.get("unit", "").strip()
        name = f"{spec['name']}, {unit}" if unit else spec["name"]
        answer = spec["answer"]
        html += f"<tr><td>{name}</td><td class='value'>{answer}</td></tr>"

    html += "</table>"

    return html
