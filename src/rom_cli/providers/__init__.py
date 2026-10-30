"""Registro unificado dos provedores disponíveis."""

from rom_cli.providers.dlarchive import DlArchiveProvider
from rom_cli.providers.romsgames import RomsGamesProvider
from rom_cli.providers.nopaystation import NoPayStationProvider
from rom_cli.providers.dlpsgame import DlpsGameProvider
from rom_cli.providers.archive_org import ArchiveOrgProvider
from rom_cli.providers.myrient import MyrientProvider

DLA = DlArchiveProvider()
ROMSGAMES = RomsGamesProvider()
NPS = NoPayStationProvider()
DLP = DlpsGameProvider()
ARCHIVE_ORG = ArchiveOrgProvider()
MYRIENT = MyrientProvider()

SOURCES = {
    "dlarchive": DLA,
    "romsgames": ROMSGAMES,
    "archive.org": ARCHIVE_ORG,
    "nps": NPS,
    "dlpsgame": DLP,
    "myrient": MYRIENT,
}
