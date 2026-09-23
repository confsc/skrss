import re


HEADER_COLOR = "#1B4332"
LIGHT_ACCENT = "#95D5B2"
TEXT_COLOR = "#1B1B1B"

GROUPS = [
    {
        "id": "range",
        "patterns": [
            r'[Дд]иапазон[аеуы]?х?\s*(\d+)',
        ],
        "label_template": "Диапазон {n}",
        "sort": "numeric",
    },
    {
        "id": "band",
        "patterns": [
            r'\b(Ku|C|X|Ka|L|S)\s*-?\s*диапазон',
            r'диапазон[аеуы]?\s+(Ku|C|X|Ka|L|S)\b',
        ],
        "label_template": "Диапазон {n}",
        "sort": "custom",
        "order": ["L", "S", "C", "X", "Ku", "Ka"],
    },
]


def _restore_base(base):
    base = base.strip()
    if re.match(r'^рабочих\s+частот$', base):
        return "Диапазон рабочих частот"
    if re.match(r'^рабочие\s+частоты$', base):
        return "Диапазон рабочих частот"
    if re.match(r'^на\s+(передачу|приём|прием)$', base):
        return "Диапазон " + base
    if base == "":
        return "Диапазон"
    return base


def _parse_name(name):
    for group in GROUPS:
        for pattern in group["patterns"]:
            m = re.search(pattern, name)
            if m:
                value = m.group(1) if m.groups() else ""
                label = group["label_template"].format(n=value)

                prefix = name[:m.start()].strip()
                suffix = name[m.end():].strip()

                prefix = re.sub(r'[\s,;:()\-]*\bв\s*$', '', prefix).strip()
                prefix = re.sub(r'[\s,;:()\-]+$', '', prefix).strip()

                suffix = re.sub(r'^[\s,;:()\-]+', '', suffix).strip()
                suffix = re.sub(r'^\bв\b\s*', '', suffix).strip()

                qualifier = ""
                m_q = re.search(r'\(([^)]+)\)', suffix)
                if m_q:
                    qualifier = m_q.group(1).strip()
                    suffix = (suffix[:m_q.start()] + suffix[m_q.end():]).strip()

                m_q2 = re.search(r'\(([^)]+)\)', prefix)
                if m_q2:
                    if qualifier:
                        qualifier = f"{m_q2.group(1).strip()}, {qualifier}"
                    else:
                        qualifier = m_q2.group(1).strip()
                    prefix = (prefix[:m_q2.start()] + prefix[m_q2.end():]).strip()

                m_on = re.match(r'^на\s+(передачу|приём|прием)$', suffix)
                if m_on:
                    qualifier = ("на " + m_on.group(1)).strip()
                    suffix = ""

                if prefix and suffix:
                    base = f"{prefix} {suffix}"
                elif prefix:
                    base = prefix
                else:
                    base = suffix

                base = re.sub(r'\s+', ' ', base).strip()
                base = re.sub(r'[\s,;:()\-]+$', '', base).strip()

                base = _restore_base(base)

                return {
                    "group_id": group["id"],
                    "value": label,
                    "base": base,
                    "qualifier": qualifier,
                }

    return None


def _sort_key(group_id, label):
    for group in GROUPS:
        if group["id"] == group_id:
            if group["sort"] == "numeric":
                m = re.search(r'(\d+)', label)
                return int(m.group(1)) if m else 0
            if group["sort"] == "custom":
                order = group.get("order", [])
                for i, o in enumerate(order):
                    if o.lower() in label.lower():
                        return i
                return 999
    return 0


def build_specs_html(station):
    specs = station["specs"]

    general = []
    grouped = {}

    for spec in specs:
        name = spec["name"]
        answer = spec["answer"]
        unit = spec.get("unit", "").strip()

        parsed = _parse_name(name)

        if not parsed:
            general.append((name, answer, unit))
        else:
            gid = parsed["group_id"]
            val = parsed["value"]
            base = parsed["base"]
            qualifier = parsed["qualifier"]

            if gid not in grouped:
                grouped[gid] = {}

            if base not in grouped[gid]:
                grouped[gid][base] = {
                    "unit": unit,
                    "entries": {},
                }

            key = qualifier if qualifier else "__no_qual__"
            if key not in grouped[gid][base]["entries"]:
                grouped[gid][base]["entries"][key] = {}
            grouped[gid][base]["entries"][key][val] = answer

    all_labels_global = set()
    for gid, bases in grouped.items():
        for base, data in bases.items():
            for key, vals in data["entries"].items():
                all_labels_global.update(vals.keys())

    sorted_labels_global = sorted(
        all_labels_global,
        key=lambda x: _sort_key(list(grouped.keys())[0], x) if grouped else 0
    )

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
            border: 1px solid #0F2A1D;
        }}
        th.group-col {{
            text-align: center;
            background-color: #2D6A4F;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #E0E0E0;
            border-right: 1px solid #EEEEEE;
            color: {TEXT_COLOR};
            vertical-align: top;
        }}
        tr:nth-child(even) td {{
            background-color: #F5F5F5;
        }}
        td.center {{
            text-align: center;
        }}
        td.parent-row {{
            background-color: #E8F5E9 !important;
            font-weight: bold;
            color: {HEADER_COLOR};
        }}
        td.child-row {{
            padding-left: 30px;
        }}
    </style>
    <h3>Тактико-технические характеристики</h3>
    <table>
    """

    total_cols = 2
    if sorted_labels_global:
        total_cols = len(sorted_labels_global) + 1

    html += "<tr><th style='width: 35%;'>Характеристика</th>"
    html += f"<th style='width: 65%;' colspan='{total_cols - 1}'>Значение</th></tr>"

    for name, ans, u in general:
        name_with_unit = f"{name}, {u}" if u else name
        html += f"<tr><td>{name_with_unit}</td>"
        html += f"<td colspan='{total_cols - 1}'><b>{ans}</b></td></tr>"

    for gid, bases in grouped.items():
        all_labels = set()
        for base, data in bases.items():
            for key, vals in data["entries"].items():
                all_labels.update(vals.keys())

        sorted_labels = sorted(
            all_labels,
            key=lambda x: _sort_key(gid, x)
        )

        html += "<tr>"
        html += "<th>Характеристика</th>"
        for label in sorted_labels:
            html += f"<th class='group-col'>{label}</th>"
        html += "</tr>"

        for base, data in bases.items():
            unit = data["unit"]
            base_with_unit = f"{base}, {unit}" if unit else base

            entries = data["entries"]
            has_only_simple = (
                len(entries) == 1 and "__no_qual__" in entries
            )

            if has_only_simple:
                vals = entries["__no_qual__"]
                present = [l for l in sorted_labels if l in vals]

                if len(present) == len(sorted_labels):
                    unique = set(vals[l] for l in present)
                    if len(unique) == 1:
                        html += f"<tr><td>{base_with_unit}</td>"
                        html += f"<td class='center' colspan='{len(sorted_labels)}'><b>{vals[present[0]]}</b></td></tr>"
                        continue

                html += f"<tr><td>{base_with_unit}</td>"
                for label in sorted_labels:
                    if label in vals:
                        html += f"<td class='center'><b>{vals[label]}</b></td>"
                    else:
                        html += "<td class='center'></td>"
                html += "</tr>"
            else:
                simple_vals = entries.get("__no_qual__", {})
                has_simple = bool(simple_vals)

                html += f"<tr><td class='parent-row' colspan='{len(sorted_labels) + 1}'>{base_with_unit}</td></tr>"

                if has_simple:
                    html += f"<tr><td class='child-row'></td>"
                    for label in sorted_labels:
                        if label in simple_vals:
                            html += f"<td class='center'><b>{simple_vals[label]}</b></td>"
                        else:
                            html += "<td class='center'></td>"
                    html += "</tr>"

                for key, vals in entries.items():
                    if key == "__no_qual__":
                        continue

                    child_name = key if key.startswith("на ") else key
                    html += f"<tr><td class='child-row'>{child_name}</td>"
                    for label in sorted_labels:
                        if label in vals:
                            html += f"<td class='center'><b>{vals[label]}</b></td>"
                        else:
                            html += "<td class='center'></td>"
                    html += "</tr>"

    html += "</table>"

    return html
