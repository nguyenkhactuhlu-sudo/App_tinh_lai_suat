from flask import Flask, render_template, request, jsonify
from tinh_lai import tinh_toan_chi_tiet

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        so_tien_vay = float(data.get('so_tien_vay', 0))
        thoi_han_nam = int(data.get('thoi_han_nam', 0))
        thoi_han_thang = int(data.get('thoi_han_thang', 0))
        thoi_han_ngay = int(data.get('thoi_han_ngay', 0))
        lai_suat_nam = float(data.get('lai_suat_nam', 0))
        loai_lai_suat = data.get('loai_lai_suat', 'nam')
        lai_suat_thoa_thuan_qh = data.get('lai_suat_thoa_thuan_qh', '')
        loai_lai_suat_qh = data.get('loai_lai_suat_qh', 'nam')
        phuong_thuc = data.get('phuong_thuc', 'du_no_giam_dan')
        ngay_vay = data.get('ngay_vay', '')
        ngay_tra_thuc_te = data.get('ngay_tra_thuc_te', '')

        list_tha_noi = data.get('list_tha_noi', [])
        list_thanh_toan = data.get('list_thanh_toan', [])

        if not ngay_vay or not ngay_tra_thuc_te:
            return jsonify({"success": False, "error": "Yêu cầu nhập đầy đủ Ngày vay và Ngày chốt nợ."})

        ket_qua = tinh_toan_chi_tiet(
            so_tien_vay, thoi_han_nam, thoi_han_thang, thoi_han_ngay, lai_suat_nam, loai_lai_suat,
            lai_suat_thoa_thuan_qh, loai_lai_suat_qh, phuong_thuc, ngay_vay, ngay_tra_thuc_te, 
            list_tha_noi, list_thanh_toan
        )
        
        return jsonify({"success": True, "data": ket_qua})

    except Exception as e:
        return jsonify({"success": False, "error": f"Lỗi hệ thống: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)