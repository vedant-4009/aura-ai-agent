from app.tools.files import list_files, read_file
from app.tools.github import github_user, github_readme
from app.tools.web import fetch_webpage


def get_tools():
    """
    Register all tools available to AURA.
    """

    return {
        "github": github_user,
        "github_readme": github_readme,
        "web": fetch_webpage,
        "files": list_files,
    }