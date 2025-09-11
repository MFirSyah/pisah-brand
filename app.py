# ===================================================================================
#  DASHBOARD ANALISIS BRAND KOMPETITOR V7.4
#  Dibuat oleh: Firman & Asisten AI Gemini
#  Deskripsi: Aplikasi ini menganalisis keberadaan produk berdasarkan brand
#             dan tanggal tertentu di berbagai toko kompetitor.
#  Pembaruan v7.4: Menambahkan kolom Terjual/Bln dan Omzet pada tabel detail.
# ===================================================================================

# ===================================================================================
# IMPORT LIBRARY
# ===================================================================================
import streamlit as st
import pandas as pd
import numpy as np
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
        
        worksheet_names = [
            "DB KLIK - REKAP - READY", "DB KLIK - REKAP - HABIS", "ABDITAMA - REKAP - READY", 
            "ABDITAMA - REKAP - HABIS", "LEVEL99 - REKAP - READY", "LEVEL99 - REKAP - HABIS",
            "IT SHOP - REKAP - READY", "IT SHOP - REKAP - HABIS", "JAYA PC - REKAP - READY", 
            "JAYA PC - REKAP - HABIS", "MULTIFUNGSI - REKAP - READY", "MULTIFUNGSI - REKAP - HABIS",
            "TECH ISLAND - REKAP - READY", "TECH ISLAND - REKAP - HABIS", "GG STORE - REKAP - READY", 
            "GG STORE - REKAP - HABIS", "SURYA MITRA ONLINE - REKAP - READY", "SURYA MITRA ONLINE - REKAP - HABIS"
        ]
        
        all_data = []
        for name in worksheet_names:
            try:
                worksheet = spreadsheet.worksheet(name)
                all_values = worksheet.get_all_values()
                if not all_values: continue
                header = all_values[0]
                clean_header = [h for h in header if h]
                num_columns = len(clean_header)
                data_rows = [row[:num_columns] for row in all_values[1:]]
                df_sheet = pd.DataFrame(data_rows, columns=clean_header)

                parts = name.split(" - ")
                df_sheet['Toko'] = parts[0].strip()
                status_rekap = parts[-1].strip()
                df_sheet['Status'] = 'Tersedia' if "READY" in status_rekap or "RE" in status_rekap else 'Habis'
                all_data.append(df_sheet)
            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"Worksheet '{name}' tidak ditemukan, dilewati.")
                continue

        if not all_data:
            st.error("Tidak ada data yang berhasil dimuat.")
            return None
            
        df_combined = pd.concat(all_data, ignore_index=True)
        # Mengubah nama kolom agar lebih konsisten
        df_combined.rename(columns={
            'NAMA': 'Nama Produk', 
            'HARGA': 'Harga', 
            'BRAND': 'Brand',
            'TERJUAL/BLN': 'Terjual/Bln'
        }, inplace=True)

        # Konversi tipe data kolom numerik, handle error jika ada
        df_combined['Harga'] = pd.to_numeric(df_combined['Harga'], errors='coerce').fillna(0).astype(int)
        df_combined['Terjual/Bln'] = pd.to_numeric(df_combined['Terjual/Bln'], errors='coerce').fillna(0).astype(int)
        df_combined['TANGGAL'] = pd.to_datetime(df_combined['TANGGAL'], errors='coerce').dt.date

        try:
            kamus_ws = spreadsheet.worksheet("kamus_brand")
            kamus_df = pd.DataFrame(kamus_ws.get_all_records())
            kamus_brand = {row['Alias'].upper(): row['Brand_Utama'].upper() for index, row in kamus_df.iterrows()}
            df_combined['Brand_Utama'] = df_combined['Brand'].str.upper().map(kamus_brand).fillna(df_combined['Brand'].str.upper())
        except gspread.exceptions.WorksheetNotFound:
            st.warning("Worksheet 'kamus_brand' tidak ditemukan.")
            df_combined['Brand_Utama'] = df_combined['Brand'].str.upper()

        return df_combined.dropna(subset=['TANGGAL', 'Brand_Utama'])

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")
        return None

# ===================================================================================
# TAMPILAN UTAMA APLIKASI
# ===================================================================================
st.title("📊 Dashboard Analisis Brand Kompetitor")
st.markdown("Pilih brand dan tanggal untuk melihat ringkasan performa di semua toko kompetitor.")

df_main = load_data_from_gsheets()

if df_main is not None and not df_main.empty:
    col1, col2 = st.columns(2)
    with col1:
        unique_brands = sorted(df_main['Brand_Utama'].unique())
        selected_brand = st.selectbox("Pilih Brand:", options=unique_brands, index=unique_brands.index("ACER") if "ACER" in unique_brands else 0)
    with col2:
        min_date = df_main['Tanggal'].min()
        max_date = df_main['Tanggal'].max()
        selected_date = st.date_input("Pilih Tanggal:", value=max_date, min_value=min_date, max_value=max_date)

    if st.button("Tampilkan Analisis", type="primary", use_container_width=True):
        st.markdown("---")
        st.subheader(f"Hasil Analisis untuk Brand '{selected_brand}' pada Tanggal {selected_date.strftime('%d %B %Y')}")

        filtered_df = df_main[(df_main['Brand_Utama'] == selected_brand) & (df_main['Tanggal'] == selected_date)]

        if filtered_df.empty:
            st.warning("Tidak ada data ditemukan untuk brand dan tanggal yang dipilih.")
        else:
            # --- MEMBUAT TABEL RINGKASAN ---
            summary_list = []
            all_stores = sorted(df_main['Toko'].unique())

            for store in all_stores:
                store_data = filtered_df[filtered_df['Toko'] == store]
                if store_data.empty:
                    summary_list.append({'Toko': store, 'Total SKU': 0, 'SKU Tersedia': 0, 'SKU Habis': 0, 'Harga Rata-rata': 0, 'Harga Termurah': 0, 'Harga Termahal': 0})
                    continue

                total_sku = len(store_data)
                tersedia_count = store_data[store_data['Status'] == 'Tersedia'].shape[0]
                habis_count = total_sku - tersedia_count
                
                harga_valid = store_data[(store_data['Status'] == 'Tersedia') & (store_data['Harga'] > 0)]['Harga']
                
                avg_price = harga_valid.mean() if not harga_valid.empty else 0
                min_price = harga_valid.min() if not harga_valid.empty else 0
                max_price = harga_valid.max() if not harga_valid.empty else 0

                summary_list.append({
                    'Toko': store, 'Total SKU': total_sku, 'SKU Tersedia': tersedia_count, 'SKU Habis': habis_count,
                    'Harga Rata-rata': avg_price, 'Harga Termurah': min_price, 'Harga Termahal': max_price
                })
            
            summary_df = pd.DataFrame(summary_list)
            
            st.markdown("#### Ringkasan Performa Brand per Toko")
            st.dataframe(
                summary_df.style.format({
                    'Harga Rata-rata': "Rp {:,.0f}", 'Harga Termurah': "Rp {:,.0f}", 'Harga Termahal': "Rp {:,.0f}"
                }).background_gradient(cmap='Greens', subset=['SKU Tersedia'])
                  .background_gradient(cmap='Reds', subset=['SKU Habis'])
                  .bar(subset=["Total SKU"], color='#86c5da'),
                use_container_width=True,
                hide_index=True
            )

            # --- TAMPILAN DETAIL (DIPERBARUI) ---
            with st.expander("Lihat Daftar Produk Lengkap per Toko"):
                for store in all_stores:
                    st.markdown(f"##### 🏪 **{store}**")
                    store_data_detail = filtered_df[filtered_df['Toko'] == store].copy()
                    
                    if store_data_detail.empty:
                        st.info(f"Brand **{selected_brand}** tidak ditemukan di toko ini.")
                    else:
                        # Hitung Omzet
                        store_data_detail['Omzet'] = store_data_detail['Harga'] * store_data_detail['Terjual/Bln']
                        
                        # Format kolom untuk tampilan
                        store_data_detail['Harga (Rp)'] = store_data_detail['Harga'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
                        store_data_detail['Omzet (Rp)'] = store_data_detail['Omzet'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
                        
                        # Tentukan urutan kolom baru
                        kolom_tampilan = ['Nama Produk', 'Harga (Rp)', 'Terjual/Bln', 'Omzet (Rp)', 'Status']
                        
                        st.dataframe(
                            store_data_detail[kolom_tampilan],
                            use_container_width=True, hide_index=True
                        )
else:
    st.error("Gagal memuat data. Periksa kembali koneksi atau konfigurasi Google Sheets Anda di st.secrets.")

