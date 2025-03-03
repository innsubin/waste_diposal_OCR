import numpy as np
 
import cv2
import re
import datetime
import os
from soynlp.hangle import jamo_levenshtein

import easyocr

# 일자
def datevalue():
    all_texts = []
    bbox_lu_points = []
    max_y_lst = []
    min_y_lst = []
    min_x_lst = []
    date_y = 0
    i0 = 0
    # 날짜 텍스트 발견 횟수 저장
    count_day = 0

    # result[0] = (bbox 4개 좌표, 인식결과, 신뢰도)
    for index, r in enumerate(result):
        # 인식 결과, 띄어쓰기 제거
        text = r[1].replace(' ', '').replace(',','') 
        # 인식된 모든 텍스트 결과들 저장
        all_texts.append(text) 
        # 인식된 바운딩 박스 모서리 4개 좌표
        point_list = r[0] 
        # 바운딩 박스 모서리 4개 좌표 리스트 -> 튜플 형태로 변환
        pts = [tuple(points) for points in point_list] 
        # 4개의 좌표가 있는 pts 중 가장 왼쪽 상단 좌표들만 저장
        bbox_lu_points.append(pts[0])
        # 각 바운딩 박스에 대한 x 좌표와 y 좌표 최대최소값을 찾고 저장
        x_coords = [point[0] for point in pts]
        y_coords = [point[1] for point in pts]
        min_x = min(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        max_y_lst.append(max_y)
        min_y_lst.append(min_y)
        min_x_lst.append(min_x)
        # 바운딩 박스의 높이
        distance_y = max_y - min_y 
        
        # 날짜 텍스트가 대부분 위에 있기 때문에 최초의 발견 시 종료
        if count_day == 0:
            # 텍스트 결과가 2023 또는 2024를 포함하는 경우 
            if re.search(r'2023|2024', text):
                # 그 때의 바운딩 박스의 높이
                date_y = distance_y
                # 결과 텍스트의 인덱스
                i0 = index
                count_day += 1

    strdate = ''
    maxy0 = 0
    miny0 = 0
    dt = []
    
    # 날짜 텍스트를 찾지 못했을 경우(초기 설정해둔 인덱스 값 = 0)
    if date_y == 0:
        strdate = 'error'
    # 날짜 텍스트를 찾은 경우
    else:
        # 바운딩 박스 길이에 0.33 비율씩 길이 추가해줌
        maxy0 = max_y_lst[i0] + date_y * 0.33
        miny0 = min_y_lst[i0] - date_y * 0.33
        # 바운딩 박스의 왼쪽 상단 좌표에서 y좌표만 추출해서 길이를 늘린 바운딩 박스 범위에 들어가는 지 확인
        for p in range(len(bbox_lu_points)):
            if miny0 <= bbox_lu_points[p][1] <= maxy0:
                # 포함된다면 그 때의 x 좌표와 텍스트 결과를 하나의 튜플로 저장
                dt.append((bbox_lu_points[p][0], all_texts[p]))
        if dt:
            # 중복제거 및 정렬
            dt = list(set(dt))
            sorted_dt = sorted(dt, key=lambda x: x[0])
            date_digits = []
            for x, text in sorted_dt:
                # 숫자만 추출
                numbers = re.findall(r'\d+', text)  
                for num in numbers:
                    # 숫자들을 이어붙임
                    date_digits.extend(num)
                    if len(date_digits) >= 8:
                        break
                    else:
                        continue
                    break
            # 8자리만 출력        
            strdate = ''.join(date_digits)[:8]
        else:
            strdate = 'error'      
    return strdate

# 차량번호
def carnum():
    # 유사도 측정을 위한 초기 값
    distance1 = 999
    all_texts = []
    bbox_lu_points = []
    max_y_lst = []
    min_y_lst = []
    min_x_lst = []
    carkey_y = 0
    i1 = 0
    mx1 = 0
    
    # result[0] = (bbox 4개 좌표, 인식결과, 신뢰도)
    for index, r in enumerate(result):
        # 인식 결과, 띄어쓰기 제거
        text = r[1].replace(' ', '').replace(',','').replace('.','')
        # 인식된 모든 텍스트 결과들 저장
        all_texts.append(text)
        # 인식된 바운딩 박스 모서리 4개 좌표
        point_list = r[0] 
        # 바운딩 박스 모서리 4개 좌표 리스트 -> 튜플 형태로 변환
        pts = [tuple(points) for points in point_list] 
        # 4개의 좌표가 있는 pts 중 가장 왼쪽 상단 좌표들만 저장
        bbox_lu_points.append(pts[0])
        # 각 바운딩 박스에 대한 x 좌표와 y 좌표 최대최소값을 찾고 저장
        x_coords = [point[0] for point in pts]
        y_coords = [point[1] for point in pts]
        max_x = max(x_coords)
        min_x = min(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        min_x_lst.append(min_x)
        min_y_lst.append(min_y)
        max_y_lst.append(max_y)
        # 바운딩 박스의 높이
        distance_y = max_y - min_y 

        # dic1 : 계량전표에 쓰이는 '차량번호'를 의미하는 key 값들
        for i in dic1:
            # 유사도 측정
            jamo_distance1 = jamo_levenshtein(i, text)
            # 가장 유사도가 작은 값을 최종 key 값으로 판단
            if jamo_distance1 < distance1:
                distance1 = jamo_distance1
                # 가장 작은 유사도를 가진 값의 바운딩 박스 높이
                carkey_y = distance_y
                # 결과 텍스트의 인덱스
                i1 = index
                # 그 때의 가장 큰 x 좌표 값
                mx1 = max_x
                
    strcar = 'error'
    maxy1 = 0
    miny1 = 0
    
    # key 텍스트를 찾지 못했을 경우(초기 설정해둔 높이 = 0)
    if carkey_y == 0:
        strcar = 'error'
    # key 텍스트를 찾은 경우
    else:
        # 바운딩 박스 길이에 0.35 비율씩 길이 추가해줌
        maxy1 = max_y_lst[i1] + carkey_y * 0.35
        miny1 = min_y_lst[i1] - carkey_y * 0.35
        # key 값과 차량번호 사이의 거리 초기값
        distance11 = 9999
        # 바운딩 박스의 왼쪽 상단 좌표에서 y좌표만 추출해서 길이를 늘린 바운딩 박스 범위에 들어가는 지 확인
        for p in range(len(bbox_lu_points)):
            # key 값이 되는 바운딩 박스의 좌표는 포함 x
            if p != i1:
                # 확장된 바운딩 박스 y 범위에 있는 값들만 찾음 
                if miny1 <= bbox_lu_points[p][1] <= maxy1:
                    # 각 바운딩 박스의 최소 값 확인, key 바운딩 박스 x 최대값보다는 크면서 가장 가까운 값을 찾음 
                    for minx in min_x_lst:
                        if 0 < minx - mx1 <= distance11:
                            # 텍스트에 숫자가 하나라도 있으면 true
                            if any(char.isdigit() for char in all_texts[p]): 
                                distance11 = minx - mx1
                                strcar = all_texts[p]
    return strcar

# 총중량
def totalweight():
    # 유사도 측정을 위한 초기 값
    distance2 = 999
    all_texts = []
    bbox_lu_points = []
    max_y_lst = []
    min_y_lst = []
    min_x_lst = []
    totalweight_y = 0
    i2 = 0
    mx2 = 0
    # result[0] = (bbox 4개 좌표, 인식결과, 신뢰도)
    for index, r in enumerate(result):
        # 인식 결과, 띄어쓰기 제거
        text = r[1].replace(' ', '').replace(',','').replace('.','') 
        # 인식된 모든 텍스트 결과들 저장
        all_texts.append(text) 
        # 인식된 바운딩 박스 모서리 4개 좌표
        point_list = r[0] 
        # 바운딩 박스 모서리 4개 좌표 리스트 -> 튜플 형태로 변환
        pts = [tuple(points) for points in point_list] 
        # 4개의 좌표가 있는 pts 중 가장 왼쪽 상단 좌표들만 저장
        bbox_lu_points.append(pts[0]) 
        # 각 바운딩 박스에 대한 x 좌표와 y 좌표 최대최소값을 찾고 저장
        x_coords = [point[0] for point in pts]
        y_coords = [point[1] for point in pts]
        max_x = max(x_coords)
        min_x = min(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        min_x_lst.append(min_x)
        min_y_lst.append(min_y)
        max_y_lst.append(max_y)
        # 바운딩 박스의 높이
        distance_y = max_y - min_y 
        
        # dic1 : 계량전표에 쓰이는 '총중량'을 의미하는 key 값들
        for i in dic2:
            # 유사도 측정
            jamo_distance2 = jamo_levenshtein(i, text)
            # 가장 유사도가 작은 값을 최종 key 값으로 판단
            if jamo_distance2 < distance2:
                distance2 = jamo_distance2
                # 가장 작은 유사도를 가진 값의 바운딩 박스 높이
                totalweight_y = distance_y
                # 결과 텍스트의 인덱스
                i2 = index
                # 그 때의 가장 큰 x 좌표 값
                mx2 = max_x
                
    strwt = ''
    maxy2 = 0
    miny2 = 0
    # key 값 바운딩 박스 라인에 위치한 여러 value 값들
    weighttotal = []
    
    # key 텍스트를 찾지 못했을 경우(초기 설정해둔 높이 = 0)
    if totalweight_y == 0:
        strwt = 'error'
    # key 텍스트를 찾은 경우
    else:
        # 바운딩 박스 길이에 0.4 비율씩 길이 추가해줌
        maxy2 = max_y_lst[i2] + totalweight_y * 0.4
        miny2 = min_y_lst[i2] - totalweight_y * 0.4
        # 바운딩 박스의 왼쪽 상단 좌표에서 y좌표만 추출해서 길이를 늘린 바운딩 박스 범위에 들어가는 지 확인
        for p in range(len(bbox_lu_points)):
            # key 값이 되는 바운딩 박스의 좌표는 포함 x
            if p != i2:
                # 확장된 바운딩 박스 y 범위에 있는 값들만 찾음 
                if miny2 <= bbox_lu_points[p][1] <= maxy2:
                    # 각 바운딩 박스의 최소 값 확인, key 바운딩 박스 x 최대값보다는 크면서 가장 가까운 값을 찾음 
                    for minx in min_x_lst:
                        # value 값들이 여러 개기 때문에 저장
                        if 0 < minx - mx2:
                            weighttotal.append((bbox_lu_points[p][0], all_texts[p].replace(',','').replace('.','')))
        # 저장된 값이 있다면
        if weighttotal:
            # 중복 제거 및 정렬(오름차순)
            # 같은 라인에 시간 - 무게 순으로 입력되어있기 때문에 뒤에서부터
            weighttotal = list(set(weighttotal))
            sorted_weighttotal = sorted(weighttotal, key=lambda x: x[0], reverse=True)
            # 두 가지 이상의 value 값이 들어온 경우
            if len(sorted_weighttotal) >= 2:
                # 첫 번째 요소의 텍스트가 특정 패턴(kg, ko, ka, k9, k8, k0)을 포함하는지 확인
                if re.search(r'(\bkg\b|\bko\b|\bka\b|\bk9\b|\bk8\b|\bk0\b)', sorted_weighttotal[0][1], re.IGNORECASE):
                    # 두 번째 요소의 텍스트가 2자리 숫자를 포함하는지 확인
                    if re.search(r'\d{2}', sorted_weighttotal[1][1]):
                        strwt = sorted_weighttotal[1][1]
                    else:
                        strwt = 'error'
                # 첫 번째 요소의 텍스트가 2자리 숫자를 포함하는지 확인
                elif re.search(r'\d{2}', sorted_weighttotal[0][1]):
                    strwt = sorted_weighttotal[0][1]
                else:
                    strwt = 'error'
            # 정렬된 리스트가 1개만 있는 경우
            else:
                if re.search(r'(kg|ko|ka|k9|k8|k0)', sorted_weighttotal[0][1], re.IGNORECASE):
                    strwt = sorted_weighttotal[0][1]
                else:
                    strwt = 'error'
        else:
            strwt = 'error'
    return strwt

## (시간) (무게) (kg) 
## (시간) (무게)
## (무게kg)

# 공차중량
def emptyweight():
    distance3 = 999
    all_texts = []
    bbox_lu_points = []
    max_y_lst = []
    min_y_lst = []
    min_x_lst = []
    i3 = 0
    emptycarweight_y = 0
    mx3 = 0
    for index, r in enumerate(result):
        ## result[0] = (bbox 4개 좌표, 인식결과, 신뢰도)
        text = r[1].replace(' ', '').replace(',','').replace('.','') # 인식 결과, 띄어쓰기 제거
        all_texts.append(text) # 모든 텍스트 저장
        point_list = r[0] # bbox 4개 좌표
        pts = [tuple(points) for points in point_list] # 4개 좌표 리스트 -> 튜플 형태로 변환
        bbox_lu_points.append(pts[0]) # 전체 결과에서 대한 각각의 좌표값 중 가장 왼쪽 상단 좌표만 저장
        x_coords = [point[0] for point in pts]
        y_coords = [point[1] for point in pts]
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        max_y_lst.append(max_y)
        min_y_lst.append(min_y)
        min_x_lst.append(min_x)
        distance_y = max_y - min_y # bbox의 높이

        for i in dic3:
            jamo_distance3 = jamo_levenshtein(i, text)
            if jamo_distance3 < distance3:
                distance3 = jamo_distance3
                emptycarweight_y = distance_y
                i3 = index
                mx3 = max_x
    strecw = ''
    maxy3 = 0
    miny3 = 0
    ecw = []
    if emptycarweight_y == 0:
        strecw = 'error'
    else:
        maxy3 = max_y_lst[i3] + emptycarweight_y * 0.4
        miny3 = min_y_lst[i3] - emptycarweight_y * 0.4
        for p in range(len(bbox_lu_points)):
            if p != i3:
                if miny3 <= bbox_lu_points[p][1] <= maxy3:
                    for minx in min_x_lst:
                        if 0 < minx - mx3:
                            ecw.append((bbox_lu_points[p][0], all_texts[p].replace(',','').replace('.',''))) # x좌표와 그에 대한 결과값
        if ecw:
            ecw = list(set(ecw))
            sorted_ecw = sorted(ecw, key=lambda x: x[0], reverse=True)
            if len(sorted_ecw) >= 2:
                if re.search(r'(\bkg\b|\bko\b|\bka\b|\bk9\b|\bk8\b|\bk0\b)', sorted_ecw[0][1], re.IGNORECASE):
                    if re.search(r'\d{2}', sorted_ecw[1][1]):
                        strecw = sorted_ecw[1][1]
                    else:
                        strecw = 'error'
                elif re.search(r'\d{2}', sorted_ecw[0][1]):
                    strecw = sorted_ecw[0][1]
                else:
                    strecw = 'error'
            else:
                if re.search(r'(kg|ko|ka|k9|k8|k0)', sorted_ecw[0][1], re.IGNORECASE):
                    strecw = sorted_ecw[0][1]
                else:
                    strecw = 'error'
        else:
            strecw = 'error'
        if re.search(r':|;', strecw):
            strecw = 0
    return strecw

# 실중량
def realweight():
    distance4 = 999
    all_texts = []
    bbox_lu_points = []
    max_y_lst = []
    min_y_lst = []
    min_x_lst = []
    i4 = 0
    realweight_y = 0
    mx4 = 0

    for index, r in enumerate(result):
        ## result[0] = (bbox 4개 좌표, 인식결과, 신뢰도)
        text = r[1].replace(' ', '').replace(',','').replace('.','') # 인식 결과, 띄어쓰기 제거
        all_texts.append(text) # 모든 텍스트 저장
        point_list = r[0] # bbox 4개 좌표
        pts = [tuple(points) for points in point_list] # 4개 좌표 리스트 -> 튜플 형태로 변환
        bbox_lu_points.append(pts[0]) # 전체 결과에서 대한 각각의 좌표값 중 가장 왼쪽 상단 좌표만 저장
        x_coords = [point[0] for point in pts]
        y_coords = [point[1] for point in pts]
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        max_y_lst.append(max_y)
        min_y_lst.append(min_y)
        min_x_lst.append(min_x)
        distance_y = max_y - min_y # bbox의 높이

        for i in dic4:
            jamo_distance4 = jamo_levenshtein(i, text)
            if jamo_distance4 < distance4:
                distance4 = jamo_distance4
                realweight_y = distance_y
                i4 = index
                mx4 = max_x
    strrw = ''
    maxy4 = 0
    miny4 = 0
    rw = []
    if realweight_y == 0:
        strrw = 'error'
    else:
        maxy4 = max_y_lst[i4] + realweight_y * 0.4
        miny4 = min_y_lst[i4] - realweight_y * 0.4
        for p in range(len(bbox_lu_points)):
            if p != i4:
                if miny4 <= bbox_lu_points[p][1] <= maxy4:
                    for minx in min_x_lst:
                        if 0 < minx - mx4:
                            rw.append((bbox_lu_points[p][0], all_texts[p].replace(',','').replace('.',''))) # x좌표와 그에 대한 결과값
        if rw:
            rw = list(set(rw))
            sorted_rw = sorted(rw, key=lambda x: x[0], reverse=True)
            if len(sorted_rw) >= 2:
                if re.search(r'(\bkg\b|\bko\b|\bka\b|\bk9\b|\bk8\b|\bk0\b)', sorted_rw[0][1], re.IGNORECASE):
                    if re.search(r'\d{2}', sorted_rw[1][1]):
                        strrw = sorted_rw[1][1]
                    else:
                        strrw = 'error'
                elif re.search(r'\d{2}', sorted_rw[0][1]):
                    strrw = sorted_rw[0][1]
                else:
                    strrw = 'error'
            else:
                if re.search(r'(kg|ko|ka|k9|k8|k0)', sorted_rw[0][1], re.IGNORECASE):
                    strrw = sorted_rw[0][1]
                else:
                    strrw = 'error'
        else:
            strrw = 'error'
    return strrw

# 품목
def objname():
    distance5 = 999
    all_texts = []
    bbox_lu_points = []
    max_y_lst = []
    min_y_lst = []
    min_x_lst = []
    i5 = 0
    obj_y = 0

    for index, r in enumerate(result):
        ## result[0] = (bbox 4개 좌표, 인식결과, 신뢰도)
        text = r[1].replace(' ', '').replace(',','').replace('.','') # 인식 결과, 띄어쓰기 제거
        all_texts.append(text) # 모든 텍스트 저장
        point_list = r[0] # bbox 4개 좌표
        pts = [tuple(points) for points in point_list] # 4개 좌표 리스트 -> 튜플 형태로 변환
        bbox_lu_points.append(pts[0]) # 전체 결과에서 대한 각각의 좌표값 중 가장 왼쪽 상단 좌표만 저장
        x_coords = [point[0] for point in pts]
        y_coords = [point[1] for point in pts]
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        max_y_lst.append(max_y)
        min_y_lst.append(min_y)
        min_x_lst.append(min_x)
        distance_y = max_y - min_y # bbox의 높이

        for i in dic5:
            jamo_distance5 = jamo_levenshtein(i, text)
            if jamo_distance5 < distance5:
                distance5 = jamo_distance5
                obj_y = distance_y
                i5 = index
                mx5 = max_x
    strobj = ''
    maxy5 = 0
    miny5 = 0
    ob = []
    if obj_y == 0:
        strobj = 'error'
    else:
        maxy5 = max_y_lst[i5] + obj_y * 0.4
        miny5 = min_y_lst[i5] - obj_y * 0.4
        for p in range(len(bbox_lu_points)):
            if p != i5:
                if miny5 <= bbox_lu_points[p][1] <= maxy5:
                    for minx in min_x_lst:
                        if 0 < minx - mx5:
                            ob.append((bbox_lu_points[p][0], all_texts[p].replace(',','').replace('.',''))) # x좌표와 그에 대한 결과값
        if ob:
            ob = list(set(ob))
            sorted_ob = sorted(ob, key=lambda x: x[0], reverse=True)
            for item in sorted_ob:
                if re.search(r'[가-힣]{2,}', item[1]):
                    strobj = item[1]
                    break
                else:
                    strobj = 'error'
        else:
            strobj = 'error'
    return strobj


input_folder = 'C:/Users/sblim/Desktop/tt/'
txt_path = 'C:/Users/sblim/Desktop/result.txt'

# 차량번호, 총중량, 공차중량, 실중량 사전
dic1 = ['차량번호', '차번호', '차량NO.', '차량', 'CAR NO.(차량번호)', 'I.D. 차량번호', '차량번호Vcl NO.', '차량/계량일자', '차량번호VdNo.', '일자/차량번호', '차량및카드번호', '차량번호Vd No.']
dic2 = ['총중량', '총중량(kg)', '총중량및시간', '총량', 'GROSS(총중량)', 'GROSS총중량', '총중량(GROSS)', '총중량kg', '총량G/W', '총중량G/W', '총중량/시간']
dic3 = ['공차중량', '공차계량', '공차중량(kg)', '공중량', '공차량', '공차량및시간', '공차', '차중량', 'TARE(차중량)', 'TARE공차중량', 'TARE차중량', '공차계량', '공차량', '감량중량', '공차중량(TARE)', '차중량kg', '중량공차', '공차중량TR/W', '공차량(TARE)', '공차량/시간', '공차량및시간', '']
dic4 = ['실중량', '적재중량', '감량,실중량', '인수량', '실중량kg', '실중량N/W', '실중량(GROSS)', '실중량/입출', '실중량/감량', '실제중량']
dic5 = ['품목', '품명', '제품', '품목명', '제품명', '품목1', '폐기물종류', 'ITEM(품명)', '폐기물의종류', '품명/C.N.', '종목', '종류', '자재명','운송품명', '품명CARGO', '반출품목']

count = 1

for file in os.listdir(input_folder):
    if file == 'desktop.ini':
        continue
    image_path = os.path.join(input_folder, file)
    
    reader = easyocr.Reader(['en', 'ko'], gpu=False) 
    
    image = cv2.imread(image_path)
    # 가로가 세로보다 큰 경우, 회전된 계량전표라 판단
    if image.shape[0] >= image.shape[1]:
        # 전처리
        # 이미지가 조금씩 기울어져 있을 때, 크게 기울어진 가로 윤곽선을 찾아 수평을 맞춤
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
        horizontal_lines = []
        max_distance = 0
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if abs(angle) < 10 or abs(angle - 180) < 10:
                distance = abs(y2 - y1)
                if distance > max_distance:
                    max_distance = distance
                    horizontal_lines = [(x1, y1, x2, y2, angle)]
        if horizontal_lines:
            (x1, y1, x2, y2, angle) = horizontal_lines[0]
            angle = angle / 2
            center = (image.shape[1] // 2, image.shape[0] // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated_image = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))
            result = reader.readtext(rotated_image)
        else:
            result = reader.readtext(image_path)

        f = datevalue() # 일자
        t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # 판독일자
        a = carnum() # 차량번호
        b = totalweight() # 총중량
        c = emptyweight() # 공차중량
        d = realweight() # 실중량
        e = objname() # 품목
        
        print(count, t, file, f, a, b, c, d, e)
#         with open(txt_path, 'a') as f:
#             f.write(f"D30 {t} {count} {file} {f} {a} {b} {c} {d} {e} \n")        
    else:
        print(count, t, file, '세로로재촬영')
#         with open(txt_path, 'a') as f:
#             f.write(f"{count} {t} {file} {'직접입력'} {'직접입력'} {'직접입력'} {'직접입력'} {'직접입력'} {'직접입력'} \n")
    count += 1
    
print('종료')