from tools.files import list_files

from tools.github import (
    github_user,
    github_readme,
    github_repository,
    github_repository_tree,
    github_repository_tree_recursive,
)

from analyzers.repository import (
    analyze_repository,
    analyze_release_readiness_tool,
)

from tools.web import fetch_webpage


def get_tools():
    return {
        "github": github_user,
        "github_readme": github_readme,
        "github_repository": github_repository,
        "github_repository_tree": github_repository_tree,
        "github_repository_tree_recursive": github_repository_tree_recursive,
        "analyze_repository": analyze_repository,
        "analyze_release_readiness": analyze_release_readiness_tool,
        "web": fetch_webpage,
        "files": list_files,
    }