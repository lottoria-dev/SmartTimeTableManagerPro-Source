# --- 스타일 및 설정 ---
STYLE_SHEET = """
/* 시스템 다크모드 무시 및 라이트 테마 강제 적용 */
QWidget {
    background-color: #ffffff;
    color: #1f2937;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
}

QMainWindow {
    background-color: #f3f4f6;
}

/* 라벨 스타일: 불필요한 여백 제거 */
QLabel {
    background-color: transparent;
    color: #1f2937;
    padding: 0px;
    margin: 0px;
}

/* 라디오 버튼 스타일 (개선됨: 마우스 오버 효과 추가) */
QRadioButton {
    background-color: transparent;
    color: #1f2937;
    font-weight: bold;
    spacing: 8px;
    padding: 6px 10px; /* 클릭 영역 확보 */
    border-radius: 6px; /* 둥근 모서리 */
}
QRadioButton:hover {
    background-color: #eff6ff; /* 마우스 오버 시 연한 파란색 배경 */
    color: #2563eb; /* 텍스트 색상 강조 */
}
QRadioButton:checked {
    background-color: #dbeafe; /* 선택 시 배경색 */
    color: #1d4ed8;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
}

/* 모드 전환 탭 버튼 스타일 */
QPushButton#ModeBtn {
    background-color: #ffffff;
    color: #4b5563;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 8px 14px; /* [v1.2.0] 패딩 축소 */
    font-weight: bold;
    font-size: 11px;
    text-align: center;
}
QPushButton#ModeBtn:hover {
    background-color: #f9fafb;
    border-color: #9ca3af;
}
QPushButton#ModeBtn:checked {
    background-color: #3b82f6;
    color: white;
    border: 1px solid #2563eb;
}

/* 일반 버튼 스타일 */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 5px 10px; /* [v1.2.0] 패딩 축소 */
    color: #374151;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #f9fafb;
    border-color: #9ca3af;
}
QPushButton#PrimaryBtn {
    background-color: #3b82f6;
    color: white;
    border: 1px solid #2563eb;
}
QPushButton#PrimaryBtn:hover {
    background-color: #2563eb;
}
QPushButton#SuccessBtn {
    background-color: #10b981;
    color: white;
    border: 1px solid #059669;
}
QPushButton#SuccessBtn:hover {
    background-color: #059669;
}
QPushButton#DangerBtn {
    background-color: #ef4444;
    color: white;
    border: 1px solid #dc2626;
}
QPushButton#DangerBtn:hover {
    background-color: #dc2626;
}
QPushButton#InfoBtn {
    background-color: #6366f1;
    color: white;
    border: 1px solid #4f46e5;
}
QPushButton#InfoBtn:hover {
    background-color: #4f46e5;
}

QFrame#Card {
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
/* 스크롤 영역 내부 위젯 배경 강제 지정 */
QScrollArea > QWidget > QWidget {
    background-color: #ffffff;
}

/* 트리 위젯 (로그창 - 다이얼로그용) */
QTreeWidget {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background-color: white;
    color: #1f2937;
}
QTreeWidget::item {
    color: #1f2937;
    height: 24px;
}
QTreeWidget::item:selected {
    background-color: #3b82f6;
    color: white;
}
QHeaderView::section {
    background-color: #f9fafb;
    padding: 4px;
    border: 0px;
    font-weight: bold;
    color: #4b5563;
}
/* 콤보박스 스타일 */
QComboBox {
    background-color: white;
    color: #1f2937;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 4px;
}
QComboBox QAbstractItemView {
    background-color: white;
    color: #1f2937;
    selection-background-color: #3b82f6;
}

/* 셀 프레임 자체의 패딩 제거 */
QFrame#Cell {
    padding: 0px;
    margin: 0px;
}
"""

COLORS = {
    "cell_default": "#f9fafb",
    "cell_locked": "#e5e7eb",
    "cell_changed": "#fef9c3",
    "cell_selected": "#dbeafe",
    "cell_target": "#dcfce7",
    "cell_conflict": "#fee2e2",
    "cell_chain_src": "#f3e8ff",
    "cell_chain_tgt": "#e9d5ff",
    "text_primary": "#111827",
    "text_secondary": "#6b7280",
    "accent": "#3b82f6"
}