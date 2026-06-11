from sqlalchemy import BigInteger, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import ActiveMixin, Base, Integer, String, Text, TimestampMixin


class CommonCode(TimestampMixin, ActiveMixin, Base):
    """여러 기능에서 재사용하는 코드값을 한 테이블에서 관리하는 공통코드 모델입니다."""

    __tablename__ = "common_codes"

    # common_codes.common_code_id: 공통코드 row를 식별하는 내부 PK입니다.
    common_code_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # common_codes.code_group: board_type처럼 같은 용도의 코드들을 묶는 그룹명입니다.
    code_group: Mapped[str] = mapped_column(String(50), nullable=False)
    # common_codes.code: API와 다른 테이블에서 참조하는 실제 코드값입니다.
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    # common_codes.code_name: 화면에 표시할 사용자 친화적인 코드 이름입니다.
    code_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # common_codes.description: 운영자가 코드의 쓰임새를 적어두는 설명입니다.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # common_codes.sort_order: 같은 그룹 안에서 화면 노출 순서를 정하는 숫자입니다.
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    __table_args__ = (
        UniqueConstraint("code_group", "code", name="uq_common_codes_group_code"),
        Index("ix_common_codes_group_active_sort", "code_group", "is_active", "sort_order"),
    )
