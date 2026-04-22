from decimal import Decimal

from app.models.payment import FeeComponent
from app.models.student import Student
from app.schemas.student import FeeComponentStatus, FeeSummary


COMPONENT_LABELS: dict[FeeComponent, str] = {
    FeeComponent.ADMISSION: "Admission Fee",
    FeeComponent.FIRST_TERM: "First Term Fee",
    FeeComponent.SECOND_TERM: "Second Term Fee",
    FeeComponent.THIRD_TERM: "Third Term Fee",
    FeeComponent.TRANSPORT: "Transport Fee",
    FeeComponent.BOOKS: "Books Fee",
}


def get_component_assessed_values(
    *,
    admission_fee: Decimal,
    first_term_fee: Decimal,
    second_term_fee: Decimal,
    third_term_fee: Decimal,
    transport_fee: Decimal,
    books_fee: Decimal,
    concession_transport: Decimal,
) -> dict[FeeComponent, Decimal]:
    return {
        FeeComponent.ADMISSION: Decimal(admission_fee),
        FeeComponent.FIRST_TERM: Decimal(first_term_fee),
        FeeComponent.SECOND_TERM: Decimal(second_term_fee),
        FeeComponent.THIRD_TERM: Decimal(third_term_fee),
        FeeComponent.TRANSPORT: Decimal(transport_fee) - Decimal(concession_transport),
        FeeComponent.BOOKS: Decimal(books_fee),
    }


def get_component_assessed(student: Student) -> dict[FeeComponent, Decimal]:
    return get_component_assessed_values(
        admission_fee=student.admission_fee,
        first_term_fee=student.first_term_fee,
        second_term_fee=student.second_term_fee,
        third_term_fee=student.third_term_fee,
        transport_fee=student.transport_fee,
        books_fee=student.books_fee,
        concession_transport=student.concession_transport,
    )


def get_component_paid(student: Student) -> dict[FeeComponent, Decimal]:
    paid_map = {component: Decimal("0.00") for component in COMPONENT_LABELS}
    for transaction in student.payment_transactions:
        for allocation in transaction.allocations:
            component = FeeComponent(allocation.component)
            paid_map[component] += Decimal(allocation.amount)
    return paid_map


def build_fee_summary(student: Student) -> FeeSummary:
    assessed_map = get_component_assessed(student)
    paid_map = get_component_paid(student)
    components: list[FeeComponentStatus] = []

    for component, assessed in assessed_map.items():
        paid = paid_map[component]
        balance = max(Decimal("0.00"), assessed - paid)
        components.append(
            FeeComponentStatus(
                component=component,
                label=COMPONENT_LABELS[component],
                assessed=assessed,
                paid=paid,
                balance=balance,
            )
        )

    total_fee = (
        Decimal(student.admission_fee)
        + Decimal(student.first_term_fee)
        + Decimal(student.second_term_fee)
        + Decimal(student.third_term_fee)
        + Decimal(student.transport_fee)
        + Decimal(student.books_fee)
    ).quantize(Decimal("0.01"))
    adjusted_total = max(Decimal("0.00"), total_fee - Decimal(student.concession_transport))
    total_paid = sum((component.paid for component in components), Decimal("0.00")).quantize(Decimal("0.01"))
    total_pending = max(Decimal("0.00"), adjusted_total - total_paid).quantize(Decimal("0.01"))

    return FeeSummary(
        total_fee=total_fee,
        concession_transport=Decimal(student.concession_transport).quantize(Decimal("0.01")),
        adjusted_total=adjusted_total.quantize(Decimal("0.01")),
        total_paid=total_paid,
        total_pending=total_pending,
        components=components,
    )
