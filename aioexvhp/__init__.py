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
from pkg_resources import require

__version__ = require(__package__)[0].version
__default_user_agent__ = f"{__package__}/{__version__}"
JUSTSTREAMLIVE_API_URL = "https://api.juststream.live"
JUSTSTREAMLIVE_URL = "https://juststream.live"
MIXTURE_URL = "https://mixture.gg"
STREAMABLE_API_URL = "https://ajax.streamable.com"
STREAMABLE_AWS_BUCKET_URL = "https://streamables-upload.s3.amazonaws.com"
STREAMABLE_URL = "https://streamable.com"
STREAMFF_URL = "https://streamff.com"
STREAMJA_URL = "https://streamja.com"

JUSTSTREAMLIVE_UPLOAD_ENDPOINT = "videos/upload"
MIXTURE_UPLOAD_ENDPOINT = "upload_file.php"
STREAMABLE_AWS_VIDEO_UPLOAD_ENDPOINT = "upload/{shortcode}"
STREAMABLE_GENERATE_SHORTCODE_ENDPOINT = "shortcode"
STREAMABLE_TRANSCODE_VIDEO_ENDPOINT = "transcode/{shortcode}"
STREAMABLE_VIDEO_ENDPOINT = "videos/{shortcode}"
STREAMFF_GENERATE_LINK_ENDPOINT = "api/videos/generate-link"
STREAMFF_VIDEO_ENDPOINT = "api/videos/{video_id}"
STREAMJA_GENERATE_SHORT_ID_ENDPOINT = "shortId.php"
STREAMJA_UPLOAD_ENDPOINT = "upload.php"

JUSTSTREAMLIVE_UPLOAD_MAX_SIZE = 200 * 0x100000
MIXTURE_UPLOAD_MAX_SIZE = 512 * 0x100000
STREAMABLE_UPLOAD_MAX_SIZE = 250 * 0x100000
STREAMFF_UPLOAD_MAX_SIZE = 200 * 0x100000
STREAMJA_UPLOAD_MAX_SIZE = 30 * 0x100000

STREAMABLE_REACT_VERSION = "5a6120a04b6db864113d706cc6a6131cb8ca3587"
