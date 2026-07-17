from pathlib import Path

from parser.main import parse_resume


class ParserService:

    def parse(self, file_path: Path) -> dict:
        return parse_resume(str(file_path))


parser_service = ParserService()