import streamlit as st
import sqlite3
from datetime import datetime, date
import pandas as pd
khachsan.png
# ============================================================
# CẤU HÌNH APP
# ============================================================

st.set_page_config(
    page_title="Hotel Manager",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "hotel.db"


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Bảng phòng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            floor INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Trống',
            note TEXT DEFAULT ''
        )
    """)

    # Bảng khách hàng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            id_card TEXT,
            address TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Bảng đặt phòng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            guest_id INTEGER NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            adults INTEGER DEFAULT 1,
            children INTEGER DEFAULT 0,
            booking_status TEXT DEFAULT 'Đang ở',
            total_amount REAL DEFAULT 0,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(room_id) REFERENCES rooms(id),
            FOREIGN KEY(guest_id) REFERENCES guests(id)
        )
    """)

    # Thêm dữ liệu mẫu nếu chưa có phòng
    cursor.execute("SELECT COUNT(*) FROM rooms")
    room_count = cursor.fetchone()[0]

    if room_count == 0:
        sample_rooms = [
            ("101", "Standard", 1, 500000, "Trống", ""),
            ("102", "Standard", 1, 500000, "Trống", ""),
            ("103", "Standard", 1, 500000, "Đang dọn", ""),
            ("104", "Deluxe", 1, 800000, "Trống", ""),
            ("201", "Deluxe", 2, 800000, "Đang ở", ""),
            ("202", "Deluxe", 2, 800000, "Trống", ""),
            ("203", "Suite", 2, 1200000, "Trống", ""),
            ("204", "Suite", 2, 1200000, "Bảo trì", ""),
            ("301", "VIP", 3, 2000000, "Trống", ""),
            ("302", "VIP", 3, 2000000, "Trống", ""),
        ]

        cursor.executemany("""
            INSERT INTO rooms
            (room_number, room_type, floor, price, status, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_rooms)

    conn.commit()
    conn.close()


# ============================================================
# HELPER
# ============================================================

def money(value):
    return f"{value:,.0f} VNĐ"


def get_rooms():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            id,
            room_number AS 'Số phòng',
            room_type AS 'Loại phòng',
            floor AS 'Tầng',
            price AS 'Giá phòng',
            status AS 'Trạng thái',
            note AS 'Ghi chú'
        FROM rooms
        ORDER BY CAST(room_number AS INTEGER)
    """, conn)
    conn.close()
    return df


def get_room_list():
    conn = get_connection()
    rooms = conn.execute("""
        SELECT id, room_number, room_type, price, status
        FROM rooms
        ORDER BY CAST(room_number AS INTEGER)
    """).fetchall()
    conn.close()
    return rooms


def get_guests():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            id AS 'ID',
            full_name AS 'Họ và tên',
            phone AS 'Số điện thoại',
            email AS 'Email',
            id_card AS 'CCCD/CMND',
            address AS 'Địa chỉ',
            created_at AS 'Ngày tạo'
        FROM guests
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def get_bookings():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT
            b.id AS 'ID',
            r.room_number AS 'Số phòng',
            r.room_type AS 'Loại phòng',
            g.full_name AS 'Khách hàng',
            g.phone AS 'Số điện thoại',
            b.check_in AS 'Ngày nhận',
            b.check_out AS 'Ngày trả',
            b.adults AS 'Người lớn',
            b.children AS 'Trẻ em',
            b.booking_status AS 'Trạng thái',
            b.total_amount AS 'Tổng tiền',
            b.note AS 'Ghi chú'
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN guests g ON b.guest_id = g.id
        ORDER BY b.id DESC
    """, conn)

    conn.close()
    return df


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    st.title("🏨 Dashboard quản lý khách sạn")
    st.caption("Hệ thống quản lý phòng và lưu trú khách sạn")

    conn = get_connection()

    total_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms"
    ).fetchone()[0]

    empty_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms WHERE status = 'Trống'"
    ).fetchone()[0]

    occupied_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms WHERE status = 'Đang ở'"
    ).fetchone()[0]

    cleaning_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms WHERE status = 'Đang dọn'"
    ).fetchone()[0]

    maintenance_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms WHERE status = 'Bảo trì'"
    ).fetchone()[0]

    total_guests = conn.execute(
        "SELECT COUNT(*) FROM guests"
    ).fetchone()[0]

    active_bookings = conn.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE booking_status = 'Đang ở'
    """).fetchone()[0]

    revenue = conn.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM bookings
        WHERE booking_status IN ('Đang ở', 'Đã trả phòng')
    """).fetchone()[0]

    conn.close()

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🏨 Tổng số phòng",
            total_rooms
        )

    with col2:
        st.metric(
            "🟢 Phòng trống",
            empty_rooms
        )

    with col3:
        st.metric(
            "🔴 Đang có khách",
            occupied_rooms
        )

    with col4:
        st.metric(
            "👥 Khách hàng",
            total_guests
        )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🧹 Đang dọn", cleaning_rooms)

    with col2:
        st.metric("🔧 Bảo trì", maintenance_rooms)

    with col3:
        st.metric("📋 Đang lưu trú", active_bookings)

    with col4:
        st.metric("💰 Doanh thu", money(revenue))

    st.divider()

    # --------------------------------------------------------
    # TRẠNG THÁI PHÒNG
    # --------------------------------------------------------

    st.subheader("📊 Tình trạng phòng")

    room_status = pd.DataFrame({
        "Trạng thái": [
            "Trống",
            "Đang ở",
            "Đang dọn",
            "Bảo trì"
        ],
        "Số lượng": [
            empty_rooms,
            occupied_rooms,
            cleaning_rooms,
            maintenance_rooms
        ]
    })

    st.bar_chart(
        room_status.set_index("Trạng thái")
    )

    # --------------------------------------------------------
    # PHÒNG HIỆN TẠI
    # --------------------------------------------------------

    st.subheader("🛏️ Danh sách phòng")

    rooms = get_rooms()

    if not rooms.empty:

        def status_icon(status):
            icons = {
                "Trống": "🟢",
                "Đang ở": "🔴",
                "Đang dọn": "🟡",
                "Bảo trì": "⚫"
            }
            return f"{icons.get(status, '⚪')} {status}"

        display_rooms = rooms.copy()

        display_rooms["Trạng thái"] = display_rooms[
            "Trạng thái"
        ].apply(status_icon)

        display_rooms["Giá phòng"] = display_rooms[
            "Giá phòng"
        ].apply(money)

        st.dataframe(
            display_rooms,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# QUẢN LÝ PHÒNG
# ============================================================

def room_management():

    st.title("🛏️ Quản lý phòng")

    tab1, tab2, tab3 = st.tabs([
        "📋 Danh sách phòng",
        "➕ Thêm phòng",
        "✏️ Cập nhật phòng"
    ])

    # --------------------------------------------------------
    # DANH SÁCH
    # --------------------------------------------------------

    with tab1:

        rooms = get_rooms()

        col1, col2 = st.columns(2)

        with col1:
            search = st.text_input(
                "🔎 Tìm phòng",
                placeholder="Nhập số phòng..."
            )

        with col2:
            status_filter = st.selectbox(
                "Lọc trạng thái",
                [
                    "Tất cả",
                    "Trống",
                    "Đang ở",
                    "Đang dọn",
                    "Bảo trì"
                ]
            )

        filtered = rooms.copy()

        if search:
            filtered = filtered[
                filtered["Số phòng"]
                .astype(str)
                .str.contains(search, case=False)
            ]

        if status_filter != "Tất cả":
            filtered = filtered[
                filtered["Trạng thái"] == status_filter
            ]

        if not filtered.empty:
            filtered["Giá phòng"] = filtered[
                "Giá phòng"
            ].apply(money)

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # THÊM PHÒNG
    # --------------------------------------------------------

    with tab2:

        with st.form("add_room_form"):

            st.subheader("Thêm phòng mới")

            col1, col2, col3 = st.columns(3)

            with col1:
                room_number = st.text_input(
                    "Số phòng *"
                )

            with col2:
                room_type = st.selectbox(
                    "Loại phòng",
                    [
                        "Standard",
                        "Deluxe",
                        "Suite",
                        "VIP"
                    ]
                )

            with col3:
                floor = st.number_input(
                    "Tầng",
                    min_value=1,
                    max_value=100,
                    value=1
                )

            col1, col2 = st.columns(2)

            with col1:
                price = st.number_input(
                    "Giá phòng / đêm",
                    min_value=0,
                    value=500000,
                    step=50000
                )

            with col2:
                status = st.selectbox(
                    "Trạng thái",
                    [
                        "Trống",
                        "Đang ở",
                        "Đang dọn",
                        "Bảo trì"
                    ]
                )

            note = st.text_area("Ghi chú")

            submitted = st.form_submit_button(
                "➕ Thêm phòng",
                use_container_width=True
            )

            if submitted:

                if not room_number.strip():
                    st.error("Vui lòng nhập số phòng.")

                else:

                    try:
                        conn = get_connection()

                        conn.execute("""
                            INSERT INTO rooms
                            (
                                room_number,
                                room_type,
                                floor,
                                price,
                                status,
                                note
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            room_number.strip(),
                            room_type,
                            floor,
                            price,
                            status,
                            note
                        ))

                        conn.commit()
                        conn.close()

                        st.success(
                            f"Đã thêm phòng {room_number}."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error(
                            "Số phòng này đã tồn tại."
                        )

    # --------------------------------------------------------
    # CẬP NHẬT
    # --------------------------------------------------------

    with tab3:

        rooms_list = get_room_list()

        if not rooms_list:

            st.info("Chưa có phòng.")

        else:

            room_options = {
                f"{r['room_number']} - {r['room_type']}": r["id"]
                for r in rooms_list
            }

            selected_room = st.selectbox(
                "Chọn phòng",
                list(room_options.keys())
            )

            room_id = room_options[selected_room]

            conn = get_connection()

            room = conn.execute("""
                SELECT *
                FROM rooms
                WHERE id = ?
            """, (room_id,)).fetchone()

            conn.close()

            with st.form("edit_room_form"):

                col1, col2 = st.columns(2)

                with col1:

                    new_number = st.text_input(
                        "Số phòng",
                        value=room["room_number"]
                    )

                    new_type = st.selectbox(
                        "Loại phòng",
                        [
                            "Standard",
                            "Deluxe",
                            "Suite",
                            "VIP"
                        ],
                        index=[
                            "Standard",
                            "Deluxe",
                            "Suite",
                            "VIP"
                        ].index(room["room_type"])
                    )

                    new_floor = st.number_input(
                        "Tầng",
                        min_value=1,
                        max_value=100,
                        value=room["floor"]
                    )

                with col2:

                    new_price = st.number_input(
                        "Giá phòng",
                        min_value=0,
                        value=float(room["price"]),
                        step=50000.0
                    )

                    new_status = st.selectbox(
                        "Trạng thái",
                        [
                            "Trống",
                            "Đang ở",
                            "Đang dọn",
                            "Bảo trì"
                        ],
                        index=[
                            "Trống",
                            "Đang ở",
                            "Đang dọn",
                            "Bảo trì"
                        ].index(room["status"])
                    )

                    new_note = st.text_area(
                        "Ghi chú",
                        value=room["note"] or ""
                    )

                save = st.form_submit_button(
                    "💾 Lưu thay đổi",
                    use_container_width=True
                )

                if save:

                    conn = get_connection()

                    try:

                        conn.execute("""
                            UPDATE rooms
                            SET
                                room_number = ?,
                                room_type = ?,
                                floor = ?,
                                price = ?,
                                status = ?,
                                note = ?
                            WHERE id = ?
                        """, (
                            new_number,
                            new_type,
                            new_floor,
                            new_price,
                            new_status,
                            new_note,
                            room_id
                        ))

                        conn.commit()

                        st.success(
                            "Đã cập nhật thông tin phòng."
                        )

                    except sqlite3.IntegrityError:

                        st.error(
                            "Số phòng đã tồn tại."
                        )

                    finally:
                        conn.close()

                    st.rerun()

            st.divider()

            st.subheader("⚠️ Xóa phòng")

            confirm_delete = st.checkbox(
                "Tôi xác nhận muốn xóa phòng này."
            )

            if st.button(
                "🗑️ Xóa phòng",
                type="secondary"
            ):

                if not confirm_delete:

                    st.warning(
                        "Vui lòng xác nhận trước khi xóa."
                    )

                else:

                    conn = get_connection()

                    booking_count = conn.execute("""
                        SELECT COUNT(*)
                        FROM bookings
                        WHERE room_id = ?
                    """, (room_id,)).fetchone()[0]

                    if booking_count > 0:

                        st.error(
                            "Không thể xóa phòng đã có lịch sử đặt phòng."
                        )

                    else:

                        conn.execute(
                            "DELETE FROM rooms WHERE id = ?",
                            (room_id,)
                        )

                        conn.commit()

                        st.success(
                            "Đã xóa phòng."
                        )

                        st.rerun()

                    conn.close()


# ============================================================
# KHÁCH HÀNG
# ============================================================

def guest_management():

    st.title("👥 Quản lý khách hàng")

    tab1, tab2 = st.tabs([
        "📋 Danh sách khách",
        "➕ Thêm khách"
    ])

    with tab1:

        guests = get_guests()

        search = st.text_input(
            "🔎 Tìm kiếm khách hàng",
            placeholder="Tên, số điện thoại hoặc CCCD..."
        )

        if search:

            mask = (
                guests["Họ và tên"].astype(str).str.contains(
                    search, case=False, na=False
                )
                |
                guests["Số điện thoại"].astype(str).str.contains(
                    search, case=False, na=False
                )
                |
                guests["CCCD/CMND"].astype(str).str.contains(
                    search, case=False, na=False
                )
            )

            guests = guests[mask]

        st.dataframe(
            guests,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        with st.form("guest_form"):

            st.subheader("Thông tin khách hàng")

            col1, col2 = st.columns(2)

            with col1:

                full_name = st.text_input(
                    "Họ và tên *"
                )

                phone = st.text_input(
                    "Số điện thoại"
                )

                email = st.text_input(
                    "Email"
                )

            with col2:

                id_card = st.text_input(
                    "CCCD / CMND"
                )

                address = st.text_area(
                    "Địa chỉ"
                )

            submit = st.form_submit_button(
                "➕ Thêm khách hàng",
                use_container_width=True
            )

            if submit:

                if not full_name.strip():

                    st.error(
                        "Vui lòng nhập họ và tên."
                    )

                else:

                    conn = get_connection()

                    conn.execute("""
                        INSERT INTO guests
                        (
                            full_name,
                            phone,
                            email,
                            id_card,
                            address,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        full_name,
                        phone,
                        email,
                        id_card,
                        address,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    ))

                    conn.commit()
                    conn.close()

                    st.success(
                        "Đã thêm khách hàng."
                    )

                    st.rerun()


# ============================================================
# ĐẶT PHÒNG
# ============================================================

def booking_management():

    st.title("📋 Quản lý đặt phòng")

    tab1, tab2 = st.tabs([
        "📋 Danh sách đặt phòng",
        "➕ Tạo đặt phòng"
    ])

    # --------------------------------------------------------
    # DANH SÁCH BOOKING
    # --------------------------------------------------------

    with tab1:

        bookings = get_bookings()

        if bookings.empty:

            st.info(
                "Chưa có dữ liệu đặt phòng."
            )

        else:

            status_filter = st.selectbox(
                "Lọc trạng thái",
                [
                    "Tất cả",
                    "Đặt trước",
                    "Đang ở",
                    "Đã trả phòng",
                    "Đã hủy"
                ]
            )

            filtered = bookings.copy()

            if status_filter != "Tất cả":

                filtered = filtered[
                    filtered["Trạng thái"]
                    == status_filter
                ]

            filtered["Tổng tiền"] = filtered[
                "Tổng tiền"
            ].apply(money)

            st.dataframe(
                filtered,
                use_container_width=True,
                hide_index=True
            )

    # --------------------------------------------------------
    # TẠO BOOKING
    # --------------------------------------------------------

    with tab2:

        rooms = get_room_list()

        conn = get_connection()

        guests = conn.execute("""
            SELECT id, full_name, phone
            FROM guests
            ORDER BY full_name
        """).fetchall()

        conn.close()

        available_rooms = [
            r for r in rooms
            if r["status"] == "Trống"
        ]

        if not available_rooms:

            st.warning(
                "Hiện tại không có phòng trống."
            )

        elif not guests:

            st.warning(
                "Chưa có khách hàng. "
                "Vui lòng thêm khách hàng trước."
            )

        else:

            with st.form("booking_form"):

                room_options = {
                    f"Phòng {r['room_number']} - "
                    f"{r['room_type']} - "
                    f"{money(r['price'])}/đêm": r
                    for r in available_rooms
                }

                guest_options = {
                    f"{g['full_name']} - "
                    f"{g['phone']}": g
                    for g in guests
                }

                selected_room_text = st.selectbox(
                    "🛏️ Chọn phòng",
                    list(room_options.keys())
                )

                selected_guest_text = st.selectbox(
                    "👤 Chọn khách hàng",
                    list(guest_options.keys())
                )

                selected_room = room_options[
                    selected_room_text
                ]

                selected_guest = guest_options[
                    selected_guest_text
                ]

                col1, col2 = st.columns(2)

                with col1:

                    check_in = st.date_input(
                        "Ngày nhận phòng",
                        value=date.today()
                    )

                with col2:

                    check_out = st.date_input(
                        "Ngày trả phòng",
                        value=date.today()
                    )

                col1, col2, col3 = st.columns(3)

                with col1:

                    adults = st.number_input(
                        "Người lớn",
                        min_value=1,
                        value=1
                    )

                with col2:

                    children = st.number_input(
                        "Trẻ em",
                        min_value=0,
                        value=0
                    )

                with col3:

                    booking_status = st.selectbox(
                        "Trạng thái",
                        [
                            "Đang ở",
                            "Đặt trước"
                        ]
                    )

                note = st.text_area(
                    "Ghi chú"
                )

                # Tính tiền
                nights = (
                    check_out - check_in
                ).days

                if nights <= 0:
                    nights = 1

                total = selected_room["price"] * nights

                st.info(
                    f"💰 Số đêm: **{nights}** | "
                    f"Tổng tiền dự kiến: "
                    f"**{money(total)}**"
                )

                submit = st.form_submit_button(
                    "✅ Tạo đặt phòng",
                    use_container_width=True
                )

                if submit:

                    if check_out <= check_in:

                        st.error(
                            "Ngày trả phòng phải sau ngày nhận phòng."
                        )

                    else:

                        conn = get_connection()

                        conn.execute("""
                            INSERT INTO bookings
                            (
                                room_id,
                                guest_id,
                                check_in,
                                check_out,
                                adults,
                                children,
                                booking_status,
                                total_amount,
                                note,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            selected_room["id"],
                            selected_guest["id"],
                            check_in.isoformat(),
                            check_out.isoformat(),
                            adults,
                            children,
                            booking_status,
                            total,
                            note,
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        ))

                        # Nếu đang ở thì chuyển phòng sang Đang ở
                        if booking_status == "Đang ở":

                            conn.execute("""
                                UPDATE rooms
                                SET status = 'Đang ở'
                                WHERE id = ?
                            """, (
                                selected_room["id"],
                            ))

                        conn.commit()
                        conn.close()

                        st.success(
                            "Đã tạo đặt phòng thành công."
                        )

                        st.rerun()


# ============================================================
# CHECK-IN / CHECK-OUT
# ============================================================

def checkin_checkout():

    st.title("🔄 Nhận phòng / Trả phòng")

    conn = get_connection()

    active_bookings = conn.execute("""
        SELECT
            b.id,
            r.room_number,
            g.full_name,
            b.check_in,
            b.check_out,
            b.total_amount,
            b.booking_status
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN guests g ON b.guest_id = g.id
        WHERE b.booking_status IN ('Đặt trước', 'Đang ở')
        ORDER BY b.id DESC
    """).fetchall()

    conn.close()

    if not active_bookings:

        st.info(
            "Không có lượt đặt phòng đang hoạt động."
        )

        return

    booking_options = {
        f"#{b['id']} - Phòng {b['room_number']} - "
        f"{b['full_name']} - {b['booking_status']}":
        b["id"]
        for b in active_bookings
    }

    selected_text = st.selectbox(
        "Chọn đặt phòng",
        list(booking_options.keys())
    )

    booking_id = booking_options[selected_text]

    selected = next(
        b for b in active_bookings
        if b["id"] == booking_id
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Phòng",
            selected["room_number"]
        )

    with col2:
        st.metric(
            "Khách",
            selected["full_name"]
        )

    with col3:
        st.metric(
            "Tổng tiền",
            money(selected["total_amount"])
        )

    st.write(
        f"**Nhận phòng:** {selected['check_in']}"
    )

    st.write(
        f"**Trả phòng dự kiến:** {selected['check_out']}"
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🔑 Xác nhận nhận phòng",
            use_container_width=True
        ):

            conn = get_connection()

            conn.execute("""
                UPDATE bookings
                SET booking_status = 'Đang ở'
                WHERE id = ?
            """, (booking_id,))

            room_id = conn.execute("""
                SELECT room_id
                FROM bookings
                WHERE id = ?
            """, (booking_id,)).fetchone()[0]

            conn.execute("""
                UPDATE rooms
                SET status = 'Đang ở'
                WHERE id = ?
            """, (room_id,))

            conn.commit()
            conn.close()

            st.success(
                "Đã xác nhận nhận phòng."
            )

            st.rerun()

    with col2:

        if st.button(
            "🚪 Xác nhận trả phòng",
            use_container_width=True
        ):

            conn = get_connection()

            conn.execute("""
                UPDATE bookings
                SET booking_status = 'Đã trả phòng'
                WHERE id = ?
            """, (booking_id,))

            room_id = conn.execute("""
                SELECT room_id
                FROM bookings
                WHERE id = ?
            """, (booking_id,)).fetchone()[0]

            conn.execute("""
                UPDATE rooms
                SET status = 'Đang dọn'
                WHERE id = ?
            """, (room_id,))

            conn.commit()
            conn.close()

            st.success(
                "Đã trả phòng. "
                "Phòng được chuyển sang trạng thái Đang dọn."
            )

            st.rerun()


# ============================================================
# BÁO CÁO
# ============================================================

def reports():

    st.title("📊 Báo cáo & thống kê")

    conn = get_connection()

    bookings = pd.read_sql_query("""
        SELECT
            b.id,
            r.room_number,
            r.room_type,
            g.full_name,
            b.check_in,
            b.check_out,
            b.booking_status,
            b.total_amount
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN guests g ON b.guest_id = g.id
    """, conn)

    conn.close()

    if bookings.empty:

        st.info(
            "Chưa có dữ liệu để thống kê."
        )

        return

    # --------------------------------------------------------
    # DOANH THU
    # --------------------------------------------------------

    total_revenue = bookings[
        bookings["booking_status"].isin(
            ["Đang ở", "Đã trả phòng"]
        )
    ]["total_amount"].sum()

    completed_revenue = bookings[
        bookings["booking_status"] == "Đã trả phòng"
    ]["total_amount"].sum()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "💰 Tổng doanh thu",
            money(total_revenue)
        )

    with col2:
        st.metric(
            "💵 Doanh thu đã hoàn tất",
            money(completed_revenue)
        )

    with col3:
        st.metric(
            "📋 Tổng lượt đặt phòng",
            len(bookings)
        )

    st.divider()

    # --------------------------------------------------------
    # TRẠNG THÁI BOOKING
    # --------------------------------------------------------

    st.subheader("📋 Trạng thái đặt phòng")

    status_data = (
        bookings["booking_status"]
        .value_counts()
        .rename_axis("Trạng thái")
        .reset_index(name="Số lượng")
    )

    st.bar_chart(
        status_data.set_index("Trạng thái")
    )

    # --------------------------------------------------------
    # DOANH THU THEO LOẠI PHÒNG
    # --------------------------------------------------------

    st.subheader("💰 Doanh thu theo loại phòng")

    revenue_by_type = bookings.groupby(
        "room_type"
    )["total_amount"].sum().reset_index()

    revenue_by_type.columns = [
        "Loại phòng",
        "Doanh thu"
    ]

    st.bar_chart(
        revenue_by_type.set_index("Loại phòng")
    )

    # --------------------------------------------------------
    # BẢNG CHI TIẾT
    # --------------------------------------------------------

    st.subheader("📑 Chi tiết doanh thu")

    detail = bookings.copy()

    detail["total_amount"] = detail[
        "total_amount"
    ].apply(money)

    detail = detail.rename(columns={
        "room_number": "Số phòng",
        "room_type": "Loại phòng",
        "full_name": "Khách hàng",
        "check_in": "Ngày nhận",
        "check_out": "Ngày trả",
        "booking_status": "Trạng thái",
        "total_amount": "Tổng tiền"
    })

    st.dataframe(
        detail,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    st.sidebar.title("🏨 HOTEL MANAGER")

    st.sidebar.caption(
        "Hệ thống quản lý khách sạn"
    )

    st.sidebar.divider()

    menu = st.sidebar.radio(
        "MENU",
        [
            "📊 Dashboard",
            "🛏️ Quản lý phòng",
            "👥 Khách hàng",
            "📋 Đặt phòng",
            "🔄 Nhận / Trả phòng",
            "📈 Báo cáo"
        ]
    )

    st.sidebar.divider()

    st.sidebar.info(
        "💡 Database sử dụng SQLite\n\n"
        "Dữ liệu được lưu tự động trong "
        "`hotel.db`."
    )

    return menu


# ============================================================
# MAIN
# ============================================================

def main():

    init_database()

    menu = sidebar()

    if menu == "📊 Dashboard":
        dashboard()

    elif menu == "🛏️ Quản lý phòng":
        room_management()

    elif menu == "👥 Khách hàng":
        guest_management()

    elif menu == "📋 Đặt phòng":
        booking_management()

    elif menu == "🔄 Nhận / Trả phòng":
        checkin_checkout()

    elif menu == "📈 Báo cáo":
        reports()


if __name__ == "__main__":
    main()
