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
from datetime import datetime, timezone
from hashlib import sha256
from hmac import new as hmac_new
from io import BufferedReader, BytesIO, SEEK_SET
from mimetypes import guess_type
from pathlib import Path
from typing import Dict
from urllib.parse import urlencode, urlparse

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
    STREAMABLE_API_URL,
    STREAMABLE_AWS_BUCKET_URL,
    STREAMABLE_AWS_VIDEO_UPLOAD_ENDPOINT,
    STREAMABLE_GENERATE_SHORTCODE_ENDPOINT,
    STREAMABLE_REACT_VERSION,
    STREAMABLE_TRANSCODE_VIDEO_ENDPOINT,
    STREAMABLE_UPLOAD_MAX_SIZE,
    STREAMABLE_URL,
    STREAMABLE_VIDEO_ENDPOINT,
    STREAMFF_GENERATE_LINK_ENDPOINT,
    STREAMFF_UPLOAD_MAX_SIZE,
    STREAMFF_URL,
    STREAMFF_VIDEO_ENDPOINT,
    STREAMJA_GENERATE_SHORT_ID_ENDPOINT,
    STREAMJA_UPLOAD_ENDPOINT,
    STREAMJA_UPLOAD_MAX_SIZE,
    STREAMJA_URL,
)
from .model import (
    JustStreamLiveVideo,
    JustStreamLiveUploadData,
    MixtureVideo,
    MixtureUploadData,
    StreamableAWSCredential,
    StreamableUploadCredential,
    StreamableUploadData,
    StreamableVideo,
    StreamffUploadData,
    StreamffVideo,
    StreamjaUploadData,
    StreamjaVideo,
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

    @staticmethod
    def __aws_api_signing_key(
        key_secret: str,
        datestamp: str,
        region: str,
        service: str,
    ):
        key_date = Client.__hmac_sha256_sign(
            f"AWS4{key_secret}".encode("utf8"),
            datestamp,
        )
        key_region = Client.__hmac_sha256_sign(key_date, region)
        key_service = Client.__hmac_sha256_sign(key_region, service)
        key_signing = Client.__hmac_sha256_sign(key_service, "aws4_request")
        return key_signing

    @staticmethod
    def __hmac_sha256_sign(key: bytes, msg: str):
        return hmac_new(key, msg.encode("utf8"), digestmod=sha256).digest()

    @staticmethod
    def __streamable_aws_authorization(
        method: str,
        headers: Dict[str, str],
        req_time: datetime,
        credential: StreamableAWSCredential,
        uri: str,
        query: Dict[str, str],
        region: str,
        service: str = "s3",
    ):
        method = method.upper()
        assert method in (
            "CONNECT",
            "DELETE",
            "GET",
            "HEAD",
            "OPTIONS",
            "PATCH",
            "POST",
            "PUT",
            "TRACE",
        ), "Invalid HTTP method specified!"

        headers_dict = {}
        query_dict = {}

        for hk, hv in dict(sorted(headers.items())).items():
            headers_dict[hk.lower()] = hv.strip()

        assert "x-amz-content-sha256" in headers_dict, \
            "Must specify Content SHA256 for AWS request"

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = "/".join([
            req_time.strftime("%Y%m%d"),
            region,
            service,
            "aws4_request",
        ])
        signed_headers = ";".join(headers_dict.keys())

        for qk, qv in dict(sorted(query.items())).items():
            query_dict[urlencode(qk)] = urlencode(qv)

        signature = hmac_new(
            Client.__aws_api_signing_key(
                credential.secretAccessKey,
                req_time.strftime("%Y%m%d"),
                region,
                service,
            ),
            "\n".join((
                algorithm,
                req_time.strftime("%Y%m%dT%H%M%SZ"),
                credential_scope,
                sha256(
                    "\n".join((
                        method,
                        uri,
                        "&".join([f"{qk}:{qv}"
                                  for qk, qv
                                  in query_dict.items()]),
                        "".join([f"{hk}:{hv}\n"
                                for hk, hv
                                in headers_dict.items()]),
                        signed_headers,
                        headers_dict["x-amz-content-sha256"],
                    )).encode("utf8")
                ).hexdigest(),
            )).encode("utf8"),
            digestmod=sha256,
        ).hexdigest()

        return (
            f"{algorithm} Credential={credential.accessKeyId}/" +
            f"{credential_scope}, SignedHeaders={signed_headers}, Signature=" +
            signature
        )

    async def __generate_mixture_link_id(self):
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

    async def __generate_streamable_shortcode(self, filesize: int):
        res = await self.__session.get(
            f"{STREAMABLE_API_URL}/{STREAMABLE_GENERATE_SHORTCODE_ENDPOINT}",
            params={
                "version": STREAMABLE_REACT_VERSION,
                "size": filesize,
            },
        )
        res.raise_for_status()

        return StreamableUploadCredential(**(await res.json()))

    async def __generate_streamff_link(self):
        res = await self.__session.post(
            f"{STREAMFF_URL}/{STREAMFF_GENERATE_LINK_ENDPOINT}"
        )
        res.raise_for_status()

        return await res.text()

    async def __generate_streamja_short_id(self) -> str:
        form_data = FormData()
        form_data.add_field("new", "1")

        res = await self.__session.post(
            f"{STREAMJA_URL}/{STREAMJA_GENERATE_SHORT_ID_ENDPOINT}",
            data=form_data,
        )
        res.raise_for_status()

        assert "error" not in (res_json := await res.json()), (
            "Error occurred while generating Streamja short ID\n" +
            f"Error: {res_json['error']}"
        )

        return (await res.json())["shortId"]

    async def __transcode_streamable_video(
        self,
        shortcode: str,
        transcoder_token: str,
        upload_data: StreamableUploadData,
    ):
        return await self.__session.post(
            "/".join((
                STREAMABLE_API_URL,
                STREAMABLE_TRANSCODE_VIDEO_ENDPOINT.format(
                    shortcode=shortcode,
                ),
            )),
            json={
                "shortcode": shortcode,
                "size": upload_data.filesize,
                "token": transcoder_token,
                "upload_source": "web",
                "url": "/".join((
                    STREAMABLE_AWS_BUCKET_URL,
                    STREAMABLE_AWS_VIDEO_UPLOAD_ENDPOINT.format(
                        shortcode=shortcode,
                    ),
                )),
            },
        )

    async def __update_streamable_upload_metadata(
        self,
        shortcode: str,
        upload_data: StreamableUploadData,
    ):
        return await self.__session.put(
            "/".join((
                STREAMABLE_API_URL,
                STREAMABLE_VIDEO_ENDPOINT.format(shortcode=shortcode),
            )),
            json={
                "original_name": upload_data.filename,
                "original_size": upload_data.filesize,
                "title": (
                    Path(upload_data.filename).stem
                    if upload_data.title is None
                    else upload_data.title
                ),
                "upload_source": "web",
            },
            params={"purge": ""},
        )

    def clear_mixture_cookies(self):
        self.__session.cookie_jar.clear_domain("mixture.com")

    def clear_streamable_cookies(self):
        self.__session.cookie_jar.clear_domain("streamable.com")

    def clear_streamja_cookies(self):
        self.__session.cookie_jar.clear_domain("streamja.com")

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

    async def get_streamable_video_stream(self, video_id: str):
        vid_src = await self.get_streamff_video_url(video_id)

        res = await self.__session.get(vid_src)
        res.raise_for_status()

        return res.content

    async def get_streamable_video_url(self, video_id: str):
        res = await self.__session.get(f"{STREAMABLE_URL}/{video_id}")
        res.raise_for_status()

        tag = BeautifulSoup(
            await res.text(),
            features="html.parser",
        ).find(
            "meta",
            attrs={"property": "og:video:secure_url"},
        )

        assert isinstance(tag, Tag), "Streamable video link not found!"
        vid_url = tag["content"]
        assert isinstance(vid_url, str), "Unexpected video link type!"
        return vid_url

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

    async def is_streamable_video_available(self, video_id: str):
        return (await self.__session.get(f"{STREAMABLE_URL}/{video_id}")).ok

    async def is_streamable_video_processing(self, video_id: str):
        res = await self.__session.get(f"{STREAMABLE_URL}/{video_id}")
        res.raise_for_status()

        tag = BeautifulSoup(
            await res.text(),
            features="html.parser",
        ).find(
            "vid",
            attrs={"id": "player-content"},
        )

        return tag is None

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
                                       upload_data: JustStreamLiveUploadData):
        assert upload_data.filename.endswith((".mkv", ".mp4")), \
            "JustStreamLive supports MKV/MP4 files only!"

        assert upload_data.filesize <= JUSTSTREAMLIVE_UPLOAD_MAX_SIZE, \
            "JustStreamLive supports " + \
            f"{JUSTSTREAMLIVE_UPLOAD_MAX_SIZE / 0x100000}MB maximum!"

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

        return JustStreamLiveVideo(**res_json)

    async def upload_to_mixture(self, upload_data: MixtureUploadData):
        assert upload_data.filename.endswith(".mp4"), \
            "Mixture supports MP4 files only!"

        assert upload_data.filesize <= MIXTURE_UPLOAD_MAX_SIZE, \
            "Mixture supports " + \
            f"{MIXTURE_UPLOAD_MAX_SIZE / 0x100000}MB maximum!"

        link_id = await self.__generate_mixture_link_id()

        form_data = FormData()
        form_data.add_field(
            "upload_file",
            upload_data.stream,
            content_type=guess_type(upload_data.filename)[0],
            filename=upload_data.filename,
        )
        form_data.add_field("link_id", link_id)

        res = await self.__session.post(
            f"{MIXTURE_URL}/{MIXTURE_UPLOAD_ENDPOINT}",
            data=form_data,
        )
        res.raise_for_status()

        return MixtureVideo(link_id=link_id)

    async def upload_to_streamable(self, upload_data: StreamableUploadData):
        assert upload_data.filename.endswith((".mkv", ".mp4")), \
            "Streamable supports MKV/MP4 files only!"

        assert upload_data.filesize <= STREAMABLE_UPLOAD_MAX_SIZE, \
            "Streamable supports " + \
            f"{STREAMABLE_UPLOAD_MAX_SIZE / 0x100000}MB maximum!"

        upload_creds = await self.__generate_streamable_shortcode(
            upload_data.filesize,
        )

        res = await self.__update_streamable_upload_metadata(
            upload_creds.shortcode,
            upload_data,
        )
        res.raise_for_status()

        req_datetime = datetime.now(tz=timezone.utc)

        headers = {
            "Host": urlparse(STREAMABLE_AWS_BUCKET_URL).netloc,
            "Content-Type": "application/octet-stream",
            "X-AMZ-ACL": "public-read",
            "X-AMZ-Content-SHA256": "UNSIGNED-PAYLOAD",
            "X-AMZ-Security-Token": upload_creds.credentials.sessionToken,
            "X-AMZ-Date": req_datetime.strftime("%Y%m%dT%H%M%SZ"),
        }

        if isinstance(upload_data.stream, (BufferedReader, BytesIO)):
            hash = sha256()
            upload_data.stream.seek(0, SEEK_SET)

            while (len(chunk := upload_data.stream.read(4096)) > 0):
                if len(chunk) > 4096:
                    raise IOError("Got more data than expected!")

                hash.update(chunk)

            upload_data.stream.seek(0, SEEK_SET)
            headers.update({"X-AMZ-Content-SHA256": hash.hexdigest()})

        headers.update({
            "Authorization": Client.__streamable_aws_authorization(
                "PUT",
                headers,
                req_datetime,
                upload_creds.credentials,
                f"/upload/{upload_creds.shortcode}",
                {},
                upload_data.upload_region,
                service="s3",
            ),
        })

        res = await self.__session.put(
            "/".join((
                STREAMABLE_AWS_BUCKET_URL,
                STREAMABLE_AWS_VIDEO_UPLOAD_ENDPOINT.format(
                    shortcode=upload_creds.shortcode,
                ),
            )),
            data=upload_data.stream,
            headers=headers,
        )
        res.raise_for_status()

        res = await self.__transcode_streamable_video(
            upload_creds.shortcode,
            upload_creds.transcoder_options.token,
            upload_data,
        )
        res.raise_for_status()

        return StreamableVideo(shortcode=upload_creds.shortcode)

    async def upload_to_streamff(self, upload_data: StreamffUploadData):
        video_id = await self.__generate_streamff_link()

        assert upload_data.filename.endswith(".mp4"), \
            "Streamff supports MP4 files only!"

        assert upload_data.filesize <= STREAMFF_UPLOAD_MAX_SIZE, \
            "Streamff supports " + \
            f"{STREAMFF_UPLOAD_MAX_SIZE / 0x100000}MB maximum!"

        form_data = FormData()
        form_data.add_field("file", upload_data.stream,
                            content_type=guess_type(upload_data.filename)[0],
                            filename=upload_data.filename)

        res = await self.__session.post(
            f"{STREAMFF_URL}/api/videos/upload/{video_id}",
            data=form_data,
        )
        res.raise_for_status()

        return StreamffVideo(id=video_id)

    async def upload_to_streamja(self, upload_data: StreamjaUploadData):
        short_id = await self.__generate_streamja_short_id()

        assert upload_data.filename.endswith(".mp4"), \
            "Streamja supports MP4 files only!"

        assert upload_data.filesize <= STREAMJA_UPLOAD_MAX_SIZE, \
            "Streamja supports " + \
            f"{STREAMJA_UPLOAD_MAX_SIZE / 0x100000}MB maximum!"

        form_data = FormData()
        form_data.add_field("file", upload_data.stream,
                            content_type=guess_type(upload_data.filename)[0],
                            filename=upload_data.filename)

        res = await self.__session.post(
            f"{STREAMJA_URL}/{STREAMJA_UPLOAD_ENDPOINT}",
            data=form_data,
            params={"shortId": short_id},
        )
        res.raise_for_status()

        assert (await res.json())["status"] == 1, (
            f"Error occurred while uploading to Streamja short ID {short_id}"
        )

        return StreamjaVideo(short_id=short_id)
