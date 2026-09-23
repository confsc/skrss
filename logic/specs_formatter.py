import re


HEADER_COLOR = "#1B4332"
LIGHT_ACCENT = "#95D5B2"
TEXT_COLOR = "#1B1B1B"


def _parse_spec_name(name):
    m = re.search(
        r'[Дд]иапазон[аеуы]?х?\s*(\d+)(?:\s*и\s*(\d+))?',
        name
    )
    if not m:
        return None, name, ""

    rn1 = int(m.group(1))
    rn2 = int(m.group(2)) if m.group(2) else None

    prefix = name[:m.start()].strip()
    suffix = name[m.end():].strip()

    prefix = re.sub(r'[\s,;:]*\bв\s*$', '', prefix).strip()
    suffix = re.sub(r'^[\s,;:]*(?:в\s+)?', '', suffix).strip()

    qual = ""
    m_q = re.search(r'\(([^)]+)\)', suffix)
    if m_q:
        qual = m_q.group(1)
        suffix = (suffix[:m_q.start()] + suffix[m_q.end():]).strip()

    if prefix and suffix:
        base = f"{prefix} {suffix}"
    elif prefix:
        base = prefix
    else:
        base = suffix

    base = re.sub(r'\s+', ' ', base).strip()

    ranges = [rn1]
    if rn2 is not None:
        ranges.append(rn2)

    return ranges, base, qual


def _is_uniform(ranges_dict, all_ranges):
    if len(all_ranges) < 2:
        return False
    values = set()
    for rn in all_ranges:
        if rn not in ranges_dict:
            return False
        entries = ranges_dict[rn]
        if len(entries) != 1:
            return False
        _, ans, _ = entries[0]
        values.add(ans)
    return len(values) == 1


def build_specs_html(station):
    specs = station["specs"]

    general = []
    ranged = {}
    ranged_units = {}
    ranged_order = []

    for spec in specs:
        name = spec["name"]
        answer = spec["answer"]
        unit = spec.get("unit", "").strip()
        rns, base, qual = _parse_spec_name(name)

        if rns is None:
            general.append((name, answer, unit))
        else:
            if base not in ranged:
                ranged[base] = {}
                ranged_units[base] = unit
                ranged_order.append(base)
            for rn in rns:
                ranged[base].setdefault(rn, []).append((qual, answer, unit))

    all_ranges = set()
    for ranges in ranged.values():
        all_ranges.update(ranges.keys())
    all_ranges = sorted(all_ranges)

    has_ranged_table = bool(ranged) and len(all_ranges) >= 2

    if ranged and not has_ranged_table:
        for base in ranged_order:
            for rn, entries in ranged[base].items():
                for qual, ans, u in entries:
                    name = f"{base} ({qual})" if qual else base
                    general.append((name, ans, u))
        ranged = {}
        ranged_order = []

    if has_ranged_table:
        to_remove = []
        for base in ranged_order:
            if _is_uniform(ranged[base], all_ranges):
                first_rn = all_ranges[0]
                _, ans, u = ranged[base][first_rn][0]
                general.append((base, ans, u))
                to_remove.append(base)
        for base in to_remove:
            del ranged[base]
            ranged_order.remove(base)

    html = f"""
    <style>
        h3 {{
            color: {HEADER_COLOR};
            font-size: 18px;
            margin-top: 12px;
            margin-bottom: 8px;
            border-bottom: 2px solid {LIGHT_ACCENT};
            padding-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 14px;
        }}
        th {{
            background-color: {HEADER_COLOR};
            color: white;
            padding: 10px;
            text-align: left;
            font-size: 14px;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #E0E0E0;
            color: {TEXT_COLOR};
            vertical-align: top;
        }}
        tr:nth-child(even) td {{
            background-color: #F5F5F5;
        }}
    </style>
    """

    if general:
        title = "Общие характеристики" if has_ranged_table else "Тактико-технические характеристики"
        html += f"<h3>{title}</h3><table>"
        html += "<tr><th style='width: 65%;'>Характеристика</th><th style='width: 35%;'>Значение</th></tr>"
        for name, ans, u in general:
            name_with_unit = f"{name}, {u}" if u else name
            html += f"<tr><td>{name_with_unit}</td><td><b>{ans}</b></td></tr>"
        html += "</table>"

    if has_ranged_table and ranged_order:
        html += "<h3>Характеристики по диапазонам</h3><table>"
        html += "<tr><th style='width: 25%;'>Характеристика</th>"
        for rn in all_ranges:
            html += f"<th>Диапазон {rn}</th>"
        html += "</tr>"

        for base in ranged_order:
            unit = ranged_units[base]
            name = f"{base}, {unit}" if unit else base
            html += f"<tr><td>{name}</td>"
            for rn in all_ranges:
                if rn in ranged[base]:
                    parts = []
                    for qual, ans, u in ranged[base][rn]:
                        parts.append(f"{qual}: {ans}" if qual else ans)
                    cell = "<br>".join(parts)
                    html += f"<td><b>{cell}</b></td>"
                else:
                    html += "<td>—</td>"
            html += "</tr>"
        html += "</table>"

    return html
