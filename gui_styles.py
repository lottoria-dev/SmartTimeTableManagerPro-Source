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

/* 라디오 버튼 스타일 (상단 라인 강조 탭 형태 - 하단 잘림 완벽 해결) */
QRadioButton {
    background-color: transparent;
    color: #6b7280;
    font-weight: bold;
    border: none;
    border-top: 3px solid transparent; /* 평소에는 투명한 상단 선으로 높이 유지 */
    border-radius: 0px; /* 탭 형태이므로 둥근 모서리 제거 */
    padding: 6px 12px;
    text-align: center;
    spacing: 0px; /* 텍스트 쏠림 방지 */
    margin: 0px;
}
QRadioButton::indicator {
    width: 0px;
    height: 0px;
    margin: 0px;
    padding: 0px;
    border: none;
    background: transparent;
}
QRadioButton:hover {
    background-color: #f9fafb;
    color: #374151;
    border-top: 3px solid #d1d5db; /* 마우스 오버 시 옅은 회색 선 */
}
QRadioButton:checked {
    background-color: #eff6ff; 
    color: #1d4ed8;
    border-top: 3px solid #3b82f6; /* 활성화 시 파란색 상단 굵은 선 */
}
QRadioButton:pressed {
    background-color: #e5e7eb;
}

/* 체크박스 지시자(네모 박스) 스타일 복원 및 테두리 추가 */
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 2px solid #9ca3af;
    border-radius: 3px;
    background-color: #ffffff;
}
QCheckBox::indicator:hover {
    border-color: #3b82f6; 
}
QCheckBox::indicator:checked {
    background-color: #3b82f6; 
    border-color: #3b82f6;
}

/* 모드 전환 탭 버튼 스타일 */
QPushButton#ModeBtn {
    background-color: #ffffff;
    color: #4b5563;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 4px 14px;
    margin-top: 0px;
    margin-bottom: 0px;
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
    padding: 4px 10px;
    margin-top: 0px;
    margin-bottom: 0px;
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
QPushButton#PrimaryBtn:hover { background-color: #2563eb; }
QPushButton#PrimaryBtn:pressed { 
    background-color: #1d4ed8; 
    border-color: #1e40af;
}

QPushButton#SuccessBtn {
    background-color: #10b981;
    color: white;
    border: 1px solid #059669;
}
QPushButton#SuccessBtn:hover { background-color: #059669; }
QPushButton#SuccessBtn:pressed { 
    background-color: #047857; 
    border-color: #064e3b;
}

QPushButton#DangerBtn {
    background-color: #ef4444;
    color: white;
    border: 1px solid #dc2626;
}
QPushButton#DangerBtn:hover { background-color: #dc2626; }
QPushButton#DangerBtn:pressed { 
    background-color: #b91c1c; 
    border-color: #7f1d1d;
}

QPushButton#InfoBtn {
    background-color: #6366f1;
    color: white;
    border: 1px solid #4f46e5;
}
QPushButton#InfoBtn:hover { background-color: #4f46e5; }
QPushButton#InfoBtn:pressed { 
    background-color: #4338ca; 
    border-color: #312e81;
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

/* [추가] 툴팁 UI 세련되게 설정 */
QToolTip {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #475569;
    border-radius: 4px;
    padding: 8px;
    font-family: 'Malgun Gothic';
    font-size: 12px;
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