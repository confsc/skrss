"""
Единая дизайн-система и стили (QSS) для Тренажёра skrss (Client и Host).
Военно-инженерный стиль (Light/Slate) с хвойно-изумрудным акцентом.
"""

# Основная палитра
COLOR_PRIMARY_DARK = "#1B4332"     # Глубокий хвойный
COLOR_PRIMARY = "#2D6A4F"          # Изумрудный (главный акцент)
COLOR_PRIMARY_HOVER = "#40916C"    # Светлее при наведении
COLOR_PRIMARY_LIGHT = "#95D5B2"    # Светлый мятный (фон выделений)
COLOR_PRIMARY_PALE = "#D8F3DC"     # Очень мягкий хвойный фон

# Нейтральные цвета (Slate)
COLOR_BG_MAIN = "#F8FAFC"          # Фоновый цвет окна (мягкий светло-серый)
COLOR_CARD_BG = "#FFFFFF"          # Фон карточек и панелей
COLOR_CARD_BG_ALT = "#F1F5F9"      # Вторичный фон карточек
COLOR_BORDER = "#E2E8F0"           # Стандартная тонкая граница
COLOR_BORDER_FOCUS = "#2D6A4F"     # Граница при фокусе
COLOR_BORDER_HOVER = "#CBD5E1"     # Граница при ховере

# Типографика
COLOR_TEXT_PRIMARY = "#0F172A"     # Основной текст (Slate 900)
COLOR_TEXT_SECONDARY = "#475569"   # Вторичный текст / подписи (Slate 600)
COLOR_TEXT_MUTED = "#94A3B8"       # Подсказки / неактивный текст (Slate 400)
COLOR_TEXT_LIGHT = "#FFFFFF"       # Белый текст для кнопок

# Статусные цвета
COLOR_SUCCESS = "#16A34A"          # Зелёный (сдано / правильно)
COLOR_SUCCESS_BG = "#DCFCE7"       # Мягкий фон успеха
COLOR_WARNING = "#D97706"          # Янтарный (в процессе / внимание)
COLOR_WARNING_BG = "#FEF3C7"       # Мягкий фон предупреждения
COLOR_DANGER = "#DC2626"           # Красный (ошибка / тревога)
COLOR_DANGER_BG = "#FEE2E2"        # Мягкий фон опасности
COLOR_INFO = "#2563EB"             # Инфо-синий
COLOR_INFO_BG = "#DBEAFE"          # Мягкий синий фон

# Семейство шрифтов
FONT_FAMILY = "Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, sans-serif"

# Глобальный стиль приложения
GLOBAL_APP_STYLE = f"""
QMainWindow, QDialog {{
    background-color: {COLOR_BG_MAIN};
    font-family: {FONT_FAMILY};
    color: {COLOR_TEXT_PRIMARY};
}}

QWidget {{
    font-family: {FONT_FAMILY};
    color: {COLOR_TEXT_PRIMARY};
}}

/* Скроллбары */
QScrollBar:vertical {{
    background: {COLOR_BG_MAIN};
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: #CBD5E1;
    min-height: 25px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: {COLOR_BG_MAIN};
    height: 10px;
    margin: 0px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: #CBD5E1;
    min-width: 25px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #94A3B8;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* Поля ввода */
QLineEdit, QComboBox {{
    background-color: {COLOR_CARD_BG};
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    color: {COLOR_TEXT_PRIMARY};
    selection-background-color: {COLOR_PRIMARY_PALE};
    selection-color: {COLOR_PRIMARY_DARK};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1.5px solid {COLOR_PRIMARY};
    background-color: #FFFFFF;
}}
QLineEdit:hover, QComboBox:hover {{
    border-color: {COLOR_BORDER_HOVER};
}}

/* Выпадающие списки */
QComboBox::drop-down {{
    border: none;
    width: 24px;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    selection-background-color: {COLOR_PRIMARY_PALE};
    selection-color: {COLOR_PRIMARY_DARK};
    outline: none;
    padding: 4px;
}}

/* Списки */
QListWidget {{
    background-color: {COLOR_CARD_BG};
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 10px;
    outline: none;
    padding: 6px;
}}
QListWidget::item {{
    padding: 10px 14px;
    border-radius: 6px;
    margin-bottom: 2px;
    border: none;
    color: {COLOR_TEXT_PRIMARY};
}}
QListWidget::item:hover {{
    background-color: {COLOR_CARD_BG_ALT};
}}
QListWidget::item:selected {{
    background-color: {COLOR_PRIMARY_PALE};
    color: {COLOR_PRIMARY_DARK};
    font-weight: 600;
}}

/* Таблицы */
QTableWidget {{
    background-color: {COLOR_CARD_BG};
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 10px;
    gridline-color: {COLOR_BORDER};
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {COLOR_BORDER};
}}
QTableWidget::item:selected {{
    background-color: {COLOR_PRIMARY_PALE};
    color: {COLOR_PRIMARY_DARK};
}}
QHeaderView::section {{
    background-color: {COLOR_CARD_BG_ALT};
    color: {COLOR_TEXT_SECONDARY};
    font-weight: 600;
    font-size: 13px;
    padding: 10px 12px;
    border: none;
    border-bottom: 1.5px solid {COLOR_BORDER};
}}

/* Вкладки (Tabs) */
QTabWidget::pane {{
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 10px;
    background-color: {COLOR_CARD_BG};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {COLOR_BG_MAIN};
    color: {COLOR_TEXT_SECONDARY};
    padding: 10px 20px;
    font-weight: 600;
    font-size: 14px;
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
}}
QTabBar::tab:selected {{
    background-color: {COLOR_CARD_BG};
    color: {COLOR_PRIMARY_DARK};
    border-top: 3px solid {COLOR_PRIMARY};
    border-bottom: 1px solid {COLOR_CARD_BG};
}}
QTabBar::tab:hover:!selected {{
    background-color: {COLOR_CARD_BG_ALT};
    color: {COLOR_TEXT_PRIMARY};
}}

/* Прогресс-бар */
QProgressBar {{
    background-color: {COLOR_BORDER};
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: 11px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}
QProgressBar::chunk {{
    background-color: {COLOR_PRIMARY};
    border-radius: 6px;
}}

/* Подсказки Tooltips */
QToolTip {{
    background-color: {COLOR_TEXT_PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""

# Стили кнопок
BTN_PRIMARY_STYLE = f"""
QPushButton {{
    background-color: {COLOR_PRIMARY};
    color: {COLOR_TEXT_LIGHT};
    font-size: 15px;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    padding: 10px 20px;
}}
QPushButton:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
}}
QPushButton:pressed {{
    background-color: {COLOR_PRIMARY_DARK};
}}
QPushButton:disabled {{
    background-color: #CBD5E1;
    color: #94A3B8;
}}
"""

BTN_SECONDARY_STYLE = f"""
QPushButton {{
    background-color: {COLOR_CARD_BG};
    color: {COLOR_TEXT_PRIMARY};
    font-size: 15px;
    font-weight: 600;
    border-radius: 8px;
    border: 1.5px solid {COLOR_BORDER};
    padding: 10px 20px;
}}
QPushButton:hover {{
    background-color: {COLOR_CARD_BG_ALT};
    border-color: {COLOR_BORDER_HOVER};
}}
QPushButton:pressed {{
    background-color: {COLOR_BORDER};
}}
QPushButton:disabled {{
    background-color: {COLOR_BG_MAIN};
    color: #94A3B8;
    border-color: {COLOR_BORDER};
}}
"""

BTN_DANGER_STYLE = f"""
QPushButton {{
    background-color: {COLOR_DANGER};
    color: {COLOR_TEXT_LIGHT};
    font-size: 14px;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    padding: 8px 16px;
}}
QPushButton:hover {{
    background-color: #B91C1C;
}}
QPushButton:pressed {{
    background-color: #991B1B;
}}
"""

BTN_SUCCESS_STYLE = f"""
QPushButton {{
    background-color: {COLOR_SUCCESS};
    color: {COLOR_TEXT_LIGHT};
    font-size: 14px;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    padding: 8px 16px;
}}
QPushButton:hover {{
    background-color: #15803D;
}}
QPushButton:pressed {{
    background-color: #166534;
}}
"""

def make_badge_html(text: str, bg_color: str, text_color: str, font_size: str = "12px") -> str:
    """Генерация аккуратного цветного чипа/бейджа."""
    return f"""
    <span style="
        background-color: {bg_color};
        color: {text_color};
        font-size: {font_size};
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 12px;
        display: inline-block;
    ">{text}</span>
    """
