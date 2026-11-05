import os
import sys
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIENT_DIR = os.path.join(ROOT_DIR, "client")
SHARED_DIR = os.path.join(ROOT_DIR, "shared")

for p in [CLIENT_DIR, os.path.join(CLIENT_DIR, "ui"), os.path.join(CLIENT_DIR, "logic"), SHARED_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.start_screen import StartScreen, ModeCard
from ui.learning_window import LearningWindow, StationListWidget

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_mode_card_structure(qapp):
    card = ModeCard(title="Обучение", btn_text="Начать обучение →", is_primary=True)
    assert not hasattr(card, "lbl_badge")
    assert not hasattr(card, "lbl_desc")
    assert card.action_btn.text() == "Начать обучение →"


def test_start_screen_initialization(qapp):
    screen = StartScreen()
    assert screen.windowTitle() == "Тренажёр: Радиорелейные и спутниковые станции"
    assert screen.learning_window is None


def test_learning_window_opens_without_crash(qapp):
    back_called = False

    def on_back():
        nonlocal back_called
        back_called = True

    # Test LearningWindow initialization - previously this crashed with AttributeError: 'StationListWidget' object has no attribute 'title_label'
    win = LearningWindow(back_callback=on_back)
    assert win is not None
    assert win.tabs.count() == 2
    assert win.tabs.tabBar().elideMode() == Qt.ElideNone
    assert win.tabs.tabText(0) == "Радиорелейные станции"
    assert win.tabs.tabText(1) == "Спутниковые станции"

    # Check radio tab widget
    radio_widget = win.tabs.widget(0)
    assert isinstance(radio_widget, StationListWidget)
    assert radio_widget.category == "radio"
    assert radio_widget.list_widget.count() > 0

    # Verify selected station details are displayed without error
    assert radio_widget.current_station is not None
    assert radio_widget.title_label.text() == radio_widget.current_station["name"]
    assert "Тактико-технические" in radio_widget.info_text.toHtml()

    # Check satellite tab widget
    sat_widget = win.tabs.widget(1)
    assert isinstance(sat_widget, StationListWidget)
    assert sat_widget.category == "satellite"
    assert sat_widget.list_widget.count() > 0
    assert sat_widget.current_station is not None

    # Test go_back
    win.go_back()
    assert back_called is True


def test_station_search_filter(qapp):
    def dummy_back():
        pass

    win = LearningWindow(back_callback=dummy_back)
    radio_widget = win.tabs.widget(0)
    initial_count = radio_widget.list_widget.count()
    assert initial_count > 0

    # Search for specific station
    first_station_name = radio_widget.filtered_stations[0]["name"]
    radio_widget.search_input.setText(first_station_name)
    assert radio_widget.list_widget.count() >= 1

    # Search for non-existent text
    radio_widget.search_input.setText("xyzNonExistent999")
    assert radio_widget.list_widget.count() == 0

    # Clear search
    radio_widget.search_input.setText("")
    assert radio_widget.list_widget.count() == initial_count
