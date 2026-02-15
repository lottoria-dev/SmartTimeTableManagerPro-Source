import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np

def create_app_icon():
    # 1. 캔버스 설정
    # 아이소메트릭 뷰의 폭이 약 174 정도 되므로, x축 범위를 넉넉하게 늘려줍니다.
    fig, ax = plt.subplots(figsize=(5, 5), dpi=300)
    ax.set_xlim(-50, 150)
    ax.set_ylim(-60, 140)
    ax.axis('off')

    # --- 변환 함수 (바닥면 투영) ---
    # 2D 평면 좌표(x,y)를 30도 아이소메트릭 뷰로 변환
    def iso_transform(x, y, z=0):
        # 중심(50, 50) 기준
        u = x - 50
        v = y - 50
        
        # 아이소메트릭 투영 공식 (30도)
        iso_x = (u - v) * 0.866
        iso_y = (u + v) * 0.5 + z # z는 높이
        
        # 화면 중앙으로 이동 (y축 보정)
        return iso_x + 50, iso_y + 30

    grid_color = "#3b82f6" # 파란색
    
    # [추가] 블록 두께 설정
    block_h = 10
    
    # 2. 표 그림자 (Shadow) - 두께만큼 더 아래로 이동
    corners = [(0,0), (100,0), (100,100), (0,100)]
    shadow_z = -5 - block_h # 블록 바닥보다 아래에 위치
    shadow_corners = [iso_transform(cx, cy, shadow_z) for cx, cy in corners]
    shadow_poly = patches.Polygon(shadow_corners, facecolor='black', alpha=0.1, zorder=0)
    ax.add_patch(shadow_poly)
    
    # [추가] 3. 측면 입체감 (Side Faces) - 윗면보다 먼저 그림 (zorder 낮음)
    
    # 왼쪽 면 (Left Face: x=0 edge)
    # 평면상 (0,100) ~ (0,0) 라인에서 아래로 확장
    left_face_corners = [
        (0, 100, 0), (0, 0, 0), (0, 0, -block_h), (0, 100, -block_h)
    ]
    iso_left = [iso_transform(x, y, z) for x, y, z in left_face_corners]
    # 약간 어두운 색으로 음영 처리
    ax.add_patch(patches.Polygon(iso_left, facecolor='#cbd5e1', edgecolor=None, zorder=0.5))

    # 오른쪽 면 (Right Face: y=0 edge)
    # 평면상 (0,0) ~ (100,0) 라인에서 아래로 확장
    right_face_corners = [
        (0, 0, 0), (100, 0, 0), (100, 0, -block_h), (0, 0, -block_h)
    ]
    iso_right = [iso_transform(x, y, z) for x, y, z in right_face_corners]
    # 왼쪽 면보다는 밝지만 윗면보단 어둡게 처리
    ax.add_patch(patches.Polygon(iso_right, facecolor='#e2e8f0', edgecolor=None, zorder=0.5))

    # [추가] 측면 세로줄 (Vertical Grid Lines)
    # 입체감을 살리기 위해 격자선이 측면으로 이어지도록 그림
    lines = np.linspace(0, 100, 6) # 5x5
    for val in lines:
        # 오른쪽 면 (Right Face, y=0)의 세로줄
        p_top = iso_transform(val, 0, 0)
        p_bot = iso_transform(val, 0, -block_h)
        ax.plot([p_top[0], p_bot[0]], [p_top[1], p_bot[1]], color=grid_color, lw=1.5, alpha=0.5, zorder=0.6)
        
        # 왼쪽 면 (Left Face, x=0)의 세로줄
        p_top = iso_transform(0, val, 0)
        p_bot = iso_transform(0, val, -block_h)
        ax.plot([p_top[0], p_bot[0]], [p_top[1], p_bot[1]], color=grid_color, lw=1.5, alpha=0.5, zorder=0.6)

    # 4. 표 배경 (Base - Top Face)
    iso_corners = [iso_transform(cx, cy, 0) for cx, cy in corners]
    bg_poly = patches.Polygon(iso_corners, facecolor='white', edgecolor=None, zorder=1)
    ax.add_patch(bg_poly)

    # 5. 윗면 격자선 (Top Grid Lines)
    for val in lines:
        # 세로결
        p1 = iso_transform(val, 0)
        p2 = iso_transform(val, 100)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, lw=1.5, alpha=0.5, zorder=1)
        # 가로결
        p3 = iso_transform(0, val)
        p4 = iso_transform(100, val)
        ax.plot([p3[0], p4[0]], [p3[1], p4[1]], color=grid_color, lw=1.5, alpha=0.5, zorder=1)

    # --- 6. 커스텀 Swap 화살표 (입체 투영) ---
    
    def create_circular_arrow(start_angle, end_angle, inner_r, outer_r, z_height):
        """평면상의 도넛형 화살표를 생성하고 투영"""
        verts = []
        codes = []
        
        # 각도 범위 생성 (부드러운 곡선을 위해 점을 많이 찍음)
        angles = np.linspace(np.radians(start_angle), np.radians(end_angle), 30)
        
        # 1. 외곽선 (Outer Arc)
        for ang in angles:
            x = 50 + outer_r * np.cos(ang)
            y = 50 + outer_r * np.sin(ang)
            px, py = iso_transform(x, y, z_height)
            verts.append((px, py))
            codes.append(Path.LINETO if len(codes) > 0 else Path.MOVETO)
            
        # 2. 화살표 머리 (Arrow Head)
        head_len = 12
        head_width = 12
        tip_ang = angles[-1]
        
        # 팁 끝점 계산
        # 팁은 경로의 끝에서 약간 더 나아감
        tip_x = 50 + (inner_r + outer_r)/2 * np.cos(tip_ang + 0.1) # 조금 더 회전
        tip_y = 50 + (inner_r + outer_r)/2 * np.sin(tip_ang + 0.1)
        
        # 내곽선 (Inner Arc) - 역순으로
        for ang in reversed(angles):
            x = 50 + inner_r * np.cos(ang)
            y = 50 + inner_r * np.sin(ang)
            px, py = iso_transform(x, y, z_height)
            verts.append((px, py))
            codes.append(Path.LINETO)
            
        codes.append(Path.CLOSEPOLY)
        verts.append((0,0)) # placeholder
        
        return Path(verts[:-1], codes[:-1])

    # 화살표 그리기 설정
    z_pos = 10 # 바닥에서 10만큼 떠있음
    arrow_color = "#f97316"
    
    # 화살표 1 (위쪽)
    path1 = create_circular_arrow(45, 200, 15, 28, z_pos)
    patch1 = patches.PathPatch(path1, facecolor=arrow_color, edgecolor='white', lw=1, zorder=3)
    ax.add_patch(patch1)
    
    # 화살표 1의 머리 (삼각형) - 별도로 추가하여 모양 잡기
    h_r = 21.5 # 중심 반경
    head_verts = [
        (50 + h_r * np.cos(np.radians(230)), 50 + h_r * np.sin(np.radians(230))), # Tip
        (50 + 32 * np.cos(np.radians(195)), 50 + 32 * np.sin(np.radians(195))),   # Outer Base
        (50 + 11 * np.cos(np.radians(195)), 50 + 11 * np.sin(np.radians(195))),   # Inner Base
    ]
    iso_head = [iso_transform(x, y, z_pos) for x, y in head_verts]
    head1 = patches.Polygon(iso_head, facecolor=arrow_color, edgecolor='white', lw=1, zorder=3)
    ax.add_patch(head1)

    # 화살표 2 (아래쪽)
    path2 = create_circular_arrow(225, 380, 15, 28, z_pos)
    patch2 = patches.PathPatch(path2, facecolor=arrow_color, edgecolor='white', lw=1, zorder=3)
    ax.add_patch(patch2)
    
    # 화살표 2의 머리
    head_verts2 = [
        (50 + h_r * np.cos(np.radians(410)), 50 + h_r * np.sin(np.radians(410))), # Tip (50도)
        (50 + 32 * np.cos(np.radians(375)), 50 + 32 * np.sin(np.radians(375))),   # Outer Base
        (50 + 11 * np.cos(np.radians(375)), 50 + 11 * np.sin(np.radians(375))),   # Inner Base
    ]
    iso_head2 = [iso_transform(x, y, z_pos) for x, y in head_verts2]
    head2 = patches.Polygon(iso_head2, facecolor=arrow_color, edgecolor='white', lw=1, zorder=3)
    ax.add_patch(head2)

    # --- 그림자 추가 (동일한 모양을 아래에 검게) ---
    shadow_z_pos = 2
    
    # Shadow Arrow 1
    path1_s = create_circular_arrow(45, 200, 15, 28, shadow_z_pos)
    patch1_s = patches.PathPatch(path1_s, facecolor='black', alpha=0.2, lw=0, zorder=2)
    ax.add_patch(patch1_s)
    
    # Shadow Head 1
    iso_head_s = [iso_transform(x, y, shadow_z_pos) for x, y in head_verts]
    head1_s = patches.Polygon(iso_head_s, facecolor='black', alpha=0.2, lw=0, zorder=2)
    ax.add_patch(head1_s)

    # Shadow Arrow 2
    path2_s = create_circular_arrow(225, 380, 15, 28, shadow_z_pos)
    patch2_s = patches.PathPatch(path2_s, facecolor='black', alpha=0.2, lw=0, zorder=2)
    ax.add_patch(patch2_s)
    
    # Shadow Head 2
    iso_head2_s = [iso_transform(x, y, shadow_z_pos) for x, y in head_verts2]
    head2_s = patches.Polygon(iso_head2_s, facecolor='black', alpha=0.2, lw=0, zorder=2)
    ax.add_patch(head2_s)

    # 저장
    plt.tight_layout()
    plt.savefig('app_icon.png', transparent=True, bbox_inches='tight', pad_inches=0)
    print("아이콘 이미지(app_icon.png)가 생성되었습니다.")

    # .ico 변환
    try:
        from PIL import Image
        img = Image.open('app_icon.png')
        img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64)])
        print("아이콘 파일(icon.ico) 변환 완료!")
    except ImportError:
        pass

if __name__ == "__main__":
    create_app_icon()