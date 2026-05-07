from PySide6.QtWidgets import QMessageBox, QApplication, QToolTip
from PySide6.QtGui import QCursor
from PySide6.QtCore import Qt, QRect, QTimer
from gui_styles import COLORS
from gui_components import ChangeDetailDialog
import config

class CellInteractionHandler:
    """그리드 셀 클릭 및 작업 모드별 비즈니스 로직을 분리한 클래스"""
    def __init__(self, main_window):
        self.mw = main_window
        
        # 1. 캔슬 액션(ESC 또는 빈공간 클릭) 몽키 패치
        self._original_cancel_action = getattr(self.mw, 'cancel_action', None)
        self.mw.cancel_action = self._safe_cancel_action
        
        # 2. 실행취소(Ctrl+Z) 몽키 패치
        if hasattr(self.mw, 'undo') and not hasattr(self.mw, '_undo_patched'):
            self._original_undo = getattr(self.mw, 'undo')
            self.mw.undo = self._safe_undo
            self.mw._undo_patched = True
            
        # 3. 디바운스(Debounce) 렌더링 최적화 몽키 패치 (랙 방지)
        if not hasattr(self.mw, '_visuals_patched'):
            self._original_update_cell_visuals = getattr(self.mw, 'update_cell_visuals', None)
            self.mw.update_cell_visuals = self._fast_update_cell_visuals
            self.mw._visuals_patched = True
            
        if not hasattr(self.mw, '_refresh_patched'):
            self._original_refresh_grid = getattr(self.mw, 'refresh_grid', None)
            self.mw.refresh_grid = self._fast_refresh_grid
            self.mw._refresh_patched = True
            
        self._render_pending = False
        self._refresh_pending = False
        self._refresh_arg = None

    def _safe_undo(self):
        """실행 취소(Undo) 발생 시 화면이 갱신되지 않는 문제를 완벽 해결합니다."""
        # 혹시 남아있을지 모르는 디바운스 렌더링 대기를 강제 해제
        self._render_pending = False
        self._refresh_pending = False
        
        # 원래의 실행 취소 로직(데이터 스택 복구) 실행
        if self._original_undo:
            self._original_undo()
            
        # [핵심] 교사 시수 등 구조적 변동을 완벽히 반영하기 위해 즉각적인 강제 새로고침 실행
        self._execute_batched_refresh()

    def _fast_update_cell_visuals(self):
        if not getattr(self, '_render_pending', False):
            self._render_pending = True
            QTimer.singleShot(0, self._execute_batched_render)

    def _execute_batched_render(self):
        if not self._render_pending: return
        self._render_pending = False
        
        if hasattr(self.mw, 'setUpdatesEnabled'): self.mw.setUpdatesEnabled(False)
        try:
            if self._original_update_cell_visuals:
                self._original_update_cell_visuals()
        finally:
            if hasattr(self.mw, 'setUpdatesEnabled'): self.mw.setUpdatesEnabled(True)

    def _fast_refresh_grid(self, arg=None):
        self._refresh_arg = arg
        if not getattr(self, '_refresh_pending', False):
            self._refresh_pending = True
            QTimer.singleShot(0, self._execute_batched_refresh)

    def _execute_batched_refresh(self):
        # 강제 호출(Undo)을 위해 pending 조건 통과
        self._refresh_pending = False
        arg = getattr(self, '_refresh_arg', None)
        self._refresh_arg = None
        
        if hasattr(self.mw, 'setUpdatesEnabled'): self.mw.setUpdatesEnabled(False)
        try:
            if self._original_refresh_grid:
                if arg is not None:
                    self._original_refresh_grid(arg)
                else:
                    self._original_refresh_grid()
        finally:
            if hasattr(self.mw, 'setUpdatesEnabled'): self.mw.setUpdatesEnabled(True)

    def _safe_cancel_action(self):
        old_swap_source = getattr(self.mw, 'swap_source', None)
        old_swap_candidates = list(getattr(self.mw, 'swap_candidates', []))
        old_selected_cell = getattr(self.mw, 'selected_cell_info', None)
        old_highlighted = list(getattr(self.mw, 'highlighted_teachers', {}).keys())
        old_chain_gc = self.mw.chain_floating_data.get('origin_gc') if getattr(self.mw, 'chain_floating_data', None) else None
        old_floater = self.mw.chain_floating_data.get('teacher') if getattr(self.mw, 'chain_floating_data', None) else None

        is_chain_reverted = False
        if self.mw.work_mode == "CHAIN" and getattr(self.mw, 'chain_floating_data', None):
            self.mw.logic.undo()
            self.mw.chain_floating_data = None
            self.mw.status_bar.setText("⚠️ 이동이 취소되어 시작 전 상태로 완벽히 복구되었습니다.")
            self.mw.update_log_view()
            is_chain_reverted = True

        # [버그 수정] 타이머 차단 방식 폐기. 
        # 원본 cancel_action 이 호출하는 무거운 렌더링만 일시적으로 무력화(Mocking) 합니다.
        temp_update = getattr(self.mw, 'update_cell_visuals', None)
        temp_refresh = getattr(self.mw, 'refresh_grid', None)
        
        if temp_update: self.mw.update_cell_visuals = lambda: None
        if temp_refresh: self.mw.refresh_grid = lambda arg=None: None
        
        try:
            if self._original_cancel_action:
                self._original_cancel_action()
        finally:
            # 원상 복구
            if temp_update: self.mw.update_cell_visuals = temp_update
            if temp_refresh: self.mw.refresh_grid = temp_refresh

        # 스마트 렌더링 처리
        if is_chain_reverted:
            if hasattr(self.mw, 'chk_only_changed') and getattr(self.mw.chk_only_changed, 'isChecked', lambda: False)():
                self.mw.refresh_grid()
            else:
                self.mw.update_cell_visuals()
        else:
            # 데이터 변동 없는 단순 취소는 핀포인트 렌더링으로 랙(Lag) 완벽 제거
            if hasattr(self.mw, 'setUpdatesEnabled'): self.mw.setUpdatesEnabled(False)
            try:
                keys_to_update = set()
                if old_swap_source: keys_to_update.add(old_swap_source)
                if old_selected_cell: keys_to_update.add(old_selected_cell)
                for d, p in old_swap_candidates:
                    keys_to_update.add((old_swap_source[0], old_swap_source[1], d, p))
                    
                if old_chain_gc:
                    for d in config.DAYS:
                        limit = config.PERIODS_PER_DAY.get(d, 7)
                        for p in range(1, limit + 1):
                            keys_to_update.add((str(old_chain_gc[0]), str(old_chain_gc[1]), d, p))
                            
                teachers_to_update = set(old_highlighted)
                if old_floater: teachers_to_update.add(old_floater)
                
                for t in teachers_to_update:
                    for d in config.DAYS:
                        limit = config.PERIODS_PER_DAY.get(d, 7)
                        for p in range(1, limit + 1):
                            keys_to_update.add(("TEACHER_VIEW", t, d, p))
                    for d, periods in self.mw.logic.teachers_schedule.get(t, {}).items():
                        for p, classes in periods.items():
                            for g, c in classes:
                                keys_to_update.add((str(g), str(c), d, p))
                                keys_to_update.add(("TEACHER_VIEW", t, d, p))
                                
                for k in keys_to_update:
                    if k in getattr(self.mw, 'cell_widget_map', {}) and hasattr(self.mw, 'grid_renderer'):
                        self.mw.grid_renderer._update_single_cell(self.mw.cell_widget_map[k], k)
            finally:
                if hasattr(self.mw, 'setUpdatesEnabled'): self.mw.setUpdatesEnabled(True)

    def handle_cell_click(self, key):
        old_highlighted = list(getattr(self.mw, 'highlighted_teachers', {}).keys())
        old_swap_source = getattr(self.mw, 'swap_source', None)
        old_swap_candidates = list(getattr(self.mw, 'swap_candidates', []))
        old_selected_cell = getattr(self.mw, 'selected_cell_info', None)
        
        old_chain_gc = self.mw.chain_floating_data.get('origin_gc') if getattr(self.mw, 'chain_floating_data', None) else None
        
        data_changed = False 
        ai_moved = False 
        pending_dialog_args = None 

        if isinstance(key, tuple) and key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = key
            
            if self.mw.work_mode == "CHAIN" and getattr(self.mw, 'chain_floating_data', None):
                orig_g, orig_c = self.mw.chain_floating_data['origin_gc']
                floater_teacher = self.mw.chain_floating_data['teacher']
                if teacher_name != floater_teacher:
                    QMessageBox.warning(self.mw, "오류", f"해당 수업은 {floater_teacher} 선생님의 수업입니다.\n{floater_teacher} 선생님의 행에만 배치할 수 있습니다.")
                    return
                key = (str(orig_g), str(orig_c), day, period)
            elif self.mw.work_mode == "SWAP" and getattr(self.mw, 'swap_source', None):
                orig_g, orig_c = self.mw.swap_source[0:2]
                key = (str(orig_g), str(orig_c), day, period)
            else:
                locations = list(self.mw.logic.teachers_schedule.get(teacher_name, {}).get(day, {}).get(period, set()))
                if locations:
                    g, c = locations[0]
                    key = (str(g), str(c), day, period)
                else:
                    self.mw.status_bar.setText("⚠️ 빈 시간입니다.")
                    return
                    
        grade, cls, day, period = key
        grade, cls = str(grade), str(cls)

        if self.mw.logic.is_excluded(grade, day):
            self.mw.status_bar.setText(f"🚫 {grade}학년은 {day}요일 행사로 인해 선택에서 제외되었습니다.")
            return

        cell_data = self.mw.logic.schedule[grade][cls][day].get(period)
        clicked_teacher = cell_data['teacher'] if cell_data else None

        if clicked_teacher: self.mw.highlighted_teachers = {clicked_teacher: COLORS["cell_selected"]}
        else: self.mw.highlighted_teachers = {}

        if self.mw.work_mode == "VIEW":
            is_locked = "🔒 " if self.mw.logic.is_locked(grade, cls, day, period) else ""
            msg = f"{is_locked}선택: {clicked_teacher} ({cell_data['subject']})" if clicked_teacher else "빈 교시"
            self.mw.status_bar.setText(msg)
            
            if self.mw.logic.is_changed(grade, cls, day, period):
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                try:
                    details = self.mw.logic.get_cell_change_details(grade, cls, day, period)
                finally:
                    QApplication.restoreOverrideCursor()
                    
                if details:
                    pending_dialog_args = (f"{grade}-{cls} {day} {period}교시 상세 변동 내역", details)
                    
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
                self.mw.highlighted_teachers = {} 
                self.mw.status_bar.setText("✅ 교체 완료")
                self.mw.update_log_view()
                
        elif self.mw.work_mode == "COVER":
            if not cell_data: return
            if self.mw.logic.is_locked(grade, cls, day, period):
                self.mw.status_bar.setText("🔒 잠긴 수업입니다.")
                return
            self.mw.selected_cell_info = key
            self.mw.highlighted_teachers = {clicked_teacher: COLORS.get("cell_cover", COLORS["cell_selected"])}
            candidates = self.mw.logic.get_cover_candidates(day, period)
            self.mw.combo_cover_teacher.clear()
            if candidates:
                self.mw.combo_cover_teacher.addItems(candidates)
                self.mw.status_bar.setText(f"대상: {clicked_teacher}. 대체 교사를 선택하고 배정 버튼을 누르세요.")
            else:
                self.mw.status_bar.setText("⚠️ 추천 가능한 교사가 없습니다.")
                
        elif self.mw.work_mode == "CHAIN":
            if self.mw.use_ai_mode:
                if not self.mw.chain_floating_data:
                    if self.mw.logic.is_locked(grade, cls, day, period): return
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
                        
                    if self.mw.logic.is_locked(grade, cls, day, period):
                        QMessageBox.warning(self.mw, "이동 불가", f"해당 시간({day} {period}교시)은 본 학급의 다른 수업이 잠금(🔒)되어 있어 옮길 수 없습니다.")
                        return
                    floater_teacher = self.mw.chain_floating_data['teacher']
                    other_classes = list(self.mw.logic.teachers_schedule.get(floater_teacher, {}).get(day, {}).get(period, set()))
                    is_other_locked = any(self.mw.logic.is_locked(str(og), str(oc), day, period) for og, oc in other_classes)
                    if is_other_locked:
                        QMessageBox.warning(self.mw, "이동 불가", f"[{floater_teacher}] 교사의 타 학급 수업이 잠금(🔒)되어 있어 밀어낼 수 없습니다.")
                        return
                    
                    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                    try:
                        success, msg, logs = self.mw.ai_mover.try_ai_move(orig_g, orig_c, orig_d, orig_p, day, period)
                    finally:
                        QApplication.restoreOverrideCursor()

                    if success: 
                        self.mw.status_bar.setText(f"✅ {msg}")
                        data_changed = True  
                        ai_moved = True
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
                    if self.mw.logic.is_locked(grade, cls, day, period): return
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
                    
                    if self.mw.logic.is_locked(grade, cls, day, period):
                        QMessageBox.warning(self.mw, "이동 불가", f"해당 시간({day} {period}교시)은 본 학급의 다른 수업이 잠금(🔒)되어 있어 옮길 수 없습니다.")
                        return
                    other_classes = list(self.mw.logic.teachers_schedule.get(floater_teacher, {}).get(day, {}).get(period, set()))
                    is_other_locked = any(self.mw.logic.is_locked(str(og), str(oc), day, period) for og, oc in other_classes)
                    if is_other_locked:
                        QMessageBox.warning(self.mw, "이동 불가", f"[{floater_teacher}] 교사의 타 학급 수업이 잠금(🔒)되어 있어 밀어낼 수 없습니다.")
                        return

                    if floater_teacher and self.mw.logic.check_consecutive_classes(floater_teacher, day, period):
                        reply = QMessageBox.question(
                            self.mw, "3연강 경고",
                            f"'{floater_teacher}' 교사의 3연강이 발생합니다. ({day} {period}교시)\n\n그래도 이동하시겠습니까?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.No:
                            return 

                    target_old_data = self.mw.logic.schedule[grade][cls][day].get(period)
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
                    
        if ai_moved:
            if hasattr(self.mw, 'chk_only_changed') and getattr(self.mw.chk_only_changed, 'isChecked', lambda: False)():
                self.mw.refresh_grid()
            else:
                self.mw.update_cell_visuals() 
        else:
            if data_changed and hasattr(self.mw, 'chk_only_changed') and getattr(self.mw.chk_only_changed, 'isChecked', lambda: False)():
                self.mw.refresh_grid()
            else:
                if hasattr(self.mw, 'setUpdatesEnabled'):
                    self.mw.setUpdatesEnabled(False)
                try:
                    keys_to_update = set([key])
                    
                    if old_swap_source: keys_to_update.add(old_swap_source)
                    if getattr(self.mw, 'swap_source', None): keys_to_update.add(self.mw.swap_source)
                    if old_selected_cell: keys_to_update.add(old_selected_cell)
                    if getattr(self.mw, 'selected_cell_info', None): keys_to_update.add(self.mw.selected_cell_info)
                    
                    if old_swap_source:
                        for d, p in old_swap_candidates:
                            keys_to_update.add((old_swap_source[0], old_swap_source[1], d, p))
                            dt = self.mw.logic.schedule[old_swap_source[0]][old_swap_source[1]][d].get(p)
                            if dt and dt.get('teacher'): keys_to_update.add(("TEACHER_VIEW", dt['teacher'], d, p))
                    
                    if getattr(self.mw, 'swap_source', None):
                        for d, p in getattr(self.mw, 'swap_candidates', []):
                            keys_to_update.add((self.mw.swap_source[0], self.mw.swap_source[1], d, p))
                            dt = self.mw.logic.schedule[self.mw.swap_source[0]][self.mw.swap_source[1]][d].get(p)
                            if dt and dt.get('teacher'): keys_to_update.add(("TEACHER_VIEW", dt['teacher'], d, p))
                            
                    current_chain_gc = self.mw.chain_floating_data.get('origin_gc') if getattr(self.mw, 'chain_floating_data', None) else None
                    chain_gcs = set()
                    if old_chain_gc: chain_gcs.add(old_chain_gc)
                    if current_chain_gc: chain_gcs.add(current_chain_gc)
                    
                    floater = self.mw.chain_floating_data.get('teacher') if getattr(self.mw, 'chain_floating_data', None) else None
                    
                    for g, c in chain_gcs:
                        for d in config.DAYS:
                            limit = config.PERIODS_PER_DAY.get(d, 7)
                            for p in range(1, limit + 1):
                                keys_to_update.add((str(g), str(c), d, p))

                    teachers_to_update = set(old_highlighted)
                    teachers_to_update.update(getattr(self.mw, 'highlighted_teachers', {}).keys())
                    if floater: teachers_to_update.add(floater)
                    if clicked_teacher: teachers_to_update.add(clicked_teacher)
                    
                    if old_swap_source:
                        old_dt = self.mw.logic.schedule[old_swap_source[0]][old_swap_source[1]][old_swap_source[2]].get(old_swap_source[3])
                        if old_dt and old_dt.get('teacher'): teachers_to_update.add(old_dt['teacher'])
                    
                    if getattr(self.mw, 'swap_source', None):
                        new_dt = self.mw.logic.schedule[self.mw.swap_source[0]][self.mw.swap_source[1]][self.mw.swap_source[2]].get(self.mw.swap_source[3])
                        if new_dt and new_dt.get('teacher'): teachers_to_update.add(new_dt['teacher'])
                    
                    for t in teachers_to_update:
                        for d in config.DAYS:
                            limit = config.PERIODS_PER_DAY.get(d, 7)
                            for p in range(1, limit + 1):
                                keys_to_update.add(("TEACHER_VIEW", t, d, p))
                                
                        for d, periods in self.mw.logic.teachers_schedule.get(t, {}).items():
                            for p, classes in periods.items():
                                for gr, cl in classes:
                                    keys_to_update.add((str(gr), str(cl), d, p))
                                    keys_to_update.add(("TEACHER_VIEW", t, d, p))
                                    
                    for k in keys_to_update:
                        if k in getattr(self.mw, 'cell_widget_map', {}) and hasattr(self.mw, 'grid_renderer'):
                            self.mw.grid_renderer._update_single_cell(self.mw.cell_widget_map[k], k)
                finally:
                    if hasattr(self.mw, 'setUpdatesEnabled'):
                        self.mw.setUpdatesEnabled(True)

        if pending_dialog_args:
            QApplication.processEvents() 
            dialog = ChangeDetailDialog(pending_dialog_args[0], pending_dialog_args[1], self.mw)
            dialog.exec()

    def handle_cell_drop(self, src_key, tgt_key):
        if src_key == tgt_key: return
            
        if isinstance(src_key, tuple) and src_key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = src_key
            locations = list(self.mw.logic.teachers_schedule.get(teacher_name, {}).get(day, {}).get(period, set()))
            if locations: g, c = locations[0]; src_key = (str(g), str(c), day, period)
            else: return
                
        if isinstance(tgt_key, tuple) and tgt_key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = tgt_key
            src_g, src_c = src_key[0:2]
            tgt_key = (str(src_g), str(src_c), day, period)
        
        src_g, src_c, src_d, src_p = src_key
        tgt_g, tgt_c, tgt_d, tgt_p = tgt_key
        
        src_g, src_c = str(src_g), str(src_c)
        tgt_g, tgt_c = str(tgt_g), str(tgt_c)

        if self.mw.logic.is_excluded(src_g, src_d) or self.mw.logic.is_excluded(tgt_g, tgt_d):
            QMessageBox.warning(self.mw, "이동 불가", "행사 등으로 제외 처리된 학년은 이동/교환할 수 없습니다.")
            return
        
        if self.mw.work_mode == "SWAP":
            if (src_g, src_c) != (tgt_g, tgt_c):
                QMessageBox.warning(self.mw, "오류", "같은 반 내에서만 교환 가능합니다.")
                return
            if self.mw.logic.is_locked(src_g, src_c, src_d, src_p) or self.mw.logic.is_locked(tgt_g, tgt_c, tgt_d, tgt_p):
                QMessageBox.warning(self.mw, "오류", "잠겨있는 수업은 교환할 수 없습니다.")
                return
            
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
            
            if self.mw.logic.is_locked(tgt_g, tgt_c, tgt_d, tgt_p):
                QMessageBox.warning(self.mw, "이동 불가", f"해당 시간({tgt_d} {tgt_p}교시)은 본 학급의 다른 수업이 잠금(🔒)되어 있어 옮길 수 없습니다.")
                return
            floater_teacher = self.mw.logic.schedule[src_g][src_c][src_d][src_p]['teacher']
            other_classes = list(self.mw.logic.teachers_schedule.get(floater_teacher, {}).get(tgt_d, {}).get(tgt_p, set()))
            is_other_locked = any(self.mw.logic.is_locked(str(og), str(oc), tgt_d, tgt_p) for og, oc in other_classes)
            if is_other_locked:
                QMessageBox.warning(self.mw, "이동 불가", f"[{floater_teacher}] 교사의 타 학급 수업이 잠금(🔒)되어 있어 밀어낼 수 없습니다.")
                return
            
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                success, msg, logs = self.mw.ai_mover.try_ai_move(src_g, src_c, src_d, src_p, tgt_d, tgt_p)
            finally:
                QApplication.restoreOverrideCursor()
                
            if success: self.mw.status_bar.setText(f"✅ 드래그 앤 드롭: {msg}")
            else: QMessageBox.warning(self.mw, "AI 자동 이동 안내", msg)
            self.mw.cancel_action()
            
        else:
            if (src_g, src_c) != (tgt_g, tgt_c):
                QMessageBox.warning(self.mw, "오류", "같은 반 내에서 이동해야 합니다.")
                return
                
            src_data = self.mw.logic.schedule[src_g][src_c][src_d].get(src_p)
            tgt_data = self.mw.logic.schedule[tgt_g][tgt_c][tgt_d].get(tgt_p)
            
            if not src_data: return
            if self.mw.logic.is_locked(src_g, src_c, src_d, src_p): return
            
            if self.mw.logic.is_locked(tgt_g, tgt_c, tgt_d, tgt_p):
                QMessageBox.warning(self.mw, "이동 불가", f"해당 시간({tgt_d} {tgt_p}교시)은 본 학급의 다른 수업이 잠금(🔒)되어 있어 옮길 수 없습니다.")
                return
            floater_teacher = src_data['teacher']
            other_classes = list(self.mw.logic.teachers_schedule.get(floater_teacher, {}).get(tgt_d, {}).get(tgt_p, set()))
            is_other_locked = any(self.mw.logic.is_locked(str(og), str(oc), tgt_d, tgt_p) for og, oc in other_classes)
            if is_other_locked:
                QMessageBox.warning(self.mw, "이동 불가", f"[{floater_teacher}] 교사의 타 학급 수업이 잠금(🔒)되어 있어 밀어낼 수 없습니다.")
                return
                
            self.mw.logic.save_snapshot()
            self.mw.logic.remove_class(src_g, src_c, src_d, src_p)
            self.mw.logic.add_class(tgt_g, tgt_c, tgt_d, tgt_p, src_data['subject'], src_data['teacher'])
            
            self.mw.logic.change_logs.append({
                "type": "연쇄", "class": f"{src_g}-{src_c}",
                "desc": f"{src_data['teacher']} → {tgt_d}{tgt_p} 이동",
                "log_key": ("CHAIN", src_g, src_c, tgt_d, tgt_p)
            })
            
            if tgt_data:
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
                return 
                
        if getattr(self.mw, 'use_ai_mode', False) and self.mw.work_mode == "CHAIN":
            if hasattr(self.mw, 'chk_only_changed') and getattr(self.mw.chk_only_changed, 'isChecked', lambda: False)():
                self.mw.refresh_grid()
            else:
                self.mw.update_cell_visuals()
        else:
            if hasattr(self.mw, 'chk_only_changed') and getattr(self.mw.chk_only_changed, 'isChecked', lambda: False)():
                self.mw.refresh_grid()
            else:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                if hasattr(self.mw, 'setUpdatesEnabled'):
                    self.mw.setUpdatesEnabled(False)
                try:
                    keys_to_update = {src_key, tgt_key}
                    teachers_to_update = set()
                    
                    src_data = self.mw.logic.schedule[src_g][src_c][src_d].get(src_p)
                    tgt_data = self.mw.logic.schedule[tgt_g][tgt_c][tgt_d].get(tgt_p)
                    if src_data and src_data.get('teacher'): teachers_to_update.add(src_data['teacher'])
                    if tgt_data and tgt_data.get('teacher'): teachers_to_update.add(tgt_data['teacher'])
                    
                    floater = self.mw.chain_floating_data.get('teacher') if getattr(self.mw, 'chain_floating_data', None) else None
                    if floater: teachers_to_update.add(floater)
                    
                    teachers_to_update.update(getattr(self.mw, 'highlighted_teachers', {}).keys())
                    
                    for t in teachers_to_update:
                        for d in config.DAYS:
                            limit = config.PERIODS_PER_DAY.get(d, 7)
                            for p in range(1, limit + 1):
                                keys_to_update.add(("TEACHER_VIEW", t, d, p))
                        for d, periods in self.mw.logic.teachers_schedule.get(t, {}).items():
                            for p, classes in periods.items():
                                for gr, cl in classes:
                                    keys_to_update.add((str(gr), str(cl), d, p))
                                    keys_to_update.add(("TEACHER_VIEW", t, d, p))
                                    
                    for k in keys_to_update:
                        if k in getattr(self.mw, 'cell_widget_map', {}) and hasattr(self.mw, 'grid_renderer'):
                            self.mw.grid_renderer._update_single_cell(self.mw.cell_widget_map[k], k)
                finally:
                    if hasattr(self.mw, 'setUpdatesEnabled'):
                        self.mw.setUpdatesEnabled(True)
                    QApplication.restoreOverrideCursor()
                        
        self.mw.update_log_view()

    def handle_right_click(self, key):
        original_key = key 
        if isinstance(key, tuple) and key[0] == "TEACHER_VIEW":
            _, teacher_name, day, period = key
            locations = list(self.mw.logic.teachers_schedule.get(teacher_name, {}).get(day, {}).get(period, set()))
            if not locations: return 
            g, c = locations[0]
            key = (str(g), str(c), day, period)
            
        grade, cls, day, period = key
        if self.mw.logic.is_excluded(grade, day):
            self.mw.status_bar.setText("🚫 행사 제외 요일은 잠금 설정이 무의미합니다.")
            return
            
        is_locked = self.mw.logic.toggle_lock(grade, cls, day, period)
        msg = "🔒 잠금 설정" if is_locked else "🔓 잠금 해제"
        self.mw.status_bar.setText(f"[{grade}-{cls} {day}{period}] {msg}")
        
        if original_key in self.mw.cell_widget_map:
            cell_widget = self.mw.cell_widget_map[original_key]
            self.mw.grid_renderer._update_single_cell(cell_widget, original_key)

    def execute_cover(self):
        if not self.mw.selected_cell_info: return
        new_teacher_display = self.mw.combo_cover_teacher.currentText()
        if not new_teacher_display: return
        
        new_teacher = new_teacher_display.replace("*", "").replace("(행사)", "")
        g, c, d, p = self.mw.selected_cell_info
        
        old_highlighted = list(getattr(self.mw, 'highlighted_teachers', {}).keys())
        
        old_data = self.mw.logic.schedule[g][c][d].get(p)
        old_teacher = old_data['teacher'] if old_data else None
        is_new_teacher = new_teacher not in self.mw.logic.all_teachers
        
        self.mw.logic.update_teacher(g, c, d, p, new_teacher)
        
        self.mw.selected_cell_info = None
        self.mw.combo_cover_teacher.clear()
        self.mw.highlighted_teachers = {}
        self.mw.status_bar.setText(f"✅ 보강 완료: {new_teacher}")
        
        needs_full_refresh = is_new_teacher and self.mw.view_mode in ["ALL_TEACHER", "TEACHER"]
        
        if needs_full_refresh or (hasattr(self.mw, 'chk_only_changed') and getattr(self.mw.chk_only_changed, 'isChecked', lambda: False)()):
            self.mw.refresh_grid()
        else:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            if hasattr(self.mw, 'setUpdatesEnabled'):
                self.mw.setUpdatesEnabled(False)
            try:
                keys_to_update = set([(str(g), str(c), d, p)])
                teachers_to_update = set(old_highlighted + [new_teacher])
                if old_teacher: teachers_to_update.add(old_teacher)
                
                for t in teachers_to_update:
                    for day in config.DAYS:
                        limit = config.PERIODS_PER_DAY.get(day, 7)
                        for prd in range(1, limit + 1):
                            keys_to_update.add(("TEACHER_VIEW", t, day, prd))
                    for day, periods in self.mw.logic.teachers_schedule.get(t, {}).items():
                        for prd, classes in periods.items():
                            for gr, cl in classes:
                                keys_to_update.add((str(gr), str(cl), day, prd))
                                keys_to_update.add(("TEACHER_VIEW", t, day, prd))
                                
                for k in keys_to_update:
                    if k in getattr(self.mw, 'cell_widget_map', {}) and hasattr(self.mw, 'grid_renderer'):
                        self.mw.grid_renderer._update_single_cell(self.mw.cell_widget_map[k], k)
            finally:
                if hasattr(self.mw, 'setUpdatesEnabled'):
                    self.mw.setUpdatesEnabled(True)
                QApplication.restoreOverrideCursor()
                    
        self.mw.update_log_view()