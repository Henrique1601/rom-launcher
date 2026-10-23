"""Classe base abstrata para os Provedores de ROMs."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from rom_cli.models import RomItem


class BaseProvider(ABC):
    name: str

    @abstractmethod
    def search(
        self,
        query: str,
        platform_key: Optional[str] = None,
        on_progress=None,
        force: bool = False
    ) -> List[RomItem]:
        """Realiza a busca por termos e retorna uma lista de RomItem."""
        pass

    @abstractmethod
    def resolve(self, item: RomItem) -> Tuple[str, str]:
        """Resolve a URL final direta de download e o nome do arquivo."""
        pass
