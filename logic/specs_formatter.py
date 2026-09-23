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
        "label_template": "{n}-диапазон",
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


def _try_group(name):
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
    group_meta = {}

    for spec in specs:
        name = spec["name"]
        answer = spec["answer"]
        unit = spec.get("unit", "").strip()

        parsed = _try_group(name)

        if not parsed:
            general.append((name, answer, unit))
        else:
            gid = parsed["group_id"]
            val = parsed["value"]
            base = parsed["base"]

            if gid not in grouped:
                grouped[gid] = {}
                group_meta[gid] = {}

            if base not in grouped[gid]:
                grouped[gid][base] = {}

            grouped[gid][base][val] = (answer, unit)

            if base not in group_meta[gid]:
                group_meta[gid][base] = unit

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
    </style>
    <h3>Тактико-технические характеристики</h3>
    <table>
    """

    total_cols = 2
    for gid, bases in grouped.items():
        labels_count = set()
        for base, vals in bases.items():
            labels_count.update(vals.keys())
        total_cols = max(total_cols, len(labels_count) + 1)

    html += f"<tr><th style='width: 35%;'>Характеристика</th>"
    html += f"<th style='width: 65%;' colspan='{total_cols - 1}'>Значение</th></tr>"

    for name, ans, u in general:
        name_with_unit = f"{name}, {u}" if u else name
        html += f"<tr><td>{name_with_unit}</td>"
        html += f"<td colspan='{total_cols - 1}'><b>{ans}</b></td></tr>"

    for gid, bases in grouped.items():
        all_labels = set()
        for base, vals in bases.items():
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

        for base, vals in bases.items():
            unit = group_meta[gid].get(base, "")
            name = f"{base}, {unit}" if unit else base

            html += f"<tr><td>{name}</td>"
            for label in sorted_labels:
                if label in vals:
                    html += f"<td class='center'><b>{vals[label][0]}</b></td>"
                else:
                    html += "<td class='center'>—</td>"
            html += "</tr>"

    html += "</table>"

    return html
