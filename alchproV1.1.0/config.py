# alchPRO/config.py

API_BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"
API_HEADERS = {
    'User-Agent': 'F2P Alch Calc - @StankyDank',
    'Accept-Encoding': 'gzip'
}
DEFAULT_NAT_PRICE = 90
MAGIC_XP_PER_CAST = 65

OSRS_STYLESHEET = """
    QMainWindow { background-color: #1c1a17; }
    QWidget {
        background-color: #1c1a17;
        color: #dcd1bc;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
    }
    QTableWidget {
        background-color: #12110f;
        border: 2px solid #3d3526;
        gridline-color: #2b251b;
        border-radius: 4px;
        selection-background-color: #4a3f29;
    }
    QHeaderView::section {
        background-color: #262118;
        color: #ff9800;
        padding: 6px;
        border: 1px solid #3d3526;
        font-weight: bold;
    }
    QLineEdit {
        background-color: #0e0d0c;
        border: 1px solid #4a3f29;
        border-radius: 3px;
        padding: 5px;
        color: #fff;
        selection-background-color: #ff9800;
    }
    QLineEdit:focus { border: 1px solid #ff9800; }
    QPushButton {
        background-color: #362e20;
        border: 1px solid #544732;
        border-radius: 4px;
        padding: 6px 12px;
        color: #ffb74d;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #4a3f29;
        border: 1px solid #ff9800;
        color: #fff;
    }
    QPushButton:pressed { background-color: #211b11; }
    QCheckBox { spacing: 6px; }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #4a3f29;
        background-color: #0e0d0c;
        border-radius: 3px;
    }
    QCheckBox::indicator:checked {
        background-color: #ff9800;
        border: 1px solid #fff;
    }
    QComboBox {
        background-color: #0e0d0c;
        border: 1px solid #4a3f29;
        border-radius: 3px;
        padding: 4px 20px 4px 6px;
        color: #ffb74d;
        min-width: 100px;
    }
    QComboBox:focus, QComboBox:hover { border: 1px solid #ff9800; }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left-width: 1px;
        border-left-color: #4a3f29;
        border-left-style: solid;
    }
    QLabel {
        color: #bfae93;
        font-weight: bold;
    }
"""