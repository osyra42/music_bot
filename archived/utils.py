import logging

logger = logging.getLogger("disnake")

class MusicUtils:
    @staticmethod
    def parse_playlist(file_path):
        """Parses a custom playlist file with sections, URLs, and descriptions."""
        playlist = {}
        current_section = None

        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                # Ignore comments and empty lines
                if line.startswith('#') or not line:
                    continue
                # Check for section headers
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    playlist[current_section] = []
                else:
                    # Split URL and description (if description exists)
                    if ';' in line:
                        url, description = line.split(';', 1)
                    else:
                        url, description = line, ''  # No description provided
                    # Add to the current section
                    playlist[current_section].append({
                        'url': url.strip(),
                        'description': description.strip()
                    })

        return playlist

def setup(bot):
    pass