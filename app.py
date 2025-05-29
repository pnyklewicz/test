import streamlit as st
import pandas as pd

st.title("Optymalizacja łączenia transportów")

uploaded_file = st.file_uploader("Wgraj plik CSV z wysyłkami", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, delimiter=",")
    st.subheader("Dane źródłowe")
    st.dataframe(df)

    df["prefix_kodu"] = df["kod_pocztowy"].str[:2]

    grouped = df.groupby(["prefix_kodu", "rodzaj_materialu"]).agg(
        suma_wagi=("waga", "sum"),
        liczba_zlecen=("numer_zlecenia", "count")
    ).reset_index()

    st.subheader("Grupowanie według prefixu kodu i rodzaju materiału")
    st.dataframe(grouped)

    max_tonaz = st.slider("Maksymalny tonaż na grupę", 1, 40, 10)
    wynik = grouped[grouped["suma_wagi"] <= max_tonaz]

    st.subheader(f"Grupy z wagą ≤ {max_tonaz} ton")
    st.dataframe(wynik)

    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(wynik)
    st.download_button("Pobierz wynik jako CSV", data=csv, file_name="grupowanie_transportow.csv", mime='text/csv')
