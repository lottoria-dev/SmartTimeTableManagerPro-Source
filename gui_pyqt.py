import sys
import os
import re  
from datetime import datetime 
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QScrollArea, QGridLayout, 
    QComboBox, QMessageBox, QFileDialog, QSplitter, QButtonGroup, 
    QRadioButton, QCheckBox, QAbstractItemView, QSizePolicy, 
    QDialog, QTextEdit, QLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData 
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QKeyEvent, QCloseEvent, QShortcut, QKeySequence

import config
from logic import TimetableLogic
from ai_mover import AIChainedMover

from gui_styles import STYLE_SHEET, COLORS
from gui_components import HelpDialog, ClickableFrame, LogDialog, DayRoutineDialog

from gui_clipboard import ClipboardManager
from gui_interaction import CellInteractionHandler
from gui_grid_renderer import GridRenderer

class TimetableWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Timetable Manager Pro v3.1.1")
        self.resize(1520, 780)
        
        self.force_light_palette()
        
        # [수정] 상단 패널(TopPanel)의 버튼들만 콕 집어서 세로 여백과 최소 높이를 줄이는 CSS 주입
        # [수정] QComboBox 내부에서 px 단위 사용 시 발생하는 QFont::setPointSize(-1) 경고를 원천 차단하기 위해 
        # 콤보박스 본체와 드롭다운 뷰 모두에 pt 단위를 강제로(!important) 덮어씌웁니다.
        slim_top_panel_css = """
            #TopPanel QPushButton, #TopPanel QPushButton#ModeBtn {
                padding: 5px 14px;
                min-height: 14px;
            }
            QComboBox, QComboBox QAbstractItemView {
                font-size: 10pt !important; 
            }
        """
        self.setStyleSheet(STYLE_SHEET + slim_top_panel_css) 

        self.logic = TimetableLogic()
        self.ai_mover = AIChainedMover(self.logic)

        self.view_mode = "ALL_WEEK"
        self.work_mode = "VIEW"
        self.use_ai_mode = False
        self.teacher_sort_mode = "과목순" 
        
        self.swap_source = None
        self.swap_candidates = []
        self.highlighted_teachers = {}
        self.selected_cell_info = None
        self.last_swapped_cells = []
        
        self.chain_floating_data = None
        self.cell_widget_map = {}
        
        # [신규] 렌더링 중복 방지 플래그
        self._block_visual_update = False
        
        self.log_dialog = LogDialog(self)
        
        self.clipboard_manager = ClipboardManager(self)
        self.interaction_handler = CellInteractionHandler(self)
        self.grid_renderer = GridRenderer(self)

        self.init_ui()
        self.init_shortcuts()

    def add_drop_shadow(self, widget, radius=15, alpha=20, offset=4):
        pass

    def init_shortcuts(self):
        self._shortcuts = [] 
        mapping = [
            ("Ctrl+O", self.load_csv),
            ("Ctrl+S", self.save_csv),
            ("Ctrl+Z", self.undo_action),
            ("Ctrl+C", self.copy_to_clipboard),
            ("Esc", self.cancel_action),
            ("1", lambda: self.set_mode_by_index(0)),
            ("2", lambda: self.set_mode_by_index(1)),
            ("3", lambda: self.set_mode_by_index(2)),
            ("4", lambda: self.set_mode_by_index(3)),
            ("5", lambda: self.set_mode_by_index(4))
        ]
        for key_str, func in mapping:
            shortcut = QShortcut(QKeySequence(key_str), self)
            shortcut.activated.connect(func)
            self._shortcuts.append(shortcut)
            
    def set_mode_by_index(self, idx):
        buttons = self.mode_btn_group.buttons()
        if 0 <= idx < len(buttons):
            buttons[idx].setChecked(True)
            self.on_mode_change(buttons[idx])

    def force_light_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 41, 59))
        palette.setColor(QPalette.ColorRole.Text, QColor(30, 41, 59))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 41, 59))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(30, 41, 59))
        self.setPalette(palette)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 1. 상단 컨트롤 패널
        top_panel = QFrame()
        top_panel.setObjectName("TopPanel")
        top_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.add_drop_shadow(top_panel, radius=10, alpha=10, offset=2)
        
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(15, 8, 15, 8) 
        top_layout.setSpacing(0) 
        
        # [좌측] 버튼 그룹
        btn_group_layout = QHBoxLayout()
        btn_group_layout.setSpacing(8)
        
        self.btn_load = QPushButton("불러오기")
        self.btn_load.clicked.connect(self.load_csv)
        self.btn_save = QPushButton("저장")
        self.btn_save.clicked.connect(self.save_csv)
        self.btn_save.setObjectName("SuccessBtn")
        
        self.btn_copy = QPushButton("복사")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_copy.setObjectName("InfoBtn")
        
        self.btn_undo = QPushButton("실행취소")
        self.btn_undo.clicked.connect(self.undo_action)
        self.btn_cancel = QPushButton("선택해제")
        self.btn_cancel.clicked.connect(self.cancel_action)
        self.btn_cancel.setObjectName("DangerBtn")

        for btn in [self.btn_load, self.btn_save, self.btn_copy, self.btn_undo, self.btn_cancel]:
            self.add_drop_shadow(btn, radius=4, alpha=10, offset=1)
            btn_group_layout.addWidget(btn)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.VLine)
        line1.setStyleSheet("border-left: 2px solid rgba(203, 213, 225, 0.6);")

        # [중앙] 모드 탭 버튼
        mode_group_layout = QHBoxLayout()
        mode_group_layout.setSpacing(6)
        
        self.mode_btn_group = QButtonGroup(self)
        self.mode_btn_group.setExclusive(True)
        self.mode_btn_group.buttonClicked.connect(self.on_mode_change)

        modes = [
            ("조회모드", "VIEW", False),
            ("맞교환모드", "SWAP", False),
            ("보강모드", "COVER", False),
            ("연쇄모드", "CHAIN", False),
            ("AI자동", "CHAIN", True)
        ]
        
        for text, val, use_ai in modes:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setObjectName("ModeBtn")
            btn.setProperty("mode_val", val)
            btn.setProperty("use_ai", use_ai)
            if val == "VIEW": btn.setChecked(True)
            self.mode_btn_group.addButton(btn)
            mode_group_layout.addWidget(btn)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.VLine)
        line2.setStyleSheet("border-left: 2px solid rgba(203, 213, 225, 0.6);")

        # [우측] 컨텍스트 옵션
        self.context_stack = QWidget()
        self.context_layout = QHBoxLayout(self.context_stack)
        self.context_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cover_widget = QWidget()
        cover_layout = QHBoxLayout(self.cover_widget)
        cover_layout.setContentsMargins(0, 0, 0, 0)
        cover_layout.addWidget(QLabel("대체 교사:"))
        self.combo_cover_teacher = QComboBox()
        self.combo_cover_teacher.setMinimumWidth(120)
        
        # [방어 코드 추가] 혹시 모를 내부 버그를 방지하기 위해 파이썬 측면에서도 폰트 단위를 pt로 초기화합니다.
        combo_font = self.combo_cover_teacher.font()
        combo_font.setPointSize(10)
        self.combo_cover_teacher.setFont(combo_font)
        
        btn_apply_cover = QPushButton("배정")
        btn_apply_cover.clicked.connect(self.execute_cover)
        btn_apply_cover.setObjectName("PrimaryBtn")
        self.add_drop_shadow(btn_apply_cover, radius=4, alpha=10, offset=1)
        cover_layout.addWidget(self.combo_cover_teacher)
        cover_layout.addWidget(btn_apply_cover)
        self.cover_widget.setVisible(False)
        self.context_layout.addWidget(self.cover_widget)

        top_layout.addLayout(btn_group_layout)
        top_layout.addSpacing(22)
        top_layout.addWidget(line1)
        top_layout.addSpacing(22)
        top_layout.addLayout(mode_group_layout)
        top_layout.addSpacing(22)
        top_layout.addWidget(line2)
        top_layout.addSpacing(22)
        top_layout.addWidget(self.context_stack)
        top_layout.addStretch()
        
        # 우측 보조 버튼들을 하나로 그룹화
        right_btn_layout = QHBoxLayout()
        right_btn_layout.setSpacing(8)
        
        btn_log = QPushButton("내역")
        btn_log.clicked.connect(self.show_log_dialog)
        self.add_drop_shadow(btn_log, radius=4, alpha=10, offset=1)
        right_btn_layout.addWidget(btn_log)

        btn_reset = QPushButton("초기화")
        btn_reset.clicked.connect(self.reset_all)
        self.add_drop_shadow(btn_reset, radius=4, alpha=10, offset=1)
        right_btn_layout.addWidget(btn_reset)
        
        btn_help = QPushButton("도움말")
        btn_help.clicked.connect(self.show_help)
        self.add_drop_shadow(btn_help, radius=4, alpha=10, offset=1)
        right_btn_layout.addWidget(btn_help)

        top_layout.addLayout(right_btn_layout)

        main_layout.addWidget(top_panel)

        # 2. 메인 콘텐츠
        grid_group = QFrame()
        grid_group.setObjectName("MainPanel")
        self.add_drop_shadow(grid_group, radius=12, alpha=8, offset=3)
        
        grid_group_layout = QVBoxLayout(grid_group)
        grid_group_layout.setContentsMargins(8, 8, 8, 8)
        grid_group_layout.setSpacing(8)

        option_bar = QFrame()
        option_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        option_bar.setObjectName("OptionBar") 
        self.add_drop_shadow(option_bar, radius=6, alpha=8, offset=2)
        
        option_layout = QHBoxLayout(option_bar)
        option_layout.setContentsMargins(12, 6, 12, 6) 
        lbl_view = QLabel("보기 방식:")
        lbl_view.setStyleSheet("font-weight: 800; color: #475569;")
        option_layout.addWidget(lbl_view)
        
        self.view_btn_group = QButtonGroup(self)
        self.view_btn_group.buttonClicked.connect(self.on_view_change)
        view_modes = [
            ("주간 전체", "ALL_WEEK"), 
            ("교사 전체", "ALL_TEACHER"),
            ("요일별", "ALL_DAY"), 
            ("학급별", "SINGLE"), 
            ("교사별", "TEACHER"), 
            ("교과별", "SUBJECT")
        ]
        for text, val in view_modes:
            rb = QRadioButton(text)
            rb.setProperty("view_val", val)
            if val == "ALL_WEEK": rb.setChecked(True)
            self.view_btn_group.addButton(rb)
            option_layout.addWidget(rb)
            
        option_layout.addSpacing(20)
        self.selector_stack = QWidget()
        self.selector_layout = QHBoxLayout(self.selector_stack)
        self.selector_layout.setContentsMargins(0, 0, 0, 0)
        option_layout.addWidget(self.selector_stack)
        
        self.chk_only_changed = QCheckBox("변경된 항목만 보기")
        self.chk_only_changed.stateChanged.connect(self.refresh_grid)
        self.chk_only_changed.setObjectName("OnlyChangedChk")
        option_layout.addWidget(self.chk_only_changed)
        
        option_layout.addSpacing(15)
        lbl_pinned = QLabel("틀 고정:")
        lbl_pinned.setStyleSheet("font-weight: 800; color: #475569;")
        option_layout.addWidget(lbl_pinned)
        self.combo_pinned_day = QComboBox()
        self.combo_pinned_day.addItem("고정 안함")
        self.combo_pinned_day.addItems(config.DAYS)
        self.combo_pinned_day.currentTextChanged.connect(self.refresh_grid)
        option_layout.addWidget(self.combo_pinned_day)

        option_layout.addStretch()

        grid_group_layout.addWidget(option_bar)

        # --- 상단 고정 헤더 영역 ---
        self.header_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.header_splitter.setHandleWidth(4)
        self.header_splitter.setObjectName("HeaderSplitter")
        self.header_splitter.setFixedHeight(78) 
        
        self.header_left_scroll = QScrollArea()
        self.header_left_scroll.setWidgetResizable(True)
        self.header_left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.header_left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header_left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.header_left_container = QWidget()
        self.header_left_layout = QGridLayout(self.header_left_container)
        self.header_left_scroll.setWidget(self.header_left_container)
        
        self.header_right_scroll = QScrollArea()
        self.header_right_scroll.setWidgetResizable(True)
        self.header_right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.header_right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header_right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.header_right_scroll.verticalScrollBar().setStyleSheet("width: 14px; background: transparent;")
        
        self.header_right_container = QWidget()
        self.header_right_layout = QGridLayout(self.header_right_container)
        self.header_right_scroll.setWidget(self.header_right_container)
        
        self.header_splitter.addWidget(self.header_left_scroll)
        self.header_splitter.addWidget(self.header_right_scroll)

        # --- 하단 메인 그리드 영역 ---
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(4)
        self.main_splitter.setObjectName("MainSplitter") 
        self.main_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.left_container = QWidget()
        self.left_layout = QGridLayout(self.left_container)
        self.left_scroll.setWidget(self.left_container)
        
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        self.right_container = QWidget()
        self.right_layout = QGridLayout(self.right_container)
        self.right_scroll.setWidget(self.right_container)
        
        self.main_splitter.addWidget(self.left_scroll)
        self.main_splitter.addWidget(self.right_scroll)

        # 동기화
        self.left_scroll.verticalScrollBar().valueChanged.connect(self.right_scroll.verticalScrollBar().setValue)
        self.right_scroll.verticalScrollBar().valueChanged.connect(self.left_scroll.verticalScrollBar().setValue)
        
        self.right_scroll.horizontalScrollBar().valueChanged.connect(self.header_right_scroll.horizontalScrollBar().setValue)
        self.left_scroll.horizontalScrollBar().valueChanged.connect(self.header_left_scroll.horizontalScrollBar().setValue)

        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.header_splitter.setStretchFactor(0, 0)
        self.header_splitter.setStretchFactor(1, 1)

        def sync_split(pos, idx, source):
            self.header_splitter.blockSignals(True)
            self.main_splitter.blockSignals(True)
            if source == 'main': self.header_splitter.moveSplitter(pos, idx)
            else: self.main_splitter.moveSplitter(pos, idx)
            self.header_splitter.blockSignals(False)
            self.main_splitter.blockSignals(False)
            
        self.main_splitter.splitterMoved.connect(lambda pos, idx: sync_split(pos, idx, 'main'))
        self.header_splitter.splitterMoved.connect(lambda pos, idx: sync_split(pos, idx, 'header'))

        grid_group_layout.addWidget(self.header_splitter)
        grid_group_layout.addWidget(self.main_splitter, 1)
        
        self.status_bar = QLabel(" 파일을 불러와주세요.")
        self.status_bar.setFixedHeight(28) 
        self.status_bar.setObjectName("StatusBar") 
        self.status_bar.setStyleSheet("color: #0284c7;") 
        grid_group_layout.addWidget(self.status_bar)

        main_layout.addWidget(grid_group, 1)

    def closeEvent(self, event: QCloseEvent):
        if self.logic.is_modified:
            reply = QMessageBox.question(
                self, "종료 확인", "변경된 내용이 저장되지 않았습니다.\n저장하고 종료하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.save_csv()
                if self.logic.is_modified: 
                    event.ignore()
                    return
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def show_log_dialog(self):
        self.log_dialog.show()
        self.log_dialog.raise_()
        self.log_dialog.activateWindow()

    def show_help(self):
        HelpDialog(self).exec()

    def toggle_excluded_grade(self, day, base_grade, is_checked):
        if is_checked: self.logic.excluded_groups[day].add(base_grade)
        else: self.logic.excluded_groups[day].discard(base_grade)
        
        self.update_cell_visuals()
        self.update_log_view()

    def change_day_routine_for(self, target_day):
        dialog = DayRoutineDialog(target_day, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            src_day = dialog.get_source_day()
            if src_day == target_day:
                QMessageBox.warning(self, "오류", "같은 요일로는 변경할 수 없습니다.")
                return
            
            old_limit = config.PERIODS_PER_DAY.get(target_day, 7)
            new_limit = config.PERIODS_PER_DAY.get(src_day, 7)
            
            reply = QMessageBox.question(
                self, "일과 변경 확인",
                f"[{target_day}]의 기존 시간표가 모두 삭제되고\n[{src_day}]의 '기초 시간표(결보강 제외)'로 덮어써집니다.\n\n"
                f"※ {target_day}의 교시 수 또한 {src_day}에 맞춰집니다.\n계속하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.logic.apply_day_routine(src_day, target_day)
                
                if old_limit == new_limit: self.update_cell_visuals()
                else: self.refresh_grid()
                
                self.update_log_view()
                self.status_bar.setText(f"🔄 {target_day} 일과가 {src_day}(기초 시간표)로 변경되었습니다.")
                QMessageBox.information(self, "완료", f"{target_day} 일과 변경이 완료되었습니다.")

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV 파일 열기", "", "CSV Files (*.csv)")
        if not file_path: return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            success, msg = self.logic.import_school_csv(file_path)
        finally:
            QApplication.restoreOverrideCursor()
            
        if success:
            self.status_bar.setText(f"✅ {msg}")
            self.status_bar.setStyleSheet("color: #059669;")
            self.view_mode = "ALL_WEEK"
            for btn in self.view_btn_group.buttons():
                if btn.property("view_val") == "ALL_WEEK":
                    btn.setChecked(True)
                    break
            self.refresh_selectors()
            self.refresh_grid()
            self.update_log_view()
        else:
            QMessageBox.critical(self, "오류", msg)

    def save_csv(self):
        if not self.logic.schedule: return
        current_time = datetime.now().strftime("%y%m%d%H%M%S")
        file_path, _ = QFileDialog.getSaveFileName(self, "CSV 파일 저장", f"timetable-{current_time}.csv", "CSV Files (*.csv)")
        if not file_path: return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            success, msg = self.logic.export_csv(file_path)
        finally:
            QApplication.restoreOverrideCursor()
            
        if success:
            self.status_bar.setText(f"💾 {msg}")
            QMessageBox.information(self, "완료", msg)
        else:
            QMessageBox.critical(self, "오류", msg)

    def undo_action(self):
        self.cancel_action()
        if self.logic.undo():
            self.refresh_grid()
            self.update_log_view()
            self.status_bar.setText("↩ 실행 취소 완료")
        else:
            self.status_bar.setText("⚠️ 더 이상 취소할 작업이 없습니다.")

    def cancel_action(self):
        self.swap_source = None
        self.swap_candidates = []
        self.selected_cell_info = None
        self.highlighted_teachers = {}
        data_changed = False  
        
        if self.work_mode == "CHAIN" and self.chain_floating_data:
            data = self.chain_floating_data
            g, c = data['origin_gc']
            d, p = data['origin_time']
            if not self.logic.schedule[g][c][d].get(p):
                self.logic.add_class(g, c, d, p, data['subject'], data['teacher'])
                data_changed = True  
            self.chain_floating_data = None
            
        self.combo_cover_teacher.clear()
        self.status_bar.setText("선택이 취소되었습니다.")
        
        if data_changed and hasattr(self, 'chk_only_changed') and self.chk_only_changed.isChecked():
            self.refresh_grid()
        else:
            self.update_cell_visuals()

    def reset_all(self):
        if not self.logic.original_schedule: return
        res = QMessageBox.question(self, "전체 초기화", "모든 변경 사항을 취소하시겠습니까?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            if self.logic.restore_original_state():
                self.cancel_action()
                self.refresh_grid()
                self.update_log_view()
                self.status_bar.setText("🔄 초기화 완료")

    def on_mode_change(self, btn):
        # [핵심 수정] 모드 전환 시 중복 렌더링을 방지하여 딜레이 제거
        self._block_visual_update = True
        self.cancel_action()
        self._block_visual_update = False
        
        self.work_mode = btn.property("mode_val")
        self.use_ai_mode = btn.property("use_ai")
        self.cover_widget.setVisible(False)
        msg = ""
        if self.work_mode == "VIEW": msg = "🔍 [조회 모드] 수업 클릭 시 교사 일정 강조. 우클릭 시 잠금 설정."
        elif self.work_mode == "SWAP": msg = "🔄 [맞교환 모드] 바꿀 두 수업을 순서대로 클릭하거나 드래그하세요."
        elif self.work_mode == "COVER":
            msg = "👤 [보강 모드] 보강할 수업을 선택하세요."
            self.cover_widget.setVisible(True)
        elif self.work_mode == "CHAIN":
            msg = "✨ [AI 자동 모드] 지정 시 연쇄 충돌 자동 해결." if self.use_ai_mode else "🔗 [연쇄 이동 모드] 수동으로 밀어내기 이동합니다."
        
        self.status_bar.setText(msg)
        self.status_bar.setStyleSheet(f"color: {COLORS['accent']};") 
        self.update_cell_visuals() # 단 1회만 일괄 반영

    def on_view_change(self, btn):
        self.view_mode = btn.property("view_val")
        self.refresh_selectors()
        self.refresh_grid()

    def update_log_view(self):
        logs = self.logic.get_diff_list() if hasattr(self.logic, 'get_diff_list') else self.logic.change_logs
        self.log_dialog.update_logs(logs)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_action()
        else:
            super().keyPressEvent(event)

    def refresh_selectors(self):
        for i in reversed(range(self.selector_layout.count())): 
            self.selector_layout.itemAt(i).widget().setParent(None)
            
        if self.view_mode == "ALL_DAY":
            lbl = QLabel("요일:")
            lbl.setStyleSheet("font-weight: bold; color: #475569;")
            self.selector_layout.addWidget(lbl)
            self.combo_sel = QComboBox()
            self.combo_sel.addItems(config.DAYS)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
            
        elif self.view_mode == "ALL_TEACHER":
            lbl = QLabel("정렬:")
            lbl.setStyleSheet("font-weight: bold; color: #475569;")
            self.selector_layout.addWidget(lbl)
            self.combo_sel = QComboBox()
            self.combo_sel.addItems(["과목순", "이름순", "시수 많은순", "시수 적은순"])
            self.combo_sel.setCurrentText(self.teacher_sort_mode)
            self.adjust_combo_width(self.combo_sel)
            
            def on_teacher_sort_change(text):
                self.teacher_sort_mode = text
                self.refresh_grid()
                
            self.combo_sel.currentTextChanged.connect(on_teacher_sort_change)
            self.selector_layout.addWidget(self.combo_sel)

        elif self.view_mode == "SINGLE":
            lbl = QLabel("학급:")
            lbl.setStyleSheet("font-weight: bold; color: #475569;")
            self.selector_layout.addWidget(lbl)
            self.combo_sel = QComboBox()
            classes = self.logic.get_all_sorted_classes()
            self.combo_sel.addItems([f"{g}-{c}" for g, c in classes])
            self.adjust_combo_width(self.combo_sel)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
            
        elif self.view_mode == "TEACHER":
            lbl = QLabel("교사:")
            lbl.setStyleSheet("font-weight: bold; color: #475569;")
            self.selector_layout.addWidget(lbl)
            self.combo_sel = QComboBox()
            teachers = self.logic.get_all_teachers_sorted()
            self.combo_sel.addItems(teachers)
            self.adjust_combo_width(self.combo_sel)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
            
        elif self.view_mode == "SUBJECT":
            lbl = QLabel("교과:")
            lbl.setStyleSheet("font-weight: bold; color: #475569;")
            self.selector_layout.addWidget(lbl)
            self.combo_sel = QComboBox()
            
            all_subjects = set()
            if self.logic.schedule:
                for g_data in self.logic.schedule.values():
                    for c_data in g_data.values():
                        for day_data in c_data.values():
                            for info in day_data.values():
                                if info and 'subject' in info:
                                    all_subjects.add(info['subject'])
            
            def subject_sort_key(s):
                has_alnum = any(c.isascii() and c.isalnum() for c in s)
                return (has_alnum, len(s), s)

            sorted_subjects = sorted(list(all_subjects), key=subject_sort_key)
            representatives = []

            for subj in sorted_subjects:
                is_covered = False
                for rep in representatives:
                    if self.is_subject_similar(rep, subj):
                        is_covered = True
                        break
                if not is_covered:
                    representatives.append(subj)
            
            representatives.sort()
            self.combo_sel.addItems(representatives)
            self.adjust_combo_width(self.combo_sel)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)

    def adjust_combo_width(self, combo):
        width = 0
        fm = combo.fontMetrics()
        for i in range(combo.count()):
            w = fm.horizontalAdvance(combo.itemText(i))
            if w > width: width = w
        combo.setMinimumWidth(width + 40)

    def is_subject_similar(self, target, selected):
        if not target or not selected: return False
        t = target.replace(" ", "")
        s = selected.replace(" ", "")
        
        if t == s: return True
        if s in t or t in s: return True
        
        if t[0] == s[0]:
            has_extra_t = any(c.isascii() and c.isalnum() for c in t)
            has_extra_s = any(c.isascii() and c.isalnum() for c in s)
            if has_extra_t or has_extra_s:
                return True
        return False

    def copy_to_clipboard(self): self.clipboard_manager.copy_to_clipboard()
    def copy_stats_to_clipboard(self): self.clipboard_manager.copy_stats_to_clipboard()

    def refresh_grid(self, _=None):
        self.setUpdatesEnabled(False)
        try:
            self.grid_renderer.refresh_grid(_)
        finally:
            self.setUpdatesEnabled(True)

    def update_cell_visuals(self): 
        # [핵심 수정] 차단 플래그가 켜져있으면 렌더링 무시
        if getattr(self, '_block_visual_update', False):
            return
        self.setUpdatesEnabled(False)
        try:
            self.grid_renderer.update_cell_visuals()
        finally:
            self.setUpdatesEnabled(True)

    def execute_cover(self):
        self.interaction_handler.execute_cover()
        self.refresh_grid()
        self.update_log_view()