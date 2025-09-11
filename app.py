import streamlit as st
import pandas as pd
import datetime

# ===================================================================================
#  DASHBOARD ANALISIS KOMPETITOR BERDASARKAN BRAND - V7 (Sederhana)
#  Dibuat oleh: Firman & Asisten AI Gemini
#  Fokus: Analisis Brand pada Tanggal Tertentu
# ===================================================================================

# ===================================================================================
# KONFIGURASI HALAMAN
# ===================================================================================
st.set_page_config(layout="wide", page_title="Analisis Brand Kompetitor")

# ===================================================================================
# FUNGSI UTAMA
# ===================================================================================
@st.cache_data(show_spinner="Memuat data...")
def load_data(file_path):
    """
    Fungsi untuk memuat dan memproses data dari file CSV.
    """
    try:
        df = pd.read_csv(file_path)
        # Konversi kolom tanggal ke tipe datetime
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        # Hapus baris dimana tanggal tidak valid
        df.dropna(subset=['TANGGAL'], inplace=True)
        df['HARGA'] = pd.to_numeric(df['HARGA'], errors='coerce').fillna(0)
        return df
    except FileNotFoundError:
        st.error(f"File tidak ditemukan di path: {file_path}")
        return pd.DataFrame()

# ===================================================================================
# APLIKASI STREAMLIT
# ===================================================================================

# Judul Dashboard
st.title("📊 Analisis Brand Kompetitor")
st.write("Dashboard ini digunakan untuk melihat produk dari brand tertentu di semua toko kompetitor pada tanggal yang dipilih.")

# Memuat data
# Pastikan file 'DATA_REKAP.xlsx - DATABASE.csv' berada di direktori yang sama dengan skrip ini
df = load_data('DATA_REKAP.xlsx - DATABASE.csv')

if not df.empty:
    # --- Sidebar untuk Filter ---
    st.sidebar.header("Filter Pencarian")

    # Filter Brand
    unique_brands = sorted(df['Brand'].astype(str).unique())
    selected_brand = st.sidebar.selectbox("Pilih Brand", unique_brands, index=unique_brands.index("ACER") if "ACER" in unique_brands else 0)

    # Filter Tanggal
    min_date = df['TANGGAL'].min().date()
    max_date = df['TANGGAL'].max().date()
    selected_date = st.sidebar.date_input(
        "Pilih Tanggal",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

    # --- Tampilan Utama ---
    st.header(f"Produk Brand '{selected_brand}' pada Tanggal {selected_date.strftime('%d-%m-%Y')}")

    # Konversi selected_date ke datetime untuk perbandingan
    selected_datetime = pd.to_datetime(selected_date)

    # Filter dataframe berdasarkan input pengguna
    filtered_df = df[(df['Brand'] == selected_brand) & (df['TANGGAL'].dt.date == selected_date)]

    if filtered_df.empty:
        st.warning("Tidak ada data yang ditemukan untuk brand dan tanggal yang dipilih.")
    else:
        st.info(f"Ditemukan **{len(filtered_df)}** produk.")
        
        # Mengelompokkan berdasarkan Kategori (yang merepresentasikan toko)
        all_stores = sorted(filtered_df['Kategori'].unique())

        for store in all_stores:
            with st.expander(f"Lihat Produk di Toko: **{store}**"):
                store_df = filtered_df[filtered_df['Kategori'] == store].copy()
                
                # Format harga agar lebih mudah dibaca
                store_df['HARGA'] = store_df['HARGA'].apply(lambda x: f"Rp {x:,.0f}".replace(',', '.'))
                
                st.dataframe(
                    store_df[['NAMA', 'HARGA', 'SKU']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "NAMA": st.column_config.TextColumn("Nama Produk", width="large"),
                        "HARGA": st.column_config.TextColumn("Harga"),
                        "SKU": st.column_config.TextColumn("SKU"),
                    }
                )
else:
    st.error("Gagal memuat data. Pastikan file 'DATA_REKAP.xlsx - DATABASE.csv' ada di direktori yang sama.")
