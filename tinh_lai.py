import os
from datetime import datetime, timedelta
import pandas as pd

def tinh_toan_chi_tiet(so_tien_vay, thoi_han_nam, thoi_han_thang, thoi_han_ngay, lai_suat_nhap, loai_lai_suat, 
                      lai_suat_thoa_thuan_qh, loai_lai_suat_qh, phuong_thuc, ngay_vay, ngay_tra_thuc_te, 
                      list_tha_noi=None, list_thanh_toan=None):
    
    so_tien_vay = float(so_tien_vay or 0)
    thoi_han_nam = int(thoi_han_nam or 0)
    thoi_han_thang = int(thoi_han_thang or 0)
    thoi_han_ngay = int(thoi_han_ngay or 0)
    lai_suat_nhap = float(lai_suat_nhap or 0)
    
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
    so_ngay_quy_dinh = abs((ngay_dao_han_dt - ngay_vay_dt).days)
    
    tha_noi_processed = []
    if list_tha_noi:
        for tn in list_tha_noi:
            if tn.get('rate') and tn.get('from') and tn.get('to'):
                r = float(tn['rate'])
                if tn.get('unit') == 'thang': 
                    r *= 12
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

    du_no_goc_hien_tai = so_tien_vay
    goc_ban_dau_co_dinh = so_tien_vay
    
    tong_lai_trong_han_tich_luy = 0.0
    tong_lai_qua_han_tich_luy = 0.0
    tong_lai_cham_tra_tich_luy = 0.0
    lai_trong_han_chua_tra = 0.0
    
    dien_giai_text = "--- DIỄN GIẢI DÒNG TIỀN VÀ ĐỐI TRỪ NỢ ---\n"
    dien_giai_text += f"Ban đầu: Gốc vay = {so_tien_vay:,.0f}đ. Kỳ hạn: {ngay_vay_dt.strftime('%d/%m/%Y')} đến {ngay_dao_han_dt.strftime('%d/%m/%Y')} ({so_ngay_quy_dinh} ngày).\n\n"
    
    base_rate_nam = lai_suat_nhap * 12 if loai_lai_suat == 'thang' else lai_suat_nhap
    
    curr_date = min(ngay_vay_dt, ngay_tra_dt)
    end_date = max(ngay_vay_dt, ngay_tra_dt)
    total_days_simulation = abs((end_date - curr_date).days)
    
    while curr_date < end_date:
        day_next = curr_date + timedelta(days=1)
        
        active_rate = base_rate_nam
        for tn in tha_noi_processed:
            if tn['from'] <= curr_date <= tn['to']:
                active_rate = tn['rate']
                break
                
        # Bộ lọc kiểm soát trần pháp luật (Tối đa 20%/năm cho trong hạn)
        if active_rate > 20.0:
            active_rate = 20.0
            
        days_in_year = 360 if curr_date < moc_thong_tu_dt else 365
        is_qua_han = (curr_date >= ngay_dao_han_dt)
        
        if not is_qua_han:
            co_so_tinh_goc = goc_ban_dau_co_dinh if phuong_thuc == "goc_ban_dau" else du_no_goc_hien_tai
            daily_interest = co_so_tinh_goc * ((active_rate / 100) / days_in_year)
            tong_lai_trong_han_tich_luy += daily_interest
            lai_trong_han_chua_tra += daily_interest
        else:
            if lai_suat_thoa_thuan_qh:
                rate_qh = float(lai_suat_thoa_thuan_qh)
                if loai_lai_suat_qh == 'thang':
                    rate_qh *= 12
                # Bộ lọc trần quá hạn (Tối đa 150% của trần trong hạn = 30%/năm)
                if rate_qh > 30.0: 
                    rate_qh = 30.0
            else:
                rate_qh = active_rate * 1.5
                if rate_qh > 30.0: 
                    rate_qh = 30.0
                
            daily_lqh = du_no_goc_hien_tai * ((rate_qh / 100) / days_in_year)
            tong_lai_qua_han_tich_luy += daily_lqh
            
            daily_lct = lai_trong_han_chua_tra * ((10.0 / 100) / days_in_year)
            tong_lai_cham_tra_tich_luy += daily_lct

        if day_next in thanh_toan_processed:
            pay_info = thanh_toan_processed[day_next]
            g_paid = pay_info['goc']
            l_paid = pay_info['lai']
            
            old_goc = du_no_goc_hien_tai
            old_lai_th = lai_trong_han_chua_tra
            
            du_no_goc_hien_tai = max(0.0, du_no_goc_hien_tai - g_paid)
            lai_trong_han_chua_tra = max(0.0, lai_trong_han_chua_tra - l_paid)
            
            dien_giai_text += f"Mốc {day_next.strftime('%d/%m/%Y')}: Khấu trừ giữa kỳ -> Gốc giảm còn {du_no_goc_hien_tai:,.0f}đ; Lãi giảm còn {lai_trong_han_chua_tra:,.0f}đ.\n"

        curr_date = day_next

    dien_giai_text += f"\nKết quả chốt dữ liệu kiểm sát:\n"
    dien_giai_text += f"Tổng số ngày chạy mô phỏng: {total_days_simulation} ngày.\n"
    dien_giai_text += f"Dư nợ gốc còn lại sau đối trừ: {du_no_goc_hien_tai:,.0f} VNĐ\n"
    dien_giai_text += f"Lãi trong hạn chưa trả còn lại: {lai_trong_han_chua_tra:,.0f} VNĐ\n"
    dien_giai_text += f"Lãi quá hạn phát sinh tính trên nợ gốc: {tong_lai_qua_han_tich_luy:,.0f} VNĐ\n"
    dien_giai_text += f"Lãi chậm trả phát sinh tính trên tiền lãi: {tong_lai_cham_tra_tich_luy:,.0f} VNĐ\n"

    tong_cong_nghia_vu = du_no_goc_hien_tai + lai_trong_han_chua_tra + tong_lai_qua_han_tich_luy + tong_lai_cham_tra_tich_luy
    he_so_nam = max(1, total_days_simulation) / 365.0
    he_so_thang = max(1, total_days_simulation) / 30.4167
    
    # Cập nhật mảng kết quả: Hàng tổng không chia đều nữa, dồn xuống mảng Trung Bình
    matrix_data = {
        "goc": {"thang": du_no_goc_hien_tai / he_so_thang, "nam": du_no_goc_hien_tai / he_so_nam, "tong": du_no_goc_hien_tai},
        "lth": {"thang": lai_trong_han_chua_tra / he_so_thang, "nam": lai_trong_han_chua_tra / he_so_nam, "tong": lai_trong_han_chua_tra},
        "lqh": {"thang": tong_lai_qua_han_tich_luy / he_so_thang, "nam": tong_lai_qua_han_tich_luy / he_so_nam, "tong": tong_lai_qua_han_tich_luy},
        "lct": {"thang": tong_lai_cham_tra_tich_luy / he_so_thang, "nam": tong_lai_cham_tra_tich_luy / he_so_nam, "tong": tong_lai_cham_tra_tich_luy},
        "tong": {"tong": tong_cong_nghia_vu},
        "tb_ky_han": {"thang": tong_cong_nghia_vu / he_so_thang, "nam": tong_cong_nghia_vu / he_so_nam}
    }
    
    excel_filename = "Bao_cao_dong_tien_kiem_sat.xlsx"
    os.makedirs("static", exist_ok=True)
    excel_filepath = os.path.join("static", excel_filename)
    
    ls_qh_display = f"{lai_suat_thoa_thuan_qh} %/{loai_lai_suat_qh}" if lai_suat_thoa_thuan_qh else "150% lãi trong hạn"
    
    t1 = "--- THÔNG TIN KHOẢN VAY BAN ĐẦU ---"
    t2 = "--- DIỄN GIẢI QUÁ TRÌNH TÍNH TOÁN ---"
    t3 = "--- KẾT QUẢ CHỐT ĐẾN NGÀY XÉT XỬ ---"
    
    excel_rows = [
        {"Hạng mục": t1, "Nội dung chi tiết": ""},
        {"Hạng mục": "Số tiền gốc vay ban đầu", "Nội dung chi tiết": f"{so_tien_vay:,.0f} VNĐ"},
        {"Hạng mục": "Ngày cho vay", "Nội dung chi tiết": ngay_vay_dt.strftime('%d/%m/%Y')},
        {"Hạng mục": "Ngày tất toán (Xét xử)", "Nội dung chi tiết": ngay_tra_dt.strftime('%d/%m/%Y')},
        {"Hạng mục": "Mức lãi suất trong hạn", "Nội dung chi tiết": f"{lai_suat_nhap} %/{loai_lai_suat}"},
        {"Hạng mục": "Lãi suất thỏa thuận quá hạn", "Nội dung chi tiết": ls_qh_display},
        {"Hạng mục": "Phương thức tính toán", "Nội dung chi tiết": "Dư nợ giảm dần" if phuong_thuc == "du_no_giam_dan" else "Gốc cố định"},
        {"Hạng mục": "Thời hạn vay hợp đồng", "Nội dung chi tiết": f"{thoi_han_nam} Năm, {thoi_han_thang} Tháng, {thoi_han_ngay} Ngày"},
        {"Hạng mục": "Ngày đáo hạn dự kiến", "Nội dung chi tiết": ngay_dao_han_dt.strftime('%d/%m/%Y')},
        {"Hạng mục": "Tổng số ngày thực tế", "Nội dung chi tiết": f"{total_days_simulation} ngày"},
        {"Hạng mục": "", "Nội dung chi tiết": ""},
        {"Hạng mục": t2, "Nội dung chi tiết": ""}
    ]
    
    for line in dien_giai_text.split("\n"):
        if line.strip() and "---" not in line:
            excel_rows.append({"Hạng mục": "Diễn giải nghiệp vụ", "Nội dung chi tiết": line.strip()})
            
    excel_rows.extend([
        {"Hạng mục": "", "Nội dung chi tiết": ""},
        {"Hạng mục": t3, "Nội dung chi tiết": ""},
        {"Hạng mục": "1. Dư nợ gốc còn lại", "Nội dung chi tiết": f"{du_no_goc_hien_tai:,.0f} VNĐ"},
        {"Hạng mục": "2. Lãi trong hạn tồn đọng", "Nội dung chi tiết": f"{lai_trong_han_chua_tra:,.0f} VNĐ"},
        {"Hạng mục": "3. Lãi quá hạn tích lũy", "Nội dung chi tiết": f"{tong_lai_qua_han_tich_luy:,.0f} VNĐ"},
        {"Hạng mục": "4. Lãi chậm trả tích lũy", "Nội dung chi tiết": f"{tong_lai_cham_tra_tich_luy:,.0f} VNĐ"},
        {"Hạng mục": "TỔNG CỘNG NGHĨA VỤ", "Nội dung chi tiết": f"{tong_cong_nghia_vu:,.0f} VNĐ"}
    ])
    
    pd.DataFrame(excel_rows).to_excel(excel_filepath, index=False)
    
    return {
        "matrix": matrix_data,
        "excel_url": f"/static/{excel_filename}",
        "so_ngay_thuc_te": total_days_simulation,
        "dien_giai": dien_giai_text
    }