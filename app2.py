import streamlit as st
import duckdb
import pandas as pd
from datetime import date

# ---------------------------
# DuckDB 초기화 및 샘플 데이터
# ---------------------------
def init_db():
    con = duckdb.connect(database=":memory:")

    # 소비자 테이블
    con.execute("""
        CREATE TABLE customers (
            custid INTEGER,
            name VARCHAR,
            address VARCHAR,
            phone VARCHAR
        );
    """)

    # 책 테이블
    con.execute("""
        CREATE TABLE books (
            bookid INTEGER,
            bookname VARCHAR,
            price INTEGER,
            publisher VARCHAR
        );
    """)

    # 주문 테이블
    con.execute("""
        CREATE TABLE orders (
            orderid INTEGER,
            custid INTEGER,
            bookid INTEGER,
            orderdate DATE,
            saleprice INTEGER
        );
    """)

    # 소비자 데이터 — 딱 한 명: 김민서
    customers_data = [
        (1, "김민서", "서울시 강남구", "010-0000-0000")
    ]
    con.executemany("INSERT INTO customers VALUES (?, ?, ?, ?);", customers_data)

    # 책 데이터
    books_data = [
        (1, "파이썬 입문", 20000, "코딩출판사"),
        (2, "데이터 분석 기초", 25000, "데이터출판"),
        (3, "통계학 개론", 23000, "수리출판"),
    ]
    con.executemany("INSERT INTO books VALUES (?, ?, ?, ?);", books_data)

    # 주문 데이터
    orders_data = [
        (1, 1, 1, date(2025, 1, 5), 20000),
        (2, 1, 2, date(2025, 1, 10), 24000),
        (3, 1, 3, date(2025, 2, 1), 23000)
    ]
    con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?);", orders_data)

    return con

# ---------------------------
# Streamlit 앱
# ---------------------------
def main():
    st.set_page_config(page_title="김민서 정보 페이지", layout="centered")

    st.title("김민서 소비자 정보 조회 페이지")

    con = init_db()

    # 김민서 정보 불러오기
    customer = con.execute("""
        SELECT custid, name, address, phone
        FROM customers
        WHERE name = '김민서';
    """).df().iloc[0]

    st.subheader("소비자 정보")
    st.table(
        pd.DataFrame([customer]).rename(columns={
            "custid": "고객ID",
            "name": "이름",
            "address": "주소",
            "phone": "전화번호",
        })
    )

    # 김민서 주문 내역
    orders_df = con.execute("""
        SELECT
            o.orderid,
            o.orderdate,
            b.bookname,
            b.publisher,
            o.saleprice
        FROM orders o
        JOIN books b ON o.bookid = b.bookid
        WHERE o.custid = 1
        ORDER BY o.orderdate;
    """).df()

    st.subheader("주문 내역")
    st.table(
        orders_df.rename(columns={
            "orderid": "주문ID",
            "orderdate": "주문일",
            "bookname": "도서명",
            "publisher": "출판사",
            "saleprice": "판매가",
        })
    )

if __name__ == "__main__":
    main()
