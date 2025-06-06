"""Download registry information from OntoBee."""

import json
import textwrap
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from bs4 import BeautifulSoup
from pystow.utils import download

from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner, load_processed

__all__ = [
    "OntobeeAligner",
    "get_ontobee",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "ontobee.html"
PROCESSED_PATH = DIRECTORY / "processed.json"

URL = "http://www.ontobee.org/"
LEGEND = {
    "F": "Foundry",
    "L": "Library",
    "N": "Not Specified/No",
}


def get_ontobee(force_download: bool = False) -> dict[str, dict[str, Any]]:
    """Get the OntoBee registry."""
    if PROCESSED_PATH.exists() and not force_download:
        return load_processed(PROCESSED_PATH)

    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as f:
        soup = BeautifulSoup(f, "html.parser")

    ontology_list = soup.find(id="ontologyList")
    if ontology_list is None:
        raise ValueError
    table_body = ontology_list.find("tbody")
    if table_body is None:
        raise ValueError

    rv = {}
    for row in table_body.find_all("tr"):  # type:ignore
        cells = row.find_all("td")
        prefix = cells[1].text
        rv[prefix] = {
            "name": cells[2].text,
            "library": LEGEND[cells[3].text.upper()],
            # "link": cells[1].find("a").attrs["href"],
        }

    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)

    return rv


class OntobeeAligner(Aligner):
    """Aligner for OntoBee xref registry."""

    key = "ontobee"
    getter = get_ontobee
    curation_header: ClassVar[Sequence[str]] = ("name", "url")

    def get_curation_row(self, external_id: str, external_entry: dict[str, Any]) -> Sequence[str]:
        """Return the relevant fields from an OntoBee entry for pretty-printing."""
        return [
            textwrap.shorten(external_entry["name"], 50),
            external_entry.get("url", ""),
        ]


if __name__ == "__main__":
    OntobeeAligner.cli()
