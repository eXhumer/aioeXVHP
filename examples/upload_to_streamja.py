from asyncio import run, set_event_loop_policy, WindowsSelectorEventLoopPolicy
from os import name as os_name
from pathlib import Path

from aioexvhp.client import Client
from aioexvhp.model import StreamjaUploadData


async def upload_to_streamja(video_path: Path):
    async with Client() as aioexvhp:
        video = await aioexvhp.upload_to_streamja(
            StreamjaUploadData(
                filename=video_path.name,
                filesize=video_path.stat().st_size,
                stream=video_path.open(mode="rb"),
            ),
        )
        print(video.url)


async def main():
    video_path = Path("<PATH-TO-MP4-VIDEO-FILE>")
    await upload_to_streamja(video_path)


if __name__ == "__main__":
    if os_name == "nt":
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    run(main())
