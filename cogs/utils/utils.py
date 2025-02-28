import logging

logger = logging.getLogger("disnake")

class MusicUtils:
    @staticmethod
    def parse_playlist(file_path):
        """
        Parses a custom playlist file with sections, URLs, and descriptions.

        The file should be formatted as follows:
        - Each section should be enclosed in square brackets (e.g., [Section Name]).
        - Each line within a section should contain a URL, optionally followed by a
          semicolon and a description (e.g., https://example.com; This is a description).
        - Lines starting with '#' or empty lines are ignored.

        Args:
            file_path (str): The path to the playlist file.

        Returns:
            dict: A dictionary where keys are section names and values are lists of
                  dictionaries, each containing 'url' and 'description' keys.
        """
        playlist = {}
        current_section = None

        try:
            with open(file_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue

                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        playlist[current_section] = []
                    else:
                        if ';' in line:
                            url, description = line.split(';', 1)
                        else:
                            url, description = line, ''

                        playlist[current_section].append({
                            'url': url.strip(),
                            'description': description.strip()
                        })

            return playlist
        except FileNotFoundError:
            logger.error(f"Playlist file not found: {file_path}")
            return {}
        except Exception as e:
            logger.exception(f"Error parsing playlist file: {file_path}")
            return {}

def setup(bot):
    pass
