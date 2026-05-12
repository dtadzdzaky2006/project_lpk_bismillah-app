import streamlit as st

st.title("🎈 Chemistry Calculation")

#Input angka
num1 = st.number_input("Masukkan angka pertama", value=0.0)
num2 = st.number_input("Masukkan angka kedua", value=0.0)

operasi = st.selectbox("Pilih operasi", ["Tambah", "Kurang", "Kali", "Bagi"])
    

if st.button("Hitung"):
    if operasi == "Tambah":
        hasil = num1 + num2
    elif operasi == "Kurang":
         hasil = num1 - num2
    elif operasi == "Kali":
         hasil = num1 * num2
    elif operasi == "Bagi":
        hasil = num1 / num2 if num2 != 0 else "Tidak bisa dibagi nol"

 st.success(f"Hasil: {hasil}")
