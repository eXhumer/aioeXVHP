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

JUSTSTREAMLIVE_UPLOAD_ENDPOINT = "videos/upload"
MIXTURE_UPLOAD_ENDPOINT = "upload_file.php"

JUSTSTREAMLIVE_UPLOAD_MAX_SIZE = 200 * 1024 * 1024
MIXTURE_UPLOAD_MAX_SIZE = 512 * 1024 * 1024
