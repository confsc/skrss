from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import random
from logic.data_loader import load_stations, resource_path
from logic.scoring import check_answer


class QuizWindow(QMainWindow):
    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback

        self.setWindowTitle("Режим контроля")
        self.resize(1100, 800)

        stations = load_stations()
        self.station = random.choice(stations)
        self.inputs = {}

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top = QHBoxLayout()
        back_btn = QPushButton("← Назад на стартовый экран")
        back_btn.clicked.connect(self.go_back)
        top.addWidget(back_btn)
        top.addStretch()
        layout.addLayout(top)

        title = QLabel(f"<h2>Станция: {self.station['name']}</h2>")
        layout.addWidget(title)

        # ===== ФОТО — через resource_path =====
        img = QLabel()
        img.setAlignment(Qt.AlignCenter)
        if self.station.get("image"):
            img_path = resource_path(self.station["image"])
            pix = QPixmap(img_path)
            if not pix.isNull():
                img.setPixmap(pix.scaled(400, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                img.setText("(картинка не найдена)")
        layout.addWidget(img)

        layout.addWidget(QLabel("Заполните тактико-технические характеристики:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)

        for spec in self.station["specs"]:
            row = QHBoxLayout()
            label = QLabel(f"{spec['name']}:")
            label.setMinimumWidth(300)
            row.addWidget(label)

            if spec["type"] == "choice":
                widget = QComboBox()
                widget.addItem("")
                for opt in spec.get("options", []):
                    widget.addItem(opt)
            else:
                widget = QLineEdit()
                widget.setPlaceholderText("Введите значение...")

            self.inputs[spec["name"]] = (spec, widget)
            row.addWidget(widget)

            if spec.get("unit"):
                row.addWidget(QLabel(spec["unit"]))

            inner_layout.addLayout(row)

        scroll.setWidget(inner)
        layout.addWidget(scroll)

        check_btn = QPushButton("Проверить")
        check_btn.setStyleSheet("font-size: 16px; padding: 12px;")
        check_btn.clicked.connect(self.check)
        layout.addWidget(check_btn)

    def go_back(self):
        self.back_callback()
        self.close()

    def check(self):
        total_score = 0.0
        max_score = 0.0
        errors = []

        for name, (spec, widget) in self.inputs.items():
            weight = spec.get("weight", 0.5)
            max_score += weight

            if isinstance(widget, QComboBox):
                user_answer = widget.currentText()
            else:
                user_answer = widget.text().strip()

            if check_answer(spec, user_answer):
                total_score += weight
            else:
                unit = f" {spec['unit']}" if spec.get("unit") else ""
                errors.append(
                    f"• {name} (вес {weight}): «{user_answer or '—'}» "
                    f"вместо «{spec['answer']}{unit}»"
                )

        percent = (total_score / max_score * 100) if max_score > 0 else 0

        msg = f"Результат: {total_score:.1f} из {max_score:.1f} баллов ({percent:.1f}%)"
        if errors:
            msg += "\n\nОшибки:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                msg += f"\n... и ещё {len(errors) - 10} ошибок."
        else:
            msg += "\n\n🎉 Все ответы верны!"

        QMessageBox.information(self, "Результат контроля", msg)
        self.go_back()
