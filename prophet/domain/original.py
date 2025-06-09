import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Original:  # BadJoke: Sting
    title: str
    summary: str
    link: str
    date: datetime
    image_link: str | None = None
    id: str = field(init=False)

    def _extract_img(self, s: str) -> tuple[str, str]:  # [img_link, rest of string]
        img: str
        m = re.match(r'<img src="(?P<img>.+?)"', s)
        try:
            img = m.group("img")
        except (IndexError, AttributeError):
            return ("", s)

        if img:
            rest = re.sub(r"<img src=.+?>", "", s)
            return (img, rest)
        return ("", s)

    def __post_init__(self):
        self.id = hashlib.sha256(self.link.encode()).hexdigest()

        extracted = self._extract_img(self.summary)
        if extracted[0]:
            self.image_link = extracted[0]
            self.summary = extracted[1]
