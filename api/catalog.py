"""Catálogo ficticio acordado con el generador; no son tickets Jira."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogItem:
    catalog_item: str
    component: str
    method: str
    status_code: int
    data: dict[str, str]


CATALOG = {
    "/api/v1/purchases": CatalogItem("INC-01", "Compras y pagos", "POST", 201,
                                    {"purchase_id": "demo-purchase", "status": "purchased"}),
    "/api/v1/coupons/issue": CatalogItem("INC-02", "QR y canje", "POST", 201,
                                        {"coupon_id": "demo-coupon", "qr_code": "demo-qr", "status": "issued"}),
    "/api/v1/coupons/redeem": CatalogItem("INC-03", "QR y canje", "POST", 200,
                                         {"status": "redeemed"}),
    "/api/v1/platform/status": CatalogItem("INC-04", "Plataforma", "GET", 200,
                                           {"status": "operational"}),
    "/api/v1/merchants": CatalogItem("SR-01", "Comercios", "POST", 201, {"status": "accepted"}),
    "/api/v1/promotions": CatalogItem("SR-02", "Promociones", "POST", 201, {"status": "accepted"}),
    "/api/v1/accounts/recovery": CatalogItem("SR-03", "Cuentas y accesos", "POST", 200,
                                             {"status": "accepted"}),
    "/api/v1/refunds": CatalogItem("SR-04", "Reembolsos", "POST", 200, {"status": "accepted"}),
}
