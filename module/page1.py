import streamlit as st
import mysql.connector
import pandas as pd
import requests

def menu_1():
    st.header("รายการสินค้า stock")

    def send_line_notify(message):
        token = "Lp802z4Gdwr47zDcF7ZWTRFK5FiHubsZO16lC1UQmSm"  # LINE Notify Access Token ของคุณ
        headers = {
            "Authorization": f"Bearer {token}"
        }
        max_length = 950  # กำหนดความยาวสูงสุดของข้อความในแต่ละชุด (รวม header)

        # แบ่งข้อความออกเป็นชุด ๆ ตามความยาวที่กำหนด
        message_parts = [message[i:i + max_length] for i in range(0, len(message), max_length)]
        
        # ส่งแต่ละชุดข้อความแยกกัน
        for part in message_parts:
            payload = {
                "message": part
            }
            response = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=payload)
            
            # ตรวจสอบสถานะการส่งของแต่ละชุด
            if response.status_code != 200:
                print("การส่งข้อมูลล้มเหลว:", response.text)
                return response.status_code
        
        return 200  # หากส่งสำเร็จทุกชุด
    
    def get_database_connection():
        return mysql.connector.connect(
            host="192.168.1.123",     # แทนที่ด้วย host ของคุณ
            user="admin",             # แทนที่ด้วยชื่อผู้ใช้ MySQL ของคุณ
            password="admin1234",     # แทนที่ด้วยรหัสผ่านของคุณ
            database="data_stock"     # แทนที่ด้วยชื่อฐานข้อมูลที่ต้องการใช้
        )

    # ฟังก์ชันดึงข้อมูลจากฐานข้อมูล
    def load_data():
        conn = get_database_connection()
        query = "SELECT * FROM product_stock"  # ดึงทุกคอลัมน์จากตาราง product_stock
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    # โหลดข้อมูล
    data = load_data()

    # คัดลอกข้อมูลที่ต้องการแสดง โดยไม่แสดงคอลัมน์ id ในตาราง
    data_to_display = data[["product_id", "product_detail", "product_stock"]].copy()

    # เติมค่าที่เป็น NaN ในคอลัมน์ product_id ด้วย ""
    data_to_display["product_id"] = data_to_display["product_id"].fillna("")

    # ช่องป้อนข้อมูลจำนวนสต็อกที่ต้องการกรอง
    col1, col2 = st.columns([1, 6])
    with col1:
        stock_threshold = st.number_input("สินค้าที่จำนวนต่ำกว่า", min_value=0, step=1, value=0, format="%d")
    
    # กรองข้อมูลตามจำนวนสต็อกที่ต่ำกว่า
    if stock_threshold > 0:
        result_data = data_to_display[data_to_display["product_stock"] < stock_threshold]
    else:
        result_data = data_to_display

    # แสดงตารางข้อมูลแบบอ่านอย่างเดียว
    st.dataframe(result_data, height=800, width=1300)


    if st.button("ส่งข้อมูลผ่าน LINE"):
        # กรองข้อมูลที่ต่ำกว่า stock_threshold
        filtered_data = result_data[result_data['product_stock'] < stock_threshold]

        # จัดรูปแบบข้อความ
        message = f"จำนวนสินค้าที่น้อยกว่า : {stock_threshold}\n"
        for _, row in filtered_data.iterrows():
            message += f"{row['product_id']} : {row['product_stock']} ชิ้น\n"

        # ส่งข้อมูลผ่าน LINE
        if filtered_data.empty:
            st.warning("ไม่มีสินค้าที่จำนวนต่ำกว่าเกณฑ์ที่กำหนด")
        else:
            result = send_line_notify(message)
            if result == 200:
                st.success("ส่งข้อมูลสำเร็จ!")
            else:
                st.error("การส่งข้อมูลล้มเหลว")
