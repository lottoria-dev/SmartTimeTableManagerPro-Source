import copy
from collections import deque
import config

class AIChainedMover:
    def __init__(self, logic_instance):
        self.logic = logic_instance
        self.max_steps = 200

    def try_ai_move(self, start_grade, start_cls, start_day, start_period, target_day, target_period):
        self.logic.save_snapshot()
        
        grade = str(start_grade)
        cls = str(start_cls)
        start_p = int(start_period)
        target_p = int(target_period)
        
        # 1. 기초 예외 처리
        if self.logic.is_excluded(grade, target_day):
            self.logic.history_stack.pop()
            return False, "행사로 제외된 학년/요일입니다.", []
            
        start_data = self.logic.schedule[grade][cls][start_day].get(start_p)
        if not start_data:
            self.logic.history_stack.pop()
            return False, "이동할 수업이 없습니다.", []
            
        start_teacher = start_data['teacher']
        start_subj = start_data['subject']
        
        self.best_logs = []
        self.found_warn_msg = ""
        
        # [핵심 로직] IDDFS (반복적 깊이 심화 탐색)
        # 모든 경우의 수를 시뮬레이션 하되, 가장 얕은 깊이(최소 이동 횟수)부터 탐색하여 최적의 경로를 보장합니다.
        def iddfs(unplaced, max_depth, current_depth, strict_mode, current_logs, visited_cells):
            # 모든 밀려난 수업이 자리를 찾았다면 성공!
            if not unplaced:
                self.best_logs = current_logs.copy()
                return True
                
            # 설정한 최대 연쇄 횟수를 초과하면 중단 (다른 경로 탐색)
            if current_depth >= max_depth:
                return False
                
            # 배치해야 할 첫 번째 수업 꺼내기
            task = unplaced[0]
            g, c, subj, teacher, t_day, forced_p = task
            
            limit = config.PERIODS_PER_DAY.get(t_day, 7)
            # 사용자가 직접 드래그한 첫 타겟 위치가 있다면 그곳만 검사, 아니면 1~7교시 전체 탐색
            candidates = [forced_p] if forced_p else list(range(1, limit + 1))
            
            # 빈 자리 및 교사 충돌이 없는 곳을 우선 탐색하도록 정렬 (탐색 속도 및 효율 극대화)
            if not forced_p:
                def score_slot(p):
                    score = 0
                    if self.logic.schedule[g][c][t_day].get(p): score += 1
                    if self.logic.is_teacher_busy(teacher, t_day, p, ignore_grade=g, ignore_class=c): score += 1
                    return score
                candidates.sort(key=score_slot)
            
            for p in candidates:
                # [버그 픽스] 방문한 셀(이번 연쇄 이동에서 이미 배치가 확정된 교시)은 다시 건드리지 않아 무한 루프(원위치)를 방지합니다.
                if (g, c, t_day, p) in visited_cells: continue
                if self.logic.is_locked(g, c, t_day, p): continue
                if self.logic.is_excluded(g, t_day): continue
                
                # 3연강 엄격 모드일 때 회피 로직
                if strict_mode:
                    if self.logic.check_consecutive_classes(teacher, t_day, p):
                        continue
                        
                # 해당 교시의 현재 상태 확인 (슬롯 충돌 및 교사 충돌)
                existing_data = self.logic.schedule[g][c][t_day].get(p)
                
                busy_locs = [loc for loc in self.logic.get_busy_info(teacher, t_day, p) if not self.logic.is_excluded(loc[0], t_day)]
                other_busy = [loc for loc in busy_locs if loc != (str(g), str(c))]
                
                # 교사가 다른 두 곳 이상의 학급에 동시에 들어가는 특수 상황이면 복잡도 방지를 위해 패스
                if len(other_busy) > 1: continue 
                
                if other_busy:
                    og, oc = other_busy[0]
                    # [버그 픽스] 타 학급 밀어내기를 할 때도 해당 자리가 이번 연쇄에서 확정된 자리면 건드리지 않음
                    if (str(og), str(oc), t_day, p) in visited_cells: continue
                    if self.logic.is_locked(og, oc, t_day, p): continue # 타 학급 수업이 잠금이면 밀어내기 불가
                
                undo_actions = []
                evicted_tasks = []
                
                # 현재 경로 탐색에서 이 자리를 확정했음을 기록
                new_visited = visited_cells.copy()
                new_visited.add((g, c, t_day, p))
                
                # [상황 1] 목표 자리에 다른 교사의 수업이 있으면 밀어내기 (Slot Eviction)
                if existing_data:
                    ex_subj, ex_teach = existing_data['subject'], existing_data['teacher']
                    self.logic.remove_class(g, c, t_day, p)
                    evicted_tasks.append((str(g), str(c), ex_subj, ex_teach, t_day, None))
                    undo_actions.append(('add', str(g), str(c), t_day, p, ex_subj, ex_teach))
                    
                # [상황 2] 이동하려는 교사가 타 학급에 수업이 있다면 타 학급 수업을 밀어내기 (Teacher Eviction - 과거 로직 복원)
                if other_busy:
                    og, oc = other_busy[0]
                    other_data = self.logic.remove_class(og, oc, t_day, p)
                    if other_data:
                        evicted_tasks.append((str(og), str(oc), other_data['subject'], other_data['teacher'], t_day, None))
                        undo_actions.append(('add', str(og), str(oc), t_day, p, other_data['subject'], other_data['teacher']))

                # 실제 수업 배치
                self.logic.add_class(g, c, t_day, p, subj, teacher)
                undo_actions.append(('remove', str(g), str(c), t_day, p))
                
                new_log = f"{g}-{c} {p}교시: {teacher}({subj})"
                new_logs = current_logs + [new_log]
                
                # 다음 밀려난 수업들을 재귀적으로 배치 시도 (new_visited 셋을 함께 전달)
                if iddfs(unplaced[1:] + evicted_tasks, max_depth, current_depth + 1, strict_mode, new_logs, new_visited):
                    return True
                    
                # 실패했다면 되돌리기 (Backtracking) - 원상 복구 후 다른 교시(p) 탐색
                for action in reversed(undo_actions):
                    if action[0] == 'add':
                        self.logic.add_class(action[1], action[2], action[3], action[4], action[5], action[6])
                    else:
                        self.logic.remove_class(action[1], action[2], action[3], action[4])
                        
            return False

        # --- 탐색 시작 ---
        # 원본 수업을 먼저 빼내고 탐색 큐에 넣습니다. (시작했던 원본 자리는 visited에 넣지 않아 다시 돌아올 수 있도록 엽니다)
        self.logic.remove_class(grade, cls, start_day, start_p)
        initial_task = (grade, cls, start_subj, start_teacher, target_day, target_p)
        
        success = False
        # 1단계: 3연강이 발생하지 않는 완벽하고 짧은 경로 탐색 (최대 7번의 연쇄까지만 허용)
        for depth in range(1, 8):
            if iddfs([initial_task], depth, 0, True, [], set()):
                success = True
                break
                
        # 2단계: 완벽한 경로가 없다면, 3연강을 허용하더라도 이동 가능한 짧은 경로 탐색
        if not success:
            for depth in range(1, 8):
                if iddfs([initial_task], depth, 0, False, [], set()):
                    success = True
                    self.found_warn_msg = "\n(💡참고: 이동 가능한 유일한 최단 경로이나, 일부 교사의 3연강이 발생했습니다.)"
                    break
                    
        # 결과 처리
        if success:
            log_desc = "AI자동연쇄: " + " -> ".join(self.best_logs)
            self.logic.change_logs.append({
                "type": "연쇄",
                "class": f"{grade}-{cls}",
                "desc": log_desc,
                "log_key": ("CHAIN_AI", grade, cls, target_day)
            })
            return True, f"AI 최적화 이동 완료! ({len(self.best_logs)}번 배치)" + self.found_warn_msg, self.best_logs
        else:
            self.logic.undo() # 실패 시 처음 snapshot으로 완벽히 롤백
            return False, "모든 경우의 수를 탐색했지만 조건을 만족하는 빈자리나 교환 가능한 조합을 찾지 못했습니다.", []