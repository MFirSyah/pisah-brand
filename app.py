import streamlit as st
import pandas as pd
import gspread

# Konfigurasi halaman
st.set_page_config(page_title="Filter Brand & Tanggal", layout="wide")
st.title("📊 Analisis Brand Berdasarkan Tanggal")

# Fungsi ambil data Google Sheets
@st.cache_data
def load_data():
    try:
        creds_dict = {
            "type": st.secrets["gcp_type"],
            "project_id": st.secrets["gcp_project_id"],
            "private_key_id": st.secrets["gcp_private_key_id"],
            "private_key": st.secrets["gcp_private_key_raw"].replace('\\n', '\n'),
            "client_email": st.secrets["gcp_client_email"],
            "client_id": st.secrets["gcp_client_id"],
            "auth_uri": st.secrets["gcp_auth_uri"],
            "token_uri": st.secrets["gcp_token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp_auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp_client_x509_cert_url"]
        }
        gc = gspread.service_account_from_dict(creds_dict)
        spreadsheet = gc.open_by_key("1hl7YPEPg4aaEheN5fBKk65YX3-KdkQBRHCJWhVr9kVQ")
        sheet = spreadsheet.worksheet("DATABASE")
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Gagal load data: {e}")
        return pd.DataFrame()

    # Normalisasi kolom
    rename_map = {
        'TANGGAL': 'Tanggal',
        'BRAND': 'Brand',
        'NAMA': 'Nama Produk',
        'HARGA': 'Harga',
        'TERJUAL/BLN': 'Terjual per Bulan'
    }
    df.rename(columns=rename_map, inplace=True)

    # Convert tipe data
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors="coerce", dayfirst=True)
    df['Harga'] = pd.to_numeric(df['Harga'], errors="coerce")
    df['Terjual per Bulan'] = pd.to_numeric(df['Terjual per Bulan'], errors="coerce").fillna(0)
    df['Omzet'] = df['Harga'] * df['Terjual per Bulan']

    return df.dropna(subset=['Tanggal', 'Brand'])

# Fungsi konversi CSV
@st.cache_data
def convert_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Load data
df = load_data()
if df.empty:
    st.stop()

# Sidebar filter
st.sidebar.header("Filter Data")
brands = sorted(df['Brand'].dropna().unique())
selected_brand = st.sidebar.selectbox("Pilih Brand:", brands)
min_date, max_date = df['Tanggal'].min().date(), df['Tanggal'].max().date()
date_range = st.sidebar.date_input("Rentang Tanggal:", [min_date, max_date])

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df[
        (df['Brand'] == selected_brand) &
        (df['Tanggal'].dt.date >= start_date) &
        (df['Tanggal'].dt.date <= end_date)
    ]
else:
    df_filtered = pd.DataFrame()

# Tampilkan hasil
st.subheader(f"Hasil Filter: Brand **{selected_brand}** dari {date_range[0]} s/d {date_range[-1]}")
if df_filtered.empty:
    st.warning("Tidak ada data untuk filter ini.")
else:
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    total_omzet = df_filtered['Omzet'].sum()
    st.metric("Total Omzet", f"Rp {total_omzet:,.0f}")

    # Tombol export CSV
    csv_data = convert_to_csv(df_filtered)
    st.download_button(
        label="📥 Export CSV",
        data=csv_data,
        file_name=f"data_{selected_brand}_{start_date}_{end_date}.csv",
        mime="text/csv"
    )
