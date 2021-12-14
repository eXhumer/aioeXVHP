# aioeXVHP - Asynchronous Python Interface for Video Hosting Platforms
# Copyright (C) 2021 - eXhumer

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from mimetypes import guess_type

from aiohttp import ClientSession, FormData
from aiohttp.hdrs import USER_AGENT
from bs4 import BeautifulSoup
from bs4.element import Tag

from . import (
    __default_user_agent__,
    JUSTSTREAMLIVE_API_URL,
    JUSTSTREAMLIVE_UPLOAD_ENDPOINT,
    JUSTSTREAMLIVE_UPLOAD_MAX_SIZE,
    MIXTURE_UPLOAD_ENDPOINT,
    MIXTURE_UPLOAD_MAX_SIZE,
    MIXTURE_URL,
    STREAMFF_GENERATE_LINK_ENDPOINT,
    STREAMFF_UPLOAD_MAX_SIZE,
    STREAMFF_URL,
    STREAMJA_SHORT_ID_ENDPOINT,
    STREAMJA_URL,
    STREAMJA_UPLOAD_ENDPOINT,
    STREAMJA_UPLOAD_MAX_SIZE,
    STREAMFF_VIDEO_ENDPOINT,
)
from .model import (
    JustStreamLiveSuccessfulUploadModel,
    JustStreamLiveUploadModel,
    MixtureSuccessfulUploadModel,
    MixtureUploadModel,
    StreamffUploadModel,
    StreamffSuccessfulUploadModel,
    StreamjaUploadModel,
    StreamjaSuccessfulUploadModel,
)


class Client:
    def __init__(
        self,
        session: ClientSession | None = None,
        user_agent: str | None = None,
    ) -> None:
        if session is None:
            session = ClientSession()

        if USER_AGENT in session.headers and user_agent is not None:
            raise Exception("User Agent specified both in class constructor " +
                            f"({user_agent}) and in specified client " +
                            f"session ({session[USER_AGENT]})!")

        session.headers[USER_AGENT] = (
            __default_user_agent__
            if user_agent is None
            else user_agent
        )

        self.__session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        if not self.__session.closed:
            await self.__session.close()

    async def generate_mixture_link_id(self):
        res = await self.__session.get(MIXTURE_URL)
        res.raise_for_status()

        tag = BeautifulSoup(
            await res.text(),
            features="html.parser",
        ).find(
            "input",
            attrs={
                "type": "hidden",
                "name": "link_id",
                "id": "link_id",
            },
        )

        assert isinstance(tag, Tag), "link_id input tag not found!"
        link_id = tag["value"]
        assert isinstance(link_id, str), "Expected link_id value to be string!"

        return link_id

    async def generate_streamff_link(self):
        res = await self.__session.post(
            f"{STREAMFF_URL}/{STREAMFF_GENERATE_LINK_ENDPOINT}"
        )
        res.raise_for_status()

        return await res.text()

    async def generate_streamja_short_id(self) -> str:
        res = await self.__session.post(
            f"{STREAMJA_URL}/{STREAMJA_SHORT_ID_ENDPOINT}",
            data=FormData(fields=(("new", "1")))
        )
        res.raise_for_status()

        assert "error" not in (res_json := await res.json()), (
            "Error occurred while generating Streamja short ID\n" +
            f"Error: {res_json['error']}"
        )

        return (await res.json())["shortId"]

    async def get_mixture_video_stream(self, video_id: str):
        vid_src = await self.get_mixture_video_url(video_id)

        res = await self.__session.get(vid_src)
        res.raise_for_status()

        return res.content

    async def get_mixture_video_url(self, video_id: str):
        res = await self.__session.get(f"{MIXTURE_URL}/v/{video_id}")
        res.raise_for_status()

        tag = BeautifulSoup(
            res.text,
            features="html.parser",
        ).find("source")

        assert isinstance(tag, Tag), "source tag not found in Mixture " + \
            f"video {video_id}"

        vid_src = tag["src"]

        assert isinstance(vid_src, str)

        return vid_src

    async def get_streamff_video_stream(self, video_id: str):
        vid_src = await self.get_streamff_video_url(video_id)

        res = await self.__session.get(vid_src)
        res.raise_for_status()

        return res.content

    async def get_streamff_video_url(self, video_id: str):
        res = await self.__session.get(
            "/".join((
                STREAMFF_URL,
                STREAMFF_VIDEO_ENDPOINT.format(video_id=video_id),
            )),
        )
        res.raise_for_status()

        return f"{STREAMFF_URL}{(await res.json())['videoLink']}"

    async def get_streamja_video_stream(self, video_id: str):
        vid_src = await self.get_streamja_video_url(video_id)

        res = await self.__session.get(vid_src)
        res.raise_for_status()

        return res.content

    async def get_streamja_video_url(self, video_id: str):
        res = await self.__session.get(f"{STREAMJA_URL}/{video_id}")
        res.raise_for_status()

        tag = BeautifulSoup(
            res.text,
            features="html.parser",
        ).find("source")

        assert isinstance(tag, Tag), "source tag not found in Streamja " + \
            f"video {video_id}"

        vid_src = tag["src"]

        assert isinstance(vid_src, str)

        return vid_src

    async def is_mixture_video_available(self, video_id: str):
        res = await self.__session.get(f"{MIXTURE_URL}/v/{video_id}")
        res.raise_for_status()

        return (
            f"<span style=\"color:#FF0000;\">File {video_id} not found</span>"
        ) not in (await res.text())

    async def is_mixture_video_processing(self, video_id: str):
        res = await self.__session.get(f"{MIXTURE_URL}/v/{video_id}")
        res.raise_for_status()

        return (
            "File upload is in progress. Page will refresh " +
            "automatically after <span id=\"remSeconds\">5</span> " +
            "seconds..."
        ) in (await res.text())

    async def is_streamja_video_available(self, video_id: str):
        return (await self.__session.get(f"{STREAMJA_URL}/{video_id}")).ok

    async def is_streamja_video_processing(self, video_id: str):
        res = await self.__session.get(f"{STREAMJA_URL}/{video_id}")
        res.raise_for_status()

        tag = BeautifulSoup(
            await res.text(),
            features="html.parser",
        ).find(
            "vid",
            attrs={"id": "video_container"},
        )

        return tag is None

    async def upload_to_juststreamlive(self,
                                       upload_data: JustStreamLiveUploadModel):
        assert upload_data.filename.endswith(".mp4"), \
            "JustStreamLive supports MP4 files only!"

        assert upload_data.filesize <= JUSTSTREAMLIVE_UPLOAD_MAX_SIZE, \
            "JustStreamLive supports " + \
            f"{JUSTSTREAMLIVE_UPLOAD_MAX_SIZE / (1024 * 1024)}MB maximum!"

        form_data = FormData()
        form_data.add_field(
            "file",
            upload_data.stream,
            content_type=guess_type(upload_data.filename)[0],
            filename=upload_data.filename,
        )

        res = await self.__session.post(
            f"{JUSTSTREAMLIVE_API_URL}/{JUSTSTREAMLIVE_UPLOAD_ENDPOINT}",
            data=form_data,
        )

        res.raise_for_status()
        res_json = await res.json()
        res.release()

        return JustStreamLiveSuccessfulUploadModel(**res_json)

    async def upload_to_mixture(self, upload_data: MixtureUploadModel):
        assert upload_data.filename.endswith(".mp4"), \
            "Mixture supports MP4 files only!"

        assert upload_data.filesize <= MIXTURE_UPLOAD_MAX_SIZE, \
            "Mixture supports " + \
            f"{MIXTURE_UPLOAD_MAX_SIZE / (1024 * 1024)}MB maximum!"

        form_data = FormData()
        form_data.add_field(
            "upload_file",
            upload_data.stream,
            content_type=guess_type(upload_data.filename)[0],
            filename=upload_data.filename,
        )
        form_data.add_field("link_id", upload_data.link_id)

        res = await self.__session.post(
            f"{MIXTURE_URL}/{MIXTURE_UPLOAD_ENDPOINT}",
            data=form_data,
        )
        res.raise_for_status()

        return MixtureSuccessfulUploadModel(link_id=upload_data.link_id)

    async def upload_to_streamff(self, upload_data: StreamffUploadModel):
        assert upload_data.filename.endswith(".mp4"), \
            "Streamff supports MP4 files only!"

        assert upload_data.filesize <= STREAMFF_UPLOAD_MAX_SIZE, \
            "Streamff supports " + \
            f"{STREAMFF_UPLOAD_MAX_SIZE / (1024 * 1024)}MB maximum!"

        form_data = FormData()
        form_data.add_field("file", upload_data.stream,
                            content_type=guess_type(upload_data.filename)[0],
                            filename=upload_data.filename)

        res = await self.__session.post(
            f"{STREAMFF_URL}/api/videos/upload/{upload_data.id}",
            data=form_data,
        )
        res.raise_for_status()

        return StreamffSuccessfulUploadModel(id=upload_data.id)

    async def upload_to_streamja(self, upload_data: StreamjaUploadModel):
        assert upload_data.filename.endswith(".mp4"), \
            "Streamja supports MP4 files only!"

        assert upload_data.filesize <= STREAMJA_UPLOAD_MAX_SIZE, \
            "Streamja supports " + \
            f"{STREAMJA_UPLOAD_MAX_SIZE / (1024 * 1024)}MB maximum!"

        form_data = FormData()
        form_data.add_field("file", upload_data.stream,
                            content_type=guess_type(upload_data.filename)[0],
                            filename=upload_data.filename)

        res = await self.__session.post(
            f"{STREAMJA_URL}/{STREAMJA_UPLOAD_ENDPOINT}",
            data=form_data,
            params={"shortId": upload_data.short_id},
        )
        res.raise_for_status()

        assert (await res.json())["status"] == 1, (
            "Error occurred while uploading to Streamja short ID " +
            upload_data.short_id
        )

        return StreamjaSuccessfulUploadModel(short_id=upload_data.short_id)
