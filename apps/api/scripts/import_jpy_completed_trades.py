import argparse
import csv
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.auth import get_user_by_identifier
from app.services.fx import create_buy_lot, create_sell_transaction

CURRENCY_CODE = "JPY"
MONEY_PATTERN = re.compile(r"[^0-9.\-]")


def parse_args() -> argparse.Namespace:
    """CLI에서 JPY 완료 거래 CSV 경로와 대상 사용자를 읽습니다."""

    parser = argparse.ArgumentParser(
        description="Import already-completed JPY FX rows as buy lots and matching sell transactions."
    )
    parser.add_argument("--login-id", required=True, help="Owner login ID")
    parser.add_argument("--csv", required=True, help="CSV file exported from the spreadsheet")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and build rows, then rollback instead of committing.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Do not compare generated sell KRW/profit with CSV values.",
    )
    return parser.parse_args()


def get_value(row: dict[str, str], *names: str) -> str:
    """여러 후보 컬럼명 중 CSV에 존재하는 첫 번째 값을 반환합니다."""

    for name in names:
        value = row.get(name)
        if value is not None:
            return value.strip()
    return ""


def parse_yy_mm_dd(value: str) -> date:
    """230605 같은 YYMMDD 값을 2023-06-05 날짜로 변환합니다."""

    cleaned = MONEY_PATTERN.sub("", value)
    if len(cleaned) != 6:
        raise ValueError(f"Invalid YYMMDD date: {value}")

    year = 2000 + int(cleaned[:2])
    month = int(cleaned[2:4])
    day = int(cleaned[4:6])
    return date(year, month, day)


def parse_int(value: str) -> int:
    """₩4,999,995 같은 금액 문자열을 정수로 변환합니다."""

    cleaned = MONEY_PATTERN.sub("", value)
    if cleaned in {"", "-", "."}:
        raise ValueError(f"Invalid integer amount: {value}")
    return int(Decimal(cleaned))


def parse_decimal(value: str) -> Decimal:
    """¥934.68 같은 환율/외화 문자열을 Decimal로 변환합니다."""

    cleaned = MONEY_PATTERN.sub("", value)
    if cleaned in {"", "-", "."}:
        raise ValueError(f"Invalid decimal amount: {value}")
    return Decimal(cleaned)


def is_blank_or_total_row(row: dict[str, str]) -> bool:
    """빈 줄이나 시트 하단의 #DIV/! 합계 줄처럼 가져오면 안 되는 행을 거릅니다."""

    buy_date = get_value(row, "매수일", "buy_date")
    sell_date = get_value(row, "매도일", "sell_date")
    return not buy_date or not sell_date or "#DIV" in "".join(row.values())


def import_row(db, *, user, row: dict[str, str], row_number: int, skip_validation: bool) -> tuple[int, int]:
    """CSV 한 행을 JPY 매수 로트와 해당 로트 전량 매도 거래로 저장합니다."""

    buy_date = parse_yy_mm_dd(get_value(row, "매수일", "buy_date"))
    buy_krw_amount = parse_int(get_value(row, "매수원화환전금액", "buy_krw_amount"))
    buy_exchange_rate = parse_decimal(get_value(row, "매수적용환율", "buy_exchange_rate"))
    sell_date = parse_yy_mm_dd(get_value(row, "매도일", "sell_date"))
    sell_exchange_rate = parse_decimal(get_value(row, "매도적용환율", "sell_exchange_rate"))

    buy_lot = create_buy_lot(
        db,
        current_user=user,
        currency_code=CURRENCY_CODE,
        buy_date=buy_date,
        buy_krw_amount=buy_krw_amount,
        buy_exchange_rate=buy_exchange_rate,
    )
    sell_transaction = create_sell_transaction(
        db,
        current_user=user,
        currency_code=CURRENCY_CODE,
        sell_date=sell_date,
        sell_usd_amount=buy_lot.usdAmount,
        sell_exchange_rate=sell_exchange_rate,
        allocation_strategy="manual",
        manual_allocations=[(buy_lot.buyLotId, buy_lot.usdAmount)],
        memo=f"JPY spreadsheet import row {row_number}",
    )

    if not skip_validation:
        expected_sell_krw = get_value(row, "매도원화환전금액", "sell_krw_amount")
        expected_profit = get_value(row, "차익", "profit_krw")
        if expected_sell_krw and sell_transaction.totalSellKrwAmount != parse_int(expected_sell_krw):
            raise ValueError(
                f"row {row_number}: sell KRW mismatch "
                f"csv={parse_int(expected_sell_krw)} generated={sell_transaction.totalSellKrwAmount}"
            )
        if expected_profit and sell_transaction.totalRealProfitKrw != parse_int(expected_profit):
            raise ValueError(
                f"row {row_number}: profit mismatch "
                f"csv={parse_int(expected_profit)} generated={sell_transaction.totalRealProfitKrw}"
            )

    return buy_lot.buyLotId, sell_transaction.sellTransactionId


def main() -> None:
    """CSV 전체를 한 트랜잭션으로 import하고 실패 시 전체 rollback합니다."""

    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    with SessionLocal() as db:
        user = get_user_by_identifier(db, args.login_id)
        if user is None:
            raise SystemExit(f"user not found: {args.login_id}")

        imported_count = 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row_number, row in enumerate(reader, start=2):
                if is_blank_or_total_row(row):
                    continue
                import_row(
                    db,
                    user=user,
                    row=row,
                    row_number=row_number,
                    skip_validation=args.skip_validation,
                )
                imported_count += 1

        if args.dry_run:
            db.rollback()
            print(f"dry-run ok: {imported_count} JPY completed trades validated")
            return

        db.commit()
        print(f"imported: {imported_count} JPY completed trades for {args.login_id}")


if __name__ == "__main__":
    main()
