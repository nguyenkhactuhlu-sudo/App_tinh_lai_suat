import os
from datetime import datetime, timedelta
import pandas as pd

def tinh_toan_chi_tiet(so_tien_vay, thoi_han_nam, thoi_han_thang, thoi_han_ngay, lai_suat_nhap, loai_lai_suat, 
                      lai_suat_thoa_thuan_qh, loai_lai_suat_qh, phuong_thuc, ngay_vay, ngay_tra_thuc_te, 
                      list_tha_noi=None, list_thanh_toan=None):
    
    # 1. XỬ LÝ CÁC MỐC THỜI GIAN CƠ BẢN
    ngay_vay_dt = datetime.strptime(ngay_vay, '%Y-%m-%d')
    ngay_tra_dt = datetime.strptime(ngay_tra_thuc_te, '%Y-%m-%d')
    moc_thong_tu_dt = datetime.strptime('2018-01-01', '%Y-%m-%d')
    
    try:
        ngay_dao_han_dt = ngay_vay_dt.replace(year=ngay_vay_dt.year + thoi_han_nam)
    except ValueError:
        ngay_dao_han_dt = ngay_vay_dt + timedelta(days=365 * thoi_han_nam)
    
    thang_hien_tai = ngay_dao_han_dt.month
    nam_hien_tai = ngay_dao_han_dt.year
    for _ in range(thoi_han_thang):
        thang_hien_tai += 1
        if thang_hien_tai > 12:
            thang_hien_tai = 1
            nam_hien_tai += 1
            
    ngay_tam = ngay_dao_han_dt.day
    while True:
        try:
            ngay_dao_han_dt = ngay_dao_han_dt.replace(year=nam_hien_tai, month=thang_hien_tai, day=ngay_tam)
            break
        except ValueError:
            ngay_tam -= 1
    ngay_dao_han_dt += timedelta(days=thoi_han_ngay)
    so_ngay_quy_dinh = (ngay_dao_han_dt - ngay_vay_dt).days
    
    # 2. XỬ LÝ DỮ LIỆU LÃI SUẤT THẢ NỔI VÀ NHẬT KÝ THANH TOÁN
    tha_noi_processed = []
    if list_tha_noi:
        for tn in list_tha_noi:
            if tn.get('rate') and tn.get('from') and tn.get('to'):
                r = float(tn['rate'])
                if tn.get('unit') == 'thang': r *= 12
                tha_noi_processed.append({
                    'rate': r,
                    'from': datetime.strptime(tn['from'], '%Y-%m-%d'),
                    'to': datetime.strptime(tn['to'], '%Y-%m-%d')
                })
                
    thanh_toan_processed = {}
    if list_thanh_toan:
        for tt in list_thanh_toan:
            if tt.get('date'):
                d_dt = datetime.strptime(tt['date'], '%Y-%m-%d')
                goc_tra = float(tt['goc']) if tt.get('goc') else 0.0
                lai_tra = float(tt['lai']) if tt.get('lai') else 0.0
                if d_dt in thanh_toan_processed:
                    thanh_toan_processed[d_dt]['goc'] += goc_tra
                    thanh_toan_processed[d_dt]['lai'] += lai_tra
                else:
                    thanh_toan_processed[d_dt] = {'goc': goc_tra, 'lai': lai_tra}

    # 3. KHỞI TẠO BIẾN DƯ NỢ VÀ TÍCH LŨY
    du_no_goc_hien_tai = so_tien_vay
    goc_ban_dau_co_dinh = so_tien_vay
    
    tong_lai_trong_han_tich_luy = 0.0
    tong_lai_qua_han_tich_luy = 0.0
    tong_lai_cham_tra_tich_luy = 0.0
    lai_trong_han_chua_tra = 0.0
    
    base_rate_nam = lai_suat_nhap * 12 if loai_lai_suat == 'thang' else lai_suat_nhap
    curr_date = ngay_vay_dt
    total_days_simulation = (ngay_tra_dt - ngay_vay_dt).days
    
    # 4. CHUẨN BỊ XUẤT BÁO CÁO VÀ FILE EXCEL
    dien_giai_text = "=== BÁO CÁO SAO KÊ CHI TIẾT TỪNG THÁNG ===\n"
    dien_giai_text += f"THÔNG TIN BAN ĐẦU:\n"
    dien_giai_text += f"- Nợ gốc vay: {so_tien_vay:,.0f} VNĐ\n"
    dien_giai_text += f"- Kỳ hạn vay: {ngay_vay_dt.strftime('%d/%m/%Y')} đến {ngay_dao_han_dt.strftime('%d/%m/%Y')} ({so_ngay_quy_dinh} ngày).\n"
    dien_giai_text += "="*60 + "\n\n"
    
    txt_lai_qh_excel = f"{lai_suat_thoa_thuan_qh} %/{loai_lai_suat_qh}" if lai_suat_thoa_thuan_qh else 'Mặc định bằng 150% lãi trong hạn'
    excel_rows = [
        {"Hạng mục": "--- THÔNG TIN VỀ KHOẢN VAY VÀ LÃI SUẤT THỎA THUẬN BAN ĐẦU ---", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "Số tiền gốc vay ban đầu", "Nội dung chi tiết": ngay_vay_dt.strftime('%d/%m/%Y'), "Giá trị (VNĐ)": f"{so_tien_vay:,.0f}"},
        {"Hạng mục": "Ngày tất toán khoản vay", "Nội dung chi tiết": ngay_tra_dt.strftime('%d/%m/%Y'), "Giá trị (VNĐ)": ""},
        {"Hạng mục": "Lãi suất trong hạn", "Nội dung chi tiết": f"{lai_suat_nhap} %/{loai_lai_suat}", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "Lãi suất quá hạn", "Nội dung chi tiết": txt_lai_qh_excel, "Giá trị (VNĐ)": ""},
        {"Hạng mục": "Ngày đáo hạn dự kiến", "Nội dung chi tiết": ngay_dao_han_dt.strftime('%d/%m/%Y'), "Giá trị (VNĐ)": ""},
        {"Hạng mục": "", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "--- BÁO CÁO SAO KÊ DÒNG TIỀN VÀ ĐỐI TRỪ CHI TIẾT THEO THÁNG ---", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""}
    ]

    # CÁC BIẾN THEO DÕI RIÊNG CHO TỪNG THÁNG
    current_month_str = curr_date.strftime('%m/%Y') if total_days_simulation > 0 else ""
    m_start_date = curr_date
    m_goc_dau = du_no_goc_hien_tai
    m_lai_trong_han_dau = lai_trong_han_chua_tra
    m_lai_qua_han_dau = tong_lai_qua_han_tich_luy
    m_lai_cham_tra_dau = tong_lai_cham_tra_tich_luy
    
    m_lai_trong_han_ps = 0.0
    m_lai_qua_han_ps = 0.0
    m_lai_cham_tra_ps = 0.0
    m_goc_tra = 0.0
    m_lai_tra = 0.0
    m_nhat_ky_tra = []
    m_so_ngay_trong_thang = 0

    # 5. CHẠY VÒNG LẶP MÔ PHỎNG TỪNG NGÀY
    while curr_date < ngay_tra_dt:
        day_next = curr_date + timedelta(days=1)
        m_so_ngay_trong_thang += 1
        
        # Xác định lãi suất áp dụng
        active_rate = base_rate_nam
        for tn in tha_noi_processed:
            if tn['from'] <= curr_date <= tn['to']:
                active_rate = tn['rate']
                break
        if active_rate > 20.0: active_rate = 20.0
            
        days_in_year = 360 if curr_date < moc_thong_tu_dt else 365
        is_qua_han = (curr_date >= ngay_dao_han_dt)
        
        # Tính toán phát sinh hàng ngày
        if not is_qua_han:
            co_so_tinh_goc = goc_ban_dau_co_dinh if phuong_thuc == "goc_ban_dau" else du_no_goc_hien_tai
            daily_interest = co_so_tinh_goc * ((active_rate / 100) / days_in_year)
            tong_lai_trong_han_tich_luy += daily_interest
            lai_trong_han_chua_tra += daily_interest
            m_lai_trong_han_ps += daily_interest
        else:
            if lai_suat_thoa_thuan_qh:
                rate_qh = float(lai_suat_thoa_thuan_qh)
                if loai_lai_suat_qh == 'thang': rate_qh *= 12
                if rate_qh > 30.0: rate_qh = 30.0
            else:
                rate_qh = active_rate * 1.5
                if rate_qh > 30.0: rate_qh = 30.0
                
            daily_lqh = du_no_goc_hien_tai * ((rate_qh / 100) / days_in_year)
            tong_lai_qua_han_tich_luy += daily_lqh
            m_lai_qua_han_ps += daily_lqh
            
            daily_lct = lai_trong_han_chua_tra * ((10.0 / 100) / days_in_year)
            tong_lai_cham_tra_tich_luy += daily_lct
            m_lai_cham_tra_ps += daily_lct

        # Ghi nhận thanh toán nếu có
        if day_next in thanh_toan_processed:
            pay_info = thanh_toan_processed[day_next]
            g_paid = pay_info['goc']
            l_paid = pay_info['lai']
            
            m_goc_tra += g_paid
            m_lai_tra += l_paid
            m_nhat_ky_tra.append(f"Ngày {day_next.strftime('%d/%m/%Y')}: Trả Gốc {g_paid:,.0f}đ, Trả Lãi {l_paid:,.0f}đ")
            
            du_no_goc_hien_tai = max(0.0, du_no_goc_hien_tai - g_paid)
            lai_trong_han_chua_tra = max(0.0, lai_trong_han_chua_tra - l_paid)

        # CHỐT SỔ KHI HẾT THÁNG LỊCH HOẶC ĐẾN NGÀY KẾT THÚC
        is_month_end = (day_next.month != curr_date.month) or (day_next == ngay_tra_dt)
        
        if is_month_end:
            m_end_date = curr_date
            tong_ps_thang = m_lai_trong_han_ps + m_lai_qua_han_ps + m_lai_cham_tra_ps
            
            # --- TẠO VĂN BẢN HIỂN THỊ WEB ---
            thang_text = f"🗓️ KỲ SAO KÊ THÁNG: {current_month_str} (Từ ngày {m_start_date.strftime('%d/%m/%Y')} đến {m_end_date.strftime('%d/%m/%Y')} - Số ngày: {m_so_ngay_trong_thang})\n"
            
            thang_text += f"  ▶ [ĐẦU KỲ] Dư nợ tồn đọng chuyển sang:\n"
            thang_text += f"    - Nợ gốc: {m_goc_dau:,.0f} VNĐ\n"
            thang_text += f"    - Lãi tồn đọng: {m_lai_trong_han_dau:,.0f} VNĐ\n"
            
            thang_text += f"  ▶ [PHÁT SINH PHẢI TRẢ] Nghĩa vụ phát sinh thêm trong tháng này: +{tong_ps_thang:,.0f} VNĐ\n"
            if m_lai_trong_han_ps > 0:
                thang_text += f"    - Tiền lãi trong hạn: +{m_lai_trong_han_ps:,.0f} VNĐ\n"
            if m_lai_qua_han_ps > 0:
                thang_text += f"    - Tiền lãi quá hạn (tính trên gốc): +{m_lai_qua_han_ps:,.0f} VNĐ\n"
            if m_lai_cham_tra_ps > 0:
                thang_text += f"    - Tiền lãi chậm trả (tính trên lãi): +{m_lai_cham_tra_ps:,.0f} VNĐ\n"
                
            thang_text += f"  ▶ [ĐÃ THANH TOÁN] Đương sự nộp trả thực tế trong tháng: Gốc đã trả {m_goc_tra:,.0f} VNĐ | Lãi đã trả {m_lai_tra:,.0f} VNĐ\n"
            if m_nhat_ky_tra:
                for nk in m_nhat_ky_tra:
                    thang_text += f"    ↳ Chi tiết: {nk}\n"
            else:
                thang_text += f"    ↳ (Không có giao dịch thanh toán nào trong tháng này)\n"
                
            thang_text += f"  ▶ [CUỐI KỲ CÒN LẠI] Dư nợ chốt cuối tháng chuyển sang kỳ sau:\n"
            thang_text += f"    - Nợ gốc còn lại: {du_no_goc_hien_tai:,.0f} VNĐ\n"
            thang_text += f"    - Lãi trong hạn còn lại: {lai_trong_han_chua_tra:,.0f} VNĐ\n"
            thang_text += "-"*60 + "\n"
            
            dien_giai_text += thang_text
            
            # --- TẠO DỮ LIỆU ĐƯA VÀO EXCEL ---
            excel_rows.append({"Hạng mục": f"--- CHI TIẾT THÁNG {current_month_str} ---", "Nội dung chi tiết": f"Từ {m_start_date.strftime('%d/%m/%Y')} đến {m_end_date.strftime('%d/%m/%Y')}", "Giá trị (VNĐ)": ""})
            excel_rows.append({"Hạng mục": "[ĐẦU KỲ] Dư nợ gốc", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_goc_dau:,.0f}"})
            excel_rows.append({"Hạng mục": "[ĐẦU KỲ] Lãi tồn đọng", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_trong_han_dau:,.0f}"})
            excel_rows.append({"Hạng mục": "[PHÁT SINH PHẢI TRẢ] Lãi trong hạn", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_trong_han_ps:,.0f}"})
            excel_rows.append({"Hạng mục": "[PHÁT SINH PHẢI TRẢ] Lãi quá hạn", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_qua_han_ps:,.0f}"})
            excel_rows.append({"Hạng mục": "[PHÁT SINH PHẢI TRẢ] Lãi chậm trả", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_cham_tra_ps:,.0f}"})
            excel_rows.append({"Hạng mục": "[ĐÃ THANH TOÁN] Tiền gốc nộp trả", "Nội dung chi tiết": " | ".join(m_nhat_ky_tra) if m_nhat_ky_tra else "Không phát sinh", "Giá trị (VNĐ)": f"{m_goc_tra:,.0f}"})
            excel_rows.append({"Hạng mục": "[ĐÃ THANH TOÁN] Tiền lãi nộp trả", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_tra:,.0f}"})
            excel_rows.append({"Hạng mục": "[CUỐI KỲ CÒN LẠI] Dư nợ gốc", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{du_no_goc_hien_tai:,.0f}"})
            excel_rows.append({"Hạng mục": "[CUỐI KỲ CÒN LẠI] Lãi tồn đọng", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{lai_trong_han_chua_tra:,.0f}"})
            excel_rows.append({"Hạng mục": "", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""})
            
            # Khởi tạo lại biến cho tháng tiếp theo
            if day_next < ngay_tra_dt:
                current_month_str = day_next.strftime('%m/%Y')
                m_start_date = day_next
                m_goc_dau = du_no_goc_hien_tai
                m_lai_trong_han_dau = lai_trong_han_chua_tra
                m_lai_qua_han_dau = tong_lai_qua_han_tich_luy
                m_lai_cham_tra_dau = tong_lai_cham_tra_tich_luy
                m_lai_trong_han_ps = 0.0
                m_lai_qua_han_ps = 0.0
                m_lai_cham_tra_ps = 0.0
                m_goc_tra = 0.0
                m_lai_tra = 0.0
                m_nhat_ky_tra = []
                m_so_ngay_trong_thang = 0
        
        curr_date = day_next

    # 6. TỔNG KẾT KẾT QUẢ CUỐI CÙNG SAU KHI KẾT THÚC VÒNG LẶP
    dien_giai_text += f"\n=== KẾT QUẢ CHỐT SỐ LIỆU TỔNG HỢP KIỂM SÁT ===\n"
    dien_giai_text += f"1. Tổng số ngày chạy mô phỏng: {total_days_simulation} ngày.\n"
    dien_giai_text += f"2. Dư nợ gốc còn lại cần thu hồi: {du_no_goc_hien_tai:,.0f} VNĐ\n"
    dien_giai_text += f"3. Lãi trong hạn chưa trả còn lại: {lai_trong_han_chua_tra:,.0f} VNĐ\n"
    dien_giai_text += f"4. Tổng lãi quá hạn tích lũy (trên gốc): {tong_lai_qua_han_tich_luy:,.0f} VNĐ\n"
    dien_giai_text += f"5. Tổng lãi chậm trả tích lũy (trên lãi): {tong_lai_cham_tra_tich_luy:,.0f} VNĐ\n"

    tong_cong_nghia_vu = du_no_goc_hien_tai + lai_trong_han_chua_tra + tong_lai_qua_han_tich_luy + tong_lai_cham_tra_tich_luy
    
    # 7. XUẤT RA EXCEL
    excel_filename = "Bao_cao_dong_tien_kiem_sat.xlsx"
    os.makedirs("static", exist_ok=True)
    excel_filepath = os.path.join("static", excel_filename)
    
    excel_rows.extend([
        {"Hạng mục": "--- KẾT QUẢ TỔNG HỢP CUỐI CÙNG CHỐT DỮ LIỆU ĐẾN NGÀY XÉT XỬ ---", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "1. Dư nợ gốc còn lại (Đã đối trừ)", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{du_no_goc_hien_tai:,.0f}"},
        {"Hạng mục": "2. Lãi trong hạn tồn đọng", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{lai_trong_han_chua_tra:,.0f}"},
        {"Hạng mục": "3. Lãi quá hạn tích lũy (trên gốc)", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{tong_lai_qua_han_tich_luy:,.0f}"},
        {"Hạng mục": "4. Lãi chậm trả tích lũy (trên lãi)", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{tong_lai_cham_tra_tich_luy:,.0f}"},
        {"Hạng mục": "TỔNG CỘNG NGHĨA VỤ TÀI CHÍNH CHỐT SAU ĐỐI TRỪ", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{tong_cong_nghia_vu:,.0f}"}
    ])
    
    pd.DataFrame(excel_rows).to_excel(excel_filepath, index=False)
    
    # 8. TÍNH BẢNG MA TRẬN HIỂN THỊ
    he_so_nam = max(1, total_days_simulation) / 365.0
    he_so_thang = max(1, total_days_simulation) / 30.4167
    
    matrix_data = {
        "goc": {"thang": du_no_goc_hien_tai / he_so_thang, "nam": du_no_goc_hien_tai / he_so_nam, "tong": du_no_goc_hien_tai},
        "lth": {"thang": lai_trong_han_chua_tra / he_so_thang, "nam": lai_trong_han_chua_tra / he_so_nam, "tong": lai_trong_han_chua_tra},
        "lqh": {"thang": tong_lai_qua_han_tich_luy / he_so_thang, "nam": tong_lai_qua_han_tich_luy / he_so_nam, "tong": tong_lai_qua_han_tich_luy},
        "lct": {"thang": tong_lai_cham_tra_tich_luy / he_so_thang, "nam": tong_lai_cham_tra_tich_luy / he_so_nam, "tong": tong_lai_cham_tra_tich_luy},
        "tong": {"thang": tong_cong_nghia_vu / he_so_thang, "nam": tong_cong_nghia_vu / he_so_nam, "tong": tong_cong_nghia_vu}
    }
    
    return {
        "matrix": matrix_data,
        "excel_url": f"/static/{excel_filename}",
        "so_ngay_thuc_te": total_days_simulation,
        "dien_giai": dien_giai_text
    }