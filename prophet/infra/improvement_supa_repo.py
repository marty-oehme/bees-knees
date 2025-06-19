from datetime import timezone
from typing import override

from datetime import datetime
from supabase import Client

from prophet.config import SupaConfig
from prophet.domain.improvement import Improvement
from prophet.domain.improvement_repo import IImprovementRepo
from prophet.domain.original import Original


class ImprovementSupaRepo(IImprovementRepo):
    config: SupaConfig
    client: Client

    def __init__(self, config: SupaConfig | None = None) -> None:
        self.config = config if config else SupaConfig.from_env()
        self.client = Client(self.config.URL, self.config.KEY)
        try:
            _ = self.client.table(self.config.TABLE).select("*").limit(1)
        except Exception as e:
            print(e)

    @override
    def add(self, improvement: Improvement) -> None:
        _ = (
            self.client.table(self.config.TABLE)
            .insert(self._to_tbl_row(improvement))
            .execute()
        )

    @override
    def add_all(self, improvements: list[Improvement]) -> None:
        _ = (
            self.client.table(self.config.TABLE)
            .insert([self._to_tbl_row(i) for i in improvements])
            .execute()
        )

    @override
    def get(self, id: str) -> Improvement:
        return self._from_tbl_row(
            self.client.table(self.config.TABLE)
            .select("*")
            .eq("uuid", id)
            .execute()
            .data[0]
        )

    @override
    def get_all(self) -> list[Improvement]:
        return [
            self._from_tbl_row(row)
            for row in self.client.table(self.config.TABLE)
            .select("*")
            .order("date_orig_ts", desc=True)
            .execute()
            .data
        ]

    def _to_tbl_row(self, imp: Improvement) -> dict[str, str | int]:
        return {
            "uuid": imp.id,
            "title": imp.title,
            "summary": imp.summary,
            "title_orig": imp.original.title,
            "summary_orig": imp.original.summary,
            "link_orig": imp.original.link,
            "image_link_orig": imp.original.image_link or "",
            "date_orig_ts": int(imp.original.date.astimezone(timezone.utc).timestamp()),
        }

    def _from_tbl_row(self, row: dict[str, str | int]) -> Improvement:
        return Improvement(
            id=str(row["uuid"]),
            title=str(row["title"]),
            summary=str(row["summary"]),
            original=Original(
                title=str(row["title_orig"]),
                summary=str(row["summary_orig"]),
                link=str(row["link_orig"]),
                date=datetime.fromtimestamp(int(row["date_orig_ts"]), tz=timezone.utc),
                image_link=str(row["image_link_orig"]),
            ),
        )


if __name__ == "__main__":
    # response = supabase.table("improvements").select("*").execute()
    repo = ImprovementSupaRepo()

    # from prophet.app import grab_latest_originals
    # latest = grab_latest_originals()
    # print("LATEST", latest)

    # improvements = [
    #     Improvement(
    #         title=f"{o.title} but cool",
    #         summary=f"{o.summary} but really cool",
    #         original=o,
    #     )
    #     for o in latest
    # ]
    # repo.add_all(improvements)
    # print(repo.get_all())
    # print(repo.get("6587d90e-952b-4866-85cc-836cebafcca2"))
