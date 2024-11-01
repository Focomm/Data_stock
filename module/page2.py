import streamlit as st
import mysql.connector
import pandas as pd

def menu_2():
    st.header("รายการสินค้า stock")
    
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

    # คัดลอกข้อมูลที่ต้องการใช้อัปเดต โดยไม่แสดงคอลัมน์ id ในตาราง
    columns_to_display = ["product_id", "product_detail", "product_stock", "Borrowed", "Claimed", "Waste", "product_quantity"]
    data_to_display = data[columns_to_display].copy()
    data_with_id = data[["id"] + columns_to_display].copy()  # รวม id เพื่อใช้อัปเดตฐานข้อมูล

    # เติมค่าที่เป็น NaN ในคอลัมน์ product_id ด้วย ""
    data_to_display["product_id"] = data_to_display["product_id"].fillna("")

    # เพิ่มช่องค้นหา
    search_query = st.text_input("ค้นหา Product ID", "")

    # กรองข้อมูลตาม Product ID
    if search_query:
        search_query_lower = search_query.lower()
        data_to_display["product_id_lower"] = data_to_display["product_id"].str.lower()
        filtered_data = data_to_display[data_to_display["product_id_lower"].str.contains(search_query_lower, na=False)]
        starts_with_query = filtered_data[filtered_data["product_id_lower"].str.startswith(search_query_lower)]
        contains_query = filtered_data[~filtered_data["product_id_lower"].str.startswith(search_query_lower)]
        result_data = pd.concat([starts_with_query, contains_query])
        result_data.drop(columns=["product_id_lower"], inplace=True)
    else:
        result_data = data_to_display

    # แสดงตารางที่แก้ไขได้โดยไม่มีคอลัมน์ id
    edited_df = st.data_editor(result_data, height=800, width=1300)

    # อัปเดตข้อมูลเมื่อกดปุ่มบันทึก
    if st.button("บันทึกการเปลี่ยนแปลง"):
        # ผนวกข้อมูลที่แก้ไขเข้ากับคอลัมน์ id โดยใช้ `data_with_id` เพื่ออ้างอิง
        updated_df = data_with_id.copy()
        updated_df.update(edited_df)  # อัปเดตเฉพาะคอลัมน์ที่แสดง

        # อัปเดตข้อมูลกลับไปยังฐานข้อมูล
        conn = get_database_connection()
        cursor = conn.cursor()
        for _, row in updated_df.iterrows():
            cursor.execute("""
                UPDATE product_stock SET
                    product_id = %s,
                    product_detail = %s,
                    product_stock = %s,
                    Borrowed = %s,
                    Claimed = %s,
                    Waste = %s,
                    product_quantity = %s
                WHERE id = %s
            """, (
                row['product_id'],
                row['product_detail'],
                row['product_stock'],
                row['Borrowed'],
                row['Claimed'],
                row['Waste'],
                row['product_quantity'],
                row['id']
            ))
        conn.commit()
        cursor.close()
        conn.close()
        st.success("บันทึกการเปลี่ยนแปลงลงในฐานข้อมูลสำเร็จ")

    if "show_add_form" not in st.session_state:
        st.session_state.show_add_form = False
    if st.button("เพิ่มข้อมูลใหม่"):
        st.session_state.show_add_form = not st.session_state.show_add_form

    if st.session_state.show_add_form:
        st.subheader("เพิ่มข้อมูลใหม่")
        with st.form("add_new_product"):
            new_product_id = st.text_input("Product ID")
            new_product_detail = st.text_input("รายละเอียดสินค้า")
            new_product_stock = st.number_input("จำนวนสินค้าในสต็อก", min_value=0, step=1)
            new_borrowed = st.number_input("Borrowed", min_value=0, step=1)
            new_claimed = st.number_input("Claimed", min_value=0, step=1)
            new_waste = st.number_input("Waste", min_value=0, step=1)
            new_product_quantity = st.number_input("จำนวนสินค้ารวม", min_value=0, step=1)
            
            # ปุ่มสำหรับเพิ่มข้อมูล
            add_product_button = st.form_submit_button("เพิ่มข้อมูล")

            # เพิ่มข้อมูลใหม่เมื่อกดปุ่ม
            if add_product_button:
                conn = get_database_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO product_stock (product_id, product_detail, product_stock, Borrowed, Claimed, Waste, product_quantity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_product_id,
                    new_product_detail,
                    new_product_stock,
                    new_borrowed,
                    new_claimed,
                    new_waste,
                    new_product_quantity
                ))
                conn.commit()
                cursor.close()
                conn.close()
                st.success("เพิ่มข้อมูลสินค้าใหม่สำเร็จ")

    if "show_delete_form" not in st.session_state:
        st.session_state.show_delete_form = False
    if st.button("ลบข้อมูลที่เลือก"):
        st.session_state.show_delete_form = not st.session_state.show_delete_form

    if st.session_state.show_delete_form:
        selected_index = st.multiselect("เลือก Index สำหรับลบ", result_data.index)
        if st.button("ลบข้อมูลที่เลือก"):
            if selected_index:
                ids_to_delete = data_with_id.loc[selected_index, 'id'].tolist()  # ดึง id ของข้อมูลที่เลือก

                # ลบข้อมูลในฐานข้อมูลตาม id ที่เลือก
                conn = get_database_connection()
                cursor = conn.cursor()
                cursor.executemany("DELETE FROM product_stock WHERE id = %s", [(id,) for id in ids_to_delete])
                conn.commit()
                cursor.close()
                conn.close()
                st.success(f"ลบข้อมูลสำเร็จ: {len(ids_to_delete)} รายการ")
            else:
                st.warning("กรุณาเลือกข้อมูลที่ต้องการลบ")
