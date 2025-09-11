# ===================================================================================
#  DASHBOARD ANALISIS BRAND KOMPETITOR V7
#  Dibuat oleh: Firman & Asisten AI Gemini
#  Deskripsi: Aplikasi ini menganalisis keberadaan produk berdasarkan brand
#             dan tanggal tertentu di berbagai toko kompetitor.
#  Metode Koneksi: Aman & Stabil (gspread + st.secrets individual)
# ===================================================================================

# ===================================================================================
# IMPORT LIBRARY
# ===================================================================================
import streamlit as st
import pandas as pd
from thefuzz import process, fuzz
import gspread
from datetime import datetime

# ===================================================================================
# KONFIGURASI HALAMAN
# ===================================================================================
st.set_page_config(layout="wide", page_title="Analisis Brand Kompetitor")

# ===================================================================================
# FUNGSI KONEKSI & PEMROSESAN DATA
# ===================================================================================
@st.cache_data(ttl=600, show_spinner="Mengambil data terbaru dari Google Sheets...")
def load_data_from_gsheets():
    """
    Fungsi untuk memuat, menggabungkan, dan membersihkan data dari Google Sheets.
    Data akan di-cache selama 10 menit untuk efisiensi.
    """
    try:
        # Menggunakan st.secrets untuk koneksi yang aman
        creds_dict = {
            "type": st.secrets["gcp_type"],
            "project_id": st.secrets["gcp_project_id"],
            "private_key_id": st.secrets["gcp_private_key_id"],
            "private_key": st.secrets["gcp_private_key"],
            "client_email": st.secrets["gcp_client_email"],
            "client_id": st.secrets["gcp_client_id"],
            "auth_uri": st.secrets["gcp_auth_uri"],
            "token_uri": st.secrets["gcp_token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp_auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp_client_x509_cert_url"]
        }
        
        gc = gspread.service_account_from_dict(creds_dict)
        spreadsheet = gc.open_by_key("1hl7YPEPg4aaEheN5fBKk65YX3-KdkQBRHCJWhVr9kVQ")
        
        # Daftar semua sheet rekap kompetitor
        worksheet_names = [
            "DB KLIK - REKAP - READY", "DB KLIK - REKAP - HABIS",
            "ABDITAMA - REKAP - READY", "ABDITAMA - REKAP - HABIS",
            "LEVEL99 - REKAP - READY", "LEVEL99 - REKAP - HABIS",
            "IT SHOP - REKAP - READY", "IT SHOP - REKAP - HABIS",
            "JAYA PC - REKAP - READY", "JAYA PC - REKAP - HABIS",
            "MULTIFUNGSI - REKAP - READY", "MULTIFUNGSI - REKAP - HABIS",
            "TECH ISLAND - REKAP - READY", "TECH ISLAND - REKAP - HABIS",
            "GG STORE - REKAP - READY", "GG STORE - REKAP - HABIS",
            "SURYA MITRA ONLINE - REKAP - RE", "SURYA MITRA ONLINE - REKAP - HA"
        ]
        
        all_data = []
        for name in worksheet_names:
            try:
                worksheet = spreadsheet.worksheet(name)
                df = pd.DataFrame(worksheet.get_all_records())
                
                # Ekstrak nama toko dan status dari nama worksheet
                parts = name.split(" - ")
                df['Toko'] = parts[0].strip()
                status_rekap = parts[-1].strip()
                if "READY" in status_rekap or "RE" in status_rekap:
                    df['Status'] = 'Tersedia'
                else:
                    df['Status'] = 'Habis'
                    
                all_data.append(df)
            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"Worksheet '{name}' tidak ditemukan, dilewati.")
                continue

        if not all_data:
            st.error("Tidak ada data yang berhasil dimuat dari worksheet kompetitor.")
            return None
            
        df_combined = pd.concat(all_data, ignore_index=True)
        df_combined.rename(columns={'NAMA': 'Nama Produk', 'HARGA': 'Harga', 'BRAND': 'Brand'}, inplace=True)

        # Proses pembersihan data
        df_combined['Harga'] = pd.to_numeric(df_combined['Harga'], errors='coerce').fillna(0).astype(int)
        df_combined['TANGGAL'] = pd.to_datetime(df_combined['TANGGAL'], errors='coerce').dt.date

        # Memuat kamus brand untuk standardisasi
        try:
            kamus_ws = spreadsheet.worksheet("kamus_brand")
            kamus_df = pd.DataFrame(kamus_ws.get_all_records())
            kamus_brand = {row['Alias'].upper(): row['Brand_Utama'].upper() for index, row in kamus_df.iterrows()}
            
            # Standardisasi nama brand
            df_combined['Brand_Utama'] = df_combined['Brand'].str.upper().map(kamus_brand).fillna(df_combined['Brand'].str.upper())
        except gspread.exceptions.WorksheetNotFound:
            st.warning("Worksheet 'kamus_brand' tidak ditemukan. Standardisasi brand tidak dilakukan.")
            df_combined['Brand_Utama'] = df_combined['Brand'].str.upper()

        return df_combined.dropna(subset=['Tanggal', 'Brand_Utama'])

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")
        return None

# ===================================================================================
# TAMPILAN UTAMA APLIKASI
# ===================================================================================
st.title("📊 Dashboard Analisis Brand Kompetitor")
st.markdown("Pilih brand dan tanggal untuk melihat daftar produk di semua toko kompetitor.")

df = load_data_from_gsheets()

if df is not None and not df.empty:
    
    # --- Filter Input ---
    col1, col2 = st.columns(2)
    
    with col1:
        # Ambil daftar brand unik yang sudah distandardisasi dan urutkan
        unique_brands = sorted(df['Brand_Utama'].unique())
        selected_brand = st.selectbox(
            "Pilih Brand:",
            options=unique_brands,
            index=unique_brands.index("ACER") if "ACER" in unique_brands else 0 # Default ke ACER jika ada
        )

    with col2:
        # Tentukan tanggal min dan max dari data
        min_date = df['Tanggal'].min()
        max_date = df['Tanggal'].max()
        selected_date = st.date_input(
            "Pilih Tanggal:",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )

    # --- Tombol untuk memulai analisis ---
    if st.button("Tampilkan Analisis", type="primary", use_container_width=True):
        st.markdown("---")
        st.subheader(f"Hasil Analisis untuk Brand '{selected_brand}' pada Tanggal {selected_date.strftime('%d %B %Y')}")

        # Filter data utama berdasarkan input pengguna
        filtered_df = df[(df['Brand_Utama'] == selected_brand) & (df['Tanggal'] == selected_date)]

        if filtered_df.empty:
            st.warning("Tidak ada data ditemukan untuk brand dan tanggal yang dipilih. Coba tanggal atau brand lain.")
        else:
            all_stores = sorted(df['Toko'].unique())
            
            for store in all_stores:
                with st.expander(f"🏪 Analisis di Toko: **{store}**"):
                    store_data = filtered_df[filtered_df['Toko'] == store].copy()
                    
                    if store_data.empty:
                        st.info(f"Brand **{selected_brand}** tidak ditemukan di toko ini pada tanggal yang dipilih.")
                    else:
                        total_produk = len(store_data)
                        tersedia_count = store_data[store_data['Status'] == 'Tersedia'].shape[0]
                        habis_count = store_data[store_data['Status'] == 'Habis'].shape[0]

                        st.metric(label="Total Produk Ditemukan", value=f"{total_produk} SKU")
                        
                        m_col1, m_col2 = st.columns(2)
                        m_col1.metric(label="Stok Tersedia", value=f"{tersedia_count} SKU")
                        m_col2.metric(label="Stok Habis", value=f"{habis_count} SKU")
                        
                        # Format harga agar lebih mudah dibaca
                        store_data['Harga (Rp)'] = store_data['Harga'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
                        
                        # Tampilkan daftar produk
                        st.dataframe(
                            store_data[['Nama Produk', 'Harga (Rp)', 'Status']],
                            use_container_width=True,
                            hide_index=True
                        )

else:
    st.error("Gagal memuat data. Periksa kembali koneksi atau konfigurasi Google Sheets Anda di st.secrets.")
