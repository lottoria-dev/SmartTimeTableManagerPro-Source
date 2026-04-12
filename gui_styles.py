# --- 스타일 및 설정 ---
STYLE_SHEET = """
/* 시스템 다크모드 무시 및 고급스러운 글래스모피즘(투명 글래스) 테마 적용 */
QWidget {
    font-family: "Segoe UI", "Apple Color Emoji", 'Pretendard', 'Malgun Gothic', sans-serif;
    color: #1e293b;
}

/* 메인 윈도우 프리미엄 배경 (세련된 쿨그레이 & 소프트 블루) */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #F4F7F9, 
                                stop:0.4 #FFFFFF, 
                                stop:1 #E2E8F0);
}

/* 라벨 기본 여백 제거 */
QLabel {
    background-color: transparent;
    padding: 0px; margin: 0px;
}

/* =========================================================
   [신규] 컨테이너 입체감(3D Bevel) 및 무채색(Gray) 효과 적용 
   ========================================================= */

/* 상단 버튼 영역 (부드러운 무채색 그라데이션 + 입체감 테두리) */
QFrame#TopPanel {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f9fafb, stop:1 #e5e7eb); /* 밝은 회색 ~ 짙은 회색 */
    border-top: 1px solid #ffffff;     /* 빛을 받는 윗면 하이라이트 */
    border-left: 1px solid #ffffff;
    border-right: 1px solid #d1d5db;   /* 그림자 지는 아랫면 */
    border-bottom: 1px solid #d1d5db;
    border-radius: 12px;
}

/* 메인 그리드 패널 (기존 화이트 반투명 유지하여 내부 콘텐츠 강조) */
QFrame#MainPanel {
    background-color: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-radius: 12px;
}

/* 보기 방식 라인 옵션 바 (상단 패널과 동일한 무채색 입체감 적용) */
QFrame#OptionBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f9fafb, stop:1 #e5e7eb);
    border-top: 1px solid #ffffff;
    border-left: 1px solid #ffffff;
    border-right: 1px solid #d1d5db;
    border-bottom: 1px solid #d1d5db;
    border-radius: 8px;
}
/* ========================================================= */


/* 상단 버튼 그룹 기본 스타일 (뚜렷한 글래스 효과) */
QPushButton {
    background-color: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(203, 213, 225, 0.8);
    border-radius: 6px;
    padding: 8px 16px; 
    min-height: 18px; 
    color: #1e293b;
    font-weight: normal; 
    font-size: 13px; 
    font-family: "Segoe UI", 'Malgun Gothic', sans-serif;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 1.0);
    border-color: #94a3b8;
    color: #0f172a;
}
QPushButton:pressed {
    background-color: rgba(241, 245, 249, 1.0);
    padding-top: 10px; padding-bottom: 6px;
}

/* 상단 버튼 일체감 통합 (기본 상태는 똑같이 맞추고 호버 시에만 은은한 톤 적용) */
QPushButton#PrimaryBtn, QPushButton#SuccessBtn, QPushButton#DangerBtn, QPushButton#InfoBtn {
    background-color: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(203, 213, 225, 0.8);
    color: #1e293b;
}
QPushButton#PrimaryBtn:hover { background-color: #f0f9ff; border-color: #7dd3fc; color: #0284c7; }
QPushButton#SuccessBtn:hover { background-color: #f0fdf4; border-color: #86efac; color: #16a34a; }
QPushButton#DangerBtn:hover { background-color: #fef2f2; border-color: #fca5a5; color: #dc2626; }
QPushButton#InfoBtn:hover { background-color: #eef2ff; border-color: #a5b4fc; color: #4f46e5; }


/* 모드 탭 버튼 */
QPushButton#ModeBtn {
    background-color: rgba(241, 245, 249, 0.6);
    color: #475569;
    border: 1px solid rgba(226, 232, 240, 0.8);
    padding: 8px 16px; 
    min-height: 18px;
    font-size: 13px;
    font-family: "Segoe UI", 'Malgun Gothic', sans-serif;
}
QPushButton#ModeBtn:hover { background-color: rgba(255, 255, 255, 0.9); color: #1e293b; }
QPushButton#ModeBtn:checked {
    background-color: #ffffff;
    color: #0ea5e9; 
    border: 1px solid #bae6fd;
    font-weight: normal; 
}


/* 콤보박스 글래스 효과 */
QComboBox {
    background-color: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(203, 213, 225, 0.8);
    border-radius: 6px; padding: 6px 10px;
    color: #1e293b; 
    font-weight: normal; 
    font-size: 13px;
}
QComboBox:hover { background-color: #ffffff; border-color: #94a3b8; }
QComboBox::drop-down { border: none; padding-right: 5px; }
QComboBox QAbstractItemView {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(203, 213, 225, 0.8);
    border-radius: 6px; selection-background-color: #e0f2fe; selection-color: #0284c7;
}

/* 체크박스 */
QCheckBox { background-color: transparent; color: #475569; font-size: 13px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    background-color: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.6);
    border-radius: 4px;
}
QCheckBox::indicator:hover { border-color: #3b82f6; }
QCheckBox::indicator:checked { background-color: #3b82f6; border-color: #2563eb; }

/* 보기 방식 탭(라디오 버튼) 세련된 상단 라인 스타일 */
QRadioButton {
    background-color: transparent;
    color: #475569;
    font-family: "Segoe UI", 'Malgun Gothic', sans-serif;
    font-weight: normal; 
    font-size: 13px;
    border: none;
    border-top: 3px solid transparent; 
    border-radius: 0px; 
    padding: 8px 14px;
    min-height: 18px;
    text-align: center;
    spacing: 0px; 
    margin: 0px;
}
QRadioButton::indicator {
    width: 0px; height: 0px; margin: 0px; padding: 0px; border: none; background: transparent;
}
QRadioButton:hover {
    background-color: rgba(241, 245, 249, 0.6);
    color: #1e293b;
    border-top: 3px solid #cbd5e1; 
}
QRadioButton:checked {
    background-color: rgba(255, 255, 255, 0.9); 
    color: #1e293b;
    border-top: 3px solid #f87171; 
}

/* =========================================================
   분산되었던 인라인 스타일 통합 관리 구역
   ========================================================= */

/* 상태 표시줄 */
QLabel#StatusBar {
    background-color: rgba(255, 255, 255, 0.65); 
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-radius: 6px; 
    font-weight: normal; 
    padding: 6px 12px; 
    font-size: 13px; 
    margin: 0px 4px;
}

/* 변경된 항목만 보기 체크박스 */
QCheckBox#OnlyChangedChk {
    font-weight: normal; color: #d97706; margin-left: 15px;
    background-color: rgba(255, 255, 255, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-radius: 6px;
    padding: 6px 10px; 
}
QCheckBox#OnlyChangedChk:hover { background-color: rgba(255, 255, 255, 0.85); }

/* 스플리터 (틀 고정용) */
QSplitter#HeaderSplitter::handle, QSplitter#MainSplitter::handle { 
    background-color: rgba(203, 213, 225, 0.5); 
    margin: 2px 0px; 
    border-radius: 2px; 
}

/* 그리드 셀 & 헤더 관련 */
QLabel#GridHeader {
    background-color: rgba(241, 245, 249, 0.85); 
    font-weight: 800;
    border: 1px solid rgba(226, 232, 240, 1.0);
    border-bottom: 2px solid rgba(203, 213, 225, 1.0);
    color: #1e293b; 
    border-radius: 6px; 
}
QLabel#EmptyCell {
    background-color: #ffffff; 
    border: 1px solid rgba(226, 232, 240, 1.0); 
    border-radius: 6px;
}
QLabel#SplitterLine {
    background-color: rgba(203, 213, 225, 0.4); 
    border-radius: 2px;
}
QLabel#EmptyMessage {
    font-size: 14px; font-weight: bold; color: #64748b; padding: 20px;
}
QLabel#SubjectMatchLabel {
    background-color: #ffffff; 
    border: 1px solid rgba(226, 232, 240, 1.0); 
    font-size: 12px; padding: 4px; border-radius: 6px; color: #1e293b;
}

/* 요일 제어 컨트롤 */
QWidget#DayControl { 
    background-color: rgba(248, 250, 252, 0.85); 
    border: 1px solid rgba(226, 232, 240, 1.0); 
    border-bottom: 2px solid rgba(203, 213, 225, 1.0);
    border-radius: 6px; 
}
QLabel#DayLabel {
    background-color: transparent; color: #1e293b; font-size: 13px;
}
QLabel#ExclLabel {
    background-color: transparent; font-size: 12px; font-weight: bold; color: #64748b;
}
QCheckBox#ExclCheck { 
    background-color: transparent; font-size: 12px; font-weight: bold; color: #475569; 
}
QCheckBox#ExclCheck::indicator { width: 14px; height: 14px; }
QPushButton#ReplaceBtn { 
    background-color: rgba(255, 255, 255, 0.9); color: #475569; 
    border: 1px solid rgba(203, 213, 225, 0.8); border-radius: 4px; 
    font-size: 12px; padding: 4px 8px; font-weight: normal; 
}
QPushButton#ReplaceBtn:hover { background-color: #f1f5f9; border-color: #0ea5e9; color: #0284c7; }

/* 맥OS 스타일 커스텀 스크롤바 */
QScrollBar:vertical { border: none; background: transparent; width: 10px; margin: 0px; }
QScrollBar::handle:vertical { background: rgba(148, 163, 184, 0.4); min-height: 30px; border-radius: 5px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: rgba(148, 163, 184, 0.7); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal { border: none; background: transparent; height: 10px; margin: 0px; }
QScrollBar::handle:horizontal { background: rgba(148, 163, 184, 0.4); min-width: 30px; border-radius: 5px; margin: 2px; }
QScrollBar::handle:horizontal:hover { background: rgba(148, 163, 184, 0.7); }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

/* 스크롤 영역 투명화 */
QScrollArea, QScrollArea > QWidget > QWidget { background-color: transparent; border: none; }

/* 트리 위젯 (로그창용) 고급화 */
QTreeWidget {
    background-color: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(203, 213, 225, 0.8);
    border-radius: 8px; outline: none;
}
QTreeWidget::item { height: 28px; border-bottom: 1px solid rgba(226, 232, 240, 0.5); }
QTreeWidget::item:selected { background-color: #e0f2fe; color: #0369a1; }
QHeaderView::section {
    background-color: #f8fafc;
    border: none; border-bottom: 1px solid rgba(203, 213, 225, 0.8);
    padding: 6px; font-weight: 800; color: #475569;
}

/* 툴팁 UI */
QToolTip {
    background-color: rgba(15, 23, 42, 0.9);
    color: #f8fafc; border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px; padding: 10px; font-size: 13px;
}

/* --- 다이얼로그 전용 배경 처리 --- */
QDialog, QMessageBox { background-color: #f8fafc; }
QMessageBox QLabel, QDialog QLabel {
    color: #1e293b; background-color: transparent; font-size: 13px;
}
QMessageBox QPushButton, QDialog QPushButton {
    background-color: #0ea5e9; color: #ffffff; border: none; border-radius: 6px;
    padding: 6px 16px; font-weight: normal; min-height: 18px; min-width: 60px;
}
QMessageBox QPushButton:hover, QDialog QPushButton:hover { background-color: #0284c7; }
"""

# 셀 배경색 단순화 (렌더링 최적화)
COLORS = {
    "cell_default": "#ffffff",
    "cell_locked": "#f1f5f9", 
    "cell_changed": "#fefcbf", 
    "cell_selected": "#dbeafe", 
    "cell_target": "#d1fae5", 
    "cell_conflict": "#fee2e2", 
    "cell_chain_src": "#f3e8ff",
    "cell_chain_tgt": "#e9d5ff",
    "cell_excluded": "#cbd5e1", 
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "accent": "#0ea5e9"
}