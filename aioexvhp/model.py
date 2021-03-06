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
from io import BytesIO, BufferedReader
from typing import Optional, Union

from pydantic import BaseModel, HttpUrl, validator
from aiohttp import StreamReader

from . import (
    JUSTSTREAMLIVE_URL,
    MIXTURE_URL,
    STREAMABLE_URL,
    STREAMFF_URL,
    STREAMJA_URL,
)


class JustStreamLiveUploadData(BaseModel):
    filename: str
    filesize: int
    stream: Union[BytesIO, BufferedReader, StreamReader]

    class Config:
        arbitrary_types_allowed = True


class JustStreamLiveVideo(BaseModel):
    id: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"{JUSTSTREAMLIVE_URL}/{values['id']}"


class MixtureUploadData(BaseModel):
    filename: str
    filesize: int
    stream: Union[BytesIO, BufferedReader, StreamReader]

    class Config:
        arbitrary_types_allowed = True


class MixtureVideo(BaseModel):
    link_id: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"{MIXTURE_URL}/v/{values['link_id']}"


class StreamableAWSCredential(BaseModel):
    accessKeyId: str
    secretAccessKey: str
    sessionToken: str


class StreamableTranscoderOptions(BaseModel):
    token: str


class StreamableUploadCredential(BaseModel):
    shortcode: str
    credentials: StreamableAWSCredential
    transcoder_options: StreamableTranscoderOptions


class StreamableUploadData(BaseModel):
    filename: str
    filesize: int
    stream: Union[BytesIO, BufferedReader, StreamReader]
    title: Optional[str] = None
    upload_region: str = "us-east-1"

    class Config:
        arbitrary_types_allowed = True


class StreamableVideo(BaseModel):
    shortcode: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"{STREAMABLE_URL}/{values['shortcode']}"


class StreamffUploadData(BaseModel):
    filename: str
    filesize: int
    stream: Union[BytesIO, BufferedReader, StreamReader]

    class Config:
        arbitrary_types_allowed = True


class StreamffVideo(BaseModel):
    id: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"{STREAMFF_URL}/v/{values['id']}"


class StreamjaUploadData(BaseModel):
    filename: str
    filesize: int
    stream: Union[BytesIO, BufferedReader, StreamReader]

    class Config:
        arbitrary_types_allowed = True


class StreamjaVideo(BaseModel):
    short_id: str
    url: HttpUrl = None
    embed_url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"{STREAMJA_URL}/{values['short_id']}"

    @validator("embed_url", pre=True, always=True)
    def embed_url_validator(cls, v, values, **kwargs):
        return f"{STREAMJA_URL}/embed/{values['short_id']}"
