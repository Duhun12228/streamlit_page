import streamlit as st
import duckdb
import pandas as pd
from datetime import date

# --------------------------------
# DuckDB 초기화 & 샘플 데이터 생성
# --------------------------------
def init_db():
    # 매번 새로 만들지만, 항상 같은 샘플 데이터가 들어가도록 설계
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

    # ---- 샘플 데이터 삽입 ----
    # 소비자: 이름은 김두훈1, 김두훈2, ...
    customers_data = [
        (1, "김두훈1", "서울시 강남구 테헤란로 1", "010-0000-0001"),
        (2, "김두훈2", "서울시 강남구 테헤란로 2", "010-0000-0002"),
        (3, "김두훈3", "서울시 서초구 서초대로 3", "010-0000-0003"),
        (4, "김두훈4", "서울시 마포구 독막로 4", "010-0000-0004"),
        (5, "김두훈5", "서울시 송파구 올림픽로 5", "010-0000-0005"),
    ]
    con.executemany("INSERT INTO customers VALUES (?, ?, ?, ?);", customers_data)

    # 책 데이터
    books_data = [
        (1, "파이썬 데이터 분석 입문", 25000, "데이터북스"),
        (2, "머신러닝 완전 정복", 32000, "AI출판사"),
        (3, "통계학 첫걸음", 21000, "수리출판"),
        (4, "알고리즘 인터뷰", 35000, "코딩북스"),
        (5, "딥러닝 기초", 40000, "AI출판사"),
    ]
    con.executemany("INSERT INTO books VALUES (?, ?, ?, ?);", books_data)

    # 주문 데이터 (대충 섞어서)
    orders_data = [
        (1, 1, 1, date(2025, 1, 3), 25000),
        (2, 1, 3, date(2025, 1, 10), 21000),
        (3, 2, 2, date(2025, 2, 1), 32000),
        (4, 2, 4, date(2025, 2, 15), 35000),
        (5, 3, 5, date(2025, 3, 2), 40000),
        (6, 3, 1, date(2025, 3, 20), 24000),  # 할인 예시
        (7, 4, 2, date(2025, 4, 5), 30000),
        (8, 5, 3, date(2025, 4, 18), 21000),
        (9, 5, 4, date(2025, 5, 2), 34000),
    ]
    con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?);", orders_data)

    return con


# --------------------------------
# Streamlit UI
# --------------------------------
def main():
    st.set_page_config(
        page_title="북스토어 대시보드",
        layout="wide",
    )

    st.title("DuckDB 활용 마당 DB 매니저")

    # DB 초기화
    con = init_db()

    # 소비자 목록 불러오기
    customers_df = con.execute("""
        SELECT custid, name, address, phone
        FROM customers
        ORDER BY custid
    """).df()

    # 사이드바에서 소비자 선택
    st.sidebar.header("소비자 선택")
    selected_name = st.sidebar.selectbox(
        "소비자를 선택하세요",
        customers_df["name"].tolist()
    )

    # 선택된 소비자 정보 찾기
    selected_customer = customers_df[customers_df["name"] == selected_name].iloc[0]
    selected_custid = int(selected_customer["custid"])

    # 선택된 소비자의 주문 + 책 정보 join
    orders_df = con.execute("""
        SELECT 
            o.orderid,
            o.orderdate,
            b.bookname,
            b.publisher,
            b.price AS list_price,
            o.saleprice,
            (b.price - o.saleprice) AS discount
        FROM orders o
        JOIN books b ON o.bookid = b.bookid
        WHERE o.custid = ?
        ORDER BY o.orderdate;
    """, [selected_custid]).df()

    # -----------------------------
    # 상단: 소비자 정보 카드
    # -----------------------------
    st.markdown("### 소비자 정보")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("고객 ID", selected_customer["custid"])
    with c2:
        st.metric("이름", selected_customer["name"])
    with c3:
        st.metric("전화번호", selected_customer["phone"])
    with c4:
        st.metric("지역", selected_customer["address"].split()[0])  # 서울시 등만 뽑기

    st.markdown("---")

    # -----------------------------
    # 중간: 주문 요약(지표)
    # -----------------------------
    st.markdown("### 주문 요약")

    if orders_df.empty:
        st.info("이 소비자는 아직 주문 내역이 없습니다.")
    else:
        total_orders = len(orders_df)
        total_spent = int(orders_df["saleprice"].sum())
        avg_spent = int(orders_df["saleprice"].mean())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 주문 건수", f"{total_orders} 건")
        with col2:
            st.metric("총 주문 금액", f"{total_spent:,.0f} 원")
        with col3:
            st.metric("1회 평균 결제 금액", f"{avg_spent:,.0f} 원")

        st.markdown("### 주문 상세 내역")
        # 날짜 기준으로 오름차순 정렬해서 보기 좋게
        orders_df_display = orders_df.copy()
        orders_df_display["orderdate"] = pd.to_datetime(orders_df_display["orderdate"])
        orders_df_display = orders_df_display.sort_values("orderdate")

        st.dataframe(
            orders_df_display[[
                "orderdate", "bookname", "publisher", "list_price", "saleprice", "discount"
            ]].rename(columns={
                "orderdate": "주문일",
                "bookname": "도서명",
                "publisher": "출판사",
                "list_price": "정가",
                "saleprice": "판매가",
                "discount": "할인금액"
            }),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
