import streamlit as st
import pandas as pd
import io
import base64

# --- 初始化 Session State (模擬資料庫與設定檔) ---
def init_state():
    # 預設管理員密碼
    if 'admin_password' not in st.session_state:
        st.session_state['admin_password'] = '131419'
    
    # 團購全域設定
    if 'config' not in st.session_state:
        st.session_state['config'] = {
            'title': '好物團購',
            'description': '歡迎來到我們的團購，請填寫下方表單訂購。',
            'bg_image': None,
            'text_color': '#000000',
            'bg_color': '#FFFFFF'
        }
    
    # 商品清單 (結構: [{'name': str, 'price': int, 'image': bytes, 'desc': str}])
    if 'products' not in st.session_state:
        st.session_state['products'] = []
    
    # 訂單資料
    if 'orders' not in st.session_state:
        st.session_state['orders'] = []

    # 登入狀態
    if 'is_logged_in' not in st.session_state:
        st.session_state['is_logged_in'] = False

init_state()

# --- 輔助函式：CSS 樣式注入 ---
def set_bg_hack(main_bg_file, bg_color, text_color):
    """
    設定背景圖片與文字顏色
    """
    style = f"""
    <style>
    .stApp {{
        background-color: {bg_color};
    }}
    .stMarkdown, .stText, h1, h2, h3, label {{
        color: {text_color} !important;
    }}
    </style>
    """
    
    if main_bg_file is not None:
        # 如果有上傳背景圖，將其轉換為 base64 並應用
        main_bg_ext = "png"
        main_bg_bytes = main_bg_file.getvalue()
        main_bg_b64 = base64.b64encode(main_bg_bytes).decode()
        
        style += f"""
        <style>
        .stApp {{
            background-image: url(data:image/{main_bg_ext};base64,{main_bg_b64});
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* 增加一個半透明遮罩讓文字清楚一點 */
        .block-container {{
            background-color: rgba(255, 255, 255, 0.85);
            padding: 2rem;
            border-radius: 10px;
        }}
        </style>
        """
    
    st.markdown(style, unsafe_allow_html=True)

# --- 頁面 1: 管理後台 ---
def admin_page():
    st.title("⚙️ 團購小幫手 - 管理後台")

    # 登入驗證
    if not st.session_state['is_logged_in']:
        password = st.text_input("請輸入管理員密碼", type="password")
        if st.button("登入"):
            if password == st.session_state['admin_password']:
                st.session_state['is_logged_in'] = True
                st.rerun()
            else:
                st.error("密碼錯誤")
        return

    # 登入後顯示內容
    st.success("已登入管理員模式")
    
    # 修改密碼區塊
    with st.expander("🔐 修改登入密碼"):
        new_pass = st.text_input("新密碼", type="password")
        if st.button("更新密碼"):
            st.session_state['admin_password'] = new_pass
            st.success("密碼已更新！")

    # 分頁管理
    tab1, tab2, tab3 = st.tabs(["📝 團購設定", "📦 商品管理", "📊 訂單匯出"])

    with tab1:
        st.subheader("基本資訊與外觀")
        st.session_state['config']['title'] = st.text_input("團購名稱", st.session_state['config']['title'])
        st.session_state['config']['description'] = st.text_area("團購說明", st.session_state['config']['description'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state['config']['text_color'] = st.color_picker("文字顏色", st.session_state['config']['text_color'])
        with col2:
            st.session_state['config']['bg_color'] = st.color_picker("背景底色 (若無圖片)", st.session_state['config']['bg_color'])
            
        bg_file = st.file_uploader("上傳背景圖片", type=['png', 'jpg', 'jpeg'])
        if bg_file:
            st.session_state['config']['bg_image'] = bg_file
        
        if st.session_state['config']['bg_image']:
            st.image(st.session_state['config']['bg_image'], caption="目前背景預覽", width=200)

    with tab2:
        st.subheader("商品上架")
        
        # 新增商品表單
        with st.form("add_product_form", clear_on_submit=True):
            p_name = st.text_input("商品名稱")
            p_desc = st.text_input("商品介紹/規格")
            p_price = st.number_input("價格", min_value=0, step=1)
            p_img = st.file_uploader("商品圖片", type=['png', 'jpg', 'jpeg'])
            
            submitted = st.form_submit_button("➕ 新增商品")
            if submitted and p_name:
                new_prod = {
                    "name": p_name,
                    "desc": p_desc,
                    "price": p_price,
                    "image": p_img
                }
                st.session_state['products'].append(new_prod)
                st.success(f"已新增：{p_name}")
                st.rerun()

        st.divider()
        st.subheader("目前架上商品")
        if not st.session_state['products']:
            st.info("目前沒有商品，請新增。")
        else:
            for idx, prod in enumerate(st.session_state['products']):
                c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
                with c1:
                    if prod['image']:
                        st.image(prod['image'], use_container_width=True)
                    else:
                        st.text("無圖片")
                with c2:
                    st.markdown(f"**{prod['name']}**")
                    st.caption(prod['desc'])
                with c3:
                    st.text(f"${prod['price']}")
                with c4:
                    if st.button("刪除", key=f"del_{idx}"):
                        st.session_state['products'].pop(idx)
                        st.rerun()

    with tab3:
        st.subheader("訂單管理")
        if not st.session_state['orders']:
            st.warning("目前尚無訂單。")
        else:
            df = pd.DataFrame(st.session_state['orders'])
            
            # 依據寄送方式排序/分類
            df = df.sort_values(by="運送方式")
            
            st.dataframe(df)
            
            # 產出 Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='團購訂單')
                # 自動調整欄寬 (簡單實作)
                worksheet = writer.sheets['團購訂單']
                for i, col in enumerate(df.columns):
                    worksheet.set_column(i, i, 20)
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 下載 Excel 訂單報表",
                data=excel_data,
                file_name="團購訂單.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    if st.button("登出後台"):
        st.session_state['is_logged_in'] = False
        st.rerun()

# --- 頁面 2: 客戶訂購表單 ---
def user_page():
    cfg = st.session_state['config']
    
    # 應用外觀設定
    set_bg_hack(cfg['bg_image'], cfg['bg_color'], cfg['text_color'])
    
    st.title(cfg['title'])
    st.markdown(cfg['description'])
    st.divider()

    with st.form("order_form"):
        st.subheader("1. 訂購人資訊")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("訂購人姓名")
        with col2:
            phone = st.text_input("聯絡電話")

        st.subheader("2. 選擇商品")
        if not st.session_state['products']:
            st.warning("目前無商品可供選購。")
            
        cart = {} # 購物車: {商品名: {'qty': int, 'subtotal': int}}
        total_product_price = 0
        
        for prod in st.session_state['products']:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if prod['image']:
                    st.image(prod['image'], use_container_width=True)
            with c2:
                st.markdown(f"**{prod['name']}** (${prod['price']})")
                st.caption(prod['desc'])
            with c3:
                qty = st.number_input(f"數量", min_value=0, step=1, key=f"user_qty_{prod['name']}")
                if qty > 0:
                    subtotal = qty * prod['price']
                    cart[prod['name']] = f"{prod['name']} x {qty}"
                    total_product_price += subtotal
        
        st.subheader("3. 運送方式")
        shipping_method = st.radio(
            "請選擇運送方式",
            options=["A.便利商店店到店 ($60)", "B.宅配到家 ($80)", "C.自取或免運 ($0)"]
        )
        
        shipping_fee = 0
        address_info = ""
        store_info = "" # 暫存店名
        
        if "A.便利商店" in shipping_method:
            shipping_fee = 60
            store_type = st.radio("選擇超商", ["7-11", "全家"], horizontal=True)
            store_name = st.text_input("請填寫：店名/店號")
            address_info = f"{store_type} - {store_name}"
        elif "B.宅配" in shipping_method:
            shipping_fee = 80
            address_info = st.text_input("請填寫：寄送地址")
        else:
            shipping_fee = 0
            # 提示雖然是自取，但如果要填地址的話 (依據 Prompt 要求：顯示出寄送地址讓客戶填寫)
            st.info("若為自取，地址欄位可填寫『自取』或您的地址。")
            address_info = st.text_input("寄送地址")

        st.subheader("4. 付款方式")
        payment_method = st.radio("請選擇付款方式", ["LINEPAY", "匯款"])
        
        if payment_method == "LINEPAY":
            st.success("✅ 請 LINEPAY 給亞當老師")
        else:
            st.info("""
            🏦 匯款資訊：
            戶名：張誠徽
            銀行：永豐銀行中壢分行
            帳號：02400491141359
            """)
        
        last_5_digit = st.text_input("請填寫匯款帳號後五碼 (或 LINEPAY 暱稱)")
        note = st.text_area("備註欄")

        st.divider()
        # --- 結算區 ---
        final_total = total_product_price + shipping_fee
        
        st.markdown(f"""
        ### 💰 訂單總結
        * 商品總金額：**${total_product_price}**
        * 運費：**${shipping_fee}**
        * **應付總金額：${final_total}**
        """)

        # 提交按鈕
        submitted = st.form_submit_button("送出訂單", type="primary")
        
        if submitted:
            # 驗證
            if not name or not phone:
                st.error("請填寫姓名與電話！")
            elif total_product_price == 0:
                st.error("您尚未選購任何商品！")
            elif "A." in shipping_method and not store_name:
                st.error("請填寫便利商店店名！")
            elif "B." in shipping_method and not address_info:
                st.error("請填寫宅配地址！")
            else:
                # 建立訂單資料
                order_data = {
                    "訂購人姓名": name,
                    "聯絡電話": phone,
                    "訂購內容": ", ".join(cart.values()),
                    "運送方式": shipping_method.split(' ')[0], # 只取 A/B/C 代號或簡稱
                    "地址/店鋪資訊": address_info,
                    "付款方式": payment_method,
                    "後五碼": last_5_digit,
                    "備註": note,
                    "商品總額": total_product_price,
                    "運費": shipping_fee,
                    "總金額": final_total
                }
                st.session_state['orders'].append(order_data)
                st.balloons()
                st.success(f"訂購成功！感謝您的訂購，{name}。")

# --- 主程式進入點 ---
def main():
    st.sidebar.title("導覽列")
    
    # 簡單的路由邏輯
    page = st.sidebar.radio("前往", ["🛒 團購表單 (客戶端)", "🔧 管理後台 (商家端)"])
    
    # 產生「短連結」模擬 (Streamlit 無法直接產生外部短網址，但可顯示當前網址)
    # 這裡顯示一個提示訊息
    if page == "🔧 管理後台 (商家端)":
        st.sidebar.info("💡 提示：設定完成後，請切換至「團購表單」，並複製瀏覽器網址傳給客戶即可。")
    
    if page == "🔧 管理後台 (商家端)":
        admin_page()
    else:
        user_page()

if __name__ == "__main__":
    main()
```

### 功能總結與使用說明

我已經依據您的「團購小幫手」需求，完成了以下功能：

1.  **安全性與後台管理**：
    * 後台登入預設密碼為 `131419`，登入後可隨時修改。
    * 後台介面包含三個分頁：「團購設定」、「商品管理」、「訂單匯出」。

2.  **高度客製化**：
    * 您可以上傳「背景圖片」及設定「文字/背景顏色」，這些設定會即時反映在前台表單。
    * 您可以新增、刪除多個商品項目（含圖片、價格、說明）。

3.  **智慧型前台表單**：
    * **運費邏輯**：選擇不同運送方式（店到店 $60 / 宅配 $80 / 自取 $0），系統會自動切換顯示對應的輸入欄位（如店名或地址），並在最後自動加總運費。
    * **付款資訊**：選擇 LINEPAY 顯示提示文字，選擇匯款顯示永豐銀行帳號。
    * **即時試算**：表單底部會即時顯示「商品總額 + 運費 = 應付總額」。

4.  **報表輸出**：
    * 所有訂單皆儲存在系統中（Session State）。
    * 後台提供 **Excel 下載按鈕**，且列表會依照「運送方式」自動排序分類，方便您出貨。

### 如何執行此程式？

1.  確保您的電腦已安裝 Python。
2.  安裝必要的套件：
    ```bash
    pip install streamlit pandas XlsxWriter
    ```
3.  將上面的程式碼存檔為 `group_buy_app.py`。
4.  在終端機（Terminal）執行：
    ```bash
    streamlit run group_buy_app.py
