# ===================================================================================
#  APLIKASI FILTER PRODUK SEDERHANA
#  Dibuat oleh: Firman & Asisten AI Gemini
#  Fitur: Filter berdasarkan Brand dan Tanggal
# ===================================================================================

import streamlit as st
import pandas as pd
import gspread
import re

# ===================================================================================
#  KONFIGURASI HALAMAN
# ===================================================================================
st.set_page_config(layout="centered", page_title="Filter Produk")

# ===================================================================================
#  FUNGSI KONEKSI & AMBIL DATA
# ===================================================================================
@st.cache_data(show_spinner="Menghubungkan ke Google Sheets...")
def load_data_from_gsheets():
    """
    Fungsi ini hanya untuk mengambil, menggabungkan, dan membersihkan data rekap
    dari semua toko di Google Sheets.
    """
    try:
        # Koneksi aman menggunakan st.secrets
        creds_dict = {
            "type": st.secrets["gcp_type"], "project_id": st.secrets["gcp_project_id"],
            "private_key_id": st.secrets["gcp_private_key_id"], "private_key": st.secrets["gcp_private_key_raw"].replace('\\n', '\n'),
            "client_email": st.secrets["gcp_client_email"], "client_id": st.secrets["gcp_client_id"],
            "auth_uri": st.secrets["gcp_auth_uri"], "token_uri": st.secrets["gcp_token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp_auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp_client_x509_cert_url"]
        }
        gc = gspread.service_account_from_dict(creds_dict)
        spreadsheet = gc.open_by_key("1hl7YPEPg4aaEheN5fBKk65YX3-KdkQBRHCJWhVr9kVQ")
    except Exception as e:
        st.error(f"GAGAL KONEKSI KE GOOGLE SHEETS: {e}")
        return None

    # Daftar semua sheet rekap yang akan digabung
    sheet_names = [
        "DB KLIK - REKAP - READY", "DB KLIK - REKAP - HABIS", "ABDITAMA - REKAP - READY",
        "ABDITAMA - REKAP - HABIS", "LEVEL99 - REKAP - READY", "LEVEL99 - REKAP - HABIS",
        "JAYA PC - REKAP - READY", "JAYA PC - REKAP - HABIS", "MULTIFUNGSI - REKAP - READY",
        "MULTIFUNGSI - REKAP - HABIS", "IT SHOP - REKAP - READY", "IT SHOP - REKAP - HABIS",
        "SURYA MITRA ONLINE - REKAP - READY", "SURYA MITRA ONLINE - REKAP - HABIS",
        "GG STORE - REKAP - READY", "GG STORE - REKAP - HABIS", "TECH ISLAND - REKAP - READY",
        "TECH ISLAND - REKAP - HABIS"
    ]
    
    rekap_list_df = []
    try:
        for sheet_name in sheet_names:
            sheet = spreadsheet.worksheet(sheet_name)
            data = sheet.get_all_records() # Lebih simpel untuk mengambil data
            if not data: continue
            
            df_sheet = pd.DataFrame(data)
            store_name_match = re.match(r"^(.*?) - REKAP", sheet_name, re.IGNORECASE)
            df_sheet['Toko'] = store_name_match.group(1).strip() if store_name_match else "Toko Tak Dikenal"
            df_sheet['Status'] = 'Tersedia' if "READY" in sheet_name.upper() else 'Habis'
            rekap_list_df.append(df_sheet)
    except Exception as e:
        st.error(f"Gagal memproses sheet: {e}.")
        return None

    if not rekap_list_df:
        st.error("Tidak ada data REKAP yang berhasil dimuat.")
        return None

    # Gabungkan semua data menjadi satu
    rekap_df = pd.concat(rekap_list_df, ignore_index=True)
    
    # Ubah nama kolom agar konsisten
    rekap_df.columns = [str(col).strip().upper() for col in rekap_df.columns]
    rename_mapping = {'NAMA': 'Nama Produk', 'TANGGAL': 'Tanggal', 'HARGA': 'Harga'}
    rekap_df.rename(columns=rename_mapping, inplace=True)

    # Buat kolom 'Brand' dari kata pertama 'Nama Produk'
    if 'Nama Produk' in rekap_df.columns:
        rekap_df['Brand'] = rekap_df['Nama Produk'].astype(str).str.split(n=1).str[0].str.upper()
    else:
        st.error("Kolom 'Nama Produk' tidak ditemukan!")
        return None
        
    # Konversi tipe data
    rekap_df['Tanggal'] = pd.to_datetime(rekap_df['Tanggal'], errors='coerce', dayfirst=True)
    rekap_df['Harga'] = pd.to_numeric(rekap_df['Harga'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce')
    
    # Hapus baris yang datanya tidak lengkap
    rekap_df.dropna(subset=['Tanggal', 'Nama Produk', 'Harga', 'Brand'], inplace=True)

    return rekap_df

# ===================================================================================
#  TAMPILAN UTAMA APLIKASI
# ===================================================================================
st.title("📊 Filter Produk Berdasarkan Brand & Tanggal")

df = load_data_from_gsheets()

if df is not None and not df.empty:
    st.sidebar.header("⚙️ Kontrol Filter")

    # --- FILTER TANGGAL ---
    min_date = df['Tanggal'].min().date()
    max_date = df['Tanggal'].max().date()
    selected_date_range = st.sidebar.date_input(
        "Pilih Rentang Tanggal:",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    # --- FILTER BRAND ---
    all_brands = sorted(df['Brand'].unique())
    selected_brands = st.sidebar.multiselect(
        "Pilih Brand:",
        options=all_brands,
        default=[] # Awalnya kosong
    )

    # --- PROSES FILTER DATA ---
    if len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        
        # 1. Filter berdasarkan tanggal
        df_filtered = df[
            (df['Tanggal'].dt.date >= start_date) & 
            (df['Tanggal'].dt.date <= end_date)
        ]
        
        # 2. Filter berdasarkan brand (jika ada yang dipilih)
        if selected_brands:
            df_filtered = df_filtered[df_filtered['Brand'].isin(selected_brands)]

        # --- TAMPILKAN HASIL ---
        st.header("Hasil Filter")
        st.write(f"Ditemukan **{len(df_filtered)}** produk yang sesuai.")

        if not df_filtered.empty:
            # Pilih kolom yang ingin ditampilkan agar rapi
            display_columns = ['Tanggal', 'Nama Produk', 'Brand', 'Harga', 'Toko', 'Status']
            st.dataframe(
                df_filtered[display_columns].sort_values('Tanggal', ascending=False), 
                hide_index=True
            )
        else:
            st.warning("Tidak ada data yang cocok dengan kriteria filter Anda.")
    else:
        st.warning("Silakan pilih rentang tanggal yang valid.")

else:
    st.info("Aplikasi siap, namun data kosong atau gagal dimuat. Periksa pesan error di atas.")
