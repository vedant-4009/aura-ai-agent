from app.tools.files import list_files, read_file
from app.tools.github import github_user
from app.tools.web import fetch_webpage


def get_tools():
    """
    Register all tools available to AURA.
    """

    return {
        "github": github_user,
        "web": fetch_webpage,
        "files": list_files,
    }