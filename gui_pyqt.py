import sys
import os
import re  
from datetime import datetime 
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QScrollArea, QGridLayout, 
    QComboBox, QMessageBox, QFileDialog, QSplitter, QButtonGroup, 
    QRadioButton, QCheckBox, QAbstractItemView, QSizePolicy, 
    QDialog, QTextEdit, QLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QMimeData 
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QKeyEvent, QCloseEvent

import config
from logic import TimetableLogic
from ai_mover import AIChainedMover

from gui_styles import STYLE_SHEET, COLORS
from gui_components import HelpDialog, ClickableFrame, LogDialog

class TimetableWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Timetable Manager Pro v1.2.0")
        self.resize(1400, 950)
        
        self.force_light_palette()
        self.setStyleSheet(STYLE_SHEET)

        # 로직 초기화
        self.logic = TimetableLogic()
        self.ai_mover = AIChainedMover(self.logic)

        # 상태 변수
        self.view_mode = "ALL_WEEK"
        self.work_mode = "VIEW"
        self.use_ai_mode = False
        
        self.swap_source = None
        self.swap_candidates = []
        self.highlighted_teachers = {}
        self.selected_cell_info = None
        self.last_swapped_cells = []
        
        self.chain_floating_data = None
        
        # 셀 위젯 관리 맵
        self.cell_widget_map = {}
        
        # [v1.2.0] 로그 다이얼로그 초기화
        self.log_dialog = LogDialog(self)

        self.init_ui()

    def force_light_palette(self):
        """시스템 다크모드를 무시하고 밝은 색상 테마를 강제 적용"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(31, 41, 55))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(249, 250, 251))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(31, 41, 55))
        palette.setColor(QPalette.ColorRole.Text, QColor(31, 41, 55))
        palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(31, 41, 55))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(59, 130, 246))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(59, 130, 246))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # [v1.2.0] 여백 최소화 (5 -> 2, Spacing 10 -> 5)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(5)

        # 1. 상단 컨트롤 패널 (Card)
        top_panel = QFrame()
        top_panel.setObjectName("Card")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(10)

        # [좌측] 버튼 그룹
        btn_group_layout = QHBoxLayout()
        btn_group_layout.setSpacing(5)
        
        self.btn_load = QPushButton("📂 불러오기")
        self.btn_load.clicked.connect(self.load_csv)
        self.btn_save = QPushButton("💾 저장")
        self.btn_save.clicked.connect(self.save_csv)
        self.btn_save.setObjectName("SuccessBtn")
        
        self.btn_copy = QPushButton("📋 복사")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_copy.setObjectName("InfoBtn")
        
        self.btn_undo = QPushButton("↩ 실행취소")
        self.btn_undo.clicked.connect(self.undo_action)
        self.btn_cancel = QPushButton("🚫 선택해제")
        self.btn_cancel.clicked.connect(self.cancel_action)
        self.btn_cancel.setObjectName("DangerBtn")
        
        btn_group_layout.addWidget(self.btn_load)
        btn_group_layout.addWidget(self.btn_save)
        btn_group_layout.addWidget(self.btn_copy) 
        btn_group_layout.addWidget(self.btn_undo)
        btn_group_layout.addWidget(self.btn_cancel)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.VLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        line1.setStyleSheet("color: #e5e7eb;")

        # [중앙] 모드 탭 버튼
        mode_group_layout = QHBoxLayout()
        mode_group_layout.setSpacing(5)
        
        self.mode_btn_group = QButtonGroup(self)
        self.mode_btn_group.setExclusive(True)
        self.mode_btn_group.buttonClicked.connect(self.on_mode_change)

        modes = [
            ("👁️ 조회모드", "VIEW", False),
            ("🔄 맞교환모드", "SWAP", False),
            ("🛠️ 보강모드", "COVER", False),
            ("🔗 연쇄모드", "CHAIN", False),
            ("🤖 AI자동", "CHAIN", True)
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
        line2.setStyleSheet("color: #e5e7eb;")

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
        btn_apply_cover = QPushButton("배정")
        btn_apply_cover.clicked.connect(self.execute_cover)
        btn_apply_cover.setObjectName("PrimaryBtn")
        cover_layout.addWidget(self.combo_cover_teacher)
        cover_layout.addWidget(btn_apply_cover)
        self.cover_widget.setVisible(False)
        self.context_layout.addWidget(self.cover_widget)

        top_layout.addLayout(btn_group_layout)
        top_layout.addWidget(line1)
        top_layout.addLayout(mode_group_layout)
        top_layout.addWidget(line2)
        top_layout.addWidget(self.context_stack)
        top_layout.addStretch()
        
        # [v1.2.0] 로그 버튼 추가
        btn_log = QPushButton("📜 내역")
        btn_log.clicked.connect(self.show_log_dialog)
        top_layout.addWidget(btn_log)

        btn_reset = QPushButton("초기화")
        btn_reset.clicked.connect(self.reset_all)
        top_layout.addWidget(btn_reset)
        
        btn_help = QPushButton("❓ 도움말")
        btn_help.clicked.connect(self.show_help)
        top_layout.addWidget(btn_help)

        main_layout.addWidget(top_panel)

        # 2. 메인 콘텐츠 (Splitter 제거 -> 단일 Grid Panel)
        # [v1.2.0] 로그창을 분리했으므로 Splitter 제거하고 Grid만 남김
        
        grid_group = QFrame()
        grid_group.setObjectName("Card")
        grid_group_layout = QVBoxLayout(grid_group)
        grid_group_layout.setContentsMargins(0, 0, 0, 0)

        option_bar = QFrame()
        option_bar.setStyleSheet("background-color: #f9fafb; border-bottom: 1px solid #e5e7eb;")
        option_layout = QHBoxLayout(option_bar)
        option_layout.setContentsMargins(10, 5, 10, 5) # 여백 축소
        option_layout.addWidget(QLabel("보기 방식:"))
        
        self.view_btn_group = QButtonGroup(self)
        self.view_btn_group.buttonClicked.connect(self.on_view_change)
        view_modes = [("주간 전체", "ALL_WEEK"), ("요일별", "ALL_DAY"), ("학급별", "SINGLE"), ("교사별", "TEACHER"), ("교과별", "SUBJECT")]
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
        option_layout.addStretch()

        grid_group_layout.addWidget(option_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.scroll_area.setWidget(self.grid_container)
        
        grid_group_layout.addWidget(self.scroll_area)
        
        self.status_bar = QLabel(" 파일을 불러와주세요.")
        self.status_bar.setFixedHeight(24) # 높이 축소
        self.status_bar.setStyleSheet("background-color: #ffffff; color: #3b82f6; font-weight: bold; padding-left: 10px; font-size: 11px;")
        grid_group_layout.addWidget(self.status_bar)

        main_layout.addWidget(grid_group)

    # [v1.2.0] 종료 시 저장 확인 로직
    def closeEvent(self, event: QCloseEvent):
        if self.logic.is_modified:
            reply = QMessageBox.question(
                self, "종료 확인",
                "변경된 내용이 저장되지 않았습니다.\n저장하고 종료하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.save_csv()
                # 저장 취소 시 종료도 취소
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

    # --- 기능 구현 ---
    def show_help(self):
        HelpDialog(self).exec()

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV 파일 열기", "", "CSV Files (*.csv)")
        if not file_path: return
        success, msg = self.logic.import_school_csv(file_path)
        if success:
            self.status_bar.setText(f"✅ {msg}")
            self.status_bar.setStyleSheet("color: #10b981; font-weight: bold; padding-left: 10px; font-size: 11px;")
            self.view_mode = "ALL_WEEK"
            self.refresh_selectors()
            self.refresh_grid()
            self.update_log_view()
        else:
            QMessageBox.critical(self, "오류", msg)

    def save_csv(self):
        if not self.logic.schedule: return
        
        current_time = datetime.now().strftime("%y%m%d%H%M%S")
        default_filename = f"timetable-{current_time}.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(self, "CSV 파일 저장", default_filename, "CSV Files (*.csv)")
        if not file_path: return
        success, msg = self.logic.export_csv(file_path)
        if success:
            self.status_bar.setText(f"💾 {msg}")
            QMessageBox.information(self, "완료", msg)
        else:
            QMessageBox.critical(self, "오류", msg)

    def copy_to_clipboard(self):
        if not self.logic.schedule:
            self.status_bar.setText("⚠️ 복사할 데이터가 없습니다.")
            return

        headers = []
        data_rows = []

        if self.view_mode == "ALL_WEEK":
            headers = ["학반"]
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    headers.append(f"{day}{p}")
            
            classes = self.logic.get_all_sorted_classes()
            for g, c in classes:
                row_items = [f"{g}-{c}"]
                for day in config.DAYS:
                    limit = config.PERIODS_PER_DAY[day]
                    for p in range(1, limit + 1):
                        data = self.logic.schedule[str(g)][str(c)][day].get(p)
                        if data:
                            row_items.append(f"{data['subject']} ({data['teacher']})")
                        else:
                            row_items.append("")
                data_rows.append(row_items)

        elif self.view_mode == "ALL_DAY":
            target_day = self.combo_sel.currentText() if hasattr(self, 'combo_sel') else config.DAYS[0]
            if not target_day: return
            
            headers = ["학반"]
            limit = config.PERIODS_PER_DAY[target_day]
            for p in range(1, limit + 1):
                headers.append(f"{p}교시")
            
            classes = self.logic.get_all_sorted_classes()
            for g, c in classes:
                row_items = [f"{g}-{c}"]
                for p in range(1, limit + 1):
                    data = self.logic.schedule[str(g)][str(c)][target_day].get(p)
                    if data:
                        row_items.append(f"{data['subject']} ({data['teacher']})")
                    else:
                        row_items.append("")
                data_rows.append(row_items)

        elif self.view_mode in ["SINGLE", "TEACHER", "SUBJECT"]:
            headers = ["교시"] + config.DAYS
            target_val = self.combo_sel.currentText()
            
            for p in range(1, config.MAX_PERIODS + 1):
                row_items = [f"{p}교시"]
                for day in config.DAYS:
                    if p > config.PERIODS_PER_DAY[day]:
                        row_items.append("")
                        continue

                    content = ""
                    if self.view_mode == "SINGLE":
                        try:
                            g, c = target_val.split('-')
                            data = self.logic.schedule[g][c][day].get(p)
                            if data: content = f"{data['subject']} ({data['teacher']})"
                        except: pass
                    elif self.view_mode == "TEACHER":
                         if target_val in self.logic.teachers_schedule:
                            if day in self.logic.teachers_schedule[target_val]:
                                if p in self.logic.teachers_schedule[target_val][day]:
                                    class_set = self.logic.teachers_schedule[target_val][day][p]
                                    if class_set:
                                        info = list(class_set)[0]
                                        content = f"{info[0]}-{info[1]} ({self.logic.schedule[str(info[0])][str(info[1])][day][p]['subject']})"
                    elif self.view_mode == "SUBJECT":
                        matches = []
                        classes = self.logic.get_all_sorted_classes()
                        for g, c in classes:
                            info = self.logic.schedule[str(g)][str(c)][day].get(p)
                            if info and self.is_subject_similar(info.get('subject'), target_val):
                                matches.append(f"{g}-{c}({info['teacher']})")
                        content = ", ".join(matches)
                    
                    row_items.append(content)
                data_rows.append(row_items)

        tsv_lines = ["\t".join(headers)]
        for row in data_rows:
            tsv_lines.append("\t".join(row))
        full_tsv = "\n".join(tsv_lines)

        html_parts = []
        html_parts.append('<meta charset="utf-8">') 
        html_parts.append('<table border="1" style="border-collapse: collapse;">')
        
        html_parts.append('<thead><tr>')
        for h in headers:
            html_parts.append(f'<th style="background-color: #f0f0f0; padding: 5px;">{h}</th>')
        html_parts.append('</tr></thead>')
        
        html_parts.append('<tbody>')
        for row in data_rows:
            html_parts.append('<tr>')
            for cell in row:
                safe_cell = str(cell).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_parts.append(f'<td style="mso-number-format:\'@\'; padding: 5px;">{safe_cell}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody></table>')
        
        full_html = "".join(html_parts)

        mime_data = QMimeData()
        mime_data.setText(full_tsv) 
        mime_data.setHtml(full_html) 

        QApplication.clipboard().setMimeData(mime_data)
        
        self.status_bar.setText("📋 복사 완료 (엑셀 날짜 변환 방지 적용)")
        self.status_bar.setStyleSheet("color: #6366f1; font-weight: bold; padding-left: 10px; font-size: 11px;")

    def undo_action(self):
        self.cancel_action()
        if self.logic.undo():
            self.update_cell_visuals()
            self.update_log_view()
            self.status_bar.setText("↩ 실행 취소 완료")
        else:
            self.status_bar.setText("⚠️ 더 이상 취소할 작업이 없습니다.")

    def cancel_action(self):
        self.swap_source = None
        self.swap_candidates = []
        self.selected_cell_info = None
        self.highlighted_teachers = {}
        if self.work_mode == "CHAIN" and self.chain_floating_data:
            data = self.chain_floating_data
            g, c = data['origin_gc']
            d, p = data['origin_time']
            if not self.logic.schedule[g][c][d].get(p):
                self.logic.add_class(g, c, d, p, data['subject'], data['teacher'])
            self.chain_floating_data = None
        self.combo_cover_teacher.clear()
        self.status_bar.setText("선택이 취소되었습니다.")
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
        self.cancel_action()
        self.work_mode = btn.property("mode_val")
        self.use_ai_mode = btn.property("use_ai")
        self.cover_widget.setVisible(False)
        msg = ""
        if self.work_mode == "VIEW": msg = "[조회 모드] 수업 클릭 시 교사의 모든 수업 강조.(우클릭 시 잠금)"
        elif self.work_mode == "SWAP": msg = "[맞교환 모드] 바꿀 두 수업을 순서대로 클릭.(교환 추천 시간은 초록색)"
        elif self.work_mode == "COVER":
            msg = "[보강 모드] 보강할 수업 선택."
            self.cover_widget.setVisible(True)
        elif self.work_mode == "CHAIN":
            msg = "[AI 자동 모드] 이동 시 연쇄 충돌 자동 해결." if self.use_ai_mode else "[연쇄 이동 모드] 수동으로 밀어내기 이동."
        self.status_bar.setText(msg)
        self.status_bar.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; padding-left: 10px; font-size: 11px;")
        self.update_cell_visuals()

    def on_view_change(self, btn):
        self.view_mode = btn.property("view_val")
        self.refresh_selectors()
        self.refresh_grid()

    # --- 그리드 렌더링 ---

    def refresh_selectors(self):
        for i in reversed(range(self.selector_layout.count())): 
            self.selector_layout.itemAt(i).widget().setParent(None)
        if self.view_mode == "ALL_DAY":
            self.selector_layout.addWidget(QLabel("요일:"))
            self.combo_sel = QComboBox()
            self.combo_sel.addItems(config.DAYS)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
        elif self.view_mode == "SINGLE":
            self.selector_layout.addWidget(QLabel("학급:"))
            self.combo_sel = QComboBox()
            
            classes = self.logic.get_all_sorted_classes()
            self.combo_sel.addItems([f"{g}-{c}" for g, c in classes])
            
            self.adjust_combo_width(self.combo_sel)
            
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
        elif self.view_mode == "TEACHER":
            self.selector_layout.addWidget(QLabel("교사:"))
            self.combo_sel = QComboBox()
            
            teachers = self.logic.get_all_teachers_sorted()
            self.combo_sel.addItems(teachers)
            
            self.adjust_combo_width(self.combo_sel)
            
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
        elif self.view_mode == "SUBJECT":
            self.selector_layout.addWidget(QLabel("교과:"))
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
            if w > width:
                width = w
        combo.setMinimumWidth(width + 40)

    def refresh_grid(self, _=None):
        old_widget = self.scroll_area.widget()
        if old_widget: old_widget.deleteLater()
            
        self.grid_container = QWidget()
        
        main_vbox = QVBoxLayout(self.grid_container)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)
        
        h_box = QHBoxLayout()
        h_box.setContentsMargins(0, 0, 0, 0)
        h_box.setSpacing(0)
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(1)
        self.grid_layout.setContentsMargins(1, 1, 1, 1)
        
        h_box.addLayout(self.grid_layout)
        h_box.addStretch(1) 
        
        main_vbox.addLayout(h_box)
        main_vbox.addStretch(1) 
        
        self.scroll_area.setWidget(self.grid_container)
        
        self.cell_widget_map.clear()
        
        if self.view_mode == "ALL_WEEK": self.render_all_week()
        elif self.view_mode == "ALL_DAY": self.render_all_day()
        elif self.view_mode == "SINGLE": self.render_single()
        elif self.view_mode == "TEACHER": self.render_teacher()
        elif self.view_mode == "SUBJECT": self.render_subject()

    def update_cell_visuals(self):
        for key, cell_widget in self.cell_widget_map.items():
            self._update_single_cell(cell_widget, key)

    def _update_single_cell(self, cell, key):
        grade, cls, day, period = key
        grade, cls = str(grade), str(cls)
        period = int(period)
        data = self.logic.schedule[grade][cls][day].get(period)
        
        main_text, sub_text = "", ""
        teacher_name = data['teacher'] if data else None

        if data:
            if self.view_mode == "TEACHER":
                main_text, sub_text = data['subject'], f"{grade}-{cls}"
            elif self.view_mode == "ALL_DAY":
                main_text = f"{data['subject']} ({teacher_name})"
            else:
                main_text, sub_text = data['subject'], teacher_name

        bg_color = COLORS["cell_default"]
        border_color = "#e5e7eb"
        border_width = 1
        text_color = "#1f2937" 

        if self.logic.is_locked(grade, cls, day, period):
            bg_color = COLORS["cell_locked"]
            main_text = "🔒 " + main_text
        if self.logic.is_changed(grade, cls, day, period):
            bg_color = COLORS["cell_changed"]

        if teacher_name:
            t_sched = self.logic.teachers_schedule.get(teacher_name, {})
            if day in t_sched and period in t_sched[day]:
                if len(t_sched[day][period]) > 1:
                    bg_color = COLORS["cell_conflict"] 

        if self.swap_source == key:
            bg_color = COLORS["cell_selected"]
            border_color, border_width = COLORS["accent"], 2
        elif self.work_mode == "SWAP" and self.swap_source:
             src_g, src_c, _, _ = self.swap_source
             if (grade, cls) == (src_g, src_c) and (day, period) in self.swap_candidates:
                 bg_color = COLORS["cell_target"]
                 border_color = "#10b981"
        elif self.work_mode == "COVER" and self.selected_cell_info == key:
            bg_color = COLORS["cell_conflict"]
            border_color, border_width = "#ef4444", 2
        elif self.work_mode == "CHAIN" and self.chain_floating_data:
            orig_g, orig_c = self.chain_floating_data['origin_gc']
            orig_d, orig_p = self.chain_floating_data['origin_time']
            floater = self.chain_floating_data['teacher']
            if key == (str(orig_g), str(orig_c), orig_d, orig_p):
                bg_color = COLORS["cell_chain_tgt"]
            elif (grade, cls) == (str(orig_g), str(orig_c)):
                 if not self.logic.is_locked(grade, cls, day, period):
                     if self.logic.is_teacher_busy(floater, day, period):
                         bg_color = COLORS["cell_conflict"]
                     else:
                         bg_color = COLORS["cell_target"]
            if teacher_name == floater:
                bg_color = COLORS["cell_chain_src"]

        if teacher_name and teacher_name in self.highlighted_teachers:
             if bg_color in [COLORS["cell_default"], COLORS["cell_locked"], COLORS["cell_changed"], COLORS["cell_conflict"]]:
                 bg_color = self.highlighted_teachers[teacher_name]
                 if bg_color == COLORS["cell_selected"]: border_color = COLORS["accent"]

        if teacher_name and self.is_consecutive_3(teacher_name, day, period):
             text_color = "#9333ea" 

        cell.set_content(main_text, sub_text, bg_color, border_color, border_width, text_color)

    def add_header(self, text, r, c, rowspan=1, colspan=1):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("background-color: #e5e7eb; font-weight: bold; border: 1px solid #d1d5db; color: #1f2937;")
        # [v1.2.0] 헤더 높이 축소 (30 -> 26)
        lbl.setMinimumHeight(26)
        if len(text) > 4: lbl.setMinimumWidth(80) 
        else: lbl.setMinimumWidth(40)
        self.grid_layout.addWidget(lbl, r, c, rowspan, colspan)

    def add_cell(self, grade, cls, day, period, r, c, rowspan=1, colspan=1):
        key = (str(grade), str(cls), day, int(period))
        cell = ClickableFrame(key)
        self._update_single_cell(cell, key)
        cell.clicked.connect(self.handle_cell_click)
        cell.right_clicked.connect(self.handle_right_click)
        self.grid_layout.addWidget(cell, r, c, rowspan, colspan)
        self.cell_widget_map[key] = cell

    def is_consecutive_3(self, teacher, day, period):
        return self.logic.check_consecutive_classes(teacher, day, period)
    
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

    # --- 핸들러 ---

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_action()
        else:
            super().keyPressEvent(event)

    def handle_cell_click(self, key):
        grade, cls, day, period = key
        grade, cls = str(grade), str(cls)
        cell_data = self.logic.schedule[grade][cls][day].get(period)
        clicked_teacher = cell_data['teacher'] if cell_data else None

        if clicked_teacher: self.highlighted_teachers = {clicked_teacher: COLORS["cell_selected"]}
        else: self.highlighted_teachers = {}

        if self.work_mode == "VIEW":
            is_locked = "🔒 " if self.logic.is_locked(grade, cls, day, period) else ""
            msg = f"{is_locked}선택: {clicked_teacher} ({cell_data['subject']})" if clicked_teacher else "빈 교시"
            self.status_bar.setText(msg)
        elif self.work_mode == "SWAP":
            if self.logic.is_locked(grade, cls, day, period):
                self.status_bar.setText("🔒 잠긴 수업입니다.")
                return
            if not self.swap_source:
                if not cell_data:
                    self.status_bar.setText("⚠️ 빈 교시는 선택할 수 없습니다.")
                    return
                self.swap_source = key
                self.swap_candidates = self.logic.get_swap_candidates(grade, cls, day, period)
                self.status_bar.setText(f"1단계: {clicked_teacher}. 이동할 위치(초록색 추천)를 선택하세요.")
            else:
                src_g, src_c, src_d, src_p = self.swap_source
                if key == self.swap_source:
                    self.cancel_action()
                    return
                if (grade, cls) != (src_g, src_c):
                    QMessageBox.warning(self, "오류", "같은 반 내에서만 교환 가능합니다.")
                    return
                if self.logic.is_locked(grade, cls, day, period):
                    QMessageBox.warning(self, "오류", "목표 대상이 잠겨있습니다.")
                    return
                self.logic.execute_swap(grade, cls, src_d, src_p, day, period)
                self.last_swapped_cells = [self.swap_source, key]
                self.swap_source = None
                self.swap_candidates = []
                self.status_bar.setText("✅ 교체 완료")
                self.update_log_view()
        elif self.work_mode == "COVER":
            if not cell_data: return
            if self.logic.is_locked(grade, cls, day, period):
                self.status_bar.setText("🔒 잠긴 수업입니다.")
                return
            self.selected_cell_info = key
            self.highlighted_teachers = {clicked_teacher: COLORS["cell_conflict"]}
            candidates = self.logic.get_cover_candidates(day, period)
            self.combo_cover_teacher.clear()
            if candidates:
                self.combo_cover_teacher.addItems(candidates)
                self.status_bar.setText(f"대상: {clicked_teacher}. 대체 교사를 선택하고 배정 버튼을 누르세요.")
            else:
                self.status_bar.setText("⚠️ 추천 가능한 교사가 없습니다.")
        elif self.work_mode == "CHAIN":
            if self.logic.is_locked(grade, cls, day, period): return
            if self.use_ai_mode:
                if not self.chain_floating_data:
                    if not cell_data: return
                    self.chain_floating_data = cell_data.copy()
                    self.chain_floating_data['origin_gc'] = (grade, cls)
                    self.chain_floating_data['origin_time'] = (day, period)
                    self.highlighted_teachers = {clicked_teacher: COLORS["cell_chain_src"]}
                    self.status_bar.setText(f"🤖 [AI] {clicked_teacher} 교사가 이동할 목표 위치를 클릭하세요.")
                else:
                    orig_g, orig_c = self.chain_floating_data['origin_gc']
                    orig_d, orig_p = self.chain_floating_data['origin_time']
                    if (grade, cls) != (orig_g, orig_c):
                        QMessageBox.warning(self, "오류", "같은 반 내에서 이동해야 합니다.")
                        return
                    success, msg, logs = self.ai_mover.try_ai_move(orig_g, orig_c, orig_d, orig_p, day, period)
                    if success: self.status_bar.setText(f"✅ {msg}")
                    else:
                        QMessageBox.warning(self, "AI 실패", msg)
                        self.status_bar.setText("AI 이동 실패")
                    self.chain_floating_data = None
                    self.update_log_view()
            else:
                if not self.chain_floating_data:
                    if not cell_data: return
                    self.logic.save_snapshot()
                    self.chain_floating_data = cell_data.copy()
                    self.chain_floating_data['origin_gc'] = (grade, cls)
                    self.chain_floating_data['origin_time'] = (day, period)
                    self.logic.remove_class(grade, cls, day, period)
                    self.highlighted_teachers = {clicked_teacher: COLORS["cell_chain_src"]}
                    self.status_bar.setText(f"🚀 [이동 중] {clicked_teacher}. 어디에 놓으시겠습니까?")
                else:
                    orig_g, orig_c = self.chain_floating_data['origin_gc']
                    if (grade, cls) != (orig_g, orig_c): return
                    floater = self.chain_floating_data
                    target_old_data = self.logic.schedule[grade][cls][day].get(period)
                    self.logic.save_snapshot()
                    self.logic.add_class(grade, cls, day, period, floater['subject'], floater['teacher'])
                    self.logic.change_logs.append({
                        "type": "연쇄", "class": f"{grade}-{cls}",
                        "desc": f"{floater['teacher']} → {day}{period} 이동",
                        "log_key": ("CHAIN", grade, cls, day, period)
                    })
                    if target_old_data:
                        self.chain_floating_data = target_old_data.copy()
                        self.chain_floating_data['origin_gc'] = (grade, cls)
                        self.chain_floating_data['origin_time'] = (day, period)
                        self.highlighted_teachers = {target_old_data['teacher']: COLORS["cell_chain_src"]}
                        self.status_bar.setText(f"🔄 [밀림] {target_old_data['teacher']} 교사를 다시 배치하세요.")
                    else:
                        self.chain_floating_data = None
                        self.status_bar.setText("✅ 이동 완료")
                    self.update_log_view()
        self.update_cell_visuals()

    def handle_right_click(self, key):
        grade, cls, day, period = key
        is_locked = self.logic.toggle_lock(grade, cls, day, period)
        msg = "🔒 잠금 설정" if is_locked else "🔓 잠금 해제"
        self.status_bar.setText(f"[{grade}-{cls} {day}{period}] {msg}")
        self.update_cell_visuals()

    def execute_cover(self):
        if not self.selected_cell_info: return
        new_teacher = self.combo_cover_teacher.currentText()
        if not new_teacher: return
        g, c, d, p = self.selected_cell_info
        self.logic.update_teacher(g, c, d, p, new_teacher)
        self.selected_cell_info = None
        self.combo_cover_teacher.clear()
        self.status_bar.setText(f"✅ 보강 완료: {new_teacher}")
        self.update_log_view()
        self.update_cell_visuals()

    def update_log_view(self):
        # [v1.2.0] 로그 다이얼로그 업데이트
        if hasattr(self.logic, 'get_diff_list'):
            logs = self.logic.get_diff_list()
        else:
            logs = self.logic.change_logs
        
        self.log_dialog.update_logs(logs)

    # --- 렌더링 함수 ---
    
    def render_all_week(self):
        self.add_header("학반", 0, 0)
        self.grid_layout.setColumnMinimumWidth(0, 80)
        
        classes = self.logic.get_all_sorted_classes()
        total_rows = len(classes) + 1  

        col = 1
        for day in config.DAYS:
            limit = config.PERIODS_PER_DAY[day]
            for p in range(1, limit + 1):
                self.add_header(f"{day}{p}", 0, col)
                col += 1
            if day != config.DAYS[-1]:
                lbl = QLabel()
                lbl.setFixedWidth(5)
                lbl.setStyleSheet("background-color: #d1d5db;")
                self.grid_layout.addWidget(lbl, 0, col, total_rows, 1)
                col += 1
        
        for r, (g, c) in enumerate(classes):
            row = r + 1
            self.add_header(f"{g}-{c}", row, 0)
            col = 1
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    self.add_cell(g, c, day, p, row, col)
                    col += 1
                if day != config.DAYS[-1]: col += 1

    def render_all_day(self):
        if not hasattr(self, 'combo_sel'): return
        target_day = self.combo_sel.currentText()
        if not target_day: return
        self.add_header("학반", 0, 0)
        self.grid_layout.setColumnMinimumWidth(0, 80)
        limit = config.PERIODS_PER_DAY[target_day]
        for p in range(1, limit + 1):
            self.add_header(f"{p}교시", 0, p)
        classes = self.logic.get_all_sorted_classes()
        for r, (g, c) in enumerate(classes):
            row = r + 1
            self.add_header(f"{g}-{c}", row, 0)
            for p in range(1, limit + 1):
                self.add_cell(g, c, target_day, p, row, p)

    def render_single(self):
        if not hasattr(self, 'combo_sel'): return
        cls_str = self.combo_sel.currentText()
        if not cls_str: return
        try: g, c = cls_str.split('-')
        except: return
        self.add_header("교시", 0, 0)
        for i, day in enumerate(config.DAYS):
            self.add_header(day, 0, i+1)
            self.grid_layout.setColumnMinimumWidth(i+1, 120)
        for p in range(1, config.MAX_PERIODS + 1):
            self.add_header(f"{p}교시", p, 0)
            for i, day in enumerate(config.DAYS):
                if p <= config.PERIODS_PER_DAY[day]:
                    self.add_cell(g, c, day, p, p, i+1)

    def render_teacher(self):
        if not hasattr(self, 'combo_sel'): return
        t_name = self.combo_sel.currentText()
        if not t_name: return
        self.add_header("교시", 0, 0)
        for i, day in enumerate(config.DAYS):
            self.add_header(day, 0, i+1)
            self.grid_layout.setColumnMinimumWidth(i+1, 120)
        for p in range(1, config.MAX_PERIODS + 1):
            self.add_header(f"{p}교시", p, 0)
            for i, day in enumerate(config.DAYS):
                found = False
                if t_name in self.logic.teachers_schedule:
                    if day in self.logic.teachers_schedule[t_name]:
                        if p in self.logic.teachers_schedule[t_name][day]:
                            class_set = self.logic.teachers_schedule[t_name][day][p]
                            if class_set:
                                info = list(class_set)[0]
                                g, c = str(info[0]), str(info[1])
                                self.add_cell(g, c, day, p, p, i+1)
                                found = True
                if not found and p <= config.PERIODS_PER_DAY[day]:
                    empty = QLabel()
                    empty.setStyleSheet(f"background-color: {COLORS['cell_default']}; border: 1px solid #e5e7eb;")
                    self.grid_layout.addWidget(empty, p, i+1)

    def render_subject(self):
        if not hasattr(self, 'combo_sel'): return
        subj_name = self.combo_sel.currentText()
        if not subj_name: return

        self.add_header("교시", 0, 0)
        for i, day in enumerate(config.DAYS):
            self.add_header(day, 0, i+1)
            self.grid_layout.setColumnMinimumWidth(i+1, 120)

        for p in range(1, config.MAX_PERIODS + 1):
            self.add_header(f"{p}교시", p, 0)
            for i, day in enumerate(config.DAYS):
                if p <= config.PERIODS_PER_DAY[day]:
                    matches = []
                    classes = self.logic.get_all_sorted_classes()
                    for g, c in classes:
                        day_sched = self.logic.schedule[str(g)][str(c)].get(day, {})
                        info = day_sched.get(p)
                        if info:
                            target_subject = info.get('subject')
                            if self.is_subject_similar(target_subject, subj_name):
                                matches.append(f"{g}-{c}({info['teacher']})")
                    
                    if matches:
                        lbl = QLabel("\n".join(matches))
                        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        lbl.setWordWrap(True)
                        lbl.setStyleSheet(f"background-color: {COLORS['cell_default']}; border: 1px solid #e5e7eb; font-size: 11px; padding: 2px;")
                        self.grid_layout.addWidget(lbl, p, i+1)
                    else:
                        empty = QLabel()
                        empty.setStyleSheet(f"background-color: {COLORS['cell_default']}; border: 1px solid #e5e7eb;")
                        self.grid_layout.addWidget(empty, p, i+1)