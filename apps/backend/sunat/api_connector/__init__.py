"""Official SUNAT API connector for DCFT read-only automation."""

from .credentials import SunatApiCredentials, SunatSolCredentials
from .token_client import SunatApiToken, SunatTokenClient
from .cpe_client import SunatCpeClient
from .sire_sales_client import SunatSireSalesClient
from .sire_purchases_client import SunatSirePurchasesClient
from .discovery import SunatApiDiscovery
from .diagnostics import SunatApiDiagnostics

__all__ = [
    "SunatApiCredentials",
    "SunatSolCredentials",
    "SunatApiToken",
    "SunatTokenClient",
    "SunatCpeClient",
    "SunatSireSalesClient",
    "SunatSirePurchasesClient",
    "SunatApiDiscovery",
    "SunatApiDiagnostics",
]
