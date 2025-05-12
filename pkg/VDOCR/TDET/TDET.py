# TDET - Table DETection

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

import numpy as np
import cv2

MIN_INTERSECT_POINTS_TO_FORM_A_LINE = 2
MIN_LINES_TO_FORM_A_TABLE = 5

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

def clustering_idx(ls, max_distance):
    # max_distance: max distance between 2 points in 1 cluster
    # Return clusters, each cluster contains indexs of the numbers in original list
    ls = np.array(ls)
    sorted_indices = np.argsort(ls)
    split_points = np.where(np.diff(ls[sorted_indices]) > max_distance)[0] + 1
    clusters = np.split(sorted_indices, split_points)
    return clusters

def merge_lsd_lines(lsd_lines_clusters, KERNEL_SIZE, idx0=1, idx1=0, idx2=3, idx3=2):
    lsd_lines = []
    in_between_points = []
    for cluster in lsd_lines_clusters:

        avg_y = int(sum([l[idx1] for l in cluster]) / len(cluster)) # Initial avg_y, = average of all lines
        for l1 in cluster:
            flag = False
            for l2 in cluster:
                if l1 != l2:
                    if not (l1[idx0] <= l2[idx0] and l1[idx2] >= l2[idx2]):
                        flag = True; break
            if flag == False:
                avg_y = l1[idx1]; break # If there is a line that wraps all other lines, set avg_y to this line

        min_x = min([e for l in cluster for e in (l[idx0], l[idx2])])
        max_x = max([e for l in cluster for e in (l[idx0], l[idx2])])

        wtf_breakpoints = [(min_x, avg_y)] if idx0==0 else [(avg_y, min_x)]
        for wtf in range(min_x+1, max_x, KERNEL_SIZE):
            flag = False
            for l in cluster:
                if l[idx0]-int(1.5*KERNEL_SIZE) <= wtf <= l[idx2]+int(1.5*KERNEL_SIZE): # 🍌 1.5*KERNEL_SIZE
                    flag = True; break
            if flag == False:
                wtf_breakpoints.append((wtf, avg_y) if idx0==0 else (avg_y, wtf))
                in_between_points.append((wtf, avg_y) if idx0==0 else (avg_y, wtf))
        wtf_breakpoints.append((max_x, avg_y) if idx0==0 else (avg_y, max_x))

        for i in range(len(wtf_breakpoints)-1):
            min_xx = float('inf')
            max_xx = float('-inf')
            for l in cluster:
                if wtf_breakpoints[i][idx0] <= (l[idx0]+l[idx2])/2 <= wtf_breakpoints[i+1][idx0]:
                    min_xx = min([min_xx, l[idx0], l[idx2]])
                    max_xx = max([max_xx, l[idx0], l[idx2]])
            if min_xx != float('inf') and max_xx != float('-inf'):
                if idx0 == 0:
                    lsd_lines.append((min_xx-int(1.5*KERNEL_SIZE), avg_y, max_xx+int(1.5*KERNEL_SIZE), avg_y)) # 🍌 1.5*KERNEL_SIZE
                elif idx0 == 1:
                    lsd_lines.append((avg_y, min_xx-int(1.5*KERNEL_SIZE), avg_y, max_xx+int(1.5*KERNEL_SIZE))) # 🍌 1.5*KERNEL_SIZE
    return lsd_lines, in_between_points

def line_intersection(line1, line2):
    (x1, y1, x2, y2) = line1
    (x3, y3, x4, y4) = line2
    # Calculate the determinants
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    # If denominator is 0, the lines are parallel or coincident
    if denominator == 0:
        return None  # No intersection
    # Compute the intersection point
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator
    # Check if the intersection point is within the bounds of both line segments
    if (min(x1, x2) <= px <= max(x1, x2) and min(y1, y2) <= py <= max(y1, y2) and
        min(x3, x4) <= px <= max(x3, x4) and min(y3, y4) <= py <= max(y3, y4)):
        return (int(px), int(py))
    return None  # Intersection point is outside the line segments

def merge_lists_same_item(lst):
    # [[10, 17], [14, 20], [17, 22]] -> [[10, 17, 22], [14, 20]]
    graph = {}  
    for sub in lst:
        for num in sub:
            graph.setdefault(num, set()).update(sub)
    def dfs(node, component):
        if node in visited:
            return
        visited.add(node)
        component.append(node)
        for neighbor in graph[node]:
            dfs(neighbor, component)
    visited, merged = set(), []
    for num in graph:
        if num not in visited:
            component = []
            dfs(num, component)
            merged.append(sorted(component))
    return merged

def get_bottom_right(right_points, bottom_points, points):
    for bottom in bottom_points:
        for right in right_points:
            if (right[0], bottom[1]) in points:
                return right[0], bottom[1]
    return None, None

def is_point_on_line(point, line):
    x0,y0 = point
    x1,y1,x2,y2 = line
    # line is horizontal
    if y0 == y1 == y2:
        if x1 < x0 < x2:
            return True
    # line is vertical
    if x0 == x1 == x2:
        if y1 < y0 < y2:
            return True
    return False

def is_bbox_in_bbox(bb1, bb2):
    if bb1[0]>=bb2[0] and bb1[2]<=bb2[2] and bb1[1]>=bb2[1] and bb1[3]<=bb2[3]:
        return True
    return False

def count_items(lst):
    counts = {}
    for item in lst:
        counts[item] = counts.get(item, 0) + 1
    return counts

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

def Process_TDET(img_ocv):
    KERNEL_SIZE = (img_ocv.shape[0] + img_ocv.shape[1]) // 200
    KERNEL_H = cv2.getStructuringElement(cv2.MORPH_RECT, (KERNEL_SIZE, 1))
    KERNEL_V = cv2.getStructuringElement(cv2.MORPH_RECT, (1, KERNEL_SIZE))

    # img_bin
    img_gray = cv2.cvtColor(img_ocv, cv2.COLOR_BGR2GRAY)
    _thresh, img_bin = cv2.threshold(img_gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    img_bin = 255-img_bin
    # img_bin (h & v)
    img_bin_h = cv2.dilate(cv2.erode(img_bin, KERNEL_H, iterations=3), KERNEL_H, iterations=3)
    img_bin_v = cv2.dilate(cv2.erode(img_bin, KERNEL_V, iterations=3), KERNEL_V, iterations=3)
    # lsd_lines (h & v)
    lsd_lines_h = [[int(e) for e in l[0]] for l in cv2.createLineSegmentDetector().detect(img_bin_h)[0]]
    lsd_lines_v = [[int(e) for e in l[0]] for l in cv2.createLineSegmentDetector().detect(img_bin_v)[0]]
    # clusters (h & v)
    lsd_lines_h_clusters = [[lsd_lines_h[idx] for idx in c] for c in clustering_idx(ls=[y1 for _,y1,_,_ in lsd_lines_h], max_distance=KERNEL_SIZE)]
    lsd_lines_v_clusters = [[lsd_lines_v[idx] for idx in c] for c in clustering_idx(ls=[x1 for x1,_,_,_ in lsd_lines_v], max_distance=KERNEL_SIZE)]
    # merged_lsd_lines (h & v)
    merged_lsd_lines_h, in_between_points_h = merge_lsd_lines(lsd_lines_h_clusters, KERNEL_SIZE, idx0=0, idx1=1, idx2=2, idx3=3)
    merged_lsd_lines_v, in_between_points_v = merge_lsd_lines(lsd_lines_v_clusters, KERNEL_SIZE, idx0=1, idx1=0, idx2=3, idx3=2)
    in_between_points = in_between_points_h + in_between_points_v

    # tables_lines: lines that intersect are group into lists
    tables_lines = []
    for l_h in merged_lsd_lines_h:
        for l_v in merged_lsd_lines_v:
            if line_intersection(l_h, l_v):
                tables_lines.append([l_h, l_v])
    tables_lines = merge_lists_same_item(tables_lines)
    tables_lines = [e for e in tables_lines if len(e) >= MIN_LINES_TO_FORM_A_TABLE]

    # tables_intersects: intersect points of lines
    tables_intersects = []
    for tbl_lines in tables_lines:
        tmp = []
        for i in range(len(tbl_lines)):
            for u in range(i+1, len(tbl_lines)):
                point_intersect = line_intersection(tbl_lines[i], tbl_lines[u])
                if point_intersect:
                    tmp.append(point_intersect)
        tables_intersects.append(tmp)

    # tables_cells
    tables_cells = []
    for tbl_intersects in tables_intersects:
        # table_cells: init
        table_cells = []
        for point in tbl_intersects:
            x1, y1 = point
            right_points = sorted([p for p in tbl_intersects if p[0] > x1 and p[1] == y1], key=lambda x: x[0])
            bottom_points = sorted([p for p in tbl_intersects if p[1] > y1 and p[0] == x1], key=lambda x: x[1])
            x2, y2 = get_bottom_right(right_points, bottom_points, tbl_intersects)
            if x2 and y2:
                # merge_down
                merge_down = False
                line_bottom = (x1,y2,x2,y2)
                for pp in in_between_points:
                    if is_point_on_line(pp, line_bottom):
                        merge_down = True
                        break
                # merge_right
                merge_right = False
                line_right = (x2,y1,x2,y2)
                for pp in in_between_points:
                    if is_point_on_line(pp, line_right):
                        merge_right = True
                        break
                # cell
                table_cells.append({
                    "bbox": (x1, y1, x2, y2),
                    "merge_down": merge_down,
                    "merge_right": merge_right,
                })
        # table_cells: remove un-merged cells and add merged cells
        unmerged_cells_idx = []
        for i, cella in enumerate(table_cells):
            if cella['merge_down']:
                ax1,ay1,ax2,ay2 = cella['bbox']
                # Find the cell down
                for u, cellb in enumerate(table_cells):
                    bx1,by1,bx2,by2 = cellb['bbox']
                    if ay2==by1 and ax1==bx1 and ax2==bx2:
                        unmerged_cells_idx.append([i, u])
                        break
            if cella['merge_right']:
                ax1,ay1,ax2,ay2 = cella['bbox']
                # Find the cell right
                for u, cellb in enumerate(table_cells):
                    bx1,by1,bx2,by2 = cellb['bbox']
                    if ax2==bx1 and ay1==by1 and ay2==by2:
                        unmerged_cells_idx.append([i, u])
                        break
        unmerged_cells_idx = merge_lists_same_item(unmerged_cells_idx)
        new_merged_cells = []
        for group in unmerged_cells_idx:
            x1 = min([table_cells[i]['bbox'][0] for i in group])
            y1 = min([table_cells[i]['bbox'][1] for i in group])
            x2 = max([table_cells[i]['bbox'][2] for i in group])
            y2 = max([table_cells[i]['bbox'][3] for i in group])
            new_merged_cells.append({
                "bbox": (x1, y1, x2, y2),
                "merge_down": True in [table_cells[i]['merge_down'] for i in group],
                "merge_right": True in [table_cells[i]['merge_right'] for i in group],
            })
        table_cells = [e for i, e in enumerate(table_cells) if i not in [ii for ee in unmerged_cells_idx for ii in ee]]
        table_cells = table_cells + new_merged_cells
        # table_cells: remove inside-other-cells cells
        inside_other_cells_idx = []
        for i in range(len(table_cells)):
            for u in range(len(table_cells)):
                if i != u and is_bbox_in_bbox(table_cells[i]['bbox'], table_cells[u]['bbox']):
                    inside_other_cells_idx.append(i)
        table_cells = [e for i, e in enumerate(table_cells) if i not in inside_other_cells_idx]
        # table_cells: Add information: row_id, col_id, row_span, col_span
        xs = sorted([item for item, count in count_items([p[0] for p in tbl_intersects]).items() if count > MIN_INTERSECT_POINTS_TO_FORM_A_LINE])
        ys = sorted([item for item, count in count_items([p[1] for p in tbl_intersects]).items() if count > MIN_INTERSECT_POINTS_TO_FORM_A_LINE])
        for i, cell in enumerate(table_cells):
            x1,y1,x2,y2 = cell['bbox']
            try:
                ix1,iy1,ix2,iy2 = xs.index(x1), ys.index(y1), xs.index(x2), ys.index(y2)
                table_cells[i]['row_id'] = iy1
                table_cells[i]['col_id'] = ix1
                table_cells[i]['row_span'] = iy2-iy1
                table_cells[i]['col_span'] = ix2-ix1
            except Exception as e:
                print(f"⚠️ TDET > Error at xs/ys > {e}")
                table_cells[i]['row_id'] = len(ys)-1
                table_cells[i]['col_id'] = len(xs)-1
                table_cells[i]['row_span'] = 1
                table_cells[i]['col_span'] = 1
        # Return
        tables_cells.append(table_cells)

    # # ---------------------------------------------------------------------------------------------------- Just to visualize
    # from pkg.UTILS.UTILS import show_ocv_multiple
    # # lsd_lines
    # img_tmp_1 = img_ocv.copy()
    # for x1,y1,x2,y2 in lsd_lines_h: cv2.line(img_tmp_1, (x1,y1), (x2,y2), (255,0,0), 2)
    # for x1,y1,x2,y2 in lsd_lines_v: cv2.line(img_tmp_1, (x1,y1), (x2,y2), (0,0,255), 2)
    # # merged_lsd_lines
    # img_tmp_2 = img_ocv.copy()
    # for x1,y1,x2,y2 in merged_lsd_lines_h: cv2.line(img_tmp_2, (x1,y1), (x2,y2), (255,0,0), 2)
    # for x1,y1,x2,y2 in merged_lsd_lines_v: cv2.line(img_tmp_2, (x1,y1), (x2,y2), (0,0,255), 2)
    # # tables_lines, tables_intersects, in_between_points
    # img_tmp_3 = img_ocv.copy()
    # for lines, intersects in zip(tables_lines, tables_intersects):
    #     for x1,y1,x2,y2 in lines: cv2.line(img_tmp_3, (x1,y1), (x2,y2), (255,0,0), 2)
    #     for x0,y0 in intersects: cv2.circle(img_tmp_3, (x0,y0), 5, (0,0,255), -1)
    # for x0,y0 in in_between_points: cv2.circle(img_tmp_3, (x0,y0), 4, (0,155,255), -1)
    # # tables_cells
    # img_tmp_4 = img_ocv.copy()
    # for tbl in tables_cells:
    #     for i, cell in enumerate(tbl):
    #         x1,y1,x2,y2 = cell['bbox']
    #         cv2.rectangle(img_tmp_4, (x1+3,y1+3), (x2-3,y2-3), (0,0,255), 2)
    #         if cell['row_span'] > 1 or cell['col_span'] > 1: cv2.putText(img_tmp_4, f"{cell['row_id']}/{cell['col_id']}/{cell['row_span']}/{cell['col_span']}", (x1+2,y1+18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,155,0), 2)
    #         else: cv2.putText(img_tmp_4, f"{cell['row_id']}/{cell['col_id']}", (x1+2,y1+18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
    # # show_ocv_multiple
    # show_ocv_multiple([img_ocv, img_bin, img_bin_h, img_bin_v], ["img_ocv", "img_bin", "img_bin_h", "img_bin_v"])
    # show_ocv_multiple([img_tmp_1, img_tmp_2, img_tmp_3, img_tmp_4], ["lsd_lines", "merged_lsd_lines", "tables_lines, tables_intersects, in_between_points", "tables_cells"])

    # ----------------------------------------------------------------------------------------------------
    return table_cells