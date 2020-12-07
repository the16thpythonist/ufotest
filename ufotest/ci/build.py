import os
from contextlib import AbstractContextManager

from ufotest.config import Config, get_path
from ufotest.util import AbstractRichOutput, get_repository_name


class BuildRunner(object):

    def __init__(self):
        self.config = Config()


class BuildContext(AbstractContextManager, AbstractRichOutput):

    def __init__(self, repository_url: str, branch_name: str):
        self.repository_url = repository_url
        self.branch = branch_name

        self.config = Config()
        self.path = get_path()
        self.builds_path =

        # derived attributes
        self.repository_name = get_repository_name(repository_url)
        self.repository_path = os.path.join(self.path, self.repository_name)

        # non initialized attributes
        self.start_time = None
        self.end_time = None

    # IMPLEMENT 'AbstractContextManger'

    def __enter__(self):


        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    # IMPLEMENT 'AbstractRichOutput'

    def to_markdown(self) -> str:
        pass

    def to_latex(self) -> str:
        pass

    def to_string(self) -> str:
        pass

    def to_html(self) -> str:
        pass


class BuildReport(AbstractRichOutput):

    def to_markdown(self) -> str:
        pass

    def to_latex(self) -> str:
        pass

    def to_string(self) -> str:
        pass

    def to_html(self) -> str:
        pass


