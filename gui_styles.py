# gui_styles.py

# [프리미엄 컬러 팔레트] 눈이 편안하면서도 세련된 파스텔톤 컬러 정의
COLORS = {
    "bg_main": "#eff3f8",           # 프리미엄 메인 배경 (소프트 쿨그레이)
    "cell_default": "rgba(255, 255, 255, 0.75)", # 글래스모르피즘 반투명 화이트
    "cell_selected": "#e0e7ff",     # 선택됨 (Indigo 100 - 부드러운 남색)
    "cell_target": "#d1fae5",       # 이동 추천 (Emerald 100 - 산뜻한 녹색)
    "cell_conflict": "#fee2e2",     # 충돌 발생 (Red 100 - 경고)
    "cell_changed": "#fef3c7",      # 변동 내역 (Yellow 100 - 직관적인 노란색으로 복구)
    "cell_chain_src": "#e0e7ff",    # 연쇄 시작점 (다른 모드의 '선택됨' 색상과 통일하여 혼동 방지)
    "cell_chain_tgt": "#dbeafe",    # 연쇄 타겟 (Blue 100 - 맑은 파랑)
    "cell_cover": "#e0e7ff",        # 보강 모드 선택 (선택됨 색상과 통일)
    "cell_excluded": "rgba(241, 245, 249, 0.5)", # 제외 학년 (반투명 Slate 100)
    "text_primary": "#0f172a",      # 진한 텍스트 (Slate 900)
    "text_secondary": "#64748b",    # 보조 텍스트 (Slate 500)
    "border": "rgba(203, 213, 225, 0.6)", # 유리 테두리 질감
    "accent": "#2563eb"             # 프리미엄 강조색 (Blue 600)
}

# [프리미엄 글로벌 QSS 스타일]
STYLE_SHEET = """
/* 1. 메인 윈도우 및 다이얼로그 (소프트 배경 적용) */
QMainWindow, QDialog {
    background-color: #eff3f8;
}

/* 전체 폰트 및 기본 텍스트 색상 통일 */
QWidget {
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    color: #1e293b;
}

/* 2. 버튼 스타일 (글래스모르피즘 적용) */
QPushButton {
    background-color: rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-bottom: 1px solid rgba(203, 213, 225, 0.6); /* 하단 그림자/입체감 효과 */
    border-radius: 8px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
    color: #334155;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid #94a3b8;
    color: #0f172a;
}
QPushButton:pressed {
    background-color: rgba(241, 245, 249, 0.8);
    padding-top: 7px;
    padding-bottom: 5px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.9); /* 눌렸을 때 입체감 해제 */
}
QPushButton:checked {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid #3b82f6;
    color: #1d4ed8;
    font-weight: bold;
}

/* 3. 콤보박스 (세련된 둥근 모서리와 여백) */
QComboBox {
    background-color: rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-bottom: 1px solid rgba(203, 213, 225, 0.6);
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 13px;
    color: #334155;
    min-width: 5em;
}
QComboBox:hover {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid #94a3b8;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    selection-background-color: #eff6ff;
    selection-color: #1d4ed8;
    outline: none;
}

/* 4. 체크박스 (클린 디자인) */
QCheckBox {
    spacing: 6px;
    color: #475569;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #94a3b8;
    background-color: rgba(255, 255, 255, 0.8);
}
QCheckBox::indicator:hover {
    border: 1px solid #64748b;
}
QCheckBox::indicator:checked {
    background-color: #3b82f6;
    border: 1px solid #2563eb;
    image: none; /* 자체 렌더링 유지 */
}

/* 5. 스크롤바 (맥 OS 스타일의 보이지 않는 얇고 둥근 스크롤바) */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: rgba(148, 163, 184, 0.3); /* 평소엔 아주 연하게 */
    min-height: 30px;
    border-radius: 5px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(100, 116, 139, 0.6); /* 마우스를 올리면 선명하게 */
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px; /* 화살표 버튼 제거 */
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 10px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: rgba(148, 163, 184, 0.3);
    min-width: 30px;
    border-radius: 5px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(100, 116, 139, 0.6);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* 6. 그리드 헤더 (요일, 교시, 학반 표시부) */
QLabel#GridHeader {
    background-color: rgba(248, 250, 252, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-bottom: 1px solid #cbd5e1;
    border-radius: 8px;
    font-weight: bold;
    color: #475569;
}

/* 7. 상태 표시줄 (Status Bar) - 과했던 색상을 빼고 고급스럽고 모던하게 톤다운! */
QStatusBar, QLabel#statusBar, QLabel#status_bar {
    background-color: rgba(248, 250, 252, 0.85); /* 세련된 파스텔 슬레이트(아주 밝은 쿨그레이) 배경 */
    border-top: 2px solid #cbd5e1; /* 무채색에 가까운 부드러운 슬레이트 실선 테두리 */
    border-bottom: 2px solid #e2e8f0; /* 하단 얇은 그림자 효과 테두리 */
    color: #334155; /* 차분하고 고급스러운 짙은 회색 텍스트 */
    font-weight: 800; /* 눈에 띄지만 부담스럽지 않은 굵기 */
    font-size: 15px; /* 세련되게 정돈된 크기 */
    padding: 6px 12px;
    min-height: 28px;
    border-radius: 6px;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    font-weight: 800;
    font-size: 15px;
    color: #334155;
    padding: 4px;
    background: transparent;
}

/* 8. 툴팁 (다크 테마 기반의 팝업 카드) */
QToolTip {
    background-color: rgba(15, 23, 42, 0.95); /* Slate 900 */
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    padding: 6px 10px;
    font-family: 'Malgun Gothic', sans-serif;
    font-size: 13px;
    font-weight: 500;
}

/* 9. 그룹박스 (옵션 패널 등) */
QGroupBox {
    border: 1px solid rgba(203, 213, 225, 0.6);
    border-radius: 10px;
    margin-top: 10px;
    background-color: rgba(255, 255, 255, 0.4);
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #64748b;
    font-weight: bold;
}

/* 10. 스플리터 (고정틀 경계선을 일반 테두리 색상과 동일하게 부드럽게 조정) */
QSplitter::handle {
    background-color: #cbd5e1; /* 밝은 회색 테두리 색상 적용 */
}
QSplitter::handle:horizontal {
    width: 2px;
}
QSplitter::handle:vertical {
    height: 2px;
}
"""