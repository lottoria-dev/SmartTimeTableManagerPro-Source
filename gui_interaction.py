from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt
from gui_styles import COLORS

class CellInteractionHandler:
    """그리드 셀 클릭 및 작업 모드별 비즈니스 로직을 분리한 클래스"""
    def __init__(self, main_window):
        self.mw = main_window

    def handle_cell_click(self, key):
        data_changed = False 

        if isinstance(key, tuple) and key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = key
            locations = list(self.mw.logic.teachers_schedule.get(teacher_name, {}).get(day, {}).get(period, set()))
            
            if locations:
                g, c = locations[0]
                key = (str(g), str(c), day, period)
            else:
                if self.mw.work_mode == "CHAIN" and self.mw.chain_floating_data:
                    orig_g, orig_c = self.mw.chain_floating_data['origin_gc']
                    floater_teacher = self.mw.chain_floating_data['teacher']
                    if teacher_name != floater_teacher:
                        QMessageBox.warning(self.mw, "오류", f"해당 수업은 {floater_teacher} 선생님의 수업입니다.\n{floater_teacher} 선생님의 행에만 배치할 수 있습니다.")
                        return
                    key = (orig_g, orig_c, day, period)
                else:
                    self.mw.status_bar.setText("⚠️ 빈 시간입니다.")
                    return
                    
        grade, cls, day, period = key
        grade, cls = str(grade), str(cls)
        cell_data = self.mw.logic.schedule[grade][cls][day].get(period)
        clicked_teacher = cell_data['teacher'] if cell_data else None

        if clicked_teacher: self.mw.highlighted_teachers = {clicked_teacher: COLORS["cell_selected"]}
        else: self.mw.highlighted_teachers = {}

        if self.mw.work_mode == "VIEW":
            is_locked = "🔒 " if self.mw.logic.is_locked(grade, cls, day, period) else ""
            msg = f"{is_locked}선택: {clicked_teacher} ({cell_data['subject']})" if clicked_teacher else "빈 교시"
            self.mw.status_bar.setText(msg)
            
        elif self.mw.work_mode == "SWAP":
            if self.mw.logic.is_locked(grade, cls, day, period):
                self.mw.status_bar.setText("🔒 잠긴 수업입니다.")
                return
            if not self.mw.swap_source:
                if not cell_data:
                    self.mw.status_bar.setText("⚠️ 빈 교시는 선택할 수 없습니다.")
                    return
                self.mw.swap_source = key
                self.mw.swap_candidates = self.mw.logic.get_swap_candidates(grade, cls, day, period)
                self.mw.status_bar.setText(f"1단계: {clicked_teacher}. 이동할 위치(초록색)를 클릭하거나 드래그하세요.")
            else:
                src_g, src_c, src_d, src_p = self.mw.swap_source
                if key == self.mw.swap_source:
                    self.mw.cancel_action()
                    return
                if (grade, cls) != (src_g, src_c):
                    QMessageBox.warning(self.mw, "오류", "같은 반 내에서만 교환 가능합니다.")
                    return
                if self.mw.logic.is_locked(grade, cls, day, period):
                    QMessageBox.warning(self.mw, "오류", "목표 대상이 잠겨있습니다.")
                    return

                src_data = self.mw.logic.schedule[src_g][src_c][src_d].get(src_p)
                tgt_data = self.mw.logic.schedule[grade][cls][day].get(period)

                src_teacher = src_data['teacher'] if src_data else None
                tgt_teacher = tgt_data['teacher'] if tgt_data else None

                warnings = []
                if src_teacher and self.mw.logic.check_consecutive_classes(src_teacher, day, period):
                    warnings.append(f"'{src_teacher}' 교사의 3연강이 발생합니다. ({day} {period}교시)")
                if tgt_teacher and self.mw.logic.check_consecutive_classes(tgt_teacher, src_d, src_p):
                    warnings.append(f"'{tgt_teacher}' 교사의 3연강이 발생합니다. ({src_d} {src_p}교시)")

                if warnings:
                    msg_text = "\n".join(warnings) + "\n\n그래도 교환하시겠습니까?"
                    reply = QMessageBox.question(self.mw, "3연강 경고", msg_text, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        self.mw.cancel_action() 
                        return

                self.mw.logic.execute_swap(grade, cls, src_d, src_p, day, period)
                data_changed = True  
                self.mw.last_swapped_cells = [self.mw.swap_source, key]
                self.mw.swap_source = None
                self.mw.swap_candidates = []
                self.mw.highlighted_teachers = {} # 교환 완료 후 선택 하이라이트 해제
                self.mw.status_bar.setText("✅ 교체 완료")
                self.mw.update_log_view()
                
        elif self.mw.work_mode == "COVER":
            if not cell_data: return
            if self.mw.logic.is_locked(grade, cls, day, period):
                self.mw.status_bar.setText("🔒 잠긴 수업입니다.")
                return
            self.mw.selected_cell_info = key
            self.mw.highlighted_teachers = {clicked_teacher: COLORS["cell_conflict"]}
            candidates = self.mw.logic.get_cover_candidates(day, period)
            self.mw.combo_cover_teacher.clear()
            if candidates:
                self.mw.combo_cover_teacher.addItems(candidates)
                self.mw.status_bar.setText(f"대상: {clicked_teacher}. 대체 교사를 선택하고 배정 버튼을 누르세요.")
            else:
                self.mw.status_bar.setText("⚠️ 추천 가능한 교사가 없습니다.")
                
        elif self.mw.work_mode == "CHAIN":
            if self.mw.logic.is_locked(grade, cls, day, period): return
            if self.mw.use_ai_mode:
                if not self.mw.chain_floating_data:
                    if not cell_data: return
                    self.mw.chain_floating_data = cell_data.copy()
                    self.mw.chain_floating_data['origin_gc'] = (grade, cls)
                    self.mw.chain_floating_data['origin_time'] = (day, period)
                    self.mw.highlighted_teachers = {clicked_teacher: COLORS["cell_chain_src"]}
                    self.mw.status_bar.setText(f"🤖 [AI] {clicked_teacher} 교사가 이동할 목표 위치를 클릭하거나 드래그하세요.")
                else:
                    orig_g, orig_c = self.mw.chain_floating_data['origin_gc']
                    orig_d, orig_p = self.mw.chain_floating_data['origin_time']
                    if (grade, cls) != (orig_g, orig_c):
                        QMessageBox.warning(self.mw, "오류", "같은 반 내에서 이동해야 합니다.")
                        return
                    
                    if day != orig_d:
                        QMessageBox.warning(self.mw, "안내", "AI 자동 연쇄 이동은 현재 같은 요일 내에서만 지원됩니다.\n다른 요일로의 이동은 수동 연쇄 모드를 이용해 주세요.")
                        return                     
                    
                    # [업데이트] 연쇄/AI 처리 시간에 모래시계 커서 적용
                    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                    try:
                        success, msg, logs = self.mw.ai_mover.try_ai_move(orig_g, orig_c, orig_d, orig_p, day, period)
                    finally:
                        QApplication.restoreOverrideCursor()

                    if success: 
                        self.mw.status_bar.setText(f"✅ {msg}")
                        data_changed = True  
                    else:
                        friendly_msg = (
                            f"🤖 AI가 모든 경우의 수를 탐색했지만 연쇄 이동을 완료하지 못했습니다.\n\n"
                            f"🔍 원인: {msg}\n\n"
                            f"💡 이렇게 해보시는 건 어떨까요?\n"
                            f"  1. 수동 '🔗 연쇄모드'로 전환하여 직접 빈자리를 찾거나 다른 요일로 넘겨보세요.\n"
                            f"  2. '🔄 맞교환모드'를 사용해 비어있는 시간이나 충돌이 없는 다른 수업과 1:1로 교환해보세요.\n"
                            f"  3. 이동하려는 흐름 중간에 🔒 고정(잠금)된 수업이 길을 막고 있는지 확인해보세요."
                        )
                        QMessageBox.warning(self.mw, "AI 자동 이동 안내", friendly_msg)
                        self.mw.status_bar.setText("⚠️ AI 이동 실패: 다른 이동 방식을 추천합니다.")
                        
                    self.mw.chain_floating_data = None
                    self.mw.highlighted_teachers = {}
                    self.mw.update_log_view()
            else:
                if not self.mw.chain_floating_data:
                    if not cell_data: return
                    self.mw.logic.save_snapshot()
                    self.mw.chain_floating_data = cell_data.copy()
                    self.mw.chain_floating_data['origin_gc'] = (grade, cls)
                    self.mw.chain_floating_data['origin_time'] = (day, period)
                    self.mw.logic.remove_class(grade, cls, day, period)
                    data_changed = True  
                    self.mw.highlighted_teachers = {clicked_teacher: COLORS["cell_chain_src"]}
                    self.mw.status_bar.setText(f"🚀 [이동 중] {clicked_teacher}. 어디에 놓으시겠습니까?")
                else:
                    orig_g, orig_c = self.mw.chain_floating_data['origin_gc']
                    if (grade, cls) != (orig_g, orig_c): return
                    floater = self.mw.chain_floating_data

                    floater_teacher = floater['teacher']
                    if floater_teacher and self.mw.logic.check_consecutive_classes(floater_teacher, day, period):
                        reply = QMessageBox.question(
                            self.mw, "3연강 경고",
                            f"'{floater_teacher}' 교사의 3연강이 발생합니다. ({day} {period}교시)\n\n그래도 이동하시겠습니까?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.No:
                            return 

                    target_old_data = self.mw.logic.schedule[grade][cls][day].get(period)
                    self.mw.logic.save_snapshot()
                    self.mw.logic.add_class(grade, cls, day, period, floater['subject'], floater['teacher'])
                    data_changed = True  
                    self.mw.logic.change_logs.append({
                        "type": "연쇄", "class": f"{grade}-{cls}",
                        "desc": f"{floater['teacher']} → {day}{period} 이동",
                        "log_key": ("CHAIN", grade, cls, day, period)
                    })
                    if target_old_data:
                        self.mw.chain_floating_data = target_old_data.copy()
                        self.mw.chain_floating_data['origin_gc'] = (grade, cls)
                        self.mw.chain_floating_data['origin_time'] = (day, period)
                        self.mw.highlighted_teachers = {target_old_data['teacher']: COLORS["cell_chain_src"]}
                        self.mw.status_bar.setText(f"🔄 [밀림] {target_old_data['teacher']} 교사를 다시 배치하세요.")
                    else:
                        self.mw.chain_floating_data = None
                        self.mw.status_bar.setText("✅ 이동 완료")
                        self.mw.highlighted_teachers = {}
                    self.mw.update_log_view()
                    
        if data_changed and hasattr(self.mw, 'chk_only_changed') and self.mw.chk_only_changed.isChecked():
            self.mw.refresh_grid()
        else:
            self.mw.update_cell_visuals()

    # [추가] 드래그 앤 드롭으로 셀 이동이 완료되었을 때 실행되는 로직
    def handle_cell_drop(self, src_key, tgt_key):
        if src_key == tgt_key:
            return
            
        # 출발지 및 목적지 키 파싱
        if isinstance(src_key, tuple) and src_key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = src_key
            locations = list(self.mw.logic.teachers_schedule.get(teacher_name, {}).get(day, {}).get(period, set()))
            if locations:
                g, c = locations[0]
                src_key = (str(g), str(c), day, period)
            else: return
                
        if isinstance(tgt_key, tuple) and tgt_key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = tgt_key
            locations = list(self.mw.logic.teachers_schedule.get(teacher_name, {}).get(day, {}).get(period, set()))
            if locations:
                g, c = locations[0]
                tgt_key = (str(g), str(c), day, period)
            else:
                self.mw.status_bar.setText("⚠️ 해당 뷰에서는 빈 셀로의 드래그 앤 드롭을 지원하지 않습니다.")
                return
        
        src_g, src_c, src_d, src_p = src_key
        tgt_g, tgt_c, tgt_d, tgt_p = tgt_key
        
        src_g, src_c = str(src_g), str(src_c)
        tgt_g, tgt_c = str(tgt_g), str(tgt_c)
        
        # 현재 선택된 모드를 기반으로 직관적인 드래그 액션 처리
        if self.mw.work_mode == "SWAP":
            if (src_g, src_c) != (tgt_g, tgt_c):
                QMessageBox.warning(self.mw, "오류", "같은 반 내에서만 교환 가능합니다.")
                return
            if self.mw.logic.is_locked(src_g, src_c, src_d, src_p) or self.mw.logic.is_locked(tgt_g, tgt_c, tgt_d, tgt_p):
                QMessageBox.warning(self.mw, "오류", "잠겨있는 수업은 교환할 수 없습니다.")
                return
            
            # 3연강 경고 생략 후 바로 처리 (드래그 앤 드롭의 신속성을 위해)
            self.mw.logic.execute_swap(src_g, src_c, src_d, src_p, tgt_d, tgt_p)
            self.mw.status_bar.setText("✅ 드래그 앤 드롭: 맞교환 완료")
            self.mw.cancel_action()
            
        elif self.mw.work_mode == "CHAIN" and self.mw.use_ai_mode:
            if (src_g, src_c) != (tgt_g, tgt_c):
                QMessageBox.warning(self.mw, "오류", "같은 반 내에서 이동해야 합니다.")
                return
            if src_d != tgt_d:
                QMessageBox.warning(self.mw, "안내", "AI 자동 이동은 현재 같은 요일 내에서만 지원됩니다.")
                return
            
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                success, msg, logs = self.mw.ai_mover.try_ai_move(src_g, src_c, src_d, src_p, tgt_d, tgt_p)
            finally:
                QApplication.restoreOverrideCursor()
                
            if success:
                self.mw.status_bar.setText(f"✅ 드래그 앤 드롭: {msg}")
            else:
                QMessageBox.warning(self.mw, "AI 자동 이동 안내", msg)
            self.mw.cancel_action()
            
        else:
            # 기본적으로 수동 연쇄(이동)으로 처리
            if (src_g, src_c) != (tgt_g, tgt_c):
                QMessageBox.warning(self.mw, "오류", "같은 반 내에서 이동해야 합니다.")
                return
                
            src_data = self.mw.logic.schedule[src_g][src_c][src_d].get(src_p)
            tgt_data = self.mw.logic.schedule[tgt_g][tgt_c][tgt_d].get(tgt_p)
            
            if not src_data: return
            if self.mw.logic.is_locked(src_g, src_c, src_d, src_p): return
                
            self.mw.logic.save_snapshot()
            self.mw.logic.remove_class(src_g, src_c, src_d, src_p)
            self.mw.logic.add_class(tgt_g, tgt_c, tgt_d, tgt_p, src_data['subject'], src_data['teacher'])
            
            self.mw.logic.change_logs.append({
                "type": "연쇄", "class": f"{src_g}-{src_c}",
                "desc": f"{src_data['teacher']} → {tgt_d}{tgt_p} 이동",
                "log_key": ("CHAIN", src_g, src_c, tgt_d, tgt_p)
            })
            
            if tgt_data:
                # 밀려난 데이터를 플로팅 상태로 변경
                self.mw.work_mode = "CHAIN"
                self.mw.use_ai_mode = False
                for btn in self.mw.mode_btn_group.buttons():
                    if btn.property("mode_val") == "CHAIN" and not btn.property("use_ai"):
                        btn.setChecked(True)
                
                self.mw.chain_floating_data = tgt_data.copy()
                self.mw.chain_floating_data['origin_gc'] = (tgt_g, tgt_c)
                self.mw.chain_floating_data['origin_time'] = (tgt_d, tgt_p)
                self.mw.highlighted_teachers = {tgt_data['teacher']: COLORS["cell_chain_src"]}
                self.mw.status_bar.setText(f"🔄 드래그 완료. 밀려난 {tgt_data['teacher']} 교사를 마저 배치하세요.")
            else:
                self.mw.status_bar.setText("✅ 드래그 앤 드롭: 빈자리 이동 완료")
                self.mw.cancel_action()
                
        if hasattr(self.mw, 'chk_only_changed') and self.mw.chk_only_changed.isChecked():
            self.mw.refresh_grid()
        else:
            self.mw.update_cell_visuals()
        self.mw.update_log_view()

    def handle_right_click(self, key):
        if isinstance(key, tuple) and key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = key
            locations = list(self.mw.logic.teachers_schedule.get(teacher_name, {}).get(day, {}).get(period, set()))
            if not locations: return 
            g, c = locations[0]
            key = (str(g), str(c), day, period)
        grade, cls, day, period = key
        is_locked = self.mw.logic.toggle_lock(grade, cls, day, period)
        msg = "🔒 잠금 설정" if is_locked else "🔓 잠금 해제"
        self.mw.status_bar.setText(f"[{grade}-{cls} {day}{period}] {msg}")
        self.mw.update_cell_visuals()

    def execute_cover(self):
        if not self.mw.selected_cell_info: return
        new_teacher = self.mw.combo_cover_teacher.currentText()
        if not new_teacher: return
        
        g, c, d, p = self.mw.selected_cell_info
        
        self.mw.logic.update_teacher(g, c, d, p, new_teacher)
        
        self.mw.selected_cell_info = None
        self.mw.combo_cover_teacher.clear()
        self.mw.highlighted_teachers = {}
        self.mw.status_bar.setText(f"✅ 보강 완료: {new_teacher}")
        
        self.mw.refresh_grid()
        self.mw.update_log_view()